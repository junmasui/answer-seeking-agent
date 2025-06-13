"""
Provides JWT (JSON Web Token) authentication and authorization for FastAPI applications.

See: https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
and https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
"""

import logging
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

from core_app.auth.api_key import get_current_user_from_api_key

from ..app_config import get_app_config
from .models import TokenData, User

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
        secret_key = get_app_config().application_jwt_secret
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


async def get_current_user_from_token(token: str):
    """
    Extract and validate user information from a JWT token.

    Returns the authenticated user object or None if no token is provided. Raises credentials error
    for invalid tokens.
    """
    if not token:
        return None

    token_data = _decode_token_data(token)

    user = User(userid=token_data.userid)

    user.username = token_data.username
    user.scopes = token_data.scope.split(' ')

    if user is None:
        raise_credentials_error()
    return user
