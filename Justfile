# Variables
docker_cmd := "docker compose"

# List available commands
default:
    @just --list

# Run local server (FastAPI) on HTTPS (requires mkcert generated files: localhost+2.pem and localhost+2-key.pem)
run-https:
    REDIS_HOST=localhost uv run uvicorn main:app --reload --ssl-keyfile=localhost+2-key.pem --ssl-certfile=localhost+2.pem

# Run background task worker (Huey)
# Using thread worker type (-k thread) to fix multiprocessing issues on macOS
worker:
    REDIS_HOST=localhost uv run huey_consumer tasks.huey -w 2 -k thread

# Format and fix code style (Ruff)
fix:
    uv run ruff format .
    uv run ruff check --fix .

# Docker: Start Redis only (for local development)
dev-redis:
    {{docker_cmd}} -f docker-compose.dev.yml up -d

# Docker: Connect to Redis CLI in the running container
logs-redis:
    iredis --url redis://localhost:6379/0

# Docker: Build and start all services
up:
    {{docker_cmd}} up -d --build

# Docker: Follow logs for all services
logs:
    {{docker_cmd}} logs -f
