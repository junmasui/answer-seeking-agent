import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import AsyncGenerator
from uuid import UUID

from cloudpathlib.s3 import S3Path
from core_db.db_models import DbTrackedDocument
from core_db.doc_mgr.doc.query import get_documents
from core_db.doc_mgr.doc.update import update_tracking_record
from core_db.doc_mgr.doc_chunk.query import list_document_chunk_vector_ids
from core_db.doc_mgr.doc_chunk.update import replace_document_chunks
from core_db.doc_mgr.doc_set.query import get_document_sets
from core_public import DocumentOcrStrategy, DocumentStatus
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from sqlalchemy import func

from ..lib_config import get_lib_config
from ..providers.doc_loader import get_doc_loader
from ..providers.file_store import get_s3_bucket
from ..providers.vector_store import delete_vectors_by_document_id, get_vector_store

logger = logging.getLogger(__name__)

__all__ = ['ingest_documents', 'reset_worker_data']


async def _load_one_source(
    source_path: Path,
    tracked_doc_id: UUID,
    tracked_doc_set_id: UUID,
    source_url: str,
    content_type: str,
    download_time_utc: datetime,
    ocr_strategy: str,
) -> AsyncGenerator[Document, None]:
    """
    Load and process documents from a single source file, enriching each document with metadata.

    Uses the appropriate document loader for the file type and yields individual document chunks
    with enhanced metadata including document set ID, source URL, content type, and download time.
    """
    loader = get_doc_loader(file_path=source_path, strategy=ocr_strategy)

    check_in_interval = 10
    check_in_time = datetime.now() + timedelta(seconds=check_in_interval)

    for doc in loader.lazy_load():
        # Periodically check if the tracking record still exists. Stop ingesting
        # if it has been deleted.
        if datetime.now() > check_in_time:
            doc_records = await get_documents(doc_uuid_list=[tracked_doc_id])
            if len(doc_records) == 0:
                logger.warning('tracked document %s no longer exists, stopping processing', tracked_doc_id)
                return

            # Update to the next check-in time.
            check_in_time = datetime.now() + timedelta(seconds=check_in_interval)

        # We backfill the document ID with Unstructured PDF's "element_id"
        # because it is unique and reproducible.
        if not doc.id:
            element_id = doc.metadata.get('element_id')
            if element_id:
                doc.id = element_id

        if not doc.id:
            logger.info('skip loading %s', doc)
            continue

        # Must convert the 'source' metadata field to a string because the metadata
        # is serialized to JSON then stored in a JSONB column in the database.
        doc.metadata['source'] = str(doc.metadata['source'])

        # Add metadata useful for search-time pre-filtering, such as the document set ID.
        doc.metadata['document_set_id'] = str(tracked_doc_set_id)
        doc.metadata['document_id'] = str(tracked_doc_id)

        doc.metadata['source_url'] = source_url
        doc.metadata['content_type'] = content_type
        doc.metadata['download_time_utc'] = download_time_utc.isoformat(timespec='minutes')

        yield doc


