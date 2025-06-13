import logging

from ..app_config import get_app_config
from .error import raise_credentials_error
from .models import User

logger = logging.getLogger(__name__)


def _get_api_keys():
    config = get_app_config()

    static_api_keys = {}
    def _add_user(api_key, user_id, scope):
        user = None
        if api_key and user_id and scope:
            user = User(userid= user_id)
            user.scopes = scope.split(' ')

        static_api_keys[api_key] = user

    _add_user(config.static_api_key_1, config.static_api_key_user_id_1, config.static_api_key_scope_1)
    _add_user(config.static_api_key_2, config.static_api_key_user_id_2, config.static_api_key_scope_2)
    _add_user(config.static_api_key_3, config.static_api_key_user_id_3, config.static_api_key_scope_3)

async def get_current_user_from_api_key(api_key: str) -> User | None:
    """
    Validates an API key and returns TokenData if valid.

    This is a simplified example. In a real application, API keys should be securely stored and
    managed, likely in a database, and associated with specific user entities and permissions.
    """
    # Check against a statically configured API key.
    # This would ideally come from a secure configuration or database.

    config = get_app_config()

    if config.disable_static_api_keys:
        return None

    static_api_keys = _get_api_keys()

    if api_key in static_api_keys:

        user = static_api_keys[api_key]

        logger.debug(f"Authenticated user '{user.user_id}' using static API key.")

        if user:
            return user

        # This case implies the API key was valid but the user does not exist.
        # This might indicate an inconsistency in the configuration.
        logger.warning(f'API key valid for {user.user_id}, but failed with incomplete configuration.')
        raise_credentials_error('X-API-Key')  # Treat as overall credential failure

    if api_key:
        # The API key itself was invalid.
        # We raise an error because an auth attempt was made with a bad key.
        logger.warning(f'Invalid API key provided: {api_key[:5]}...')
        raise_credentials_error('X-API-Key')

    return None
