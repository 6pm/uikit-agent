"""Database module for Redis connection."""

import redis.asyncio as redis

# Global variable, initially empty
redis_client: redis.Redis | None = None
