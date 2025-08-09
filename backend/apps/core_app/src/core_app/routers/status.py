import asyncio
import logging
from typing import Union

from celery.result import AsyncResult
from core import status_check
from core_tasks import get_worker_logger_tree
from fastapi import APIRouter
from log_config_monitor import dump_logger_tree

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get('')  # Empty path handles no trailing slash without using 307 redirect.
@router.get('/')
async def handle_status_check():
    """
    Handle requests to the status path.

    Returns the application status.
    """
    return status_check()


@router.get('/loggers')
async def dump_loggers(include_all: Union[bool, None] = False, worker: bool = False):
    """
    Dump the current logger tree for the main application or a Celery worker.

    If 'worker' is true, it retrieves the logger tree from a Celery worker asynchronously.
    'include_all' determines if non-default loggers are included.
    """
    if worker:
        task = get_worker_logger_tree.delay(include_all=include_all)
        task_id = task.id
        task_result = AsyncResult(task_id)
        # For possible values:
        # see https://docs.celeryq.dev/en/latest/reference/celery.result.html#celery.result.AsyncResult.status
        #
        # Celery 5 does not have async-await support. We will wait the old-fashioned way,
        # which is to loop and poll. The sleep itself is async so that we don't block
        # the process from getting other work done.
        loop_count = 0
        while task_result.status not in ['SUCCESS', 'FAILURE'] and loop_count < 30:
            await asyncio.sleep(1)
            loop_count += 1

        if task_result.status == 'SUCCESS':
            result = task_result.result
        else:
            logger.info('celery task failed: %s %s %s', repr(task_result), task_result.status, task_result.result)
            result = {}

        return result

    return dump_logger_tree(include_all=include_all)
