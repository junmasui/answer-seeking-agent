import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query

from core.prompt_mgr import add_prompt, delete_prompt, get_prompt_statistics, list_prompts, update_prompt
from core.public_models import AgentPromptAddRequest, AgentPromptList, AgentPromptStats, AgentPromptUpdateRequest
from core.public_models.base import OwnerType
from core.public_models.prompt import AgentPromptStatus
from global_config import get_global_config
from simple_auth import Scope, User, get_scoped_current_user

from .util import parse_sort_by

logger = logging.getLogger(__name__)

router = APIRouter()

jwt_write_claim_missing_ok = get_global_config().jwt_write_claim_missing_ok


@router.get('/', response_model=AgentPromptList)
async def handle_list_prompts(
    name: Annotated[str, Query(..., description='Prompt name')] = None,
    page: Annotated[int, Query(..., description='Zero-indexed page', ge=0)] = 0,
    items_per_page: Annotated[int, Query(..., alias='itemsPerPage', description='Item count per page', ge=1)] = 10,
    sort_by: Annotated[
        str,
        Query(
            ...,
            alias='sortBy',
            description='Sort by comma-separated list of fields. Higher precedence first, prefix - for descending',
        ),
    ] = 'name',
    _current_user: Annotated[User, Depends(get_scoped_current_user(Scope.PROMPT_READ, missing_ok=True))] = None,
):
    """Returns a list of document sets."""
    parsed_sort_by = parse_sort_by(sort_by)

    return list_prompts(name=name, start=page * items_per_page, length=items_per_page, sort_by=parsed_sort_by)


@router.post('/')
async def handle_single_insert(
    body: Annotated[AgentPromptAddRequest, Body(...)],
    current_user: Annotated[
        User, Depends(get_scoped_current_user(Scope.PROMPT_WRITE, missing_ok=jwt_write_claim_missing_ok))
    ] = None,
):
    """Add document set."""
    status = AgentPromptStatus.ACTIVE
    user_id = current_user.userid if current_user is not None else None

    add_prompt(
        name=body.name,
        owner_type=OwnerType.USER,
        status=status,
        system_message=body.system_message,
        human_message=body.human_message,
        include_history=body.include_history,
        user_id=user_id,
    )

    return {}


@router.get('/stats', response_model=AgentPromptStats)
async def handle_table_stats(
    _current_user: Annotated[User, Depends(get_scoped_current_user(Scope.PROMPT_READ, missing_ok=True))] = None,
):
    """Returns statistics about tracking table."""
    return get_prompt_statistics()


@router.patch('/{prompt_uuid}')
async def handle_single_update(
    body: Annotated[AgentPromptUpdateRequest, Body(...)],
    prompt_uuid: Annotated[uuid.UUID, Path(..., discription='Prompt UUID')],
    current_user: Annotated[
        User, Depends(get_scoped_current_user(Scope.PROMPT_WRITE, missing_ok=jwt_write_claim_missing_ok))
    ] = None,
):
    """Delete the file and associated embeddings specified by the document UUID."""
    user_id = current_user.userid if current_user is not None else None

    update_prompt(
        prompt_uuid,
        status=None,
        system_message=body.system_message,
        human_message=body.human_message,
        include_history=body.include_history,
        last_user_id=user_id,
    )

    return {}


@router.delete('/{prompt_uuid}')
async def handle_single_delete(
    prompt_uuid: Annotated[uuid.UUID, Path(..., discription='Prompt UUID')],
    _current_user: Annotated[
        User, Depends(get_scoped_current_user(Scope.PROMPT_WRITE, missing_ok=jwt_write_claim_missing_ok))
    ] = None,
):
    """Delete the file and associated embeddings specified by the document UUID."""
    _user_id = _current_user.userid if _current_user is not None else None

    delete_prompt(prompt_uuid)

    return {}
