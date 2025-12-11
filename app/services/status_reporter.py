"""
Status reporter service.
"""

import json

import redis.asyncio as redis

from agents.code_generator.state import StatusEvent
from app.core.settings import settings
from app.utils.logger_config import logger


class StatusReporter:
    """
    Service for reporting task execution status events.

    It saves reports for each step of the workflow (validation, MCP context retrieval,
    code generation, linting, code saving) to Redis.
    """

    def __init__(self, task_id: str):
        """
        Initialize the StatusReporter.

        Args:
            task_id: The unique identifier of the task being reported.
        """
        self.task_id = task_id
        # Key for the list of events (history)
        self.history_key = f"task:{task_id}:history"

        self._redis_local = None

    async def _get_local_redis(self) -> redis.Redis:
        """
        Create connection strictly inside the current Event Loop.
        """
        if self._redis_local is None:
            # Create new Redis connection.
            # Important: redis.from_url does not block connection, it will be opened when the first command is executed.
            self._redis_local = redis.from_url(f"redis://{settings.REDIS_HOST}:6379/0", encoding="utf-8", decode_responses=True)
        return self._redis_local

    async def report(self, status_event: StatusEvent):
        """
        Records a status event to Redis immediately.

        Args:
            status_event: The event data to record.
        """
        try:
            client = await self._get_local_redis()

            if not client:
                logger.error("StatusReporter: Failed to get Redis client")
                return

            # 1. Append the event to the end of the list (History Log)
            await client.rpush(self.history_key, json.dumps(status_event))
            # Set TTL so history doesn't persist forever
            await client.expire(self.history_key, settings.TASK_HISTORY_TTL)

            logger.info("StatusReporter: Event %s reported to Redis", status_event)

        except Exception as e:
            # Important: we catch the error to avoid the entire generation process from crashing due to logs
            logger.error(f"StatusReporter failed: {e}", exc_info=True)

    async def close(self):
        """Close the connection (it is recommended to call it at the end) or in __aexit__ method"""
        if self._redis_local:
            try:
                await self._redis_local.close()
            except Exception as e:
                # Log, but do not raise the error further.
                # We don't care if the closing failed, as long as we tried.
                logger.warning(f"StatusReporter: Error closing Redis connection: {e}")
            finally:
                # Ensure the reference is cleared, so the object can be garbage collected.
                self._redis_local = None
