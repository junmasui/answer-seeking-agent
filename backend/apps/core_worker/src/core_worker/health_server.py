"""
Lightweight HTTP health-check server for the Celery worker.

Celery workers do not expose an HTTP endpoint.  This module starts a tiny
``http.server`` in a daemon thread so that Docker health checks can reach
the worker via ``curl``.

The handler recognises the ``X-Health-Check`` header, tags the current
OpenTelemetry span (if one is active), and mirrors the header back on
the response — matching the behaviour of the FastAPI
:class:`HealthCheckMiddleware`.
"""

import http.server
import logging
import threading

from opentelemetry import trace

logger = logging.getLogger(__name__)

HEALTH_CHECK_HEADER = 'X-Health-Check'
HEALTH_CHECK_SPAN_ATTRIBUTE = 'health_check'

_server: http.server.HTTPServer | None = None


class _HealthHandler(http.server.BaseHTTPRequestHandler):
    """Minimal request handler that always returns ``200 OK``."""

    def do_GET(self):  # noqa: N802 — must match http.server API
        is_health_check = self.headers.get(HEALTH_CHECK_HEADER)
        if is_health_check:
            span = trace.get_current_span()
            if span and span.is_recording():
                span.set_attribute(HEALTH_CHECK_SPAN_ATTRIBUTE, True)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        if is_health_check:
            self.send_header(HEALTH_CHECK_HEADER, 'true')
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

    # Silence per-request log lines that would pollute celery output.
    def log_message(self, format, *args):  # noqa: A002
        pass


def start(port: int = 8101) -> None:
    """Start the health-check HTTP server on *port* in a daemon thread."""
    global _server  # noqa: PLW0603
    if _server is not None:
        return
    try:
        _server = http.server.HTTPServer(('0.0.0.0', port), _HealthHandler)
        thread = threading.Thread(
            target=_server.serve_forever,
            daemon=True,
            name='healthcheck-server',
        )
        thread.start()
        logger.info('Health-check server started on port %d', port)
    except Exception:
        logger.exception('Failed to start health-check server on port %d', port)


def stop() -> None:
    """Shut down the health-check HTTP server (if running)."""
    global _server  # noqa: PLW0603
    if _server is not None:
        _server.shutdown()
        _server = None
        logger.info('Health-check server stopped')
