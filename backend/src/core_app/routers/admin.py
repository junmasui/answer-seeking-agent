import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from core.signals import send_reset_data
from core_worker import reset_data_task
from global_config import get_global_config
from simple_auth import Scope, User, get_current_user, get_scoped_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

jwt_write_claim_missing_ok = get_global_config().jwt_write_claim_missing_ok


@router.post('/reset-database')
def reset_database(
    include_workers: Annotated[bool, Query()] = None,
    current_user: Annotated[
        User, Depends(get_scoped_current_user(Scope.ADMIN, missing_ok=jwt_write_claim_missing_ok))
    ] = None,
):
    """Reset database, vector store, and file store."""
    send_reset_data()

    if include_workers:
        task = reset_data_task.delay()

    result = {}
    return result
