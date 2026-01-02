import logging
from typing import Annotated

from core.signals import send_reset_data
from core_tasks import reset_data_task
from fastapi import APIRouter, Depends, Query

from ..auth import Scope, User, get_scoped_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post('/reset-database')
async def reset_database(
    include_workers: Annotated[bool, Query(alias='includeWorkers')] = None,
    _current_user: Annotated[User, Depends(get_scoped_current_user(Scope.ADMIN))] = None,
):
    """Reset database, vector store, and file store."""
    await send_reset_data()

    if include_workers:
        _task = reset_data_task.delay()

    result = {}
    return result
