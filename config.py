"""Configuration module for Huey task queue with Redis backend.

This module provides:
    - Huey instance configuration for async task processing
    - Redis connection settings
    - Task history TTL configuration
    - Worker startup hooks for initialization

The startup hook initializes:
    - uvloop event loop policy (Linux/macOS only)
    - Global Redis client for status reporting
    - Logging configuration

Note: uvloop does not work on Windows, so this module is designed for Unix-like systems.
"""

import asyncio

import uvloop  # uvloop does not work on Windows
from dotenv import load_dotenv
from huey import RedisHuey

from app.core.sentry_config import init_sentry
from app.core.settings import settings
from app.utils.logger_config import logger, setup_logging

# Load environment variables from .env file
load_dotenv()


# Configure logging
setup_logging()

# Create Huey instance with logging enabled
huey = RedisHuey("my_app", host=settings.REDIS_HOST, port=6379)


@huey.on_startup()
def startup_hook() -> None:
    """Execute once when the Huey worker starts.

    This hook performs critical initialization tasks:
        1. Configures uvloop event loop policy (Linux/macOS only)
           - Must be called at the beginning of this function
        2. Lazy imports database module to break circular dependencies
           - Import the module only when it's actually needed
        3. Initializes global Redis client for status reporting

    The initialization order is important:
        - uvloop must be set before any async operations
        - Database imports must be lazy to avoid circular dependencies
        - Redis client initialization happens last

    Raises:
        RuntimeError: If Redis connection fails during initialization.
    """
    logger.info("Huey Worker: Bootstrapping...")

    # 0. Initialize Sentry for Huey tasks
    init_sentry(service_name="huey_worker")

    # 1. Configure uvloop (Only for Linux/macOS)
    # uvloop must be at the beginning of this function
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    logger.info("Huey Worker: uvloop policy activated")

    # 2. Lazy Import to break circular dependency
    # Import the module only when it's actually needed
    from app.core import database  # pylint: disable=import-outside-toplevel

    # 3. Initialize Redis
    logger.info("Huey Worker: Initializing global Redis client...")
    database.init_redis_client()
    logger.info("Huey Worker: Ready to process tasks.")
