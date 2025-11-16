#!/bin/bash
# One-command installation script for MCP Accurate Click Server
# Usage: ./scripts/install.sh [cpu|gpu|dev]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Banner
echo "================================================"
echo "  MCP Accurate Click Server - Installation"
echo "================================================"
echo ""

# Detect installation type
INSTALL_TYPE="${1:-cpu}"

case "$INSTALL_TYPE" in
  cpu)
    echo -e "${GREEN}Installing CPU version...${NC}"
    REQUIREMENTS="requirements.txt"
    ;;
  gpu)
    echo -e "${GREEN}Installing GPU version...${NC}"
    REQUIREMENTS="requirements-gpu.txt"
    ;;
  dev)
    echo -e "${GREEN}Installing development version...${NC}"
    REQUIREMENTS="requirements-dev.txt"
    ;;
  *)
    echo -e "${RED}Error: Invalid installation type '$INSTALL_TYPE'${NC}"
    echo "Usage: $0 [cpu|gpu|dev]"
    exit 1
    ;;
esac

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.10"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo -e "${RED}Error: Python 3.10+ required, found $PYTHON_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"

# Upgrade pip
echo "Upgrading pip, setuptools, wheel..."
python3 -m pip install --upgrade pip setuptools wheel

# Install dependencies
echo "Installing dependencies from $REQUIREMENTS..."
python3 -m pip install -r "$REQUIREMENTS"

# Install package in editable mode
echo "Installing mcp-accurate-click-server..."
python3 -m pip install -e .

# Verify installation
echo "Verifying installation..."
if python3 -c "import mcp_accurate_click" 2>/dev/null; then
    echo -e "${GREEN}✓ Package installed successfully${NC}"
else
    echo -e "${RED}✗ Installation verification failed${NC}"
    exit 1
fi

# Check command availability
if command -v mcp-accurate-click &> /dev/null; then
    VERSION=$(mcp-accurate-click --version 2>/dev/null || echo "unknown")
    echo -e "${GREEN}✓ CLI command available: $VERSION${NC}"
else
    echo -e "${YELLOW}⚠ CLI command not in PATH${NC}"
fi

# Install pre-commit hooks (dev only)
if [ "$INSTALL_TYPE" = "dev" ]; then
    echo "Installing pre-commit hooks..."
    pre-commit install
    echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"
fi

# Success message
echo ""
echo "================================================"
echo -e "${GREEN}Installation complete!${NC}"
echo "================================================"
echo ""
echo "Next steps:"
echo "  1. Run calibration:"
echo "     $ mcp-click-calibrate"
echo ""
echo "  2. Start the MCP server:"
echo "     $ mcp-click-server"
echo ""
echo "  3. Or use the Makefile:"
echo "     $ make calibrate"
echo "     $ make run"
echo ""
echo "For Claude Desktop integration, see:"
echo "  claude_desktop_config.json.example"
echo ""
