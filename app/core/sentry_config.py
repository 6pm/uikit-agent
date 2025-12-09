"""Sentry configuration module."""

import os
from typing import Literal

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.utils.logger_config import logger

ENVIRONMENT = os.getenv("ENV", "local")
SENTRY_DSN = os.getenv("SENTRY_DSN")


def init_sentry(service_name: Literal["api", "huey_worker"]):
    """
    Shared initialization function.
    service_name: helps distinguish where the error came from (api or huey_worker).
    """

    if not SENTRY_DSN:
        logger.warning("SENTRY_DSN is not set, skipping Sentry initialization")
        return

    # Basic integrations (FastAPI integrations only needed for API)
    integrations = []
    if service_name == "api":
        integrations = [StarletteIntegration(), FastApiIntegration()]

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        send_default_pii=True,
        environment=ENVIRONMENT,
        traces_sample_rate=1.0 if ENVIRONMENT == "local" else 0.2,
        integrations=integrations,
    )

    # Set global tag for the process for better debugging
    sentry_sdk.set_tag("service", service_name)
