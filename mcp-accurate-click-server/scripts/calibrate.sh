#!/bin/bash
# Calibration script for MCP Accurate Click Server
# Runs the interactive calibration workflow

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo "================================================"
echo "  MCP Accurate Click - Calibration Workflow"
echo "================================================"
echo ""

# Configuration
CALIBRATION_DIR="${MCP_CALIBRATION_DIR:-$HOME/.config/mcp-accurate-click/calibration}"
CALIBRATION_FILE="${CALIBRATION_FILE:-default.npz}"
NUM_POINTS="${MCP_CALIBRATION_POINTS:-20}"

# Create calibration directory
mkdir -p "$CALIBRATION_DIR"

echo -e "${BLUE}Calibration Configuration:${NC}"
echo "  Directory: $CALIBRATION_DIR"
echo "  File: $CALIBRATION_FILE"
echo "  Points: $NUM_POINTS"
echo ""

# Check if calibration already exists
FULL_PATH="$CALIBRATION_DIR/$CALIBRATION_FILE"
if [ -f "$FULL_PATH" ]; then
    echo -e "${YELLOW}Warning: Calibration file already exists:${NC}"
    echo "  $FULL_PATH"
    echo ""
    read -p "Overwrite? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Calibration cancelled."
        exit 0
    fi
fi

# Run calibration
echo -e "${GREEN}Starting calibration...${NC}"
echo ""
echo "Instructions:"
echo "  1. Click on each crosshair as accurately as possible"
echo "  2. Use the center of the crosshair"
echo "  3. Take your time for accurate results"
echo ""
echo "Press Enter to begin..."
read

# Execute calibration command
if command -v mcp-click-calibrate &> /dev/null; then
    mcp-click-calibrate \
        --num-points "$NUM_POINTS" \
        --output "$FULL_PATH" \
        --interactive
else
    python3 -m mcp_accurate_click.calibration \
        --num-points "$NUM_POINTS" \
        --output "$FULL_PATH" \
        --interactive
fi

# Check if calibration was successful
if [ -f "$FULL_PATH" ]; then
    echo ""
    echo "================================================"
    echo -e "${GREEN}Calibration complete!${NC}"
    echo "================================================"
    echo ""
    echo "Calibration saved to:"
    echo "  $FULL_PATH"
    echo ""
    echo "To use this calibration:"
    echo "  1. Set environment variable:"
    echo "     export MCP_CALIBRATION_FILE=\"$FULL_PATH\""
    echo ""
    echo "  2. Or update Claude Desktop config:"
    echo "     \"env\": {"
    echo "       \"MCP_CALIBRATION_FILE\": \"$FULL_PATH\""
    echo "     }"
    echo ""
    echo "  3. Or pass to server directly:"
    echo "     mcp-click-server --calibration \"$FULL_PATH\""
    echo ""
else
    echo -e "${RED}Calibration failed - file not created${NC}"
    exit 1
fi
