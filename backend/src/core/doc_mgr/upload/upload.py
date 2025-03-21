from contextlib import contextmanager
import logging
import uuid
from datetime import datetime

from sqlalchemy import and_, select

from global_config import get_global_config

from ...providers.sql_database import get_sessionmaker, DataDomain
from ...providers.file_store import get_s3_directory, get_s3_bucket

from ..doc_set.query import get_document_sets, list_document_sets
from ..doc.add import add_document

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

def upload_document(doc_set_uuid, file_name, local_file, source_url, content_type, download_time_utc, user_id):
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

    add_document(document_set_uuid=doc_set.id,
                 file_dir=file_dir, file_name=file_name,
                 cloud_path=cloud_path,
                 bucket_path=bucket,
                 source_url=source_url,
                 content_type=content_type,
                 download_time_utc=download_time_utc,
                 user_id=user_id)


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


def merge_chunked_document(doc_set_uuid, file_name, total_chunks, source_url, content_type, download_time_utc, user_id):
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

    add_document(document_set_uuid=doc_set.id,
                 file_dir=file_dir,
                 file_name=file_name,
                 cloud_path=cloud_path,
                 bucket_path=bucket,
                 source_url=source_url,
                 content_type=content_type,
                 download_time_utc=download_time_utc,
                 user_id=user_id)


def _merge_file_chunks(file_dir, chunk_dir, file_name, total_chunks):
    """Merge file chunks and store the resulting file in cloud storage.
    """
    logger.info('merging chunks %s %d in cloud file store', file_name, total_chunks)

    chunk_cloud_dir = get_s3_directory(chunk_dir)

    chunk_list = []
    with _cloud_store_file(file_dir, file_name) as (cloud_path, dest_file):
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
    with _cloud_store_file(file_dir, file_name) as (cloud_path, dest_file):
        while True:
            chunk = local_file.read(1_000_000)
            if not chunk:
                break
            dest_file.write(chunk)
    return cloud_path

@contextmanager
def _cloud_store_file(file_dir, file_name):
    """Open a file in cloud storage.
    """
    cloud_dir = get_s3_directory(file_dir)

    cloud_path = cloud_dir / file_name

    with cloud_path.open(mode='wb') as cloud_file:
        yield cloud_path, cloud_file
