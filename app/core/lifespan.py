"""lifespan handler for FastAPI"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter

from app.core import database
from app.utils.logger_config import logger
from config import REDIS_HOST


# @asynccontextmanager transforms the function into a context manager.
# This allows FastAPI to use it for lifecycle management.
@asynccontextmanager
async def lifespan_handler(_app: FastAPI):
    """
    Manages the application lifecycle (Startup -> Run -> Shutdown).
    Init Redis connection to global variable and check if it is connected on startup.
    Add Rate Limiter to the application.
    """

    # ---------------------------------------------------------
    # PHASE 1: STARTUP
    # Executed once when uvicorn/server starts.
    # ---------------------------------------------------------

    logger.info("Lifespan: Starting up resources...")

    # 1. Initialize Redis connection.
    redis_client = database.init_redis_client()

    # 2. Check if Redis connection is established
    try:
        await redis_client.ping()
        logger.info("Redis connected successfully")
    except Exception as e:
        logger.error("Redis connection failed: %s", e)
        raise e

    # 3. Initialize Rate Limiter.
    # FastAPILimiter is a global object (Singleton), it needs Redis to
    # know where to store request counters.
    await FastAPILimiter.init(redis_client)

    logger.info("FastAPILimiter initialized with Redis at %s", REDIS_HOST)

    # ---------------------------------------------------------
    # PHASE 2: YIELD (Running)
    # Here we pass control back to FastAPI.
    # While the server is running and processing requests, execution "hangs" on this line.
    # ---------------------------------------------------------
    yield

    # ---------------------------------------------------------
    # PHASE 3: SHUTDOWN
    # This code executes when a stop signal is received (e.g., SIGTERM).
    # ---------------------------------------------------------

    logger.info("Lifespan: Shutting down resources...")

    # 3. Close Redis connection.
    # This is critical! If the connection is not closed, it might "hang"
    # on the Redis server side as a zombie connection, clogging memory.
    await redis_client.close()

    logger.info("Redis connection closed safely")
