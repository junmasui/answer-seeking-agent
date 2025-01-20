# Explicitly define the exported symbols: the exported symbols
# is part of the contract of this provider module.
__all__ = ['get_s3_client', 'get_s3_bucket',
           'get_s3_directory']

# For now, there is only one file store provider.
from .minio import (get_s3_client, get_s3_bucket,
                    get_s3_directory)
