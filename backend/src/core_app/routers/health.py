import logging

from fastapi import APIRouter

from core import health_check

from ..app_config import get_app_config

logger = logging.getLogger(__name__)

router = APIRouter()

jwt_write_claim_missing_ok = get_app_config().jwt_write_claim_missing_ok


@router.get('')  # Empty path handles no trailing slash without using 307 redirect.
@router.get('/')
async def handle_health_check():
    """
    Handle requests to the health path.

    Returns the system health.
    """
    return health_check()
