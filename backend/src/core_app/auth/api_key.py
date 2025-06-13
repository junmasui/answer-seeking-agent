import hashlib
import logging
import uuid

from fastapi import HTTPException, status

from .models import TokenData, User
from ..app_config import get_app_config

logger = logging.getLogger(__name__)

def raise_credentials_error():
    """Raise an HTTP 401 Unauthorized error for invalid credentials."""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'X-API-Key'},
    )


async def get_current_user_from_api_key(api_key: str) -> User | None:
    """
    Validates an API key and returns TokenData if valid.

    This is a simplified example. In a real application, API keys should be securely stored and
    managed, likely in a database, and associated with specific user entities and permissions.
    """
    # Check against a statically configured API key.
    # This would ideally come from a secure configuration or database.

    config = get_app_config()

    static_key = config.static_api_key

    if static_key and api_key == static_key:

        static_user_id = config.static_api_key_user_id
        static_username = config.static_api_key_username
        static_scope = config.static_api_key_scope

        hex_string = hashlib.md5(static_user_id.encode("utf-8")).hexdigest()
        static_user_id = uuid.UUID(hex=hex_string)        

        logger.info(f"Authenticated user '{static_username}' using static API key.")

        if static_user_id and static_username:
            user = User(userid=static_user_id)

            user.username = static_username
            user.scopes = static_scope.split(' ')

            return user
        else:
            # This case implies the API key was valid and produced TokenData,
            # but retrieve_user failed to find/construct a user from that TokenData.
            # This might indicate an inconsistency or an issue with retrieve_user
            # for API key-derived TokenData.
            logger.error(
                f'API key valid for {static_username}, but failed with incomplete configuration.'
            )
            raise_credentials_error()  # Treat as overall credential failure
    else:
        # _get_user_from_api_key returned None, meaning the API key itself was invalid.
        # We raise an error because an auth attempt was made with a bad key.
        raise_credentials_error()



    # Add more sophisticated API key validation here (e.g., database lookup)
    # Example:
    # db_user = await query_db_for_api_key_user(api_key)
    # if db_user:
    #     return TokenData(userid=db_user.id, username=db_user.email, scope=db_user.scopes)

    logger.warning(f'Invalid API key provided: {api_key[:5]}...')
    return None