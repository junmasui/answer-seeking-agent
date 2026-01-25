import logging
import uuid
from datetime import datetime

from core_db.doc_mgr.doc.add import add_or_update_document

logger = logging.getLogger(__name__)


async def add_document(
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
    ocr_strategy='use_document_set',
):
    """Adds or updates the tracking record for the document."""
    if not isinstance(document_set_uuid, uuid.UUID):
        raise TypeError('document_set_uuid must be a UUID object')

    file_stat = cloud_path.stat()
    size_bytes = file_stat.st_size
    file_modification_time = datetime.fromtimestamp(file_stat.st_mtime)

    # We store the path relative to the bucket. This is useful when we
    # need to move the bucket to another location.
    s3_rel_path = cloud_path.relative_to(bucket_path)

    return await add_or_update_document(
        document_set_uuid=document_set_uuid,
        file_dir=file_dir,
        file_name=file_name,
        source_url=source_url,
        content_type=content_type,
        download_time_utc=download_time_utc,
        user_id=user_id,
        size_bytes=size_bytes,
        file_modification_time=file_modification_time,
        s3_rel_path=s3_rel_path,
        ocr_strategy=ocr_strategy,
    )
