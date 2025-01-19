import logging
import torch

logger = logging.getLogger(__name__)

def status_check():

    status = {
        'status': 'not good'
    }
    try:

        cuda_available = torch.cuda.is_available()
        status['CUDA available'] = cuda_available

        if cuda_available:
            device_name = torch.cuda.get_device_name(0)
            status['CUDA device'] =  device_name

        if True:
            #do something
            pass

        # TODO ping redis
        # TODO ping postgres
        # TODO ping minio

        status['status'] = 'good'

    except Exception as ex:
        logger.warning('status check failed', exc_info=ex)


    return status