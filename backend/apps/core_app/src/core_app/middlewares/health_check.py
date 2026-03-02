"""
Middleware that detects the ``X-Health-Check`` HTTP request header,
annotates the current OpenTelemetry span, and mirrors the header back on the
response so that the caller can confirm the annotation was applied.
"""

import logging

from fastapi import Request
from opentelemetry import trace
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

HEALTH_CHECK_HEADER = 'X-Health-Check'
HEALTH_CHECK_SPAN_ATTRIBUTE = 'health_check'


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Detect *X-Health-Check* header, tag the OTel span, and echo the header on the response."""

    def __init__(self, app: ASGIApp):
        """Initialise the health-check middleware with the ASGI application."""
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """
        Intercept every HTTP request.

        If the ``X-Health-Check`` header is present the current span is tagged
        with ``health_check = true`` and the same header is set on the response.
        """
        is_health_check = request.headers.get(HEALTH_CHECK_HEADER)

        if is_health_check:
            span = trace.get_current_span()
            if span and span.is_recording():
                span.set_attribute(HEALTH_CHECK_SPAN_ATTRIBUTE, True)

        response = await call_next(request)

        if is_health_check:
            response.headers[HEALTH_CHECK_HEADER] = 'true'

        return response
