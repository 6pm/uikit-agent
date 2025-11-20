# Local Setup

```sh
uv venv # create new env
source .venv/bin/activate # activate and choose local venv in the Cursor
uv pip install -r requirements.txt
```

## 📝 Code Formatting

This project uses **Black** and **isort** for automatic code formatting to ensure consistent style across all files.

### Format all files:
```sh
./format.sh
```

Or manually:
```sh
source .venv/bin/activate
black .
isort .
```

### Configuration
- Formatting settings are in `pyproject.toml`
- Line length: 100 characters
- Black automatically formats code according to PEP 8
- isort sorts imports and is configured to be compatible with Black

### Auto-formatting in Cursor/VS Code
The project includes `.vscode/settings.json` that automatically formats Python files on save using Black and organizes imports with isort.

**Required extensions:**
- [Black Formatter](https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter) (official Microsoft extension)
- [isort](https://marketplace.visualstudio.com/items?itemName=ms-python.isort) (optional, for import sorting)

After installing the extensions, files will automatically format when you save them (Cmd+S / Ctrl+S).

---

## 🚀 Local Development (Recommended for Debugging)

**Best Practice**: Run FastAPI and Huey locally with hot reload, and only use Docker for Redis. This gives you:
- ✅ Instant code changes (no Docker rebuilds)
- ✅ Full debugging support with breakpoints
- ✅ Faster iteration cycle
- ✅ Better IDE integration

### Quick Start (Local Development)

1. **Start Redis only** (in Docker):
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

1. **Set breakpoints** in your code (`main.py`, `tasks.py`, etc.)

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
   curl -X POST http://localhost:8000/create-task/HelloDebug
   ```

Your breakpoints will now work! You can step through code, inspect variables, and see the full call stack.

### Environment Variables for Local Development

When running locally, set:
```sh
export REDIS_HOST=localhost
```

The scripts handle this automatically, but if running manually:
```sh
REDIS_HOST=localhost uvicorn main:app --reload
REDIS_HOST=localhost huey_consumer tasks.huey --workers 2
```

### Hot Reload Benefits

- **FastAPI**: Changes to `main.py` automatically reload (thanks to `--reload` flag)
- **Huey**: Changes to `tasks.py` require restarting the worker (run `./run-dev-worker.sh` again)
- **No Docker rebuilds**: Code changes are instant!

---

## 🐳 Build and Run with Docker (Production-like)
This command will read your docker-compose.yml and start all 3 containers in the background (-d):
```sh
docker-compose up --build -d
```
You will see Docker loading Redis, building your Python image (using uv) and starting 3 containers.


To stop and remove all containers:
```sh
docker-compose down
```
