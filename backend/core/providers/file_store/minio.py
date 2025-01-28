from functools import cache
import os
from urllib.parse import unquote
import logging

from cloudpathlib.s3 import S3Client, S3Path

from global_config import get_global_config

from ...signals import start_up_handler, reset_data_handler


logger = logging.getLogger(__name__)

@cache
def get_s3_client():
    """Returns S3 client.
    """
    config = get_global_config()
    return S3Client(
        aws_access_key_id=config.minio_user_name,
        aws_secret_access_key=config.minio_user_password,
        endpoint_url=str(config.minio_endpoint_url)
    )

@cache
def get_s3_bucket():
    """Returns S3 bucket used by this application.
    """
    config = get_global_config()
    client = get_s3_client()
    return S3Path(f's3://{config.minio_bucket_name}/', client=client)

@cache
def get_s3_directory(dir_name):
    """Returns S3 directory within the application S3 bucket. If the directory does not exist, it is created.
    """
    bucket = get_s3_bucket()
    dir_path = bucket / dir_name
    if not dir_path.exists():
        dir_path.mkdir(parents=True)
    return dir_path

@start_up_handler
def startup(sender):
    pass

@reset_data_handler
def reset(sender):
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
            logger.debug('cleared %d files from %s', len(dirnames), str(dirpath))
