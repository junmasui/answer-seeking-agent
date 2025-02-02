

from typing import Union, Optional, Annotated
import logging

from fastapi import UploadFile, Form, Depends, APIRouter

from core import (list_documents, upload_document, upload_chunk,
                  merge_chunked_document, delete_document, get_document_stats, update_document_status)
from core.public_models import DocumentList, DocumentStats, IngestRequestBody, DocumentStatus


from core_worker import ingest_task
from simple_auth import User, get_scoped_current_user, Scope

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get('/', response_model=DocumentList)
async def handle_list_files(page: Union[int, None] = 0,
                            itemsPerPage: Union[int, None] = 10,
                            current_user: Annotated[User, Depends(
                                get_scoped_current_user(Scope.DOC_READ, missing_ok=True))] = None
                            ):
    """Returns a list of documents.
    """

    return list_documents('documents', start=page*itemsPerPage, length=itemsPerPage)


@router.get('/stats', response_model=DocumentStats)
async def handle_table_stats(current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_READ, missing_ok=True))] = None
                             ):
    """Returns statistics about tracking table.
    """

    return get_document_stats('documents')


@router.post('/upload')
async def handle_upload(file: UploadFile,
                        totalChunks: int = Form(),
                        chunkIndex: int = Form(),
                        current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_WRITE))] = None):
    """Upload a file. Chunked upload of large files is supported.
    """

    user_id = current_user.userid if current_user is not None else None

    logger.debug(f'handling %s chunk: %d %d',
                 file.filename, chunkIndex, totalChunks)

    if totalChunks > 1:
        upload_chunk('upload_chunks', file.filename, chunkIndex, file.file)

        if chunkIndex == totalChunks - 1:
            merge_chunked_document(
                'documents', 'upload_chunks', file.filename, totalChunks, user_id)
        return

    upload_document('documents', file.filename, file.file, user_id)


@router.post('/{doc_uuid}/ingest')
async def handle_single_ingest(doc_uuid,
                               current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_INGEST))] = None):
    """Ingest the file specified by the document UUID.
    """

    user_id = current_user.userid if current_user is not None else None

    update_document_status(
        doc_uuid, DocumentStatus.QUEUING, last_user_id=user_id)

    task = ingest_task.delay(doc_ids=[doc_uuid])

    return {'task_id': task.id}


@router.delete('/{doc_uuid}')
async def handle_single_delete(doc_uuid,
                               current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_WRITE))] = None):
    """Delete the file and associated embeddings specified by the document UUID.
    """

    user_id = current_user.userid if current_user is not None else None

    success = delete_document(doc_uuid)

    return {}


@router.post('/ingest')
async def handle_ingest(
        body: Optional[IngestRequestBody] = None,
        current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_INGEST_BULK))] = None):
    """Ingest the files specified in the list of document UUIDs
    """
    user_id = current_user.userid if current_user is not None else None

    doc_uuids = body.doc_uuids if body.doc_uuids else []

    task_ids = []
    for doc_uuid in doc_uuids:

        update_document_status(
            doc_uuid, DocumentStatus.QUEUING, last_user_id=user_id)

        task = ingest_task.delay(doc_ids=[doc_uuid])

        task_ids.append({'doc_uuid': doc_uuid, 'task_id': task.id})

    return {'task_ids': task_ids}
