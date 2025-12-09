"""
Route to retrieve task execution history from Redis.
"""

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis

from app.core.dependencies import get_redis
from app.utils.logger_config import logger

router = APIRouter(tags=["Task History"])


@router.get("/{task_id}/history", summary="Get task execution events")
async def get_task_history(task_id: str, redis_client: Redis = Depends(get_redis)) -> dict[str, Any]:
    """
    Retrieves the full list of status events for a specific task.
    This corresponds to data saved by StatusReporter.
    """
    # 1. Form the same key as in StatusReporter
    history_key = f"task:{task_id}:history"

    try:
        # 2. Get the entire list from Redis
        # lrange(key, 0, -1) means "take everything from the beginning (0) to the end (-1)"
        raw_events = await redis_client.lrange(history_key, 0, -1)

        if not raw_events:
            # Can return 404 if there's no history, or just an empty list
            # Here it's more logical to just return an empty list, because the task might have just been created
            logger.info("No history found for task %s", task_id)
            return {"task_id": task_id, "count": 0, "events": []}

        # 3. Parse JSON strings back into objects
        parsed_events = []
        for event_str in raw_events:
            try:
                # Redis (with decode_responses=True) returns str, need to convert to dict
                event_data = json.loads(event_str)
                parsed_events.append(event_data)
            except json.JSONDecodeError:
                logger.warning("Skipping corrupted event log for task %s", task_id)
                continue

        # 4. Return the result
        return {"task_id": task_id, "count": len(parsed_events), "events": parsed_events}

    except Exception as e:
        logger.error("Error fetching history for %s: %s", task_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error while fetching history: {e}") from e
