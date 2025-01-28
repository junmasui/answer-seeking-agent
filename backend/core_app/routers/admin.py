

from typing import Annotated
import logging

from fastapi import Depends, APIRouter

from core.signals import send_reset_data


from core_worker import reset_data_task
from simple_auth import User, get_scoped_current_user, get_current_user, Scope

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post('/resetDatabase')
def reset_database(current_user: Annotated[User, Depends(get_scoped_current_user(Scope.ADMIN))] = None):
    """Reset database, vector store, and file store.
    """
    send_reset_data(is_worker=False)

    task = reset_data_task.delay()

    result = {
    }
    return result
