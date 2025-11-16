# Deployment Guide

Complete guide for deploying the MCP Accurate Click Server in various environments.

## Table of Contents

1. [Local Installation](#local-installation)
2. [Docker Deployment](#docker-deployment)
3. [Production Deployment](#production-deployment)
4. [Claude Desktop Integration](#claude-desktop-integration)
5. [Environment Configuration](#environment-configuration)
6. [Scaling and Performance](#scaling-and-performance)

---

## Local Installation

### Quick Start

```bash
# Clone repository
git clone https://github.com/mcp-accurate-click/mcp-accurate-click-server.git
cd mcp-accurate-click-server

# Install (choose one method)
./scripts/install.sh cpu          # CPU version
./scripts/install.sh gpu          # GPU version
./scripts/install.sh dev          # Development version

# Or use Makefile
make install                       # CPU version
make install-gpu                   # GPU version
make install-dev                   # Development version
```

### Manual Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install package
pip install -e .

# Verify installation
mcp-accurate-click --version
```

### System Requirements

- **Python**: 3.10 or higher
- **RAM**: 4GB minimum, 8GB+ recommended
- **GPU**: Optional (NVIDIA CUDA for GPU acceleration)
- **OS**: Windows 10+, Linux with X11

---

## Docker Deployment

### Using Docker Compose (Recommended)

```bash
# CPU version
docker-compose up mcp-server

# GPU version (requires nvidia-docker)
docker-compose up mcp-server-gpu

# Run in background
docker-compose up -d mcp-server

# View logs
docker-compose logs -f mcp-server

# Stop server
docker-compose down
```

### Manual Docker

#### Build Images

```bash
# CPU version
docker build -t mcp-accurate-click:latest -f docker/Dockerfile .

# GPU version
docker build -t mcp-accurate-click:gpu -f docker/Dockerfile.gpu .
```

#### Run Container

```bash
# CPU version
docker run -it --rm \
  --name mcp-server \
  -v $(pwd)/calibration:/app/calibration \
  -v $(pwd)/data:/app/data \
  -v /tmp/.X11-unix:/tmp/.X11-unix:ro \
  -e DISPLAY=$DISPLAY \
  --network host \
  mcp-accurate-click:latest

# GPU version
docker run -it --rm \
  --name mcp-server-gpu \
  --gpus all \
  -v $(pwd)/calibration:/app/calibration \
  -v $(pwd)/data:/app/data \
  -v /tmp/.X11-unix:/tmp/.X11-unix:ro \
  -e DISPLAY=$DISPLAY \
  --network host \
  mcp-accurate-click:gpu
```

### Docker Hub

```bash
# Pull from Docker Hub (when available)
docker pull mcp-accurate-click/server:latest
docker pull mcp-accurate-click/server:gpu

# Run
docker run -it mcp-accurate-click/server:latest
```

---

## Production Deployment

### Systemd Service (Linux)

Create `/etc/systemd/system/mcp-accurate-click.service`:

```ini
[Unit]
Description=MCP Accurate Click Server
After=network.target

[Service]
Type=simple
User=mcpuser
Group=mcpuser
WorkingDirectory=/opt/mcp-accurate-click-server
Environment="PATH=/opt/mcp-accurate-click-server/venv/bin"
Environment="MCP_CALIBRATION_FILE=/opt/mcp-accurate-click-server/calibration/production.npz"
Environment="MCP_LOG_LEVEL=info"
ExecStart=/opt/mcp-accurate-click-server/venv/bin/mcp-click-server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mcp-accurate-click
sudo systemctl start mcp-accurate-click
sudo systemctl status mcp-accurate-click
```

### Windows Service

Use [NSSM](https://nssm.cc/) to run as a Windows service:

```powershell
# Install NSSM
choco install nssm

# Create service
nssm install MCPAccurateClick "C:\Python310\Scripts\mcp-click-server.exe"
nssm set MCPAccurateClick AppDirectory "C:\mcp-accurate-click-server"
nssm set MCPAccurateClick AppEnvironmentExtra "MCP_CALIBRATION_FILE=C:\mcp-accurate-click-server\calibration\production.npz"

# Start service
nssm start MCPAccurateClick
```

### Process Manager (PM2)

```bash
# Install PM2
npm install -g pm2

# Create ecosystem.config.js
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: 'mcp-accurate-click',
    script: 'mcp-click-server',
    interpreter: 'python3',
    env: {
      MCP_CALIBRATION_FILE: '/path/to/calibration.npz',
      MCP_LOG_LEVEL: 'info'
    },
    max_memory_restart: '1G',
    autorestart: true
  }]
}
EOF

# Start with PM2
pm2 start ecosystem.config.js

# Save configuration
pm2 save

# Setup startup script
pm2 startup
```

---

## Claude Desktop Integration

### Configuration File Location

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Basic Configuration

```json
{
  "mcpServers": {
    "accurate-click": {
      "command": "mcp-click-server",
      "args": [],
      "env": {
        "MCP_CALIBRATION_FILE": "/absolute/path/to/calibration.npz",
        "MCP_LOG_LEVEL": "info"
      }
    }
  }
}
```

### Advanced Configuration

```json
{
  "mcpServers": {
    "accurate-click": {
      "command": "/full/path/to/venv/bin/mcp-click-server",
      "args": ["--use-gpu", "--port", "8080"],
      "env": {
        "MCP_CALIBRATION_FILE": "/path/to/calibration.npz",
        "MCP_LOG_LEVEL": "debug",
        "MCP_OCR_LANGUAGE": "en",
        "MCP_CONFIDENCE_THRESHOLD": "0.8",
        "PYTHONPATH": "/path/to/mcp-accurate-click-server/src"
      },
      "timeout": 30000
    }
  }
}
```

### Multiple Configurations

```json
{
  "mcpServers": {
    "accurate-click-cpu": {
      "command": "mcp-click-server",
      "args": [],
      "env": {
        "MCP_CALIBRATION_FILE": "/path/to/calibration.npz"
      }
    },
    "accurate-click-gpu": {
      "command": "mcp-click-server",
      "args": ["--use-gpu"],
      "env": {
        "MCP_CALIBRATION_FILE": "/path/to/calibration.npz"
      }
    },
    "accurate-click-debug": {
      "command": "mcp-click-server",
      "args": ["--log-level", "debug"],
      "env": {
        "MCP_DEBUG": "1"
      }
    }
  }
}
```

---

## Environment Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_CALIBRATION_FILE` | Path to calibration file | None |
| `MCP_LOG_LEVEL` | Logging level (debug/info/warning/error) | info |
| `MCP_OCR_LANGUAGE` | OCR language | en |
| `MCP_CONFIDENCE_THRESHOLD` | Minimum OCR confidence | 0.8 |
| `MCP_USE_GPU` | Enable GPU acceleration | false |
| `MCP_PORT` | Server port | 8080 |
| `MCP_DEBUG` | Enable debug mode | false |
| `DISPLAY` | X11 display (Linux) | :0 |

### Configuration File

Create `config.yaml`:

```yaml
# Server configuration
server:
  host: localhost
  port: 8080
  log_level: info

# OCR configuration
ocr:
  language: en
  confidence_threshold: 0.8
  use_gpu: false
  model_dir: ~/.paddleocr/models

# Calibration
calibration:
  file: /path/to/calibration.npz
  auto_recalibrate: false
  recalibration_interval: 86400  # 24 hours in seconds

# Click executor
click:
  double_click_delay: 0.1
  click_duration: 0.05
  verify_clicks: true

# Performance
performance:
  screenshot_cache_ttl: 5
  ocr_cache_enabled: true
  max_workers: 4
```

Load with:

```bash
mcp-click-server --config config.yaml
```

---

## Scaling and Performance

### Performance Tuning

#### CPU Optimization

```bash
# Increase worker threads
export MCP_MAX_WORKERS=8

# Reduce screenshot quality for speed
export MCP_SCREENSHOT_QUALITY=50

# Enable caching
export MCP_CACHE_ENABLED=true
```

#### GPU Optimization

```bash
# Use GPU acceleration
mcp-click-server --use-gpu

# Set CUDA device
export CUDA_VISIBLE_DEVICES=0

# Optimize batch size
export MCP_OCR_BATCH_SIZE=16
```

### Load Balancing

Run multiple instances behind nginx:

```nginx
upstream mcp_backend {
    least_conn;
    server localhost:8080;
    server localhost:8081;
    server localhost:8082;
}

server {
    listen 80;

    location / {
        proxy_pass http://mcp_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Monitoring

#### Prometheus Metrics

```python
# Add to server.py
from prometheus_client import start_http_server, Counter, Histogram

click_counter = Counter('mcp_clicks_total', 'Total clicks')
ocr_duration = Histogram('mcp_ocr_duration_seconds', 'OCR processing time')

# Start metrics server
start_http_server(9090)
```

#### Health Checks

```bash
# HTTP health endpoint
curl http://localhost:8080/health

# Docker health check
HEALTHCHECK --interval=30s --timeout=10s \
  CMD mcp-accurate-click --version || exit 1
```

### Backup and Recovery

```bash
# Backup calibration data
cp /path/to/calibration.npz /backup/calibration-$(date +%Y%m%d).npz

# Automated backup script
0 2 * * * /usr/local/bin/backup-calibration.sh
```

---

## Troubleshooting

### Common Issues

#### Server won't start
```bash
# Check logs
journalctl -u mcp-accurate-click -f

# Verify Python version
python3 --version

# Check dependencies
pip list | grep -E 'paddleocr|mcp'
```

#### High memory usage
```bash
# Limit OCR cache
export MCP_OCR_CACHE_SIZE=100

# Reduce workers
export MCP_MAX_WORKERS=2
```

#### Permission errors (Linux)
```bash
# Add user to required groups
sudo usermod -aG video $USER

# X11 access
xhost +local:
```

---

## Security Considerations

1. **Run as non-root user**
2. **Use virtual environments**
3. **Keep dependencies updated**: `pip list --outdated`
4. **Enable authentication** if exposing externally
5. **Use HTTPS** for network communication
6. **Regular calibration backups**
7. **Monitor logs** for suspicious activity

---

For more information, see the [main README](README.md) and [documentation](docs/).
