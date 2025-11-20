"""FastAPI REST API for handling background tasks with Huey."""
import logging
from fastapi import FastAPI, Request, HTTPException
from tasks.testing import long_running_task
from tasks.code_generation_task import code_generation_task
from models.request_models import CodeGenerationRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="UIKit Agent API",
    description="API for generating code from Figma components using LangGraph",
    version="0.0.1"
)


@app.get("/")
def read_root(request: Request):
    """Simple check if API works"""
    client_host = request.client.host if request.client else 'unknown'
    logger.info("Health check from %s", client_host)

    task = long_running_task('Test get data')

    resp = {"message": "FastAPI works!", "task_id": task.id}  # type: ignore
    return resp


@app.post("/generate-code", response_model=dict)
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
    logger.info("[FASTAPI]: Received code generation request with %d components", len(request.request))

    try:
        # BEST PRACTICE: Convert Pydantic model to dict before passing to Huey
        # Huey can't serialize Pydantic models directly
        request_dict = request.model_dump()

        # BEST PRACTICE: Queue task immediately, don't wait
        task = code_generation_task(request_dict)

        task_id = task.id  # type: ignore
        logger.info("[FASTAPI]: Task queued with ID: %s", task_id)

        return {
            "message": "Code generation task accepted",
            "task_id": task_id,
            "status": "queued",
            "components_count": "it just test field"
        }

    except Exception as e:
        logger.error("[FASTAPI]: Error queuing task: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {str(e)}") from e


# @app.post("/create-task/{data}")
# async def create_task(data: str):
#     """
#     This endpoint instantly creates a background task
#     and returns a response.
#     """
#     logger.info("[FASTAPI]: Received request to create task. Data: %s", data)

#     # Instantly send task to queue (Redis)
#     # Huey will handle executing it in the background
#     task = long_running_task(data)

#     # Instantly return Task ID (though we don't use it)
#     return {
#         "message": "Task accepted for processing!",
#         "task_id": task.id  # type: ignore
#     }

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
