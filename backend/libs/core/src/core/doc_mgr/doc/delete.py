import logging

from core_db.doc_mgr.doc.delete import delete_tracking_record
from core_db.doc_mgr.doc.query import get_documents

from ...providers.file_store import get_s3_bucket
from ...providers.vector_store import delete_vectors_by_document_id

logger = logging.getLogger(__name__)

def delete_document(document_id):
    """Delete tracking record, document from file store, and embeddings from vector store."""
    # Retrieve tracking record.

    tracking_records = get_documents(doc_uuid_list=[document_id])
    if not tracking_records:
        return False

    tracking_record = tracking_records[0]

    # Delete vectors from vector store.

    delete_vectors_by_document_id(tracking_record.id)

    logger.info('deleted vectors: %s (%s)', tracking_record.id, tracking_record.source_url)

    # Delete file from cloud storage.

    s3_rel_path = tracking_record.s3_rel_path

    bucket = get_s3_bucket()
    cloud_path = bucket.joinpath(s3_rel_path)
    cloud_path.unlink()

    success = not cloud_path.exists()

    # Delete tracking record.

    delete_tracking_record(tracking_record.id)

    return success


