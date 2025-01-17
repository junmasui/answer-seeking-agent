"""
See: https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
and https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
"""
from typing import Annotated
import logging

from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordRequestForm

from simple_auth import create_token_from_login, User, Token, get_current_user

logger = logging.getLogger(__name__)


app = FastAPI()


@app.post('/token', response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """Return a JWT token for the user specified in the OAuth2 FormData.
    """

    return create_token_from_login(form_data)


@app.get('/users/me/', response_model=User)
async def who_am_i(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user is None:
        current_user = User(username=None)
    return current_user
