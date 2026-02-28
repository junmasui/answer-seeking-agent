"""
Provides JWT (JSON Web Token) authentication and authorization for FastAPI applications.

See: https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
and https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
"""

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer

from ..auth import Scope
from .api_key import get_current_user_from_api_key
from .error import raise_credentials_error
from .jwt_util import get_current_user_from_token

ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30

logger = logging.getLogger(__name__)


# authentication is optional: When HTTP Authorization header is not available,
# the dependency will return None instead of throwing a 401.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token', auto_error=False)
api_key_header = APIKeyHeader(name='X-API-Key', auto_error=False)


async def _get_current_user(
    bearer_token: Annotated[str | None, Depends(oauth2_scheme)] = None,
    x_api_key: Annotated[str | None, api_key_header] = None,
    missing_ok: bool = False,
):
    """
    FastAPI dependency to get the current authenticated user.

    Tries JWT Bearer token first. If not present or invalid, tries X-API-Key header.
    """
    if bearer_token:
        # get_current_user_from_token will raise HTTPException if token is invalid or user
        # not found. It returns None only if the input `token` string itself is None/empty,
        # but oauth2_scheme (with auto_error=False) handles making bearer_token None if no
        # header.
        user = await get_current_user_from_token(bearer_token)
        if user is not None:
            return user

    if x_api_key:
        user = await get_current_user_from_api_key(x_api_key)
        if user is not None:
            return user

    # No valid user was retrieved by get_current_user. This implies no valid
    # credentials were provided (or get_current_user already raised an error).
    if not missing_ok:
        # If user is None (no auth provided or invalid auth that get_current_user
        # handled by returning None) and missing is NOT ok, raise a 401 error.
        raise_credentials_error('Bearer, X-API-Key')

    return None


def get_scoped_current_user(scope: str | list[str], missing_ok: bool = False):
    """
    Create a FastAPI dependency that validates user authentication and authorization scope.

    Supports both JWT Bearer tokens and X-API-Key header.

    Returns a dependency function that checks if the user has the required scope. If missing_ok is
    True, returns None when no valid authentication is provided instead of raising an error. If
    missing_ok is False and no valid authentication is provided, a 401 error is raised. If
    authentication is successful but the required scope is missing, a 403 error is raised.
    """

    async def scoped_user(
        # Use the global oauth2_scheme (auto_error=False) to get bearer token if present
        bearer_token: Annotated[str | None, Depends(oauth2_scheme)] = None,
        x_api_key: Annotated[str | None, Depends(api_key_header)] = None,
    ):
        # get_current_user handles trying bearer_token, then x_api_key.
        # It returns a user object if successful, None if no auth was provided,
        # or raises HTTPException if auth was provided but was invalid.
        logger.info('get_scoped_current_user: retrieving user (missing_ok=%s)', missing_ok)
        user = await _get_current_user(bearer_token=bearer_token, x_api_key=x_api_key, missing_ok=missing_ok)
        logger.info('get_scoped_current_user: retrieved user: %s', user)

        if user is not None:
            # Check for the required scope.
            if not user.scopes or (scope not in user.scopes and Scope.ADMIN not in user.scopes):
                # User is authenticated, but not authorized for this specific scope.
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail=f"Not enough permissions. Requires scope: '{scope}'."
                )
        elif missing_ok:
            return None
        else:
            # Should be unreachable if _get_current_user works as expected (raises 401 when missing_ok=False),
            # but serves as a failsafe.
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
            )
        return user

    return scoped_user
