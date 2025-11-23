"""Configuration module for Huey task queue with Redis backend."""

import asyncio
import logging
import os

import uvloop
from dotenv import load_dotenv
from huey import RedisHuey
from rich.logging import RichHandler

# Load environment variables from .env file
load_dotenv()

# Docker Compose will create a service named 'redis'
# We get this name from the environment variable,
# or use 'redis' as default.
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")

# Configure logging for Huey via RichHandler
# Це автоматично зробить логи Huey, твоїх тасок і системних повідомлень кольоровими
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",  # Rich сам додає час і рівень, тому тут лишаємо тільки повідомлення
    datefmt="[%X]",  # Формат часу (тільки години:хвилини:секунди)
    handlers=[
        RichHandler(
            rich_tracebacks=True,  # Гарні кольорові трейсбеки помилок
            markup=True,  # Дозволяє писати "[bold red]Error![/]" у логах
        )
    ],
)

# Create Huey instance with logging enabled
huey = RedisHuey("my_app", host=REDIS_HOST, port=6379)


@huey.on_startup()
def patch_asyncio():
    """Patch asyncio to use uvloop"""
    print("🚀 Worker starting: Installing uvloop...")
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
