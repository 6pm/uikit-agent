"""lifespan handler for FastAPI"""

from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter

from config import REDIS_HOST
from src.logger_config import logger


# @asynccontextmanager transforms the function into a context manager.
# This allows FastAPI to use it for lifecycle management.
@asynccontextmanager
async def lifespan_handler(_app: FastAPI):
    """
    Manages the application lifecycle (Startup -> Run -> Shutdown).
    """

    # ---------------------------------------------------------
    # PHASE 1: STARTUP
    # Executed once when uvicorn/server starts.
    # ---------------------------------------------------------

    logger.info("Lifespan: Starting up resources...")

    # 1. Create Redis connection.
    # We create a connection pool to be used for the Rate Limiter.
    # decode_responses=True means we get strings (str), not bytes.
    redis_connection = redis.from_url(f"redis://{REDIS_HOST}:6379", encoding="utf-8", decode_responses=True)

    # 2. Initialize Rate Limiter.
    # FastAPILimiter is a global object (Singleton), it needs Redis to
    # know where to store request counters.
    await FastAPILimiter.init(redis_connection)

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
    await redis_connection.close()

    logger.info("Redis connection closed safely")
