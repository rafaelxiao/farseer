#!/bin/bash
# Monitor disk space during fetch
# Run: ./scripts/disk-monitor.sh

THRESHOLD_GB=5  # Stop if less than 5GB free

while true; do
    FREE_GB=$(df / --output=avail -BG | tail -1 | tr -d ' G')
    
    if [ "$FREE_GB" -lt "$THRESHOLD_GB" ]; then
        echo "WARNING: Only ${FREE_GB}GB free! Stopping fetch..."
        pkill -f "fetch_jobs"
        echo "Fetch stopped."
        exit 1
    fi
    
    # Show status
    DB_SIZE=$(sudo -u postgres psql -t -c "SELECT pg_size_pretty(pg_database_size('farseer'));" 2>/dev/null | tr -d ' ')
    PROGRESS=$(cat /home/ubuntu/projects/farseer/backend/data/fetch_progress.json 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('completed',[])))" 2>/dev/null)
    
    echo "$(date '+%H:%M:%S') | Free: ${FREE_GB}GB | DB: ${DB_SIZE} | Progress: ${PROGRESS}/5533"
    
    sleep 300  # Check every 5 minutes
done
