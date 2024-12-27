import logging
import torch

logger = logging.getLogger(__name__)

def health_check():
    logger.info('health check starting')

    health = {}

    cuda_available = torch.cuda.is_available()
    health['CUDA available'] = cuda_available

    if cuda_available:
        device_name = torch.cuda.get_device_name(0)
        health['CUDA device'] =  device_name

    if True:
        #do something
        pass

    # TODO ping redis
    # TODO ping postgres
    # TODO ping minio

    health['status'] = 'healthy'

    logger.info('health check completed')
    return health