# Variables
docker_cmd := "docker compose"

# List available commands
default:
    @just --list

# Run local development server (FastAPI)
run:
    uv run uvicorn main:app --reload

# Run background task worker (Huey)
worker:
    uv run huey_consumer tasks.huey -w 2 -k process

# Format and fix code style (Ruff)
fix:
    uv run ruff format .
    uv run ruff check --fix .

# Docker: Start Redis only (for local development)
dev-redis:
    {{docker_cmd}} -f docker-compose.dev.yml up -d redis

# Docker: Connect to Redis CLI in the running container
logs-redis:
    docker exec -it uikit-agent-redis-1 redis-cli

# Docker: Build and start all services
up:
    {{docker_cmd}} up -d --build

# Docker: Follow logs for all services
logs:
    {{docker_cmd}} logs -f
