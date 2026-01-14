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
        aws_access_key_id=config.s3_access_key,
        aws_secret_access_key=config.s3_secret_key,
        endpoint_url=str(config.s3_endpoint_url),
    )
    yield client


@pytest.fixture(scope='module')
def s3_bucket(s3_client) -> Generator[S3Path, None, None]:
    """Returns S3 bucket used by this application."""
    config = get_test_config()
    bucket = S3Path(f's3://{config.s3_bucket_name}/', client=s3_client)

    purge_s3_bucket(bucket, force=True)

    yield bucket

    return purge_s3_bucket(bucket)


def purge_s3_bucket(bucket, force: bool = False):
    if not force:
        config = get_test_config()
        if config.skip_tear_down:
            logger.info('Skipping s3 bucket clean up')
            return

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
