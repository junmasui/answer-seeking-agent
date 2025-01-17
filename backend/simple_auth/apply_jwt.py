"""
See: https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
and https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
"""
from typing import Annotated
import logging

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

from global_config import get_global_config

from .models import TokenData, User
from .users import retrieve_user


ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30

logger = logging.getLogger(__name__)

#
# Use token
#
def raise_credentials_error():
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )


def _decode_token_data(token: str):
    try:
        secret_key = get_global_config().application_jwt_secret
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

    if not token:
        return None

    token_data = _decode_token_data(token)

    user = retrieve_user(token_data)
    if user is None:
        raise_credentials_error()
    return user

# authentication is optional: When HTTP Authorization header is not available,
# the dependency will return None instead of throwing a 401.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl='token',
    auto_error=False)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    return await get_current_user_from_token(token)


def get_scoped_current_user(scope: str, missing_ok: bool = False):

    auto_error = not missing_ok
    # When auto_error=False: if HTTP Authorization header is not available,
    # the dependency will return None instead of throwing a 401.
    oauth2_scheme = OAuth2PasswordBearer(
        tokenUrl='token',
        auto_error=auto_error)

    async def scoped_user(token: Annotated[str, Depends(oauth2_scheme)]):
        user = await get_current_user_from_token(token)
        if not user:
            return None
        if not user.scopes:
            raise_credentials_error()
        if not scope in user.scopes:
            raise_credentials_error()
        return user

    return scoped_user
