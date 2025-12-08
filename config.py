"""Configuration module for Huey task queue with Redis backend."""

import asyncio
import os

import uvloop
from dotenv import load_dotenv
from huey import RedisHuey

from src.logger_config import setup_logging

# Load environment variables from .env file
load_dotenv()

# Docker Compose will create a service named 'redis'
# We get this name from the environment variable,
# or use 'redis' as default.
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")

# Configure logging
setup_logging()

# Create Huey instance with logging enabled
huey = RedisHuey("my_app", host=REDIS_HOST, port=6379)


@huey.on_startup()
def patch_asyncio():
    """Patch asyncio to use uvloop"""
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
