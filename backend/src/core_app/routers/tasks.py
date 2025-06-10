import logging
from typing import Annotated

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, Query

from core.signals import send_reset_data
from core_worker import reset_data_task
from simple_auth import Scope, User, get_scoped_current_user

from ..app_config import get_app_config

logger = logging.getLogger(__name__)

router = APIRouter()

jwt_write_claim_missing_ok = get_app_config().jwt_write_claim_missing_ok

@router.get('/')
async def handle_status(
    _current_user: Annotated[User, Depends(get_scoped_current_user(Scope.ADMIN, missing_ok=True))] = None,
):
    return {}


@router.get('/{task_id}')
def get_status(
    task_id,
    _current_user: Annotated[User, Depends(get_scoped_current_user(Scope.ADMIN, missing_ok=True))] = None,
):
    """Return the status of specified task."""
    task_result = AsyncResult(task_id)
    result = {'taskId': task_id, 'taskStatus': task_result.status, 'taskResult': task_result.result}
    return result
