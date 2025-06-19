"""
Defines a simple FastAPI application for user authentication and token management.

See: https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
and https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
"""

from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordRequestForm

from .models import Token
from .sim_create_jwt import create_token_from_login

app = FastAPI()


@app.post('/token', response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    """Return a JWT token for the user specified in the OAuth2 FormData."""
    return create_token_from_login(form_data)
