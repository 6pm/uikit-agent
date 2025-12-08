"""Background task definitions for Huey task queue."""

import asyncio
import time

from config import huey
from src.logger_config import logger


@huey.task()
def long_running_task(some_data: str):
    """
    This is a "heavy" task that simulates work (e.g. LangGraph)
    """
    # Use logger.info instead of print
    logger.info("test_task: [HUEY WORKER]: Received task! Data: %s", some_data)

    # Huey tasks must be synchronous, but we can run async code inside
    result = asyncio.run(_long_running_task(some_data))

    #  Log our result!
    logger.info("test_task: [HUEY WORKER]: Task completed! Result: %s", result)

    return result


async def _long_running_task(some_data: str):
    """
    Asynchronous implementation of the long running task.
    """
    time.sleep(3)  # Simulate few seconds of work

    result = f"Processing result: {some_data.upper()}"

    return result
