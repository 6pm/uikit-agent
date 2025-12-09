"""Database module for Redis connection."""

import redis.asyncio as redis

from config import REDIS_HOST

# Global variable
redis_client: redis.Redis | None = None


def init_redis_client() -> redis.Redis:
    """
    Creates and returns a Redis client.
    This function simply creates an object, it doesn't do 'await', so it's safe for synchronous calls.
    """
    global redis_client  # pylint: disable=global-statement

    # If already exists - return it (Singleton)
    if redis_client is not None:
        return redis_client

    redis_client = redis.from_url(
        f"redis://{REDIS_HOST}:6379",
        encoding="utf-8",
        decode_responses=True,  # decode_responses=True means we get strings (str), not bytes.
        # Important for worker: pool configuration
        socket_keepalive=True,  # To prevent connection drops during idle time
        health_check_interval=30,  # Redis-py will ping the server automatically
    )
    return redis_client


def get_redis_client():
    """Safely returns the client."""
    return redis_client


async def close_redis_client():
    """Closes the Redis client."""
    global redis_client  # pylint: disable=global-statement
    if redis_client:
        await redis_client.close()
        redis_client = None
