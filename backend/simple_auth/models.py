"""
See: https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
and https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
"""
from typing import Optional
import uuid
from enum import StrEnum

from pydantic import BaseModel, Field

#
#
#
class Scope(StrEnum):
    DOC_READ = 'doc:read'
    DOC_WRITE = 'doc:write'
    DOC_INGEST = 'doc:ingest'
    DOC_INGEST_ALL = 'doc:ingest:all'

    QUERY = 'query'

    ADMIN = 'admin'

#
# Models
#

class Token(BaseModel):
    access_token: str
    token_type: str
    # Number of seconds until access token expires.
    expires_in: int
    refresh_token: Optional[str] = None


class TokenData(BaseModel):
    userid: uuid.UUID
    username: str
    scope: str | None


class User(BaseModel):
    userid: uuid.UUID
    username: Optional[str] = None
    scopes: Optional[list[str]] = None
