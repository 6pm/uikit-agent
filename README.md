# UIKit Agent

AI-powered code generation agent for converting Figma components to code using LangGraph and FastAPI.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Local Development](#local-development)
- [Code Formatting](#code-formatting)
- [Docker Deployment](#docker-deployment)
- [Project Structure](#project-structure)

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- Docker and Docker Compose (for Redis)
- Redis (via Docker or local installation)

## Quick Start

### 1. Initial Setup

```sh
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies from pyproject.toml
uv sync
```

### 2. Install Additional Dependencies

```sh
# Add a new package
uv add PACKAGE-NAME

# Clean cache if needed
uv cache clean
```

## Local Development

**Recommended Approach**: Run FastAPI and Huey locally with hot reload, and use Docker only for Redis. This provides:
- ✅ Instant code changes (no Docker rebuilds)
- ✅ Full debugging support with breakpoints
- ✅ Faster iteration cycle
- ✅ Better IDE integration

### Quick Start (Local Development)

1. **Start Redis** (in Docker):
   ```sh
   docker-compose -f docker-compose.dev.yml up -d redis
   ```

2. **Run everything locally** (FastAPI + Huey with hot reload):
   ```sh
   ./run-dev.sh
   ```

   This script will:
   - Check if Redis is running (start it if needed)
   - Activate your virtual environment
   - Start FastAPI with `--reload` (auto-reloads on code changes)
   - Start Huey worker
   - Run both in parallel

3. **Or run separately** (useful for debugging):
   ```sh
   # Terminal 1: FastAPI only
   ./run-dev-api.sh

   # Terminal 2: Huey worker only
   ./run-dev-worker.sh
   ```

### Debugging in VS Code/Cursor

1. **Set breakpoints** in your code (`main.py`, `tasks/`, etc.)

2. **Start Redis** (if not already running):
   ```sh
   docker-compose -f docker-compose.dev.yml up -d redis
   ```

3. **Open the Run and Debug panel** (Cmd+Shift+D / Ctrl+Shift+D)

4. **Choose a debug configuration**:
   - `Python: FastAPI (Debug)` - Debug FastAPI only
   - `Python: Huey Worker (Debug)` - Debug Huey worker only
   - `Python: FastAPI + Huey (Debug Both)` - Debug both simultaneously

5. **Press F5** to start debugging

6. **Test your API**:
   ```sh
   # Health check
   curl -X GET http://localhost:8000

   # Generate code
   curl -X POST http://localhost:8000/generate-code \
     -H "Content-Type: application/json" \
     -d '{
       "request": [
         {
           "component_id": "comp_123",
           "name": "PrimaryButton",
           "root_node": {
             "id": "1:23",
             "name": "Button",
             "type": "FRAME",
             "properties": {"width": 120, "height": 40}
           }
         }
       ],
       "target_framework": "react",
       "style_approach": "tailwind"
     }'
   ```

Your breakpoints will now work! You can step through code, inspect variables, and see the full call stack.

### Environment Variables

When running locally, set:
```sh
export REDIS_HOST=localhost
```

The development scripts handle this automatically, but if running manually:
```sh
REDIS_HOST=localhost uvicorn main:app --reload
REDIS_HOST=localhost huey_consumer tasks.huey --workers 2
```

### Hot Reload

- **FastAPI**: Changes to `main.py` automatically reload (thanks to `--reload` flag)
- **Huey**: Changes to `tasks/` require restarting the worker (run `./run-dev-worker.sh` again)
- **No Docker rebuilds**: Code changes are instant!

## Code Formatting

This project uses **Ruff** for automatic code formatting and linting. Configuration is in `pyproject.toml`.

### Format All Files

```sh
# Format code
uv run ruff format .

# Check and fix linting issues
uv run ruff check --fix .
```

### Auto-formatting in Cursor/VS Code

The project includes `.vscode/settings.json` that automatically formats Python files on save using Ruff.

**Required extensions:**
- [Ruff](https://marketplace.cursorapi.com/items/?itemName=charliermarsh.ruff) (for code linting and formatting)

After installing the extension, files will automatically format when you save them (Cmd+S / Ctrl+S).

## Docker Deployment

For production-like environments, you can run everything in Docker.

### Build and Run

This command will read your `docker-compose.yml` and start all containers in the background:

```sh
docker-compose up --build -d
```

You will see Docker:
- Loading Redis
- Building your Python image (using uv)
- Starting all containers

### Stop Containers

```sh
docker-compose down
```

## Project Structure

```
uikit-agent/
├──agents/
│  └── code_generator/
│       ├── agent.py          # The main class (CodeGeneratorAgent) - Orchestrator
│       ├── nodes.py          # The logic (CodeGenNodes) - where the work happens
│       ├── state.py          # The data schema (State)
│       └── prompts.py        # System prompts (Strings)
├── schemas/             # Pydantic models and type definitions
│   ├── api/            # API request/response models
│   └── ai_models/      # AI model response schemas
├── tasks/              # Huey background tasks
├── config.py           # Application configuration
├── main.py             # FastAPI application
└── pyproject.toml      # Project dependencies and configuration
```

## Technology Stack

- **FastAPI** - REST API framework
- **Huey + Redis** - Background task queue + rate limiting for heavy queries
- **LangGraph** - Multi-stage AI agent workflows
- **LangChain** - LLM integration (OpenAI/Anthropic)
- **LangSmith** - Detailed logs for each agent call
- **Pydantic** - Data validation and type safety
- **Ruff** - Code formatting and linting
- **uv** - Fast Python package manager
