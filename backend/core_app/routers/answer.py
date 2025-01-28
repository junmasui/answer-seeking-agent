

from typing import Union, Annotated
import logging
import uuid

from fastapi import Depends, APIRouter
from celery.result import AsyncResult

from core import (seek_answer)
from core.public_models import Answer
from core.signals import send_start_up, send_reset_data


from simple_auth import User, get_scoped_current_user, get_current_user, Scope

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get('/', response_model=Answer)
async def handle_question(q: Union[str, None] = None,
                          threadId: Union[uuid.UUID, None] = None,
                          current_user: Annotated[User, Depends(get_scoped_current_user(Scope.QUERY, missing_ok=True))] = None):

    user_id = current_user.user_id if current_user is not None else None

    answer = seek_answer(user_input=q, thread_id=threadId, user_id=user_id)

    logger.info(f'returning {answer}')

    return answer
