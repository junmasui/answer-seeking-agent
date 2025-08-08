import logging
import uuid
from datetime import datetime

from core_db.db_models import DbTrackedDocument
from core_db.providers.sql_database import DataDomain, get_sessionmaker
from core_public import DocumentStatus
from sqlalchemy import and_, select

logger = logging.getLogger(__name__)


def add_document(
    *,
    document_set_uuid,
    file_dir,
    file_name,
    source_url,
    content_type,
    download_time_utc,
    cloud_path,
    bucket_path,
    user_id,
):
    """Adds or updates the tracking record for the document."""
    return _add_or_update_document(
        document_set_uuid=document_set_uuid,
        file_dir=file_dir,
        file_name=file_name,
        cloud_path=cloud_path,
        bucket_path=bucket_path,
        source_url=source_url,
        content_type=content_type,
        download_time_utc=download_time_utc,
        user_id=user_id,
    )


def _add_or_update_document(
    *,
    document_set_uuid,
    file_dir,
    file_name,
    source_url,
    content_type,
    download_time_utc,
    cloud_path,
    bucket_path,
    user_id,
):
    """
    Add or update a document tracking record in the database.

    Creates a new tracking record or updates an existing one based on filename and document set.
    Extracts file metadata from the cloud storage path and stores relative path information.
    """
    if not isinstance(document_set_uuid, uuid.UUID):
        raise TypeError('document_set_uuid must be a UUID object')

    file_stat = cloud_path.stat()
    size_bytes = file_stat.st_size
    file_modification_time = datetime.fromtimestamp(file_stat.st_mtime)

    # We store the path relative to the bucket. This is useful when we
    # need to move the bucket to another location.
    s3_rel_path = cloud_path.relative_to(bucket_path)

    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    with sessionmaker() as session:
        with session.begin():
            stmt = select(DbTrackedDocument).where(
                and_(DbTrackedDocument.filename == file_name, DbTrackedDocument.document_set_id == document_set_uuid)
            )
            result = session.execute(stmt)
            existing_obj = result.scalar_one_or_none()

        with session.begin():
            if existing_obj:
                doc_uuid = existing_obj.id

                existing_obj.document_set_id = document_set_uuid
                existing_obj.size_bytes = size_bytes
                existing_obj.file_modified_time = file_modification_time
                existing_obj.source_url = source_url
                existing_obj.content_type = content_type
                existing_obj.download_time_utc = download_time_utc
                existing_obj.s3_rel_path = str(s3_rel_path)
                existing_obj.last_user_id = user_id
            else:
                doc_uuid = uuid.uuid4()

                new_obj = DbTrackedDocument(
                    id=doc_uuid,
                    document_set_id=document_set_uuid,
                    status=DocumentStatus.UPLOADED,
                    filedir=file_dir,
                    filename=file_name,
                    size_bytes=size_bytes,
                    file_modified_time=file_modification_time,
                    source_url=source_url,
                    content_type=content_type,
                    download_time_utc=download_time_utc,
                    s3_rel_path=str(s3_rel_path),
                    last_user_id=user_id,
                )
                session.add(new_obj)

        return doc_uuid
