"""Background task definitions for Huey task queue."""

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

    time.sleep(5)  # Simulate 5 seconds of work

    result = f"Processing result: {some_data.upper()}"

    #  Log our result!
    logger.info("test_task: [HUEY WORKER]: Task completed! Result: %s", result)

    return result
