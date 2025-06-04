import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from core.signals import send_reset_data
from core_worker import reset_data_task
from ..app_config import get_app_config
from simple_auth import Scope, User, get_scoped_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

jwt_write_claim_missing_ok = get_app_config().jwt_write_claim_missing_ok


@router.post('/reset-database')
def reset_database(
    include_workers: Annotated[bool, Query(alias='includeWorkers')] = None,
    _current_user: Annotated[
        User, Depends(get_scoped_current_user(Scope.ADMIN, missing_ok=jwt_write_claim_missing_ok))
    ] = None,
):
    """Reset database, vector store, and file store."""
    send_reset_data()

    if include_workers:
        _task = reset_data_task.delay()

    result = {}
    return result
