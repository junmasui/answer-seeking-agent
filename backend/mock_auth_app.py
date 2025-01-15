"""
See: https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
and https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
"""
from typing import Annotated
import logging

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from mock_auth import access_token_from_login, User, Token, get_current_user_from_token

logger = logging.getLogger(__name__)


app = FastAPI()


@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """Return a JWT token for the user specified in the OAuth2 FormData.
    """

    return access_token_from_login(form_data.username, form_data.password)

# authentication is optional: When HTTP Authorization header is not available,
# the dependency will return None instead of throwing a 401.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    auto_error=False)


async def get_current_active_user(token: Annotated[str, Depends(oauth2_scheme)]):
    return await get_current_user_from_token(token)


@app.get("/users/me/", response_model=User)
async def who_am_i(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    if current_user is None:
        current_user = User(username=None)
    return current_user
