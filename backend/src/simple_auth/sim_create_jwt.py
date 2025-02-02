"""
See: https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
and https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
"""
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
import uuid
import math
import logging

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from global_config import get_global_config

from .models import Token, Scope
from .users import authenticate_user


ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30

logger = logging.getLogger(__name__)

#
# Simulated token creation
#


def _create_access_token(*,
                         userid: uuid.UUID,
                         username: str,
                         expires_in: Optional[timedelta] = None,
                         scopes: Optional[list[str]] = None,
                         additional_claims: Optional[dict] = None) -> Token:
    """
    Simulates an actual token creation inside an true authentication service.
    """
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

    secret_key = get_global_config().application_jwt_secret
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)

    # Round down so that the information we give back to the client
    # is always correct regarding the expiration.
    expires_in_secs = math.floor(expires_in.total_seconds())
    return Token(access_token=encoded_jwt, expires_in=expires_in_secs, token_type='bearer')


def create_token_from_login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """
    Simulates the user-password workflow inside an true authentication service.
    """

    user = authenticate_user(username=form_data.username,
                             password=form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    scopes = [
        Scope.DOC_READ,
        Scope.DOC_WRITE,
        Scope.DOC_INGEST,
        Scope.DOC_INGEST_BULK,
        Scope.QUERY,
        Scope.ADMIN
    ]

    access_token = _create_access_token(
        additional_claims={}, userid=user.userid, username=user.username, scopes=scopes
    )
    return access_token


