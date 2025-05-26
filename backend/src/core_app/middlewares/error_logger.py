import logging

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Configure logging
logger = logging.getLogger(__name__)


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs HTTP requests and responses for error status codes.

    Captures and logs request/response details when HTTP status codes are >= 400,
    helping with debugging and monitoring of API errors.
    """

    def __init__(self, app: ASGIApp):
        """Initialize the error logging middleware with the ASGI application."""
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """
        Handle HTTP requests and log errors for responses with status codes >= 400.

        Captures request and response bodies for logging purposes while preserving
        the original request body for downstream handlers.
        """
        try:
            # Read the request body
            request_body_bytes = await request.body()
            try:
                request_body_text = request_body_bytes.decode('utf-8')
            except UnicodeDecodeError:
                request_body_text = request_body_bytes.decode('utf-8', errors='replace')

            # Reassign body so downstream can still read it
            request._body = request_body_bytes

            response = await call_next(request)

            if response.status_code >= 400:
                response_body = b''
                async for chunk in response.body_iterator:
                    response_body += chunk

                # Clone the response
                new_response = Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )

                logger.warning(
                    '\nHTTP %s %s\nRequest Body: %s\nResponse Status: %s\nResponse Body: %s\n',
                    request.method,
                    request.url,
                    request_body_text,
                    response.status_code,
                    response_body.decode('utf-8', errors='replace'),
                )

                return new_response
            return response

        except Exception as ex:
            logger.warning(
                '\nHTTP %s %s\nRequest Body: %s\nException: %s\n',
                request.method,
                request.url,
                request_body_text,
                str(ex),
            )
            raise  # re-raise so FastAPI returns default 500 response
