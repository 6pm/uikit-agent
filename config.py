"""Configuration module for Huey task queue with Redis backend."""
import os
import logging
from huey import RedisHuey

# Docker Compose will create a service named 'redis'
# We get this name from the environment variable,
# or use 'redis' as default.
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')

# Configure logging for Huey
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create Huey instance with logging enabled
huey = RedisHuey('my_app', host=REDIS_HOST, port=6379)
