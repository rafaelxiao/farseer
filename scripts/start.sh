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

echo -e "${GREEN}Starting Farseer in ${MODE} mode...${NC}"

# Source environment
source "$PROJECT_ROOT/.env.${MODE}"

# Kill existing processes
echo -e "${YELLOW}Stopping existing processes...${NC}"
pkill -f "uvicorn farseer.main:app" 2>/dev/null || true
pkill -f "vite.*--port ${VITE_PORT}" 2>/dev/null || true
sleep 1

# Start backend
echo -e "${GREEN}Starting backend on port ${PORT}...${NC}"
cd "$PROJECT_ROOT/backend"
PYTHONPATH=src nohup python3 -m uvicorn farseer.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --reload \
    > "$PROJECT_ROOT/logs/backend.log" 2>&1 &
BACKEND_PID=$!
echo -e "  Backend PID: ${BACKEND_PID}"

# Start frontend
echo -e "${GREEN}Starting frontend on port ${VITE_PORT}...${NC}"
cd "$PROJECT_ROOT/frontend"
mkdir -p "$PROJECT_ROOT/logs"
nohup bun run vite --host 0.0.0.0 --port "$VITE_PORT" \
    > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo -e "  Frontend PID: ${FRONTEND_PID}"

# Wait for services
sleep 3

# Check if services are running
echo ""
echo -e "${GREEN}Checking services...${NC}"

if curl -s "http://127.0.0.1:${PORT}/health" > /dev/null 2>&1; then
    echo -e "  Backend:  ${GREEN}✓ Running${NC}"
else
    echo -e "  Backend:  ${RED}✗ Failed${NC} (check logs/backend.log)"
fi

if curl -s "http://127.0.0.1:${VITE_PORT}/" > /dev/null 2>&1; then
    echo -e "  Frontend: ${GREEN}✓ Running${NC}"
else
    echo -e "  Frontend: ${RED}✗ Failed${NC} (check logs/frontend.log)"
fi

# Show URLs
echo ""
echo -e "${GREEN}=== URLs ===${NC}"
echo -e "  Frontend: http://175.178.10.229/farseer/${MODE}/"
echo -e "  API Docs: http://175.178.10.229/farseer/${MODE}/docs"
echo -e "  Health:   http://175.178.10.229/farseer/${MODE}/health"
echo ""
echo -e "  Logs: tail -f $PROJECT_ROOT/logs/backend.log"
echo -e "        tail -f $PROJECT_ROOT/logs/frontend.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop (or run: pkill -f 'uvicorn|vite')${NC}"