async def _ingest_one_document(
    detached_record: DbTrackedDocument, bucket: S3Path, vector_store: VectorStore, staging_dir: Path
) -> None:
    """
    Ingest a single tracked document into the vector store.

    This function ingests a single tracked document by downloading it, processing it, and storing it
    in the vector store. It also updates the document's tracking record with the ingestion status.
    """
    async with update_tracking_record(doc_uuid=detached_record.id) as updateable_record:
        if updateable_record is None:
            return

        updateable_record.status = DocumentStatus.INGESTING

    actual_local_path = None
    local_path = None
    try:
        # We staging the file locally. There are a few good reasons for doing so:
        # 1. We time-separate the file downloads from file processing. If any bad network
        #    event occurs, we have a clearer understanding of the clean up.
        # 2. If file processing uses block reads or rewinds, then processing a local file is faster.
        # 3. If our dependencies (ex unstructured, langchain) are testing against type, cloudlib's
        #    S3Path object might encounter troubles because it is not a subtype of pathlib.Path.
        #    (S3Path is a duck-type of Path).
        rel_path = detached_record.s3_rel_path
        cloud_path = bucket / rel_path
        local_path = staging_dir / rel_path

        # Get additional metadata
        doc_id = detached_record.id
        source_url = detached_record.source_url
        content_type = detached_record.content_type
        download_time_utc = detached_record.download_time_utc

        if not cloud_path.exists():
            # Something was unexpected. Maybe tracking is broken. Let's log it and move on.
            logger.debug('cloud file no longer exists: %s', cloud_path)

        local_path.parent.mkdir(exist_ok=True, parents=True)

        actual_local_path = cloud_path.download_to(local_path)

        if actual_local_path != local_path:
            # Something was unexpected. Maybe a broken clean up. Let's log it and move on.
            logger.debug('unexpected actual local path: %s, expected: %s', actual_local_path, local_path)

        # From the tracking record, get metadata useful for search-time pre-filtering, such as
        # the document-set ID.
        doc_set_id = detached_record.document_set_id

        ocr_strategy_value = detached_record.ocr_strategy or DocumentOcrStrategy.USE_DOCUMENT_SET.value
        if ocr_strategy_value == DocumentOcrStrategy.USE_DOCUMENT_SET.value:
            document_sets = await get_document_sets([doc_set_id])
            if document_sets:
                ocr_strategy_value = document_sets[0].ocr_strategy
            else:
                ocr_strategy_value = DocumentOcrStrategy.HI_RES.value

        # Process the file.
        # Update the vector store in increments. The vector store
        # will represent a partially processed file while the file is
        # being processed.
        new_vector_ids = []
        chunk_data = []

        document_chunks = []
        batch_size = 10
        async for doc_chunk in _load_one_source(
            actual_local_path,
            tracked_doc_id=doc_id,
            tracked_doc_set_id=doc_set_id,
            source_url=source_url,
            content_type=content_type,
            download_time_utc=download_time_utc,
            ocr_strategy=ocr_strategy_value,
        ):
            document_chunks.append(doc_chunk)
            if len(document_chunks) >= batch_size:
                ids = vector_store.add_documents(documents=document_chunks)
                new_vector_ids.extend(ids)
                for doc_chunk, vector_id in zip(document_chunks, ids, strict=False):
                    page_number = doc_chunk.metadata.get('page_number')
                    if page_number is not None:
                        try:
                            page_number = int(page_number)
                        except (TypeError, ValueError):
                            page_number = None
                    chunk_data.append((vector_id, page_number))
                document_chunks = []

        if len(document_chunks) > 0:
            ids = vector_store.add_documents(documents=document_chunks)
            new_vector_ids.extend(ids)
            for doc_chunk, vector_id in zip(document_chunks, ids, strict=False):
                page_number = doc_chunk.metadata.get('page_number')
                if page_number is not None:
                    try:
                        page_number = int(page_number)
                    except (TypeError, ValueError):
                        page_number = None
                chunk_data.append((vector_id, page_number))
            document_chunks = []

        # Update the tracking store.
        # Also at this time, remove orphaned vectors from the vector store. We didn't
        # remove orphans earlier in case re-processing a file resulted in identical
        # vectors to the prior processing.

        prior_vector_ids = await list_document_chunk_vector_ids(detached_record.id)

        async with update_tracking_record(doc_uuid=detached_record.id) as updateable_record:
            if updateable_record is None:
                # The tracking record should exist when operations are normal: this big function
                # started with a verification that the tracking record existed.
                logger.warning('tracking record %s was deleted elsewhere', detached_record.id)

                await delete_vectors_by_document_id(detached_record.id)

                return

            updateable_record.status = DocumentStatus.INGESTED
            updateable_record.ingested_time = func.current_timestamp()

            await replace_document_chunks(detached_record.id, chunk_data)

        logger.info('stored %d vectors regarding %s', len(new_vector_ids), rel_path)

        new_vector_id_coll = set(new_vector_ids)
        prior_vector_id_coll = set(prior_vector_ids)
        # Subtract the set of new IDs from the set of prior IDs. The result
        # will be the set of orphans to delete from the vector store.
        to_remove = list(prior_vector_id_coll - new_vector_id_coll)
        if len(to_remove) > 0:
            vector_store.delete(to_remove)

            logger.info('pruned %d stale vectors regarding %s', len(to_remove), rel_path)

    except Exception as _ex:
        async with update_tracking_record(doc_uuid=detached_record.id) as updateable_record:
            if updateable_record is None:
                # The tracking record should exist when operations are normal: the same call at
                # the beginning of this function tested for existance.
                logger.warning('tracking record %s was deleted elsewhere', detached_record.id)

                await delete_vectors_by_document_id(detached_record.id)

                return

            updateable_record.status = DocumentStatus.ERROR

        raise
    finally:
        if actual_local_path is not None:
            try:
                actual_local_path.unlink()
            except Exception as ex:
                # An error deleting the staged file does not indicate a failure
                # of ingest. So log this error but let the ingestion be a success
                # if this is the case.
                logger.warning('could not delete staged file %s', str(local_path), exc_info=ex)


async def ingest_documents(doc_ids):
    """
    Ingest cloud files.

    Ingesting is the process of extracting textual data from PDF, HTML, etc and generating and
    storing searchable semantic vectors.
    """
    if not doc_ids:
        raise NotImplementedError()

    config = get_lib_config()

    bucket = get_s3_bucket()
    vector_store = get_vector_store()

    staging_dir = config.staging_dir / 'ingest'
    staging_dir.mkdir(parents=True, exist_ok=True)

    tracking_records = await get_documents(doc_uuid_list=doc_ids)

    for record in tracking_records:
        await _ingest_one_document(record, bucket, vector_store, staging_dir)

    logger.info('completed ingesting')

    return {'status': 'completed'}


async def reset_worker_data():
    """Cleanse the staging area."""
    config = get_lib_config()

    staging_dir = config.staging_dir / 'ingest'

    for dirpath, dirnames, filenames in staging_dir.walk(top_down=False):
        for subdirname in dirnames:
            subdirpath = dirpath / subdirname
            subdirpath.rmdir()
        if len(dirnames) > 0:
            logger.debug('cleared %d subdirs from %s', len(dirnames), str(dirpath))
        for filename in filenames:
            filepath = dirpath / filename
            filepath.unlink()
        if len(filenames) > 0:
            logger.debug('cleared %d files from %s', len(filenames), str(dirpath))
