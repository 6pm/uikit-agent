"""
Status reporter service.
"""

import json

from agents.code_generator.state import StatusEvent
from app.core.database import get_redis_client
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

    async def report(self, status_event: StatusEvent):
        """
        Records a status event to Redis immediately.

        Args:
            status_event: The event data to record.
        """
        client = get_redis_client()

        if not client:
            logger.error("StatusReporter: Failed to get Redis client")
            return

        # 1. Append the event to the end of the list (History Log)
        await client.rpush(self.history_key, json.dumps(status_event))
        # Set TTL so history doesn't persist forever
        await client.expire(self.history_key, settings.TASK_HISTORY_TTL)

        logger.info("StatusReporter: Event %s reported to Redis", status_event)
