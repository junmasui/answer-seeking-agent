import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends
from fastapi.responses import Response

from core import get_mermaid_graph, seek_answer
from core.public_models import Answer, AnswerRequestBody
from simple_auth import Scope, User, get_current_user, get_scoped_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get('/', response_model=Answer)
async def handle_question(
    params: Annotated[AnswerRequestBody, Depends()],
    current_user: Annotated[User, Depends(get_scoped_current_user(Scope.QUERY, missing_ok=True))] = None,
):
    """Handle a question submitted via GET request and return an answer."""
    user_id = current_user.user_id if current_user is not None else None

    answer = seek_answer(user_input=params.input, thread_id=params.thread_id, user_id=user_id)

    logger.info(f'returning {answer}')

    return answer


@router.post('/', response_model=Answer)
async def handler_question(
    body: Annotated[AnswerRequestBody, Body(...)],
    current_user: Annotated[User, Depends(get_scoped_current_user(Scope.QUERY, missing_ok=True))] = None,
):
    """Handle a question submitted via POST request and return an answer."""
    user_id = current_user.user_id if current_user is not None else None

    answer = seek_answer(user_input=body.input, thread_id=body.thread_id, user_id=user_id)

    logger.info(f'returning {answer}')

    return answer


@router.get('/mermaid')
async def handle_mermaid_graph(current_user: Annotated[User, Depends(get_current_user)] = None):
    """Generate and return a Mermaid diagram representation of the agent graph.

    Returns the agent's workflow graph in Mermaid format for visualization purposes.
    """
    # For the MIME type, https://www.iana.org/assignments/media-types/application/vnd.mermaid
    # See https://github.com/mermaid-js/mermaid/issues/3098 and https://github.com/mermaid-js/mermaid/pull/4485

    media_type = 'application/vnd.mermaid'
    content = get_mermaid_graph()

    return Response(content=content, media_type=media_type)
