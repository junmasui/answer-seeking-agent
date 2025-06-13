"""
Defines Pydantic models for authentication and user representation.

See: https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
and https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
"""

import uuid
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel


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


class User(BaseModel):
    """Represents a user with identification and authorization scopes."""

    userid: uuid.UUID
    scopes: Optional[list[str]] = None
