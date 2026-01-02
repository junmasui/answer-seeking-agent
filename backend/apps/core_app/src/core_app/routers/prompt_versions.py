import logging
import uuid
from typing import Annotated

from core.prompt_mgr.prompt_version import (
    add_prompt_version,
    delete_prompt_version,
    get_prompt_version_stats,
    list_prompt_versions,
    update_prompt_version,
)
from core_public.prompt_version import (
    PromptVersionAddRequest,
    PromptVersionList,
    PromptVersionStats,
    PromptVersionUpdateRequest,
)
from fastapi import APIRouter, Body, Depends, Path, Query

from ..auth import Scope, User, get_scoped_current_user
from .util import parse_sort_by

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/prompt-versions')

versions_router = APIRouter(prefix='')


@router.get('', response_model=PromptVersionList)
@router.get('/', response_model=PromptVersionList)
async def handle_list_prompt_versions(
    prompt_id: Annotated[uuid.UUID, Query(..., alias='promptId', description='Prompt UUID')] = None,
    page: Annotated[int, Query(..., description='Zero-indexed page', ge=0)] = 0,
    items_per_page: Annotated[int, Query(..., alias='itemsPerPage', description='Item count per page', ge=1)] = 10,
    sort_by: Annotated[
        str,
        Query(
            ...,
            alias='sortBy',
            description='Sort by comma-separated list of fields. Higher precedence first, prefix - for descending',
        ),
    ] = 'version',
    _current_user: Annotated[User, Depends(get_scoped_current_user(Scope.PROMPT_READ))] = None,
):
    """Returns a list of prompt versions."""
    parsed_sort_by = parse_sort_by(sort_by)

    return await list_prompt_versions(
        prompt_id=prompt_id, start=page * items_per_page, length=items_per_page, sort_by=parsed_sort_by
    )


@router.get('/stats', response_model=PromptVersionStats)
async def handle_table_stats(
    _current_user: Annotated[User, Depends(get_scoped_current_user(Scope.PROMPT_READ))] = None,
):
    """Returns statistics about tracking table."""
    return await get_prompt_version_stats()


@versions_router.get('/{prompt_id}/versions', response_model=PromptVersionList)
@versions_router.get('/{prompt_id}/versions/', response_model=PromptVersionList)
async def handle_list_prompt_versions_for_prompt(
    prompt_id: Annotated[uuid.UUID, Path(..., discription='Prompt UUID')],
    page: Annotated[int, Query(..., description='Zero-indexed page', ge=0)] = 0,
    items_per_page: Annotated[int, Query(..., alias='itemsPerPage', description='Item count per page', ge=1)] = 10,
    sort_by: Annotated[
        str,
        Query(
            ...,
            alias='sortBy',
            description='Sort by comma-separated list of fields. Higher precedence first, prefix - for descending',
        ),
    ] = 'version',
    _current_user: Annotated[User, Depends(get_scoped_current_user(Scope.PROMPT_READ))] = None,
):
    """Returns a list of prompt versions."""
    parsed_sort_by = parse_sort_by(sort_by)

    return await list_prompt_versions(
        prompt_id=prompt_id, start=page * items_per_page, length=items_per_page, sort_by=parsed_sort_by
    )


@versions_router.post('/{prompt_id}/versions')
async def handle_single_insert(
    prompt_id: Annotated[uuid.UUID, Path(..., discription='Prompt UUID')],
    body: Annotated[PromptVersionAddRequest, Body(...)],
    current_user: Annotated[User, Depends(get_scoped_current_user(Scope.PROMPT_WRITE))] = None,
):
    """Add prompt version."""
    user_id = current_user.userid if current_user is not None else None

    await add_prompt_version(
        prompt_id=prompt_id,
        status=body.status,
        include_history=body.include_history,
        system_message=body.system_message,
        human_message=body.human_message,
        user_id=user_id,
    )

    return {}


@versions_router.patch('/{prompt_id}/versions/{prompt_version_id}')
async def handle_single_update(
    prompt_id: Annotated[uuid.UUID, Path(..., discription='Prompt UUID')],
    prompt_version_id: Annotated[uuid.UUID, Path(..., discription='Prompt Version UUID')],
    body: Annotated[PromptVersionUpdateRequest, Body(...)],
    current_user: Annotated[User, Depends(get_scoped_current_user(Scope.PROMPT_WRITE))] = None,
):
    """Update a prompt version."""
    user_id = current_user.userid if current_user is not None else None

    await update_prompt_version(
        prompt_id=prompt_id,
        prompt_version_id=prompt_version_id,
        status=None,
        include_history=body.include_history,
        system_message=body.system_message,
        human_message=body.human_message,
        last_user_id=user_id,
    )

    return {}


@versions_router.delete('/{prompt_id}/versions/{prompt_version_id}')
async def handle_single_delete(
    prompt_id: Annotated[uuid.UUID, Path(..., discription='Prompt UUID')],
    prompt_version_id: Annotated[uuid.UUID, Path(..., discription='Prompt Version UUID')],
    _current_user: Annotated[User, Depends(get_scoped_current_user(Scope.PROMPT_WRITE))] = None,
):
    """Delete a prompt version."""
    await delete_prompt_version(prompt_version_id)

    return {}
