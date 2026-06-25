#!/bin/bash
# start.sh — Always use the venv's Python/uvicorn to avoid system Python conflicts

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

HOST="${1:-127.0.0.1}"
PORT="${2:-9001}"

echo "Starting Scoping AI on http://$HOST:$PORT ..."
.venv/bin/python -m uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
