import logging
import uuid

from sqlalchemy import delete

from ...db_models import DbTrackedDocument
from ...providers.file_store import get_s3_bucket
from ...providers.sql_database import DataDomain, get_sessionmaker
from ...providers.vector_store import delete_vectors_by_document_id, get_vector_store
from ...public_models.doc import DocumentStatus
from .query import get_documents

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

    _delete_tracking_record(tracking_record.id)

    return success


def _delete_tracking_record(doc_uuid):
    """Deletes the tracking record."""
    if isinstance(doc_uuid, str):
        doc_uuid = uuid.UUID(hex=doc_uuid)

    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    with sessionmaker() as session:
        with session.begin():
            stmt = delete(DbTrackedDocument).where(DbTrackedDocument.id == doc_uuid)
            result = session.execute(stmt)

    if result.rowcount == 0:
        logger.warning('No tracking record found with UUID %s', doc_uuid)
    else:
        logger.debug('Successfully deleted tracking record with UUID %s', doc_uuid)
