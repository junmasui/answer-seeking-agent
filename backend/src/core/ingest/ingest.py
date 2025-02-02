import os
import logging
from datetime import datetime
from pathlib import Path

from sqlalchemy import func

from ..doc_mgr.model import DocumentStatus

from ..doc_mgr.model_ops import get_tracking_records, update_tracking_record
from ..providers.file_store import get_s3_bucket
from ..providers.doc_loader import get_doc_loader
from ..providers.vector_store import get_vector_store

from global_config import get_global_config


logger = logging.getLogger(__name__)

__all__ = ['ingest_documents', 'reset_worker_data']

def ingest_documents(doc_ids):
    """Ingest cloud files. Ingesting is the process of extracting textual data
    from PDF, HTML, etc and generating and storing searchable semantic vectors.
    """
    
    if not doc_ids:
        raise NotImplementedError()

    config = get_global_config()

    bucket = get_s3_bucket()
    vector_store = get_vector_store()

    staging_dir = config.staging_dir / 'ingest'
    staging_dir.mkdir(parents=True, exist_ok=True)

    def _load_one_source(source_path, tracked_rel_path):

        loader = get_doc_loader(file_path=source_path)

        for doc in loader.lazy_load():
            # We backfill the document ID with Unstructured PDF's "element_id"
            # because it is unique and reproducible.
            if not doc.id:
                element_id = doc.metadata.get('element_id')
                if element_id:
                    doc.id = element_id

            if not doc.id:
                logger.info(f'skip loading {doc}')
                continue

            # Must convert the 'source' metadata field to a string because the metadata
            # is serialized to JSON then stored in a JSONB column in the database.
            doc.metadata['source'] = str(doc.metadata['source'])

            doc.metadata['relative_path'] = tracked_rel_path

            yield doc

    def _ingest_one_document(detached_record):
        with update_tracking_record(doc_uuid=detached_record.id) as updateable_record:
            updateable_record.status = DocumentStatus.INGESTING

        actual_local_path = None
        try:
            # We staging the file locally. There are a few good reasons for doing so:
            # 1. We time-separate the file downloads from file processing. If any bad network
            #    event occurs, we have a clearer understanding of the clean up.
            # 2. If file processing uses block reads or rewinds, then processing a local file is faster.
            # 3. If our dependencies (ex unstructured, langchain) are testing against type, cloudlib's
            #    S3Path object might encounter troubles because it is not a subtype of pathlib.Path.
            #    (S3Path is a duck-type of Path). 
            rel_path = detached_record.s3_rel_path
            source_path = bucket / rel_path
            local_path = staging_dir / rel_path

            if not source_path.exists():
                # Something was unexpected. Maybe tracking is broken. Let's log it and move on.
                logger.debug('cloud file no longer exists: %s', source_path)

            local_path.parent.mkdir(exist_ok=True)

            actual_local_path = source_path.download_to(local_path)

            if actual_local_path != local_path:
                # Something was unexpected. Maybe a broken clean up. Let's log it and move on.
                logger.debug('unexpected actual local path: %s, expected: %s', actual_local_path, local_path)

            # Process the file
            documents = list(_load_one_source(actual_local_path, rel_path))

            # Update the vector store. Since the file is fully processed, the vector store
            # will not represent a partially processed file.
            new_pg_doc_ids = [doc.id for doc in documents]

            vector_store.add_documents(documents=documents)

            # Update the tracking store.
            # Also at this time, remove orphaned vectors from the vector store. We didn't
            # remove orphans earlier in case re-processing a file resulted in identical
            # vectors to the prior processing. 

            with update_tracking_record(doc_uuid=detached_record.id) as updateable_record:
                updateable_record.status = DocumentStatus.INGESTED
                updateable_record.ingested_time = func.current_timestamp()

                if updateable_record.pg_doc_ids is None:
                    updateable_record.pg_doc_ids = []
                prior_pg_doc_ids =  list(updateable_record.pg_doc_ids)

                updateable_record.pg_doc_ids.extend(new_pg_doc_ids)

            logger.info('stored %d vectors regarding %s', len(new_pg_doc_ids), rel_path)

            new_pg_doc_set_id = set(new_pg_doc_ids)
            prior_pg_doc_set_id = set(prior_pg_doc_ids)
            # Subtract the set of new IDs from the set of prior IDs. The result
            # will be the set of orphans to delete from the vector store.
            to_remove = list(prior_pg_doc_set_id - new_pg_doc_set_id)
            if len(to_remove) > 0:
                vector_store.delete(to_remove)

                logger.info('pruned %d stale vectors regarding %s', len(to_remove), rel_path)

            
        except Exception as ex:
            with update_tracking_record(doc_uuid=detached_record.id) as updateable_record:
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

    tracking_records = get_tracking_records(doc_uuid_list=doc_ids)

    for record in tracking_records:
        _ingest_one_document(record)


    logger.info(f'completed ingesting')

    return {
        'status': 'completed'
    }


def reset_worker_data():
    """Cleanse the staging area.
    """
    config = get_global_config()

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
            logger.debug('cleared %d files from %s', len(dirnames), str(dirpath))
