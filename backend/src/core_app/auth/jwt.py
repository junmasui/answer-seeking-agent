"""
Provides JWT (JSON Web Token) authentication and authorization for FastAPI applications.

See: https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
and https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
"""

import logging

import jwt
from jwt.exceptions import InvalidTokenError

from ..app_config import get_app_config
from .error import raise_credentials_error
from .models import User

ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30

logger = logging.getLogger(__name__)

#
# Use token
#


def _decode_token_data(token: str):
    """
    Decode JWT token and extract user data.

    Validates the token signature and extracts userid, username, and scope claims. Raises
    credentials error for invalid or malformed tokens.
    """
    try:
        secret_key = get_app_config().application_jwt_secret
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])

        # JWT for OAuth 2 (RFC 7523)
        # Claims that MUST be in the token:
        #   sub (subject): An identifier for the resource owner, or for the client in the case
        #     of a client credentials grant.
        # Claims that SHOULD be in the token:
        #   scope: If the `scope` parameter was present in the authorization request.
        userid: str = payload.get('sub')
        scope: str = payload.get('scope')
        if userid is None:
            raise_credentials_error('Bearer')
        scopes = scope.split(' ')

        user = User(userid=userid, scope=scopes)
    except InvalidTokenError:
        raise_credentials_error('Bearer')
    return user


async def get_current_user_from_token(token: str):
    """
    Extract and validate user information from a JWT token.

    Returns the authenticated user object or None if no token is provided. Raises credentials error
    for invalid tokens.
    """
    if not token:
        return None

    user = _decode_token_data(token)

    if user is None:
        raise_credentials_error('Bearer')
    return user
