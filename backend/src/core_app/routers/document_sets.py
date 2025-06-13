import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query

from core import list_document_sets
from core.doc_mgr import add_document_set, delete_document_set, get_document_set_statistics, update_document_set
from core.public_models import DocumentSetAddRequest, DocumentSetList, DocumentSetStats, DocumentSetUpdateRequest

from ..auth import Scope, User, get_scoped_current_user
from .util import parse_sort_by

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get('/', response_model=DocumentSetList)
async def handle_list_doc_sets(
    name: Annotated[str, Query(..., description='Document set name')] = None,
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
    _current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_READ))] = None,
):
    """Returns a list of document sets."""
    parsed_sort_by = parse_sort_by(sort_by)

    return list_document_sets(name=name, start=page * items_per_page, length=items_per_page, sort_by=parsed_sort_by)


@router.post('/')
async def handle_single_insert(
    body: Annotated[DocumentSetAddRequest, Body(...)],
    current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_WRITE))] = None,
):
    """Add document set."""
    user_id = current_user.userid if current_user is not None else None

    add_document_set(
        name=body.name,
        is_new_doc_default=body.is_new_doc_default,
        is_public_viewable=body.is_public_viewable,
        user_id=user_id,
    )

    return {}


@router.get('/stats', response_model=DocumentSetStats)
async def handle_table_stats(_current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_READ))] = None):
    """Returns statistics about tracking table."""
    return get_document_set_statistics()


@router.patch('/{doc_set_uuid}')
async def handle_single_update(
    body: Annotated[DocumentSetUpdateRequest, Body(...)],
    doc_set_uuid: Annotated[uuid.UUID, Path(..., discription='Document set UUID')],
    current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_WRITE))] = None,
):
    """Delete the file and associated embeddings specified by the document UUID."""
    user_id = current_user.userid if current_user is not None else None

    update_document_set(
        doc_set_uuid,
        is_new_doc_default=body.is_new_doc_default,
        is_public_viewable=body.is_public_viewable,
        last_user_id=user_id,
    )

    return {}


@router.delete('/{doc_set_uuid}')
async def handle_single_delete(
    doc_set_uuid: Annotated[uuid.UUID, Path(..., discription='Document set UUID')],
    _current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_WRITE))] = None,
):
    """Delete the file and associated embeddings specified by the document UUID."""
    _user_id = _current_user.userid if _current_user is not None else None

    delete_document_set(doc_set_uuid)

    return {}
