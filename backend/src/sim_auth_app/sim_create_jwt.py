"""
Handles the creation of JWT access tokens for a simulated authentication service.

See: https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
and https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
"""

import logging
import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from .app_config import get_lib_config
from .models import Scope, Token
from .users import authenticate_user, get_user_by_name

ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

logger = logging.getLogger(__name__)

#
# Simulated token creation
#


def _create_access_token(
    *,
    userid: uuid.UUID,
    username: str,
    expires_in: Optional[timedelta] = None,
    scopes: Optional[list[str]] = None,
    additional_claims: Optional[dict] = None,
) -> Token:
    """Simulates an actual token creation inside an true authentication service."""
    to_encode = {'sub': userid.urn}

    if not expires_in:
        expires_in = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_in
    to_encode.update({'exp': expire})

    #
    to_encode['email'] = username

    # Scopes are included as a space-delimited string on the 'scope' claim.
    if scopes:
        to_encode['scope'] = ' '.join(scopes)

    if additional_claims:
        to_encode.update(additional_claims)

    secret_key = get_lib_config().application_jwt_secret
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)

    # Round down so that the information we give back to the client
    # is always correct regarding the expiration.
    expires_in_secs = math.floor(expires_in.total_seconds())
    return Token(access_token=encoded_jwt, expires_in=expires_in_secs, token_type='bearer')


def _create_refresh_token(
    *, userid: uuid.UUID, expires_in: Optional[timedelta] = None, additional_claims: Optional[dict] = None
) -> str:
    """Simulates an actual token creation inside an true authentication service."""
    to_encode = {'sub': userid.urn}

    if not expires_in:
        expires_in = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    expire = datetime.now(timezone.utc) + expires_in
    to_encode.update({'exp': expire})

    if additional_claims:
        to_encode.update(additional_claims)

    secret_key = get_lib_config().application_jwt_secret
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(*, encoded_token: str) -> dict:
    """Decodes a JWT token and returns the payload."""
    try:
        payload = jwt.decode(encoded_token, get_lib_config().application_jwt_secret, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError as e:
        logger.warning(f'Failed to decode token: {e}')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token', headers={'WWW-Authenticate': 'Bearer'}
        )


def create_token_from_login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """Simulates the user-password workflow inside an true authentication service."""
    logger.info('creating JWT token from login form')
    user = authenticate_user(username=form_data.username, password=form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    scopes = [Scope.DOC_READ, Scope.DOC_WRITE, Scope.DOC_INGEST, Scope.QUERY, Scope.ADMIN]

    access_token = _create_access_token(additional_claims={}, userid=user.userid, username=user.username, scopes=scopes)

    refresh_token = _create_refresh_token(userid=user.userid)
    access_token.refresh_token = refresh_token

    return access_token


def create_token_from_refresh_token(refresh_token: str):
    """Simulates the refresh token workflow inside a true authentication service."""
    logger.info('creating JWT token from refresh token')
    payload = decode_token(encoded_token=refresh_token)
    userid_urn = payload.get('sub')
    if not userid_urn:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid refresh token',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    # The 'sub' claim in the refresh token might not contain the original username,
    # so we need a way to retrieve the user. For this simulation, we'll assume
    # the user's email is in the payload, but in a real application, you would
    # look up the user by their user ID (from the 'sub' claim).
    user = get_user_by_name(username=payload.get('email'))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found', headers={'WWW-Authenticate': 'Bearer'}
        )

    # For simplicity, we'll reuse the same scopes. In a real application, you might
    # have a more sophisticated way of managing scopes.
    scopes = [Scope.DOC_READ, Scope.DOC_WRITE, Scope.DOC_INGEST, Scope.QUERY, Scope.ADMIN]

    access_token = _create_access_token(additional_claims={}, userid=user.userid, username=user.username, scopes=scopes)

    # Issue a new refresh token
    new_refresh_token = _create_refresh_token(userid=user.userid)
    access_token.refresh_token = new_refresh_token
    access_token.grant_type = 'refresh_token'

    return access_token
