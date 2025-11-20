"""Tasks package - exposes the Huey instance for task queue consumers."""
from config import huey

# Import all tasks so they are registered with Huey
# This is required when running: huey_consumer tasks.huey
from . import testing  # noqa: F401
from . import code_generation_task  # noqa: F401

__all__ = ['huey']
