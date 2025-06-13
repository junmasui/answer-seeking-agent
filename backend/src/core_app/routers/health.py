import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from core import health_check
from ..auth import get_scoped_current_user, Scope, User

from ..app_config import get_app_config

logger = logging.getLogger(__name__)

router = APIRouter()

jwt_write_claim_missing_ok = get_app_config().jwt_write_claim_missing_ok


@router.get('')  # Empty path handles no trailing slash without using 307 redirect.
@router.get('/')
async def handle_health_check(_current_user: Annotated[User, Depends(get_scoped_current_user(Scope.ADMIN, missing_ok=True))]):
    """
    Handle requests to the health path.

    Returns the system health.
    """
    return health_check()
