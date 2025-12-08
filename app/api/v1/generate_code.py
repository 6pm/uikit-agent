"""route '/generate-code' - it is endpoint for generating code from Figma JSON structure"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi_limiter.depends import RateLimiter

from schemas.api.code_generation_types import CodeGenerationRequest, CodeGenerationResponse
from src.logger_config import logger
from tasks.code_generation_task import code_generation_task

router = APIRouter(tags=["Code Generation"])


@router.post(
    "/generate-code",
    response_model=CodeGenerationResponse,
    dependencies=[Depends(RateLimiter(times=5, seconds=1))],
    summary="Generate UI code from Figma JSON structure",
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
