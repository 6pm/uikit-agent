"""Router configuration and all API endpoints."""

from fastapi import APIRouter

from app.api.v1 import generate_code, healthcheck

api_router = APIRouter()

# Include routers
api_router.include_router(healthcheck.router)  # Root route - /
api_router.include_router(generate_code.router)  # /generate-code
