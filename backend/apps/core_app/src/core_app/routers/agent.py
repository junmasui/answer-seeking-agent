import logging
from typing import Annotated

from core import get_mermaid_graph, process_input
from core_public import AgentResponse, AgentRequestBody
from fastapi import APIRouter, Body, Depends
from fastapi.responses import Response

from ..auth import Scope, User, get_scoped_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get('', response_model=AgentResponse)  # Empty path handles no trailing slash without using 307 redirect.
@router.get('/', response_model=AgentResponse)
async def handle_input(
    params: Annotated[AgentRequestBody, Depends()],
    current_user: Annotated[User, Depends(get_scoped_current_user(Scope.QUERY, missing_ok=True))] = None,
):
    """Handle an input submitted via GET request and return a response."""
    user_id = current_user.user_id if current_user is not None else None

    response = await process_input(user_input=params.input, thread_id=params.thread_id, user_id=user_id)

    logger.info('returning %s', response)

    return response


@router.post('', response_model=AgentResponse)  # Empty path handles no trailing slash without using 307 redirect.
@router.post('/', response_model=AgentResponse)
async def handle_input_post(
    body: Annotated[AgentRequestBody, Body(...)],
    current_user: Annotated[User, Depends(get_scoped_current_user(Scope.QUERY, missing_ok=True))] = None,
):
    """Handle an input submitted via POST request and return a response."""
    user_id = current_user.userid if current_user is not None else None

    response = await process_input(user_input=body.input, thread_id=body.thread_id, user_id=user_id)

    logger.info('returning %s', response)

    return response


@router.get('/mermaid')
async def handle_mermaid_graph(_current_user: Annotated[User, Depends(get_scoped_current_user(Scope.ADMIN))] = None):
    """
    Generate and return a Mermaid diagram representation of the agent graph.

    Returns the agent's workflow graph in Mermaid format for visualization purposes.
    """
    # For the MIME type, https://www.iana.org/assignments/media-types/application/vnd.mermaid
    # See https://github.com/mermaid-js/mermaid/issues/3098 and https://github.com/mermaid-js/mermaid/pull/4485

    media_type = 'application/vnd.mermaid'
    content = get_mermaid_graph()

    return Response(content=content, media_type=media_type)
