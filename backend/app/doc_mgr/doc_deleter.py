import logging
from datetime import datetime

from ..providers.file_store import get_s3_bucket
from ..providers.vector_store import get_vector_store

from .model_ops import get_tracking_records, delete_tracking_record


logger = logging.getLogger(__name__)

def delete_document(document_id):
    """Delete file from cloud storage.
    """

    logger.info('deleting unimplemeted  %s', document_id)

    # Retrieve tracking record.

    tracking_records = get_tracking_records(doc_uuid_list=[document_id])
    if not tracking_records:
        return False

    tracking_record = tracking_records[0]

    # Delete vectors from vector store.

    pg_doc_ids = tracking_record.pg_doc_ids

    vector_store = get_vector_store()
    vector_store.delete(ids=pg_doc_ids)

    # Delete file from cloud storage.

    s3_rel_path = tracking_record.s3_rel_path

    bucket = get_s3_bucket()
    cloud_path = bucket.joinpath(s3_rel_path)
    cloud_path.unlink()

    success = not cloud_path.exists()

    # Delete tracking record.

    delete_tracking_record(tracking_record.id)

    return success

