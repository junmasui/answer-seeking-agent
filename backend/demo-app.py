import early_config

from typing import Union, Optional, Annotated, Any
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, Form, Depends, Request
from pydantic.alias_generators import to_camel, to_snake
from celery.result import AsyncResult

from app import (health_check, seek_answer, list_documents, upload_document, upload_chunk,
                 merge_chunked_document, delete_document, get_document_stats, update_document_status,
                 documents_startup, documents_reset)
from app.public_models import CamelModel, Answer, DocumentList, DocumentStats, IngestRequestBody, DocumentStatus

from worker import ingest_task
import sim_auth_app
from simple_auth import User, get_scoped_current_user, get_current_user, Scope

logger = logging.getLogger(__name__)

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database tables are created.
    logger.info('Application is starting up...')
    documents_startup()

    yield


app = FastAPI(lifespan=lifespan)

app.mount('/sim_auth', sim_auth_app.app)


@app.get('/')
async def handle_root():
    return {'Tag': 'Seeking answers'}


@app.get('/health')
async def handle_health_check():
    return health_check()


class GetUserResponse(CamelModel):
    user_id: str


@app.get('/answer', response_model=Answer)
async def handle_question(q: Union[str, None] = None,
                          threadId: Union[uuid.UUID, None] = None,
                          current_user: Annotated[User, Depends(get_scoped_current_user(Scope.QUERY, missing_ok=True))] = None):

    user_id = current_user.user_id if current_user is not None else None

    answer = seek_answer(user_input=q, thread_id=threadId, user_id=user_id)

    logger.info(f'returning {answer}')

    return answer


@app.get('/documents/', response_model=DocumentList)
async def handle_list_files(page: Union[int, None] = 0,
                            itemsPerPage: Union[int, None] = 10,
                            current_user: Annotated[User, Depends(
                                get_scoped_current_user(Scope.DOC_READ, missing_ok=True))] = None
                            ):
    """Returns a list of documents.
    """

    return list_documents('documents', start=page*itemsPerPage, length=itemsPerPage)


@app.get('/documents/stats', response_model=DocumentStats)
async def handle_table_stats(current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_READ, missing_ok=True))] = None
                             ):
    """Returns statistics about tracking table.
    """

    return get_document_stats('documents')


@app.post('/documents/upload')
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


@app.post('/documents/{doc_uuid}/ingest')
async def handle_single_ingest(doc_uuid,
                               current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_INGEST))] = None):
    """Ingest the file specified by the document UUID.
    """

    user_id = current_user.userid if current_user is not None else None

    update_document_status(
        doc_uuid, DocumentStatus.QUEUING, last_user_id=user_id)

    task = ingest_task.delay(doc_ids=[doc_uuid])

    return {'task_id': task.id}


@app.delete('/documents/{doc_uuid}')
async def handle_single_delete(doc_uuid,
                               current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_WRITE))] = None):
    """Delete the file and associated embeddings specified by the document UUID.
    """

    user_id = current_user.userid if current_user is not None else None

    success = delete_document(doc_uuid)

    return {}


@app.post('/documents/ingest')
async def handle_ingest(
        body: Optional[IngestRequestBody] = None,
        current_user: Annotated[User, Depends(get_scoped_current_user(Scope.DOC_INGEST))] = None):
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


@app.get('/tasks/{task_id}')
def get_status(task_id,
               current_user: Annotated[User, Depends(get_scoped_current_user(Scope.ADMIN))] = None):
    """Returns the status of specified task.
    """
    task_result = AsyncResult(task_id)
    result = {
        'taskId': task_id,
        'taskStatus': task_result.status,
        'taskResult': task_result.result
    }
    return result


@app.post('/admin/resetDatabase')
def reset_database(current_user: Annotated[User, Depends(get_scoped_current_user(Scope.ADMIN))] = None):
    """Reset database.
    """
    documents_reset()
    result = {
    }
    return result
