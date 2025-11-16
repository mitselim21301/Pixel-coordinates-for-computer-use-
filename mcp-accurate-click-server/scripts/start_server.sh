#!/bin/bash
# Start MCP Accurate Click Server
# Usage: ./scripts/start_server.sh [--gpu] [--debug]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo "================================================"
echo "  MCP Accurate Click Server"
echo "================================================"
echo ""

# Parse arguments
USE_GPU=false
DEBUG=false
EXTRA_ARGS=()

for arg in "$@"; do
    case $arg in
        --gpu)
            USE_GPU=true
            shift
            ;;
        --debug)
            DEBUG=true
            shift
            ;;
        *)
            EXTRA_ARGS+=("$arg")
            ;;
    esac
done

# Configuration
CALIBRATION_FILE="${MCP_CALIBRATION_FILE:-$HOME/.config/mcp-accurate-click/calibration/default.npz}"
LOG_LEVEL="${MCP_LOG_LEVEL:-info}"

if [ "$DEBUG" = true ]; then
    LOG_LEVEL="debug"
fi

# Check if calibration file exists
if [ ! -f "$CALIBRATION_FILE" ]; then
    echo -e "${YELLOW}Warning: Calibration file not found:${NC}"
    echo "  $CALIBRATION_FILE"
    echo ""
    echo "For better accuracy, run calibration first:"
    echo "  $ make calibrate"
    echo "  $ mcp-click-calibrate"
    echo ""
    read -p "Continue without calibration? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Server start cancelled."
        exit 0
    fi
    CALIBRATION_ARG=""
else
    echo -e "${GREEN}✓ Using calibration: $CALIBRATION_FILE${NC}"
    CALIBRATION_ARG="--calibration $CALIBRATION_FILE"
fi

# Display configuration
echo -e "${BLUE}Server Configuration:${NC}"
echo "  GPU Enabled: $USE_GPU"
echo "  Log Level: $LOG_LEVEL"
echo "  Calibration: ${CALIBRATION_FILE:-none}"
echo ""

# Build command
CMD="mcp-click-server"
CMD="$CMD --log-level $LOG_LEVEL"

if [ "$USE_GPU" = true ]; then
    CMD="$CMD --use-gpu"
fi

if [ -n "$CALIBRATION_ARG" ]; then
    CMD="$CMD $CALIBRATION_ARG"
fi

# Add extra arguments
if [ ${#EXTRA_ARGS[@]} -gt 0 ]; then
    CMD="$CMD ${EXTRA_ARGS[*]}"
fi

# Start server
echo -e "${GREEN}Starting MCP server...${NC}"
echo "Command: $CMD"
echo ""
echo "Press Ctrl+C to stop"
echo "================================================"
echo ""

# Execute
if command -v mcp-click-server &> /dev/null; then
    exec $CMD
else
    exec python3 -m mcp_accurate_click.server $CMD
fi
