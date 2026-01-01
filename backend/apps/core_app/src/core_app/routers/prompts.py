import logging
import uuid
from typing import Annotated

from core.prompt_mgr import add_prompt, delete_prompt, get_prompt_statistics, list_prompts, update_prompt
from core_public import OwnerType, PromptAddRequest, PromptList, PromptStats, PromptUpdateRequest
from fastapi import APIRouter, Body, Depends, Path, Query

from ..auth import Scope, User, get_scoped_current_user
from .prompt_versions import versions_router
from .util import parse_sort_by

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/prompts')

router.include_router(versions_router)


@router.get('', response_model=PromptList)  # Empty path handles no trailing slash without using 307 redirect.
@router.get('/', response_model=PromptList)
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
    _current_user: Annotated[User, Depends(get_scoped_current_user(Scope.PROMPT_READ))] = None,
):
    """Returns a list of document sets."""
    parsed_sort_by = parse_sort_by(sort_by)

    return await list_prompts(name=name, start=page * items_per_page, length=items_per_page, sort_by=parsed_sort_by)


@router.post('/')
async def handle_single_insert(
    body: Annotated[PromptAddRequest, Body(...)],
    current_user: Annotated[User, Depends(get_scoped_current_user(Scope.PROMPT_WRITE))] = None,
):
    """Add document set."""
    user_id = current_user.userid if current_user is not None else None

    await add_prompt(name=body.name, owner_type=OwnerType.USER, user_id=user_id)

    return {}


@router.get('/stats', response_model=PromptStats)
async def handle_table_stats(
    _current_user: Annotated[User, Depends(get_scoped_current_user(Scope.PROMPT_READ))] = None,
):
    """Returns statistics about tracking table."""
    return await get_prompt_statistics()


@router.patch('/{prompt_uuid}')
async def handle_single_update(
    body: Annotated[PromptUpdateRequest, Body(...)],
    prompt_uuid: Annotated[uuid.UUID, Path(..., discription='Prompt UUID')],
    current_user: Annotated[User, Depends(get_scoped_current_user(Scope.PROMPT_WRITE))] = None,
):
    """Delete the file and associated embeddings specified by the document UUID."""
    user_id = current_user.userid if current_user is not None else None

    await update_prompt(prompt_uuid, last_user_id=user_id)

    return {}


@router.delete('/{prompt_uuid}')
async def handle_single_delete(
    prompt_uuid: Annotated[uuid.UUID, Path(..., discription='Prompt UUID')],
    _current_user: Annotated[User, Depends(get_scoped_current_user(Scope.PROMPT_WRITE))] = None,
):
    """Delete the file and associated embeddings specified by the document UUID."""
    _user_id = _current_user.userid if _current_user is not None else None

    await delete_prompt(prompt_uuid)

    return {}
