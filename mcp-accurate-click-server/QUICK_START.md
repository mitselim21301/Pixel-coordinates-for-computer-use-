# MCP Accurate Click Server - Quick Start

## Installation (Choose One Method)

### Method 1: One-Command Script (Recommended)
```bash
./scripts/install.sh cpu    # CPU version
./scripts/install.sh gpu    # GPU version
./scripts/install.sh dev    # Development version
```

### Method 2: Makefile
```bash
make install              # CPU version
make install-gpu          # GPU version
make install-dev          # Development version
```

### Method 3: pip (Manual)
```bash
pip install -r requirements.txt
pip install -e .
```

### Method 4: Docker
```bash
docker-compose up mcp-server      # CPU version
docker-compose up mcp-server-gpu  # GPU version
```

---

## Quick Usage

### 1. Run Calibration (Recommended)
```bash
# Using script
./scripts/calibrate.sh

# Using Makefile
make calibrate

# Using command directly
mcp-click-calibrate
```

### 2. Start MCP Server
```bash
# Using script
./scripts/start_server.sh
./scripts/start_server.sh --gpu      # GPU version
./scripts/start_server.sh --debug    # Debug mode

# Using Makefile
make run
make run-debug

# Using command directly
mcp-click-server
mcp-click-server --use-gpu
```

### 3. Configure Claude Desktop

**Location**:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Add this configuration**:
```json
{
  "mcpServers": {
    "accurate-click": {
      "command": "mcp-click-server",
      "env": {
        "MCP_CALIBRATION_FILE": "/path/to/.config/mcp-accurate-click/calibration/default.npz"
      }
    }
  }
}
```

---

## Common Commands

### Development
```bash
make test              # Run tests
make lint              # Run linters
make format            # Format code
make check             # Run all checks
```

### Docker
```bash
make docker-build      # Build CPU image
make docker-build-gpu  # Build GPU image
make docker-run        # Run container
```

### Building & Publishing
```bash
make build             # Build package
make publish-test      # Publish to TestPyPI
make publish           # Publish to PyPI
```

---

## File Locations

- **Calibration**: `~/.config/mcp-accurate-click/calibration/default.npz`
- **Config**: `claude_desktop_config.json`
- **Logs**: Check server output

---

## Troubleshooting

### Installation Issues
```bash
# Verify Python version (requires 3.10+)
python3 --version

# Check installation
mcp-accurate-click --version
```

### Server Won't Start
```bash
# Check dependencies
pip list | grep -E 'paddleocr|mcp'

# Verify calibration
ls ~/.config/mcp-accurate-click/calibration/
```

### Slow Performance
```bash
# Use GPU version
./scripts/start_server.sh --gpu
```

---

## All Available Commands

### Installation Scripts
- `./scripts/install.sh [cpu|gpu|dev]` - One-command installation
- `./scripts/calibrate.sh` - Run calibration workflow
- `./scripts/start_server.sh [--gpu] [--debug]` - Start MCP server

### Makefile Targets (28 total)
```bash
make help              # Show all available targets
make install           # Install dependencies
make install-dev       # Install with dev tools
make install-gpu       # Install with GPU support
make test              # Run tests
make lint              # Run linters
make format            # Format code
make calibrate         # Run calibration
make run               # Start server
make docker-build      # Build Docker image
make build             # Build package
```

### Direct Commands
```bash
mcp-accurate-click --version           # Check version
mcp-click-server                       # Start server
mcp-click-calibrate                    # Run calibration
```

---

## Next Steps

1. **Install**: Choose an installation method
2. **Calibrate**: Run calibration for best accuracy
3. **Configure**: Add to Claude Desktop config
4. **Use**: Start clicking with Claude!

For full documentation, see:
- [README.md](README.md) - Main documentation
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
- [TEAM10_COMPLETE_DELIVERY.md](TEAM10_COMPLETE_DELIVERY.md) - Complete delivery report
