"""route '/' - it is health check endpoint to verify if API works"""

from fastapi import APIRouter, Request

from app.utils.logger_config import logger
from tasks.test_task import long_running_task

router = APIRouter(tags=["Health Check"])


@router.get("/", summary="Health Check")
def read_root(request: Request):
    """Simple check if API works"""
    client_host = request.client.host if request.client else "unknown"
    logger.info("Health check from %s", client_host)

    task = long_running_task("Test get data")

    return {
        "message": "FastAPI works! Huey task started",
        "task_id": task.id,
        "status": "started",
    }
