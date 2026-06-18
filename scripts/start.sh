#!/bin/bash
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
MODE="${1:-dev}"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ "$MODE" != "dev" && "$MODE" != "prod" && "$MODE" != "all" && "$MODE" != "stop" ]]; then
    echo -e "${RED}Usage: $0 [dev|prod|all|stop]${NC}"
    exit 1
fi

stop_processes() {
    local suffix="$1"
    echo -e "${YELLOW}Stopping ${suffix}...${NC}"
    pkill -f "uvicorn.*--port ${!BACKEND_PORT}" 2>/dev/null && echo "  Stopped backend ${suffix}" || echo "  No backend ${suffix}"
    pkill -f "vite.*--port ${!FRONTEND_PORT}" 2>/dev/null && echo "  Stopped frontend ${suffix}" || echo "  No frontend ${suffix}"
}

start_instance() {
    local mode="$1"
    local env_file="$PROJECT_ROOT/.env.${mode}"
    
    source "$env_file"
    
    BACKEND_PORT="${PORT}"
    FRONTEND_PORT="${VITE_PORT}"
    
    echo -e "${GREEN}Starting ${mode} (backend:${BACKEND_PORT} frontend:${FRONTEND_PORT})${NC}"
    
    mkdir -p "$PROJECT_ROOT/logs"
    
    # Start backend
    cd "$PROJECT_ROOT/backend"
    source .venv/bin/activate
    
    # Use env file specific to this mode (relative to backend dir)
    ENV_FILE=".env.${mode}" PYTHONPATH=src nohup uvicorn farseer.main:app \
        --host 0.0.0.0 --port "$BACKEND_PORT" \
        > "$PROJECT_ROOT/logs/backend_${mode}.log" 2>&1 &
    disown
    echo "  Backend PID: $!"
    
    # Start frontend
    cd "$PROJECT_ROOT/frontend"
    local vite_mode="development"
    [[ "$mode" == "prod" ]] && vite_mode="prod"
    nohup bun run vite --host 0.0.0.0 --port "$FRONTEND_PORT" --mode "$vite_mode" \
        > "$PROJECT_ROOT/logs/frontend_${mode}.log" 2>&1 &
    disown
    echo "  Frontend PID: $!"
    
    sleep 2
    
    # Health check
    curl -sf "http://127.0.0.1:${BACKEND_PORT}/health" > /dev/null \
        && echo -e "  Backend:  ${GREEN}✓${NC}" \
        || echo -e "  Backend:  ${RED}✗${NC}"
    curl -sf "http://127.0.0.1:${FRONTEND_PORT}/" > /dev/null \
        && echo -e "  Frontend: ${GREEN}✓${NC}" \
        || echo -e "  Frontend: ${RED}✗${NC}"
}

case "$MODE" in
    stop)
        source "$PROJECT_ROOT/.env.dev"; BACKEND_PORT=$PORT; FRONTEND_PORT=$VITE_PORT
        stop_processes "dev"
        source "$PROJECT_ROOT/.env.prod"; BACKEND_PORT=$PORT; FRONTEND_PORT=$VITE_PORT
        stop_processes "prod"
        exit 0
        ;;
    all)
        start_instance "dev"
        start_instance "prod"
        ;;
    *)
        source "$PROJECT_ROOT/.env.${MODE}"; BACKEND_PORT=$PORT; FRONTEND_PORT=$VITE_PORT
        stop_processes "$MODE"
        sleep 1
        start_instance "$MODE"
        ;;
esac

echo ""
echo -e "${GREEN}=== URLs ===${NC}"
echo "  Dev:  http://175.178.10.229/farseer/dev/"
echo "        http://175.178.10.229/farseer/dev/docs"
echo "  Prod: http://175.178.10.229/farseer/"
echo "        http://175.178.10.229/farseer/docs"
