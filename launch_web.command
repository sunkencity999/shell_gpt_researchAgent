#!/bin/bash
# Find and kill the process using port 8000
PID=$(lsof -t -i:8000)
if [ -n "$PID" ]; then
  echo "Killing process on port 8000 with PID: $PID"
  kill -9 $PID
fi

source venv/bin/activate
uvicorn sgpt-research-web.main:app --host 0.0.0.0 --port 8000