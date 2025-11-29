"""Logging configuration module using Rich."""

import logging

from rich.logging import RichHandler


def setup_logging():
    """Configure logging for the application using RichHandler."""
    # Configure logging for Huey via RichHandler
    # This will automatically colorize Huey logs, your tasks, and system messages
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",  # Rich adds time and level automatically, so we keep only the message
        datefmt="[%X]",  # Time format (only hours:minutes:seconds)
        handlers=[
            RichHandler(
                rich_tracebacks=True,  # Beautiful colored error tracebacks
                markup=True,  # Allows writing "[bold red]Error![/]" in logs
            )
        ],
    )
