import early_config

from typing import Union, Optional
import logging
import uuid

from fastapi import FastAPI, UploadFile, Form
from pydantic.alias_generators import to_camel, to_snake
from celery.result import AsyncResult

from app import health_check, seek_answer, list_documents, upload_document, upload_chunk, merge_chunked_document, delete_document, get_document_stats
from app.public_models import CamelModel, Answer, DocumentList, DocumentStats, IngestRequestBody

from worker import ingest_task

logger = logging.getLogger(__name__)



app = FastAPI()


@app.get('/')
async def handle_root():
    return {'Tag': 'Seeking answers'}

@app.get('/health')
async def handle_health_check():
    return health_check()


class GetUserResponse(CamelModel):
    user_id: str


@app.get('/users/', response_model=GetUserResponse)
async def get_user(email: str):
    namespace = uuid.NAMESPACE_URL

    # Generate the UUID from the namespace and name
    user_id = uuid.uuid5(namespace, email.lower().strip())

    return {
        'user_id': user_id
    }


@app.get('/answer', response_model=Answer)
async def handle_question(q: Union[str, None] = None, threadId: Union[uuid.UUID, None] = None):
    answer = seek_answer(user_input=q, thread_id=threadId)

    logger.info(f'returning {answer}')

    return answer


@app.get('/documents/', response_model=DocumentList)
async def handle_list_files(page: Union[int, None] = 0, itemsPerPage: Union[int, None] = 10):
    """Returns a list of documents.
    """
    
    return list_documents('documents', start=page*itemsPerPage, length=itemsPerPage)

@app.get('/documents/stats', response_model=DocumentStats)
async def handle_table_stats():
    """Returns table statistics.
    """
    
    return get_document_stats('documents')


@app.post('/documents/upload')
async def handle_upload(file: UploadFile, totalChunks: int = Form(), chunkIndex: int = Form() ):
    """Uploads a file. Chunked upload of large files is supported.
    """
    logger.debug(f'handling %s chunk: %d %d', file.filename, chunkIndex, totalChunks)

    if totalChunks > 1:
        upload_chunk('upload_chunks', file.filename, chunkIndex, file.file)

        if chunkIndex == totalChunks - 1:
            merge_chunked_document('documents', 'upload_chunks', file.filename, totalChunks)
        return
    
    upload_document('documents', file.filename, file.file)

@app.post('/documents/{doc_uuid}/ingest')
async def handle_single_ingest(doc_uuid):
    """Ingests the file specified by the document UUID.
    """
    """Queues an ingest task for the specified document.
    """

    task = ingest_task.delay(doc_ids=[doc_uuid])

    return {'task_id': task.id}

@app.delete('/documents/{doc_uuid}')
async def handle_single_delete(doc_uuid):
    """Deletes the file and associated embeddings specified by the document UUID.
    """

    success = delete_document(doc_uuid)

    return {}



@app.post('/ingest')
async def handle_ingest(body: Optional[IngestRequestBody] = None):
    """Ingests the files matched to the glob pattern or to the document UUID
    """
    logger.info(f'ingest {body}')

    file_dir = body.file_dir if body is not None else None
    glob_pattern = body.glob_pattern if body is not None else None

    doc_uuid = body.doc_uuid if body is not None else None

    file_dir = 'documents'
        
    if glob_pattern:
        task = ingest_task.delay(file_dir, glob_pattern=glob_pattern)
    if doc_uuid:
        task = ingest_task.delay(doc_ids=[doc_uuid])

    return {'taskId': task.id}


@app.get('/tasks/{task_id}')
def get_status(task_id):
    """Returns the status of specified task.
    """
    task_result = AsyncResult(task_id)
    result = {
        'taskId': task_id,
        'taskStatus': task_result.status,
        'taskResult': task_result.result
    }
    return result
