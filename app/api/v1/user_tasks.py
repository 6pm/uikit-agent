"""
Route to retrieve list of tasks for a user from Redis.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis

from app.core.dependencies import get_redis
from app.utils.logger_config import logger

router = APIRouter(tags=["User Tasks"])


@router.get("/tasks/{user_id}", summary="Get list of tasks for a user")
async def get_user_tasks(user_id: str, redis_client: Redis = Depends(get_redis)) -> dict[str, Any]:
    """
    Retrieves the detailed list of tasks for a specific user.
    Fetches IDs first, then hydrates them with metadata using a pipeline.
    """

    user_tasks_key = f"user:{user_id}:tasks"

    try:
        # 1. Get List of IDs (Fast, O(N))
        # Get last 50 task IDs
        task_ids = await redis_client.lrange(user_tasks_key, 0, 49)

        if not task_ids:
            logger.info("No tasks found for user %s", user_id)
            return {"tasks": []}

        # 2. Hydration: Fetch details for each ID in one go (Pipeline)
        async with redis_client.pipeline() as pipe:
            for t_id in task_ids:
                # If redis returns bytes, verify if decoding is needed.
                # Assuming your redis_client handles decode_responses=True, otherwise: t_id.decode()
                meta_key = f"task:{t_id}:metadata"
                pipe.hgetall(meta_key)

            # Execute all hgetall commands at once
            tasks_data = await pipe.execute()

        # 3. Filter & Clean results
        # Some tasks might be expired (TTL) but their ID is still in the list.
        # We filter out empty results.
        valid_tasks = [task for task in tasks_data if task]

        # 4. Return the result
        return {"tasks": valid_tasks}

    except Exception as e:
        logger.error("Error fetching tasks for user %s: %s", user_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error while fetching tasks: {e}") from e
