#!/bin/bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Default to dev
MODE="${1:-dev}"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Validate mode
if [[ "$MODE" != "dev" && "$MODE" != "prod" ]]; then
    echo -e "${RED}Error: Mode must be 'dev' or 'prod'${NC}"
    echo "Usage: $0 [dev|prod]"
    exit 1
fi

# Source environment
source "$PROJECT_ROOT/.env.${MODE}"

# Stop existing
echo -e "${YELLOW}Stopping existing processes...${NC}"
pkill -f "uvicorn farseer.main:app" 2>/dev/null && echo "  Stopped backend" || echo "  No backend running"
pkill -f "vite.*--port" 2>/dev/null && echo "  Stopped frontend" || echo "  No frontend running"
sleep 1

echo -e "${GREEN}Starting Farseer in ${MODE} mode...${NC}"

# Logs dir
mkdir -p "$PROJECT_ROOT/logs"

# Start backend
echo -e "${GREEN}Starting backend on port ${PORT}...${NC}"
cd "$PROJECT_ROOT/backend"
PYTHONPATH=src nohup python3 -m uvicorn farseer.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --reload \
    > "$PROJECT_ROOT/logs/backend.log" 2>&1 &
echo -e "  Backend PID: $!"

# Start frontend
echo -e "${GREEN}Starting frontend on port ${VITE_PORT}...${NC}"
cd "$PROJECT_ROOT/frontend"
nohup bun run vite --host 0.0.0.0 --port "$VITE_PORT" \
    > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
echo -e "  Frontend PID: $!"

# Wait for services
sleep 3

# Check status
echo ""
echo -e "${GREEN}=== Status ===${NC}"
curl -s "http://127.0.0.1:${PORT}/health" > /dev/null 2>&1 \
    && echo -e "  Backend:  ${GREEN}✓${NC}" \
    || echo -e "  Backend:  ${RED}✗${NC} (see logs/backend.log)"

curl -s "http://127.0.0.1:${VITE_PORT}/" > /dev/null 2>&1 \
    && echo -e "  Frontend: ${GREEN}✓${NC}" \
    || echo -e "  Frontend: ${RED}✗${NC} (see logs/frontend.log)"

# URLs
echo ""
echo -e "${GREEN}=== URLs ===${NC}"
echo "  http://175.178.10.229/farseer/${MODE}/"
echo "  http://175.178.10.229/farseer/${MODE}/docs"
echo ""
echo "  Logs: tail -f logs/backend.log"
echo "        tail -f logs/frontend.log"
