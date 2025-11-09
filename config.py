import os
from huey import RedisHuey

# Docker Compose will create a service named 'redis'
# We get this name from the environment variable,
# or use 'redis' as default.
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')

# Create Huey instance
huey = RedisHuey('my_app', host=REDIS_HOST, port=6379)
