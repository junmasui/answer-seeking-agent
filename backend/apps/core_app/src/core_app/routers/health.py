import logging
from typing import Annotated

from core import health_check
from fastapi import APIRouter, Depends

from ..auth import Scope, User, get_scoped_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get('')  # Empty path handles no trailing slash without using 307 redirect.
@router.get('/')
async def handle_health_check(_current_user: Annotated[User, Depends(get_scoped_current_user(Scope.ADMIN))]):
    """
    Handle requests to the health path.

    Returns the system health.
    """
    return await health_check()
