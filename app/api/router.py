"""Router configuration and all API endpoints."""

from fastapi import APIRouter

from app.api.v1 import generate_code, healthcheck, task_history, user_tasks

api_router = APIRouter()

# Include routers
api_router.include_router(healthcheck.router)  # Root route - /
api_router.include_router(generate_code.router)  # /generate-code
api_router.include_router(task_history.router)  # /{task_id}/history
api_router.include_router(user_tasks.router)  # /history/{user_id}
