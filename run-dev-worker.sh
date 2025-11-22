#!/bin/bash
# Run only Huey worker locally (useful when debugging just the worker)
# Make sure Redis is running first

set -e

export REDIS_HOST=localhost

if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Run: uv venv && source .venv/bin/activate && uv pip install -e ."
    exit 1
fi

source .venv/bin/activate

echo "Starting Huey worker..."
huey_consumer tasks.huey --workers 2
