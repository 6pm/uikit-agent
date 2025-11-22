#!/bin/bash
# Local development script - runs FastAPI and Huey locally with hot reload
# Make sure Redis is running first (via docker-compose.dev.yml)

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting local development environment...${NC}"

# Check if Redis is running
if ! nc -z localhost 6379 2>/dev/null; then
    echo -e "${YELLOW}Redis is not running. Starting Redis with docker-compose...${NC}"
    docker-compose -f docker-compose.dev.yml up -d redis
    echo -e "${GREEN}Waiting for Redis to be ready...${NC}"
    sleep 2
fi

# Set environment variable for local development
export REDIS_HOST=localhost

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating one...${NC}"
    uv venv
    source .venv/bin/activate
    uv pip install -e .
else
    source .venv/bin/activate
fi

echo -e "${GREEN}Starting FastAPI with hot reload...${NC}"
echo -e "${GREEN}Starting Huey worker...${NC}"

# Run FastAPI and Huey in parallel using background processes
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
FASTAPI_PID=$!

huey_consumer tasks.huey --workers 2 &
HUEY_PID=$!

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Stopping services...${NC}"
    kill $FASTAPI_PID 2>/dev/null || true
    kill $HUEY_PID 2>/dev/null || true
    exit 0
}

# Trap Ctrl+C
trap cleanup INT TERM

echo -e "${GREEN}✓ FastAPI running on http://localhost:8000 (PID: $FASTAPI_PID)${NC}"
echo -e "${GREEN}✓ Huey worker running (PID: $HUEY_PID)${NC}"
echo -e "${BLUE}Press Ctrl+C to stop both services${NC}"

# Wait for both processes
wait
