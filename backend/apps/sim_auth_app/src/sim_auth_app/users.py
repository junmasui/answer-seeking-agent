import logging
import uuid

from .models import User

logger = logging.getLogger(__name__)


def generate_uuid_from_username(name):
    """
    Generate a deterministic UUID from a username using UUID5.

    Uses a custom namespace to ensure consistent UUID generation for the same username across
    application restarts.
    """
    # Custom namespace
    namespace = uuid.UUID(hex='cdff7507b56c4c81a5cb29bf6aaa9de1')

    # Generate the UUID from the namespace and name
    return uuid.uuid5(namespace, name)


def get_user_by_name(*, username: str = None):
    """
    Retrieve a user object by username.

    Creates a User object with a deterministic UUID generated from the username.
    """
    userid = generate_uuid_from_username(username)
    return User(userid=userid, username=username)


def authenticate_user(username: str, password: str):
    """
    Returns the user object specified by username only when the password check passed.

    Otherwise None is returned.
    """
    # When the mock password is blank or less than 3 characters, fail the
    # password check.
    if len(password) < 3:
        return None

    # Since we are simulating authentication, the password check always passes here.
    user = get_user_by_name(username=username)

    return user
