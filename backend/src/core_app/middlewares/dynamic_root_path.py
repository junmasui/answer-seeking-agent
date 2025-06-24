from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class DynamicRootPathMiddleware(BaseHTTPMiddleware):
    """
    Middleware to dynamically set the root_path based on the X-Forwarded-Prefix header.

    This allows the application to work correctly behind a reverse proxy with a dynamic path prefix.
    The proxy must be configured to pass the 'X-Forwarded-Prefix' header.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Checks for the 'X-Forwarded-Prefix' and updates the request's root_path scope."""
        forwarded_prefix = request.headers.get('X-Forwarded-Prefix')
        if forwarded_prefix:
            request.scope['root_path'] = forwarded_prefix.rstrip('/')

        response = await call_next(request)
        return response
