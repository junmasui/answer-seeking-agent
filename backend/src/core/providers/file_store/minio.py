import logging
from functools import cache

from cloudpathlib.s3 import S3Client, S3Path

from ...lib_config import get_lib_config
from ...signals import reset_data_handler, start_up_handler
from ..status_models import PingResult, PingStatus

logger = logging.getLogger(__name__)


@cache
def get_s3_client() -> S3Client:
    """Returns S3 client."""
    config = get_lib_config()
    return S3Client(
        aws_access_key_id=config.minio_user_name,
        aws_secret_access_key=config.minio_user_password,
        endpoint_url=str(config.minio_endpoint_url),
    )


@cache
def get_s3_bucket() -> S3Path:
    """Returns S3 bucket used by this application."""
    config = get_lib_config()
    client = get_s3_client()
    return S3Path(f's3://{config.minio_bucket_name}/', client=client)


@cache
def get_s3_directory(dir_name: str) -> S3Path:
    """
    Returns S3 directory within the application S3 bucket.

    If the directory does not exist, it is created.
    """
    bucket = get_s3_bucket()
    dir_path = bucket / dir_name
    if not dir_path.exists():
        dir_path.mkdir(parents=True)
    return dir_path


def ping_file_store() -> PingResult:
    """
    Pings the MinIO file store to check its availability and permissions.

    Tries to list objects in the root of the bucket to verify connectivity and permissions.
    """
    try:
        bucket = get_s3_bucket()
        # Attempt to list objects in the bucket root as a basic check
        list(bucket.iterdir())
        return PingResult(status=PingStatus.GOOD, message='MinIO connection successful.')
    except Exception as e:
        logger.error('Error pinging MinIO', exc_info=e)
        return PingResult(status=PingStatus.BAD, message='MinIO connection failed.', error=str(e))


@start_up_handler
def startup(_sender):
    """
    Handle the startup signal for file store initialization.

    Currently a no-op placeholder for future file store startup logic.
    """
    pass


@reset_data_handler
def reset(sender):
    """
    Handle the reset_data signal to clear the S3 bucket if not a worker process.

    It recursively deletes all files and subdirectories within the configured S3 bucket.
    """
    if sender.is_worker:
        return

    bucket = get_s3_bucket()
    for dirpath, dirnames, filenames in bucket.walk(top_down=False):
        for subdirname in dirnames:
            subdirpath = dirpath / subdirname
            subdirpath.rmdir()
        if len(dirnames) > 0:
            logger.debug('cleared %d subdirs from %s', len(dirnames), str(dirpath))
        for filename in filenames:
            filepath = dirpath / filename
            filepath.unlink()
        if len(filenames) > 0:
            logger.debug('cleared %d files from %s', len(filenames), str(dirpath))
