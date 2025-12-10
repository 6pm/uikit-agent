"""Sentry configuration module."""

from typing import Literal

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.core.settings import settings
from app.utils.logger_config import logger


def init_sentry(service_name: Literal["api", "huey_worker"]):
    """
    Shared initialization function.
    service_name: helps distinguish where the error came from (api or huey_worker).
    """

    if not settings.SENTRY_DSN:
        logger.warning("SENTRY_DSN is not set, skipping Sentry initialization")
        return

    # Basic integrations (FastAPI integrations only needed for API)
    integrations = []
    if service_name == "api":
        integrations = [StarletteIntegration(), FastApiIntegration()]

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        send_default_pii=True,
        environment=settings.ENV,
        traces_sample_rate=1.0 if settings.ENV == "local" else 0.2,
        integrations=integrations,
    )

    # Set global tag for the process for better debugging
    sentry_sdk.set_tag("service", service_name)
