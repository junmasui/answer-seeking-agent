import logging

from ..providers.file_store import get_s3_directory, get_s3_bucket

from .model_ops import add_or_update_tracking_record


logger = logging.getLogger(__name__)


def upload_document(file_dir, file_name, local_file, user_id):
    """Upload a complete document into our document system.
    This involves storing the document in our cloud file store
    and adding a tracking record.
    """

    logger.info('uploading file %s to cloud file store', file_name)

    cloud_path = _store_file_in_cloud(file_dir, file_name, local_file)

    success = cloud_path.exists()
    if not success:
        logger.warning('failed to upload file %s to cloud file store', file_name)
        return

    bucket = get_s3_bucket()
    add_or_update_tracking_record(file_dir, file_name, cloud_path, bucket, user_id)


def upload_chunk(chunk_dir, file_name, chunk_index, local_file):
    """Upload a document chunk to cloud storage."""
    logger.info('uploading chunk %s %d to cloud file store', file_name, chunk_index)

    chunk_file_name = _get_chunk_file_name(file_name, chunk_index)
    cloud_path = _store_file_in_cloud(chunk_dir, chunk_file_name, local_file)

    success = cloud_path.exists()
    if not success:
        logger.warning('failed to upload chunk %s %d to cloud file store', file_name)
        return False
    return True

def merge_chunked_document(file_dir, chunk_dir, file_name, total_chunks, user_id):
    """Merge then upload a chunked document into our document system.
    This involves storing the document in our cloud file store
    and adding a tracking record.
    """

    logger.info('uploading file %s to cloud file store', file_name)

    cloud_path = _merge_file_chunks(file_dir, chunk_dir, file_name, total_chunks)

    success = cloud_path.exists()
    if not success:
        logger.warning('failed to upload file %s to cloud file store', file_name)
        return

    bucket = get_s3_bucket()
    add_or_update_tracking_record(file_dir, file_name, cloud_path, bucket, user_id)



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


