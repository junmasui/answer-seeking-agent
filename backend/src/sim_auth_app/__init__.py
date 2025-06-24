"""
Defines a simple FastAPI application for user authentication and token management.

See: https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
and https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
"""

from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordRequestForm

from .models import Token
from .sim_create_jwt import create_token_from_login, create_token_from_refresh_token

app = FastAPI()


@app.get('')
@app.get('/')
@app.get('/status')
@app.get('/api/status')
async def handle_root():
    """
    Handle requests to the root path.

    Returns a simple tag line.
    """
    return {'Description': 'Simulates OAuth Service'}


@app.post('/token', response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    """Return a JWT token for the user specified in the OAuth2 FormData."""
    return create_token_from_login(form_data)


@app.post('/refresh', response_model=Token)
async def refresh_access_token(refresh_token: str) -> Token:
    """Return a new JWT token for the user specified in the refresh token."""
    return create_token_from_refresh_token(refresh_token)
