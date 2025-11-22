#!/bin/bash
# Run only FastAPI locally (useful when debugging just the API)
# Make sure Redis is running first

set -e

export REDIS_HOST=localhost

if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Run: uv venv && source .venv/bin/activate && uv sync"
    exit 1
fi

source .venv/bin/activate

echo "Starting FastAPI with hot reload on http://localhost:8000"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
