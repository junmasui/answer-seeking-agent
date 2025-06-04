import logging
from typing import Generator

import pytest
from cloudpathlib.s3 import S3Client, S3Path

from ..runtime_config import get_test_config

logger = logging.getLogger(__name__)


@pytest.fixture(scope='module')
def s3_client() -> Generator[S3Client, None, None]:
    """Returns S3 client."""
    config = get_test_config()
    client = S3Client(
        aws_access_key_id=config.minio_user_name,
        aws_secret_access_key=config.minio_user_password,
        endpoint_url=str(config.minio_endpoint_url),
    )
    yield client


@pytest.fixture(scope='module')
def s3_bucket(s3_client) -> Generator[S3Path, None, None]:
    """Returns S3 bucket used by this application."""
    config = get_test_config()
    bucket = S3Path(f's3://{config.minio_bucket_name}/', client=s3_client)

    yield bucket

    # Walk the bucket and clean out subdirectories and files added during the test(s).
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
