import logging
from pathlib import Path

from core_db.doc_mgr.doc_set.query import get_document_sets

from ...lib_config import get_lib_config
from ...providers.file_store import get_s3_bucket, get_s3_directory
from ..doc.add import add_document
from ..doc_set.query import list_document_sets

logger = logging.getLogger(__name__)


def _get_doc_set(doc_set_uuid):
    """Retrieve a document set by its UUID, or the default document set if no UUID is provided."""
    if doc_set_uuid:
        document_sets = get_document_sets([doc_set_uuid])
        if len(document_sets) > 0:
            doc_set = document_sets[0]

    if not doc_set:
        results = list_document_sets(is_default=True)
        doc_set = results.document_sets[0]

    return doc_set


def _get_chunk_file_path(doc_set, partial_doc_path, chunk_index):
    """
    Generate the file path for a document chunk.

    This function generates a file path for a document chunk based on the document set, its partial
    path, and the chunk's index.
    """
    chunk_root_dir = get_lib_config().chunk_root_dir
    chunk_root_dir = Path(chunk_root_dir)
    if chunk_root_dir.is_absolute():
        raise ValueError

    joined = Path(chunk_root_dir) / doc_set.name / partial_doc_path

    cloud_dir = get_s3_directory(joined.parent)

    return cloud_dir / f'{joined.name}.{chunk_index:03d}'


def _get_doc_file_path(doc_set, partial_doc_path):
    """
    Generate the full cloud file path for a document.

    Combines the document root directory, document set name, and partial path to create the complete
    cloud storage path for a document.
    """
    doc_root_dir = get_lib_config().doc_root_dir
    doc_root_dir = Path(doc_root_dir)
    if doc_root_dir.is_absolute():
        raise ValueError

    joined = Path(doc_root_dir) / doc_set.name / partial_doc_path

    cloud_dir = get_s3_directory(joined.parent)

    return cloud_dir / joined.name


def upload_document(doc_set_uuid, partial_doc_path, local_file, source_url, content_type, download_time_utc, user_id):
    """
    Upload a complete document into our document system.

    This involves storing the document in our cloud file store and adding a tracking record.
    """
    doc_set = _get_doc_set(doc_set_uuid)

    cloud_doc_path = _get_doc_file_path(doc_set, partial_doc_path)

    logger.info('uploading file %s to cloud file store', partial_doc_path)

    _store_file_in_cloud(cloud_doc_path, local_file)

    success = cloud_doc_path.exists()
    if not success:
        logger.warning('failed to upload file %s to cloud file store', partial_doc_path)
        return

    bucket = get_s3_bucket()

    add_document(
        document_set_uuid=doc_set.id,
        file_dir=str(Path(partial_doc_path).parent),
        file_name=Path(partial_doc_path).name,
        cloud_path=cloud_doc_path,
        bucket_path=bucket,
        source_url=source_url,
        content_type=content_type,
        download_time_utc=download_time_utc,
        user_id=user_id,
    )


def upload_chunk(doc_set_uuid, partial_doc_path, chunk_index, local_file):
    """Upload a document chunk to cloud storage."""
    logger.info('uploading chunk filename %s index %d to cloud file store', partial_doc_path, chunk_index)

    doc_set = _get_doc_set(doc_set_uuid)

    cloud_chunk_path = _get_chunk_file_path(doc_set, partial_doc_path, chunk_index)

    logger.info('uploading chunk %d file %s to cloud chunk store', chunk_index, partial_doc_path)

    _store_file_in_cloud(cloud_chunk_path, local_file)

    success = cloud_chunk_path.exists()
    if not success:
        logger.warning('failed to upload chunk %d %s to cloud file store', chunk_index, partial_doc_path)
        return False
    return True


def merge_chunked_document(
    doc_set_uuid, partial_doc_path, total_chunks, source_url, content_type, download_time_utc, user_id
):
    """
    Merge then upload a chunked document into our document system.

    This involves storing the document in our cloud file store and adding a tracking record.
    """
    logger.info('merging file %s to cloud file store', partial_doc_path)

    doc_set = _get_doc_set(doc_set_uuid)

    cloud_doc_path = _get_doc_file_path(doc_set, partial_doc_path)

    cloud_chunk_paths = [
        _get_chunk_file_path(doc_set, partial_doc_path, chunk_index) for chunk_index in range(total_chunks)
    ]

    _merge_file_chunks(cloud_doc_path, cloud_chunk_paths)

    success = cloud_doc_path.exists()
    if not success:
        logger.warning('failed to upload merged file %s to cloud file store', partial_doc_path)
        return

    bucket = get_s3_bucket()

    add_document(
        document_set_uuid=doc_set.id,
        file_dir=str(Path(partial_doc_path).parent),
        file_name=Path(partial_doc_path).name,
        cloud_path=cloud_doc_path,
        bucket_path=bucket,
        source_url=source_url,
        content_type=content_type,
        download_time_utc=download_time_utc,
        user_id=user_id,
    )


def _merge_file_chunks(cloud_doc_path, cloud_chunk_paths):
    """Merge file chunks and store the resulting file in cloud storage."""
    with cloud_doc_path.open(mode='wb') as dest_file:
        for src_path in cloud_chunk_paths:
            with src_path.open(mode='rb') as src_file:
                while True:
                    chunk = src_file.read(1_000_000)
                    if not chunk:
                        break
                    dest_file.write(chunk)

    for chunk_path in cloud_chunk_paths:
        chunk_path.unlink()


def _store_file_in_cloud(cloud_path, local_file):
    """Upload a local file to cloud storage."""
    with cloud_path.open(mode='wb') as dest_file:
        while True:
            chunk = local_file.read(1_000_000)
            if not chunk:
                break
            dest_file.write(chunk)
