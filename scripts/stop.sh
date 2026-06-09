#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${RED}Stopping Farseer services...${NC}"

pkill -f "uvicorn farseer.main:app" 2>/dev/null && echo "  Stopped backend" || echo "  Backend not running"
pkill -f "vite.*--port" 2>/dev/null && echo "  Stopped frontend" || echo "  Frontend not running"

echo -e "${GREEN}Done.${NC}"
