"""
Dependencies module.

This module provides dependency injection helpers for FastAPI endpoints,
primarily for accessing the global Redis client.
"""

import redis.asyncio as redis

from app.core import database


async def get_redis() -> redis.Redis:
    """
    Returns the global Redis instance.

    Does not close the connection because it is shared across the entire app.
    """
    if database.redis_client is None:
        raise RuntimeError("Redis client is not initialized. Check lifespan.")

    return database.redis_client
