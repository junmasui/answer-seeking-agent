import uuid

from .models import User, TokenData

def generate_uuid_from_username(name):
    # Custom namespace
    namespace = uuid.UUID(hex='cdff7507b56c4c81a5cb29bf6aaa9de1')

    # Generate the UUID from the namespace and name
    return uuid.uuid5(namespace, name)

def get_user_by_name(*, username: str = None):
    userid = generate_uuid_from_username(username)
    return User(userid=userid, username=username)

def get_user_by_id(*, userid: str = None):
    return User(userid=userid)


def authenticate_user(username: str, password: str):
    """Returns the user object specified by username only when
    the password check passed. Otherwise None is returned.
    """
    user = get_user_by_name(username=username)

    # Since we are simulating authentication, the password check always passes here.

    return user

def retrieve_user(token_data: TokenData):
    """Returns the user object specified in the token data.
    """
    user = get_user_by_id(userid=token_data.userid)

    user.username = token_data.username
    user.scopes = token_data.scope.split(' ')

    return user

