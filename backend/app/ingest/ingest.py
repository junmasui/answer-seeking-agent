import os
import logging
from datetime import datetime

from sqlalchemy import func

from ..doc_mgr.model import DocumentStatus

from ..doc_mgr.model_ops import get_tracking_records, update_tracking_record
from ..providers.file_store import get_s3_bucket
from ..providers.doc_loader import get_doc_loader
from ..providers.vector_store import get_vector_store


logger = logging.getLogger(__name__)

__all__ = ['ingest_documents']

def ingest_documents(doc_ids):
    """Ingest cloud files. Ingesting is the process of extracting textual data
    from PDF, HTML, etc and generating and storing searchable semantic vectors.
    """
    
    if not doc_ids:
        raise NotImplementedError()

    bucket = get_s3_bucket()
    vector_store = get_vector_store()

    def _load_one_source(source_path):

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

            doc.metadata['relative_path'] = str(source_path.relative_to(bucket))

            yield doc

    def _ingest_one_document(detached_record):
        with update_tracking_record(doc_uuid=detached_record.id) as updateable_record:
            updateable_record.status = DocumentStatus.INGESTING

        try:
            source_path = bucket / detached_record.s3_rel_path

            documents = list(_load_one_source(source_path))

            pg_doc_ids = [doc.id for doc in documents]

            vector_store.add_documents(documents=documents)

            with update_tracking_record(doc_uuid=detached_record.id) as updateable_record:
                updateable_record.status = DocumentStatus.INGESTED
                updateable_record.ingested_time = func.current_timestamp()
                if updateable_record.pg_doc_ids is None:
                    updateable_record.pg_doc_ids = []
                updateable_record.pg_doc_ids.extend(pg_doc_ids)
        except Exception as ex:
            with update_tracking_record(doc_uuid=detached_record.id) as updateable_record:
                updateable_record.status = DocumentStatus.ERROR

            raise

    tracking_records = get_tracking_records(doc_uuid_list=doc_ids)

    for record in tracking_records:
        _ingest_one_document(record)


    logger.info(f'completed ingesting')

    return {
        'status': 'completed'
    }
