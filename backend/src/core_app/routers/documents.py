

from typing import Union, Optional, Annotated
from datetime import datetime
import logging
import uuid

from fastapi import UploadFile, Form, Depends, APIRouter, Path, Query

from core import (list_documents, upload_document, upload_chunk,
                  merge_chunked_document, delete_document, get_document_statistics, update_document, update_document_status)
from core.public_models import (
    DocumentList,
    DocumentStats,
    IngestRequestBody,
    DocumentStatus,
    DocumentUpdateRequest,
    BulkDeleteRequestBody
)

from core_worker import ingest_task
from simple_auth import User, get_scoped_current_user, Scope

from .util import parse_sort_by

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get('/', response_model=DocumentList)
async def handle_list_files(doc_set_uuid: Annotated[uuid.UUID, Path(..., discription='Document set UUID')] = None,
                            page: Annotated[int, Query(..., description='Zero-indexed page', ge=0)] = 0,
                            itemsPerPage: Annotated[int, Query(..., description='Item count per page', ge=1)] = 10,
                            sortBy: Annotated[str, Query(..., description='Sort by comma-separated list of fields. Higher precedence first, prefix - for descending')]  = 'name',
                            current_user: Annotated[User, Depends(
                                get_scoped_current_user(Scope.DOC_READ, missing_ok=True))] = None
                            ):
    """Returns a list of documents.
    """
    sort_by = parse_sort_by(sortBy)

    return list_documents(doc_set_id=doc_set_uuid, start=page*itemsPerPage, length=itemsPerPage, sort_by=sort_by)


@router.get('/stats', response_model=DocumentStats)
async def handle_table_stats(current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_READ, missing_ok=True))] = None
                             ):
    """Returns statistics about tracking table.
    """

    return get_document_statistics()


@router.post('/upload')
async def handle_upload(file: UploadFile,
                        documentSetId: Annotated[uuid.UUID, Form()],
                        totalChunks: Annotated[int, Form()],
                        chunkIndex: Annotated[int, Form()],
                        sourceUrl: Annotated[str, Form()],
                        contentType: Annotated[str, Form()],
                        downloadTimeUtc: Annotated[str, Form()],
                        current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_WRITE, missing_ok=True))] = None):
    """Upload a file. Chunked upload of large files is supported.
    """

    user_id = current_user.userid if current_user is not None else None
    downloadTimeUtc = datetime.fromisoformat(downloadTimeUtc)

    logger.debug(f'handling %s chunk: %d %d',
                 file.filename, chunkIndex, totalChunks)

    if totalChunks > 1:
        upload_chunk(doc_set_uuid=documentSetId,
                     partial_doc_path=file.filename,
                     chunk_index=chunkIndex,
                     local_file=file.file)

        if chunkIndex == totalChunks - 1:
            merge_chunked_document(doc_set_uuid=documentSetId,
                                   partial_doc_path=file.filename,
                                   total_chunks=totalChunks,
                                   source_url=sourceUrl,
                                   content_type=contentType,
                                   download_time_utc=downloadTimeUtc,
                                   user_id=user_id)
        return

    upload_document(doc_set_uuid=documentSetId,
                    partial_doc_path=file.filename,
                    local_file=file.file,
                    source_url=sourceUrl,
                    content_type=contentType,
                    download_time_utc=downloadTimeUtc,
                    user_id=user_id)


@router.patch('/{doc_uuid}')
async def handle_single_update(doc_uuid: Annotated[uuid.UUID, Path(..., discription='Document UUID')],
                               body: Optional[DocumentUpdateRequest] = None,
                               current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_INGEST))] = None):
    """Update the file specified by the document UUID.
    """

    user_id = current_user.userid if current_user is not None else None

    update_document(
        doc_uuid, doc_set_uuid=body.document_set_id, last_user_id=user_id)

    return {}


@router.delete('/{doc_uuid}')
async def handle_single_delete(doc_uuid: Annotated[uuid.UUID, Path(..., discription='Document UUID')],
                               current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_WRITE))] = None):
    """Delete the file and associated embeddings specified by the document UUID.
    """

    user_id = current_user.userid if current_user is not None else None

    success = delete_document(doc_uuid)

    return {}

# NOTE: Declaration order matters for path patterns. 
#
@router.post('/{doc_uuid}/ingest')
async def handle_single_ingest(doc_uuid: Annotated[uuid.UUID, Path(..., discription='Document UUID')],
                               current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_INGEST))] = None):
    """Ingest the file specified by the document UUID.
    """

    user_id = current_user.userid if current_user is not None else None

    update_document_status(
        doc_uuid, DocumentStatus.QUEUING, last_user_id=user_id)

    task = ingest_task.delay(doc_ids=[doc_uuid])

    return {'task_id': task.id}

@router.post('/ingest')
async def handle_ingest(
        body: Optional[IngestRequestBody] = None,
        current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_INGEST))] = None):
    """Ingest the files specified in the list of document UUIDs
    """
    user_id = current_user.userid if current_user is not None else None

    doc_uuids = set()

    if body.doc_uuids:
        doc_uuids = set(body.doc_uuids)

    if body.all_uploaded:
        result = list_documents(doc_set_id=body.doc_set_uuid, status=DocumentStatus.UPLOADED)
        uningested_doc_ids = [ doc.id for doc in result.documents ]
        doc_uuids = doc_uuids.union(uningested_doc_ids)
        logger.info('queued %d items with uploaded status', len(uningested_doc_ids))

    task_ids = []
    for doc_uuid in doc_uuids:

        update_document_status(
            doc_uuid, DocumentStatus.QUEUING, last_user_id=user_id)

        task = ingest_task.delay(doc_ids=[doc_uuid])

        task_ids.append({'doc_uuid': doc_uuid, 'task_id': task.id})

    return {'task_ids': task_ids}

@router.post('/delete')
async def handle_delete(
        body: Optional[BulkDeleteRequestBody] = None,
        current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_WRITE))] = None):
    """Delete the files specified in the list of document UUIDs
    """
    user_id = current_user.userid if current_user is not None else None

    doc_uuids = body.doc_uuids if body.doc_uuids else []

    for doc_uuid in doc_uuids:

        delete_document(doc_uuid)


    return {}
