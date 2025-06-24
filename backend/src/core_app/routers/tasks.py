import logging
from typing import Annotated

from celery.result import AsyncResult
from fastapi import APIRouter, Depends

from ..auth import Scope, User, get_scoped_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get('')  # Empty path handles no trailing slash without using 307 redirect.
@router.get('/')
async def handle_status(_current_user: Annotated[User, Depends(get_scoped_current_user(Scope.ADMIN))] = None):
    return {}


@router.get('/{task_id}')
def get_status(task_id, _current_user: Annotated[User, Depends(get_scoped_current_user(Scope.ADMIN))] = None):
    """Return the status of specified task."""
    task_result = AsyncResult(task_id)
    result = {'taskId': task_id, 'taskStatus': task_result.status, 'taskResult': task_result.result}
    return result
