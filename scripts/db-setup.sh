#!/bin/bash
# Enable TimescaleDB extension
docker exec -i farseer-db psql -U postgres -d farseer <<EOF
CREATE EXTENSION IF NOT EXISTS timescaledb;
EOF
echo "TimescaleDB extension enabled"
