"""FastAPI REST API for handling background tasks with Huey."""

from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

from config import REDIS_HOST
from schemas.api.code_generation_types import CodeGenerationRequest, CodeGenerationResponse
from src.logger_config import logger
from tasks.code_generation_task import code_generation_task
from tasks.test_task import long_running_task


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Connect to Redis for rate limiting
    # We use the same Redis host as Huey
    redis_connection = redis.from_url(f"redis://{REDIS_HOST}:6379", encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis_connection)
    logger.info("main: FastAPILimiter initialized with Redis at %s", REDIS_HOST)
    yield
    await redis_connection.close()


app = FastAPI(
    title="UIKit Agent API",
    description="API for generating code from Figma components using LangGraph",
    version="0.0.1",
    lifespan=lifespan,
)

# --- CORS SETTINGS
app.add_middleware(
    CORSMiddleware,
    # For Figma (Origin: null) wildcard is required,
    # BUT we disable credentials so the browser allows it.
    allow_origins=["*"],
    # DISABLE this for wildcard (safer)
    # Enable only if you are sure you are sending cookies
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root(request: Request):
    """Simple check if API works"""
    client_host = request.client.host if request.client else "unknown"
    logger.info("main: Health check from %s", client_host)

    task = long_running_task("Test get data")

    return {
        "message": "FastAPI works! Hey there!",
        "task_id": task.id,
        "status": "started",
    }


@app.post(
    "/generate-code",
    response_model=CodeGenerationResponse,
    dependencies=[Depends(RateLimiter(times=5, seconds=1))],
)
async def generate_code(request: CodeGenerationRequest):
    """
    Generate code from Figma components.

    BEST PRACTICE:
    - Validate input with Pydantic models
    - Return task ID immediately (async pattern)
    - Process in background with Huey

    Args:
        request: Validated request with components and generation options

    Returns:
        Task ID and status
    """
    logger.info("main: [FASTAPI]: Received code generation request with component name: %s", request.componentName)

    try:
        # BEST PRACTICE: Convert Pydantic model to dict before passing to Huey
        # Huey can't serialize Pydantic models directly
        request_dict = request.model_dump()

        # BEST PRACTICE: Queue task immediately, don't wait
        task = code_generation_task(request_dict)

        task_id = task.id
        logger.info("main: [FASTAPI]: Task queued with ID: %s", task_id)

        return {
            "message": "Code generation task accepted",
            "task_id": task_id,
            "status": "queued",
        }

    except Exception as e:
        logger.error("main: [FASTAPI]: Error queuing task: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {str(e)}") from e


# @app.get("/task-status/{task_id}")
# async def get_task_status(task_id: str):
#     """
#     Get status and result of a task.

#     BEST PRACTICE: Provide status endpoint for async tasks.
#     """
#     from config import huey

#     try:
#         # BEST PRACTICE: Use Huey's storage to get result
#         # Huey stores results in Redis, we can access them via storage
#         storage = huey.storage

#         # Try to get result from storage
#         result = storage.get_result(task_id)

#         if result is None:
#             # Task might still be pending or doesn't exist
#             # Check if task is in queue
#             return {
#                 "task_id": task_id,
#                 "status": "pending",
#                 "result": None
#             }

#         return {
#             "task_id": task_id,
#             "status": "completed",
#             "result": result
#         }

#     except Exception as e:
#         logger.error("[FASTAPI]: Error retrieving task %s: %s", task_id, str(e), exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Failed to retrieve task: {str(e)}") from e
