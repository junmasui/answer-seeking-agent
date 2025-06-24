import logging
import uuid
from datetime import datetime
from typing import Annotated, Optional, Union

from fastapi import APIRouter, Body, Depends, Form, Path, Query, UploadFile

from core import (
    delete_document,
    get_document_statistics,
    list_documents,
    merge_chunked_document,
    update_document,
    update_document_status,
    upload_chunk,
    upload_document,
)
from core.public_models import (
    BulkDeleteRequestBody,
    DocumentList,
    DocumentStats,
    DocumentStatus,
    DocumentUpdateRequest,
    DocumentUploadFormData,
    IngestRequestBody,
)
from core_worker import ingest_task

from ..auth import Scope, User, get_scoped_current_user
from .util import parse_sort_by

logger = logging.getLogger(__name__)

router = APIRouter()


# Dependency function to gather form data into the Pydantic model
async def get_upload_form_data(
    document_set_id: Annotated[uuid.UUID, Form(alias='documentSetId')],
    total_chunks: Annotated[int, Form(alias='totalChunks')],
    chunk_index: Annotated[int, Form(alias='chunkIndex')],
    source_url: Annotated[str, Form(alias='sourceUrl')],
    content_type: Annotated[str, Form(alias='contentType')],
    download_time_utc_str: Annotated[str, Form(alias='downloadTimeUtc')],
) -> DocumentUploadFormData:
    """Parse and validate document upload form data into a Pydantic model."""
    return DocumentUploadFormData(
        document_set_id=document_set_id,
        total_chunks=total_chunks,
        chunk_index=chunk_index,
        source_url=source_url,
        content_type=content_type,
        download_time_utc_str=download_time_utc_str,
    )


@router.get('', response_model=DocumentList)  # Empty path handles no trailing slash without using 307 redirect.
@router.get('/', response_model=DocumentList)
async def handle_list_files(
    doc_set_uuid: Annotated[uuid.UUID, Path(..., discription='Document set UUID')] = None,
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
    """Returns a list of documents."""
    parsed_sort_by = parse_sort_by(sort_by)

    return list_documents(
        doc_set_id=doc_set_uuid, start=page * items_per_page, length=items_per_page, sort_by=parsed_sort_by
    )


@router.get('/stats', response_model=DocumentStats)
async def handle_table_stats(_current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_READ))] = None):
    """Returns statistics about tracking table."""
    return get_document_statistics()


@router.post('/upload')
async def handle_upload(
    file: UploadFile,
    form_data: Annotated[DocumentUploadFormData, Depends(get_upload_form_data)],  # Use the dependency
    current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_WRITE))] = None,
):
    """
    Upload a file.

    Chunked upload of large files is supported.
    """
    user_id = current_user.userid if current_user is not None else None
    # Convert string to datetime from the form_data model
    download_time_utc = datetime.fromisoformat(form_data.download_time_utc_str)

    logger.debug('handling %s chunk: %d %d', file.filename, form_data.chunk_index, form_data.total_chunks)

    if form_data.total_chunks > 1:
        upload_chunk(
            doc_set_uuid=form_data.document_set_id,
            partial_doc_path=file.filename,
            chunk_index=form_data.chunk_index,
            local_file=file.file,
        )

        if form_data.chunk_index == form_data.total_chunks - 1:
            merge_chunked_document(
                doc_set_uuid=form_data.document_set_id,
                partial_doc_path=file.filename,
                total_chunks=form_data.total_chunks,
                source_url=form_data.source_url,
                content_type=form_data.content_type,
                download_time_utc=download_time_utc,
                user_id=user_id,
            )
        return

    upload_document(
        doc_set_uuid=form_data.document_set_id,
        partial_doc_path=file.filename,
        local_file=file.file,
        source_url=form_data.source_url,
        content_type=form_data.content_type,
        download_time_utc=download_time_utc,
        user_id=user_id,
    )


@router.patch('/{doc_uuid}')
async def handle_single_update(
    doc_uuid: Annotated[uuid.UUID, Path(..., discription='Document UUID')],
    body: Annotated[Optional[DocumentUpdateRequest], Body()] = None,
    current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_INGEST))] = None,
):
    """Update the file specified by the document UUID."""
    user_id = current_user.userid if current_user is not None else None

    update_document(doc_uuid, doc_set_uuid=body.document_set_id, last_user_id=user_id)

    return {}


@router.delete('/{doc_uuid}')
async def handle_single_delete(
    doc_uuid: Annotated[uuid.UUID, Path(..., discription='Document UUID')],
    current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_WRITE))] = None,
):
    """Delete the file and associated embeddings specified by the document UUID."""
    _user_id = current_user.userid if current_user is not None else None

    delete_document(doc_uuid)

    return {}


# NOTE: Declaration order matters for path patterns.
#
@router.post('/{doc_uuid}/ingest')
async def handle_single_ingest(
    doc_uuid: Annotated[uuid.UUID, Path(..., discription='Document UUID')],
    current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_INGEST))] = None,
):
    """Ingest the file specified by the document UUID."""
    user_id = current_user.userid if current_user is not None else None

    update_document_status(doc_uuid, DocumentStatus.QUEUING, last_user_id=user_id)

    task = ingest_task.delay(doc_ids=[doc_uuid])

    return {'task_id': task.id}


@router.post('/ingest')
async def handle_ingest(
    body: Annotated[Union[IngestRequestBody, None], Body()] = None,
    current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_INGEST))] = None,
):
    """Ingest the files specified in the list of document UUIDs."""
    user_id = current_user.userid if current_user is not None else None

    doc_uuids = set()

    if body.doc_uuids:
        doc_uuids = set(body.doc_uuids)

    if body.all_uploaded:
        result = list_documents(doc_set_id=body.doc_set_uuid, status=DocumentStatus.UPLOADED)
        uningested_doc_ids = [doc.id for doc in result.documents]
        doc_uuids = doc_uuids.union(uningested_doc_ids)
        logger.info('queued %d items with uploaded status', len(uningested_doc_ids))

    task_ids = []
    for doc_uuid in doc_uuids:
        update_document_status(doc_uuid, DocumentStatus.QUEUING, last_user_id=user_id)

        task = ingest_task.delay(doc_ids=[doc_uuid])

        task_ids.append({'doc_uuid': doc_uuid, 'task_id': task.id})

    return {'task_ids': task_ids}


@router.post('/delete')
async def handle_delete(
    body: Optional[BulkDeleteRequestBody] = None,
    current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_WRITE))] = None,
):
    """Delete the files specified in the list of document UUIDs."""
    _user_id = current_user.userid if current_user is not None else None

    doc_uuids = body.doc_uuids if body.doc_uuids else []

    for doc_uuid in doc_uuids:
        delete_document(doc_uuid)

    return {}
