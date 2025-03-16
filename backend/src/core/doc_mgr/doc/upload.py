import logging
import uuid
from datetime import datetime

from sqlalchemy import and_, select

from global_config import get_global_config

from ...providers.sql_database import get_sessionmaker
from ...providers.file_store import get_s3_directory, get_s3_bucket

from ..doc_set.query import get_document_sets, list_document_sets

from ..model_ops import generate_uuid_from_name
from ..model import TrackedDocument, DocumentStatus


logger = logging.getLogger(__name__)


def _get_doc_set(doc_set_uuid):
    if doc_set_uuid:
        document_sets = get_document_sets([doc_set_uuid])
        if len(document_sets) > 0:
            doc_set = document_sets[0]

    if not doc_set:
        results = list_document_sets(is_default=True)
        doc_set = results.document_sets[0]

    return doc_set

def upload_document(doc_set_uuid, file_name, local_file, user_id):
    """Upload a complete document into our document system.
    This involves storing the document in our cloud file store
    and adding a tracking record.
    """

    doc_root_dir = get_global_config().doc_manager.doc_root_dir

    doc_set = _get_doc_set(doc_set_uuid)

    # TODO - Use doc_set.s3_rel_path
    file_dir = doc_root_dir + '/' + doc_set.name

    logger.info('uploading file %s to cloud file store', file_name)

    cloud_path = _store_file_in_cloud(file_dir, file_name, local_file)

    success = cloud_path.exists()
    if not success:
        logger.warning('failed to upload file %s to cloud file store', file_name)
        return

    bucket = get_s3_bucket()

    _add_or_update_tracking_record(doc_set.id, file_dir, file_name, cloud_path, bucket, user_id)


def upload_chunk(file_name, chunk_index, local_file):
    """Upload a document chunk to cloud storage."""
    logger.info('uploading chunk %s %d to cloud file store', file_name, chunk_index)

    chunk_dir = get_global_config().doc_manager.chunk_root_dir

    chunk_file_name = _get_chunk_file_name(file_name, chunk_index)
    cloud_path = _store_file_in_cloud(chunk_dir, chunk_file_name, local_file)

    success = cloud_path.exists()
    if not success:
        logger.warning('failed to upload chunk %s %d to cloud file store', file_name)
        return False
    return True


def merge_chunked_document(doc_set_uuid, file_name, total_chunks, user_id):
    """Merge then upload a chunked document into our document system.
    This involves storing the document in our cloud file store
    and adding a tracking record.
    """

    logger.info('uploading file %s to cloud file store', file_name)

    chunk_dir = get_global_config().doc_manager.chunk_root_dir
    doc_root_dir = get_global_config().doc_manager.doc_root_dir

    doc_set = _get_doc_set(doc_set_uuid)

    # TODO - Use doc_set.s3_rel_path
    file_dir = doc_root_dir + '/' + doc_set.name

    cloud_path = _merge_file_chunks(file_dir, chunk_dir, file_name, total_chunks)

    success = cloud_path.exists()
    if not success:
        logger.warning('failed to upload file %s to cloud file store', file_name)
        return

    bucket = get_s3_bucket()

    _add_or_update_tracking_record(doc_set.id, file_dir, file_name, cloud_path, bucket, user_id)


def _merge_file_chunks(file_dir, chunk_dir, file_name, total_chunks):
    """Merge file chunks and store the resulting file in cloud storage.
    """
    logger.info('merging chunks %s %d in cloud file store', file_name, total_chunks)

    cloud_dir = get_s3_directory(file_dir)
    cloud_path = cloud_dir.joinpath(file_name)

    chunk_cloud_dir = get_s3_directory(chunk_dir)

    chunk_list = []
    with cloud_path.open(mode='wb') as dest_file:
        for chunk_index in range(total_chunks):
            chunk_file_name = _get_chunk_file_name(file_name, chunk_index)
            src_path = chunk_cloud_dir.joinpath(chunk_file_name)
            with src_path.open(mode='rb') as src_file:
                while True:
                    chunk = src_file.read(1_000_000)
                    if not chunk:
                        break
                    dest_file.write(chunk)
            chunk_list.append(src_path)

    for chunk_path in chunk_list:
        chunk_path.unlink()
            
    return cloud_path


def _get_chunk_file_name(file_name, chunk_index):
    return f'{file_name}.{chunk_index:03d}'



def _store_file_in_cloud(file_dir, file_name, local_file):
    """Upload a local file to cloud storage.
    """
    cloud_dir = get_s3_directory(file_dir)

    cloud_path = cloud_dir.joinpath(file_name)
    with cloud_path.open(mode='wb') as cloud_file:
        while True:
            chunk = local_file.read(1_000_000)
            if not chunk:
                break
            cloud_file.write(chunk)
    return cloud_path



def _add_or_update_tracking_record(document_set_uuid, file_dir, file_name, cloud_path, bucket_path, user_id):
    """Adds or updates the tracking record for the document.
    """
    if not isinstance(document_set_uuid, uuid.UUID):
        raise TypeError('document_set_uuid must be a UUID object')

    file_stat = cloud_path.stat()
    size_bytes = file_stat.st_size
    file_modification_time = datetime.fromtimestamp(file_stat.st_mtime)

    # We store the path relative to the bucket. This is useful when we
    # need to move the bucket to another location.
    s3_rel_path = cloud_path.relative_to(bucket_path)

    sessionmaker = get_sessionmaker()

    with sessionmaker() as session:
        with session.begin():
            stmt = select(TrackedDocument).where(
                and_(TrackedDocument.filename == file_name,
                     TrackedDocument.document_set_id == document_set_uuid))
            result = session.execute(stmt)
            existing_obj = result.scalar_one_or_none()

        with session.begin():
            if existing_obj:
                existing_obj.document_set_id = document_set_uuid
                existing_obj.size_bytes = size_bytes
                existing_obj.file_modified_time = file_modification_time
                existing_obj.s3_rel_path = str(s3_rel_path)
                existing_obj.last_user_id = user_id
            else:
                doc_uuid = generate_uuid_from_name()

                new_obj = TrackedDocument(
                    id=doc_uuid,
                    document_set_id=document_set_uuid,
                    status=DocumentStatus.UPLOADED,
                    filedir=file_dir,
                    filename=file_name,
                    size_bytes=size_bytes,
                    file_modified_time=file_modification_time,
                    s3_rel_path=str(s3_rel_path),
                    last_user_id=user_id
                )
                session.add(new_obj)

