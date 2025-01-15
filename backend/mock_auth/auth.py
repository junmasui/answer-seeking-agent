"""
See: https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
and https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
"""
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel

from global_config import get_global_config

# to get a string like this run:
# openssl rand -hex 32
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

#
# Models
#

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str


def get_user(username: str):
    return User(username=username)

#
# Create tokens
#


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    return user


def create_access_token(*, username: str, expires_delta: timedelta | None = None, data: dict | None = None):
    to_encode = {"sub": username}

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})

    if data:
        to_encode.update(data)

    secret_key = get_global_config().application_jwt_secret
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt

def access_token_from_login(username, password):
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={}, username=user.username, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")



#
# Use token
#

async def get_current_user_from_token(token: str):
    def raise_credentials_error():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print('HULLO!!!!')

    if not token:
        return None

    try:
        secret_key = get_global_config().application_jwt_secret

        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise_credentials_error()
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise_credentials_error()

    user = get_user(username=token_data.username)
    if user is None:
        raise_credentials_error()
    return user

