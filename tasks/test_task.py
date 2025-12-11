"""Background task definitions for Huey task queue."""

import anyio

from app.utils.logger_config import logger
from config import huey


@huey.task()
def long_running_task(some_data: str):
    """
    This is a "heavy" task that simulates work (e.g. LangGraph)
    """
    # Use logger.info instead of print
    logger.info("test_task: [HUEY WORKER]: Received task! Data: %s", some_data)

    # Huey tasks must be synchronous, but we can run async code inside
    result = anyio.run(_long_running_task, some_data)

    #  Log our result!
    logger.info("test_task: [HUEY WORKER]: Task completed! Result: %s", result)

    return result


async def _long_running_task(some_data: str):
    """
    Asynchronous implementation of the long running task.
    """
    await anyio.sleep(3)  # Simulate few seconds of work

    result = f"Processing result: {some_data.upper()}"

    return result
