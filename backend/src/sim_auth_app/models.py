"""
Defines Pydantic models for authentication and user representation.

See: https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
and https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
"""

import uuid
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


#
#
#
class Scope(StrEnum):
    """Enumeration of available authorization scopes for API access control."""

    DOC_READ = 'doc:read'
    DOC_WRITE = 'doc:write'
    DOC_INGEST = 'doc:ingest'

    PROMPT_READ = 'prompt:read'
    PROMPT_WRITE = 'prompt:write'

    QUERY = 'query'

    ADMIN = 'admin'


#
# Models
#


class Token(BaseModel):
    """Represents an authentication token with expiration and optional refresh token."""

    access_token: str
    token_type: str
    # Number of seconds until access token expires.
    expires_in: int
    refresh_token: Optional[str] = None
    # The grant type for the token.
    grant_type: Optional[str] = None


class User(BaseModel):
    """Represents a user with identification and authorization scopes."""

    userid: uuid.UUID
    username: Optional[str] = None
    scopes: Optional[list[str]] = None
