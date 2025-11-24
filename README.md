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

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- [Just](https://github.com/casey/just) - Install `brew install just`
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
We have 2 approaches: using VScode/Cursor debugger or running comands in terminal.

**Recommended Approach**: Run FastAPI and Huey locally with hot reload, and use Docker only for Redis.


### Debugging in VS Code/Cursor (Recommended)

1. **Set breakpoints** in your code (`main.py`, `tasks/`, etc.)

2. **Start Redis** (if not already running):
   ```sh
   just dev-redis
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



### Using Just

We use `just` to manage development commands.

1. **Start Redis** (required for local dev):
   ```sh
   just dev-redis
   ```

2. **Run FastAPI Server** (in one terminal):
   ```sh
   just run
   ```

3. **Run Worker** (in another terminal):
   ```sh
   just worker
   ```

   FastAPI will reload automatically on code changes. For Huey workers, you may need to restart the worker process if you change task definitions.


### Environment Variables

When running locally via `just` or VS Code debuggers, environment variables are handled automatically.
If running manually, ensure `REDIS_HOST=localhost`.

## Code Formatting

This project uses **Ruff** for automatic code formatting and linting.

```sh
# Format code and fix linting issues
just fix
```

### Auto-formatting in Cursor/VS Code

The project includes `.vscode/settings.json` that automatically formats Python files on save using Ruff.

**Required extensions:**
- [Ruff](https://marketplace.cursorapi.com/items/?itemName=charliermarsh.ruff) (for code linting and formatting)

After installing the extension, files will automatically format when you save them (Cmd+S / Ctrl+S).

## Docker Deployment

For production-like environments, you can run everything in Docker.

### Build and Run

```sh
just up
```

This command will build and start all services in the background.

### View Logs

```sh
just logs
```

### Stop Containers

```sh
docker compose down
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

- **uv** - Fast Python package manager
- **FastAPI** - REST API framework
- **Huey + Redis** - Background task queue + rate limiting for heavy queries
- **LangGraph** - Multi-stage AI agent workflows
- **LangChain** - LLM integration (OpenAI/Anthropic)
- **LangSmith** - Detailed logs for each agent call
- **Pydantic** - Data validation and type safety
- **Ruff** - Code formatting and linting
- **uvloop** - Fastest event loop implementation
