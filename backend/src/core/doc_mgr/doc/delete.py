import logging
import uuid

from sqlalchemy import delete

from ...providers.sql_database import get_sessionmaker
from ...providers.file_store import get_s3_bucket
from ...providers.vector_store import get_vector_store

from ..model import TrackedDocument

from .query import get_documents


logger = logging.getLogger(__name__)

def delete_document(document_id):
    """Delete tracking record, document from file store, and embeddings from vector store.
    """

    # Retrieve tracking record.

    tracking_records = get_documents(doc_uuid_list=[document_id])
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

    _delete_tracking_record(tracking_record.id)

    return success


def _delete_tracking_record(doc_uuid):
    """Deletes the tracking record.
    """
    if isinstance(doc_uuid, str):
        doc_uuid = uuid.UUID(hex=doc_uuid)

    sessionmaker = get_sessionmaker()

    with sessionmaker() as session:

        with session.begin():
            stmt = delete(TrackedDocument).where(
                TrackedDocument.id == doc_uuid)
            result = session.execute(stmt)
