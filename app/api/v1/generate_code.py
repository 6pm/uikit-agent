"""route '/generate-code' - it is endpoint for generating code from Figma JSON structure"""

from datetime import UTC, datetime

import anyio
import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException
from fastapi_limiter.depends import RateLimiter

from app.core.dependencies import get_redis
from app.core.settings import settings
from app.utils.logger_config import logger
from schemas.api.code_generation_types import CodeGenerationRequest, CodeGenerationResponse
from tasks.code_generation_task import code_generation_task

router = APIRouter(tags=["Code Generation"])


@router.post(
    "/generate-code",
    response_model=CodeGenerationResponse,
    dependencies=[Depends(RateLimiter(times=5, seconds=1))],
    summary="Generate UI code from Figma JSON structure",
)
async def generate_code(
    request: CodeGenerationRequest,
    # FastAPI itself injects the global Redis client here
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Generate code from Figma components.

    BEST PRACTICE:
    - Validate input with Pydantic models
    - Return task ID immediately (async pattern)
    - Process in background with Huey

    Args:
        request: Validated request with components and generation options
        redis_client: Redis client dependency

    Returns:
        Task ID and status
    """
    logger.info("main: [FASTAPI]: Received code generation request with component name: %s", request.componentName)

    try:
        # BEST PRACTICE: Convert Pydantic model to dict before passing to Huey
        # Huey can't serialize Pydantic models directly
        request_dict = request.model_dump()

        # ---------------------------------------------------------------------
        # Huey: create task in background
        # ---------------------------------------------------------------------
        # BEST PRACTICE: Queue task immediately, don't wait
        def enqueue_task():
            return code_generation_task(request_dict)

        task = await anyio.to_thread.run_sync(enqueue_task)

        task_id = task.id
        logger.info("main: [FASTAPI]: Task queued with ID: %s", task_id)

        # ---------------------------------------------------------------------
        # Redis Storage: Link Task to User
        # ---------------------------------------------------------------------
        try:
            user_tasks_key = f"user:{request.userId}:tasks"
            task_meta_key = f"task:{task_id}:metadata"

            async with redis_client.pipeline(transaction=True) as pipe:
                # 1. Add task ID to user's list of tasks

                pipe.lpush(user_tasks_key, task_id)
                pipe.expire(user_tasks_key, settings.TASK_HISTORY_TTL)

                # 2. Store task metadata (ownership)
                event_data = {
                    "taskId": task_id,
                    "userId": request.userId,
                    "userName": request.userName,
                    "componentName": request.componentName,
                    "createdAt": datetime.now(UTC).isoformat(),
                }
                pipe.hset(
                    task_meta_key,
                    mapping=event_data,
                )
                pipe.expire(task_meta_key, settings.TASK_HISTORY_TTL)
                await pipe.execute()

                logger.info("main: [FASTAPI]: Saved task %s for user %s in Redis", task_id, request.userId)

        except Exception as e:
            # Non-blocking error: if Redis save fails, we still return the task ID
            # but we log it as an error.
            logger.error("main: [FASTAPI]: Failed to save user-task mapping in Redis: %s", e, exc_info=True)

        return {
            "message": "Code generation task accepted",
            "task_id": task_id,
            "status": "queued",
        }

    except Exception as e:
        logger.error("main: [FASTAPI]: Error queuing task: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {str(e)}") from e
