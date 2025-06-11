"""
See: https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
and https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
"""

import logging
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, status  # Modified import
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

from .lib_config import get_lib_config
from .models import TokenData
from .users import retrieve_user

ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30

logger = logging.getLogger(__name__)


#
# Use token
#
def raise_credentials_error():
    """Raise an HTTP 401 Unauthorized error for invalid credentials."""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )


def _decode_token_data(token: str):
    """
    Decode JWT token and extract user data.

    Validates the token signature and extracts userid, username, and scope claims. Raises
    credentials error for invalid or malformed tokens.
    """
    try:
        secret_key = get_lib_config().application_jwt_secret
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])

        userid: str = payload.get('sub')
        username: str = payload.get('email')
        scope: str = payload.get('scope')
        if username is None:
            raise_credentials_error()
        token_data = TokenData(userid=userid, username=username, scope=scope)
    except InvalidTokenError:
        raise_credentials_error()
    return token_data


async def _get_user_from_api_key(api_key: str, config) -> TokenData | None:
    """
    Validates an API key and returns TokenData if valid.

    This is a simplified example. In a real application, API keys should be securely stored and
    managed, likely in a database, and associated with specific user entities and permissions.
    """
    # Example: Check against a statically configured API key.
    # This would ideally come from a secure configuration or database.
    # For demonstration, we assume lib_config might have these (they'd need to be added).
    static_key = getattr(config, 'static_api_key', None)
    static_user_id = getattr(config, 'static_api_key_user_id', 'api_user_default_id')
    static_username = getattr(config, 'static_api_key_username', 'api_user@example.com')
    static_scope = getattr(config, 'static_api_key_scope', 'api:read api:write')

    if static_key and api_key == static_key:
        logger.info(f"Authenticated user '{static_username}' using static API key.")
        return TokenData(userid=static_user_id, username=static_username, scope=static_scope)

    # Add more sophisticated API key validation here (e.g., database lookup)
    # Example:
    # db_user = await query_db_for_api_key_user(api_key)
    # if db_user:
    #     return TokenData(userid=db_user.id, username=db_user.email, scope=db_user.scopes)

    logger.warning(f'Invalid API key provided: {api_key[:5]}...')
    return None


async def get_current_user_from_token(token: str):
    """
    Extract and validate user information from a JWT token.

    Returns the authenticated user object or None if no token is provided. Raises credentials error
    for invalid tokens.
    """
    if not token:
        return None

    token_data = _decode_token_data(token)

    user = retrieve_user(token_data)
    if user is None:
        raise_credentials_error()
    return user


# authentication is optional: When HTTP Authorization header is not available,
# the dependency will return None instead of throwing a 401.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token', auto_error=False)


async def get_current_user(
    bearer_token: Annotated[str | None, Depends(oauth2_scheme)] = None,
    x_api_key: Annotated[str | None, Header(alias='X-API-Key')] = None,
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
        user_via_jwt = await get_current_user_from_token(bearer_token)
        if user_via_jwt:
            return user_via_jwt

    if x_api_key:
        config = get_lib_config()
        token_data_from_api_key = await _get_user_from_api_key(x_api_key, config)
        if token_data_from_api_key:
            user_via_api_key = retrieve_user(token_data_from_api_key)
            if user_via_api_key:
                return user_via_api_key
            else:
                # This case implies the API key was valid and produced TokenData,
                # but retrieve_user failed to find/construct a user from that TokenData.
                # This might indicate an inconsistency or an issue with retrieve_user
                # for API key-derived TokenData.
                logger.error(
                    f'API key valid for {token_data_from_api_key.username}, but failed to retrieve user object.'
                )
                raise_credentials_error()  # Treat as overall credential failure
        else:
            # _get_user_from_api_key returned None, meaning the API key itself was invalid.
            # We raise an error because an auth attempt was made with a bad key.
            raise_credentials_error()

    # No authentication provided, or JWT was explicitly None and no API key.
    return None


def get_scoped_current_user(scope: str, missing_ok: bool = False):
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
        x_api_key: Annotated[str | None, Header(alias='X-API-Key')] = None,
    ):
        # get_current_user handles trying bearer_token, then x_api_key.
        # It returns a user object if successful, None if no auth was provided,
        # or raises HTTPException if auth was provided but was invalid.
        user = await get_current_user(bearer_token=bearer_token, x_api_key=x_api_key)

        if not user:
            # No valid user was retrieved by get_current_user. This implies no valid
            # credentials were provided (or get_current_user already raised an error).
            if not missing_ok:
                # If user is None (no auth provided or invalid auth that get_current_user
                # handled by returning None) and missing is NOT ok, raise a 401 error.
                raise_credentials_error()
            return None  # missing_ok is True, so return None as no auth was found

        # User object exists, now check for the required scope.
        if not user.scopes or scope not in user.scopes:
            # User is authenticated, but not authorized for this specific scope.
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"Not enough permissions. Requires scope: '{scope}'."
            )
        return user

    return scoped_user
