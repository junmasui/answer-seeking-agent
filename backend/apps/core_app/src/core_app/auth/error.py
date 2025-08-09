from fastapi import HTTPException, status


def raise_credentials_error(www_authenticate_header: str):
    """Raise an HTTP 401 Unauthorized error for invalid credentials."""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': www_authenticate_header},
    )
