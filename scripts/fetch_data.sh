#!/bin/bash
# Fetch historical data for A-shares
#
# Usage:
#   ./scripts/fetch_data.sh                    # Fetch all A-shares
#   ./scripts/fetch_data.sh baostock 1d        # Specify source and timeframe
#   ./scripts/fetch_data.sh baostock 1d 100    # Fetch first 100 symbols only
#
# Features:
#   - Rate limiting (respects API limits)
#   - Retry with exponential backoff
#   - Progress tracking (resume capability)
#   - Logs to file

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT/backend"

SOURCE="${1:-baostock}"
TIMEFRAME="${2:-1d}"
LIMIT="${3:-}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Farseer Data Fetcher ===${NC}"
echo "Source: $SOURCE"
echo "Timeframe: $TIMEFRAME"
if [ -n "$LIMIT" ]; then
    echo "Limit: $LIMIT symbols"
fi
echo ""

# Create logs directory
mkdir -p "$PROJECT_ROOT/logs"

# Run fetcher
if [ -n "$LIMIT" ]; then
    # Fetch limited symbols
    PYTHONPATH=src python3 -c "
import asyncio
import logging
from farseer.scheduler.fetch_jobs import fetch_batch, get_all_a_share_symbols

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

async def main():
    symbols = get_all_a_share_symbols()[:$LIMIT]
    print(f'Fetching {len(symbols)} symbols...')
    await fetch_batch(source='$SOURCE', symbols=symbols, timeframe='$TIMEFRAME')

asyncio.run(main())
" 2>&1 | tee "$PROJECT_ROOT/logs/fetch_$(date +%Y%m%d_%H%M%S).log"
else
    # Fetch all symbols
    PYTHONPATH=src python3 -m farseer.scheduler.fetch_jobs "$SOURCE" "$TIMEFRAME" 2>&1 | tee "$PROJECT_ROOT/logs/fetch_$(date +%Y%m%d_%H%M%S).log"
fi

echo ""
echo -e "${GREEN}Done! Check logs/fetch_*.log for details.${NC}"
