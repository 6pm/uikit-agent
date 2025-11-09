"""Background task definitions for Huey task queue."""
import time
import logging
from config import huey

# Get logger instance
logger = logging.getLogger(__name__)

@huey.task()
def long_running_task(some_data: str):
    """
    This is a "heavy" task that simulates work (e.g. LangGraph)
    """
    # Use logger.info instead of print
    logger.info("[HUEY WORKER]: Received task! Data: %s", some_data)

    time.sleep(5) # Simulate 5 seconds of work

    result = f"Processing result: {some_data.upper()}"

    #  Log our result!
    logger.info("[HUEY WORKER]: Task completed! Result: %s", result)

    return result
