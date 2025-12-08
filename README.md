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

1. Install Docker.

2. Install Just:
```sh
brew install just
```

3. Setup HTTPS for local development(first time launch):
```sh
brew install mkcert
mkcert -install

# generate certificates in the certificates folder
cd certificates
mkcert localhost 127.0.0.1 ::1 # it generates 2 files: localhost+2.pem, localhost+2-key.pem

```

4. Setup virtual env using UV package manager(first time launch):
```sh
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies from pyproject.toml
uv sync
```

###  Useful commands:
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
   curl -X GET https://localhost:8000

   # Generate code
   curl -k -X POST https://0.0.0.0:8000/generate-code \
   -H "Content-Type: application/json" \
   -H "TRAEFIK_SECRET_HEADER: TRAEFIK_SECRET_TOKEN" \
  -d '{
    "figmaJson": {"name":"Flex","id":"417:617","type":"FRAME","layout":{"layoutMode":"VERTICAL","itemSpacing":10,"autoLayout":"start-center","maxWidth":500,"width":500,"height":470},"children":[{"name":"Card","id":"419:135","type":"FRAME","variables":"itemSpacing:spacing/6 paddingLeft:spacing/6 paddingTop:spacing/6 paddingRight:spacing/6 paddingBottom:spacing/6 topLeftRadius:border radius/xl topRightRadius:border radius/xl bottomLeftRadius:border radius/xl bottomRightRadius:border radius/xl fills:base/card strokes:base/border","layout":{"layoutMode":"VERTICAL","itemSpacing":24,"padding":"24 24 24 24","autoLayout":"start-start","width":500,"height":470},"children":[{"name":"Title Text","id":"I419:136;268:956","type":"TEXT","variables":"fills:base/card-foreground letterSpacing:font/letter-spacing/tight fontSize:typography/base sizes/base/font-size fontFamily:typography/font family/font-sans fontWeight:font/weight/semibold","layout":{"width":452,"height":16},"text":{"content":"Title Text","fontSize":16,"fontWeight":600,"textAlignHorizontal":"LEFT","textAlignVertical":"TOP","letterSpacing":{"unit":"PIXELS","value":-0.4000000059604645},"lineHeight":100,"color":"rgb(236, 195, 255)","fontFamily":"Lato"}},{"name":"CardFooter","id":"419:138","type":"INSTANCE","componentProperties":{"Variant":"2 Buttons"},"variables":"paddingLeft:spacing/6 paddingRight:spacing/6","layout":{"layoutMode":"HORIZONTAL","itemSpacing":10,"padding":"0 24 0 24","autoLayout":"space-between-center","width":452,"height":36},"children":[{"name":"Button","id":"I419:138;268:933","type":"INSTANCE","componentProperties":{"Right Icon#267:65":"503:4218","Left Icon#46:0":"503:4218","Show Left Icon#37:11":false,"Show Right Icon#267:0":false,"Button Text#37:10":"Cancel","Variant":"Outline","State":"Default","Size":"default"},"variables":"itemSpacing:spacing/2 paddingLeft:spacing/4 paddingTop:spacing/2 paddingRight:spacing/4 paddingBottom:spacing/2 height:height/h-9 topLeftRadius:components/button/outline/border-radius topRightRadius:components/button/outline/border-radius bottomLeftRadius:components/button/outline/border-radius bottomRightRadius:components/button/outline/border-radius strokeTopWeight:components/button/outline/border-width strokeBottomWeight:components/button/outline/border-width strokeLeftWeight:components/button/outline/border-width strokeRightWeight:components/button/outline/border-width fills:components/button/outline/background-color strokes:components/button/outline/border-color","layout":{"layoutMode":"HORIZONTAL","itemSpacing":8,"padding":"8 16 8 16","autoLayout":"center-center","width":74,"height":36},"children":[{"name":"Icon / Circle","id":"I419:138;268:933;37:1559","type":"INSTANCE","componentProperties":{},"variables":"width:width/w-4 height:height/h-4","layout":{"width":16,"height":16}},{"name":"Button","id":"I419:138;268:933;37:1478","type":"TEXT","variables":"fills:components/button/outline/color fontSize:typography/base sizes/small/font-size fontFamily:typography/font family/font-sans lineHeight:typography/base sizes/small/line-height fontWeight:font/weight/medium","layout":{"width":42,"height":20},"text":{"content":"Cancel","fontSize":14,"fontWeight":500,"textAlignHorizontal":"LEFT","textAlignVertical":"CENTER","letterSpacing":{"unit":"PERCENT","value":0},"lineHeight":20,"color":"rgb(71, 255, 244)","fontFamily":"Lato"}},{"name":"Icon / Circle","id":"I419:138;268:933;267:4103","type":"INSTANCE","componentProperties":{},"variables":"width:width/w-4 height:height/h-4","layout":{"width":16,"height":16}}]},{"name":"Button","id":"I419:138;268:934","type":"INSTANCE","componentProperties":{"Right Icon#267:65":"503:4218","Left Icon#46:0":"503:4218","Show Right Icon#267:0":false,"Show Left Icon#37:11":false,"Button Text#37:10":"Deploy","Variant":"Default","State":"Default","Size":"default"},"variables":"itemSpacing:spacing/2 paddingLeft:spacing/4 paddingTop:spacing/2 paddingRight:spacing/4 paddingBottom:spacing/2 height:height/h-9 topLeftRadius:components/button/default/border-radius topRightRadius:components/button/default/border-radius bottomLeftRadius:components/button/default/border-radius bottomRightRadius:components/button/default/border-radius strokeTopWeight:components/button/default/border-width strokeBottomWeight:components/button/default/border-width strokeLeftWeight:components/button/default/border-width strokeRightWeight:components/button/default/border-width fills:components/button/default/background-color-to fills:components/button/default/background-color-from strokes:components/button/default/border-color","layout":{"layoutMode":"HORIZONTAL","itemSpacing":8,"padding":"8 16 8 16","autoLayout":"center-center","width":77,"height":36},"children":[{"name":"Icon / Circle","id":"I419:138;268:934;37:1562","type":"INSTANCE","componentProperties":{},"variables":"width:width/w-4 height:height/h-4","layout":{"width":16,"height":16}},{"name":"Button","id":"I419:138;268:934;37:925","type":"TEXT","variables":"fills:components/button/default/color fontSize:typography/base sizes/small/font-size fontFamily:typography/font family/font-sans lineHeight:typography/base sizes/small/line-height fontWeight:font/weight/medium","layout":{"width":45,"height":20},"text":{"content":"Deploy","fontSize":14,"fontWeight":500,"textAlignHorizontal":"LEFT","textAlignVertical":"CENTER","letterSpacing":{"unit":"PERCENT","value":0},"lineHeight":20,"color":"rgb(255, 255, 255)","fontFamily":"Lato"}},{"name":"Icon / Circle","id":"I419:138;268:934;267:4072","type":"INSTANCE","componentProperties":{},"variables":"width:width/w-4 height:height/h-4","layout":{"width":16,"height":16}}]}]}]}]},
    "componentName": "someTestComponent",
    "userPrompt": "always add !! to the end of each text element in the end",
    "userId": "111222",
    "userName": "your-name"
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


## Working with redis locally
Install this client:
```sh
uv tool install iredis # first time install

# run this command to connect to redis. It's better than default client and has autocomplete
iredis --url redis://localhost:6379/0
```
Redis Insight link - http://localhost:5540

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
│       ├── nodes/            # The logic (CodeGenNodes) - where the work happens
│       │   ├── web_generator.py
│       │   ├── mobile_generator.py
│       │   └── ...
│       ├── state.py          # The data schema (State)
│       └── prompts.py        # System prompts (Strings)
├── app/
│   ├── api/                  # API Routes
│   ├── core/                 # Core application logic (lifespan, etc.)
│   └── utils/                # Utility functions (logger, etc.)
├── schemas/             # Pydantic models and type definitions
│   └── api/            # API request/response models
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



## More docs
[How to deploy this docker container to Hetzner VPS](/docs/prepare-prod-hosting.md)
[Guides how to troubleshoot issues on your local machine](/docs/local-environment-troubleshooting.md)