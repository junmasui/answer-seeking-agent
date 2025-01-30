
from typing import Union
import logging
from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from celery.result import AsyncResult
from prometheus_fastapi_instrumentator import Instrumentator

from core import (status_check)
from core.public_models import CamelModel
from core.signals import send_start_up, send_reset_data

from core_worker import get_worker_logger_tree
import sim_auth_app
from log_config_monitor import get_logging_conf_monitor, dump_logger_tree


from .routers import admin, answer, documents

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('Logging config watcher starting')
    get_logging_conf_monitor().start()

    instrumentator.expose(app, include_in_schema=False, should_gzip=False)

    logger.info('Application is starting up...')
    send_start_up(is_worker=False)

    yield

    logger.info('Logging config watcher stopping')
    get_logging_conf_monitor().stop()


app = FastAPI(lifespan=lifespan)

instrumentator = Instrumentator().instrument(app)

app.include_router(router=admin.router, prefix='/admin', )
app.include_router(router=answer.router, prefix='/answer')
app.include_router(router=documents.router, prefix='/documents')

app.mount('/sim_auth', sim_auth_app.app)




@app.get('/')
async def handle_root():
    return {'Tag': 'Seeking answers'}


@app.get('/status')
async def handle_status_check():
    return status_check()


class GetUserResponse(CamelModel):
    user_id: str




@app.get('/tasks/{task_id}')
def get_status(task_id,
               # current_user: Annotated[User, Depends(get_scoped_current_user(Scope.ADMIN))] = None
               ):
    """Return the status of specified task.
    """
    task_result = AsyncResult(task_id)
    result = {
        'taskId': task_id,
        'taskStatus': task_result.status,
        'taskResult': task_result.result
    }
    return result


@app.get('/loggers')
async def dump_loggers(includeAll: Union[bool, None] = False, worker: bool = False):

    if worker:
        task = get_worker_logger_tree.delay(include_all=includeAll)
        task_id = task.id
        task_result = AsyncResult(task_id)
        # For possible values:
        # see https://docs.celeryq.dev/en/latest/reference/celery.result.html#celery.result.AsyncResult.status
        #
        # Celery 5 does not have async-await support. We will wait the old-fashioned way,
        # which is to loop and poll. The sleep itself is async so that we don't block
        # the process from getting other work done.
        loop = 0
        while task_result.status not in ['SUCCESS', 'FAILURE'] and loop < 30:
            await asyncio.sleep(1)
            loop += 1

        if task_result.status == 'SUCCESS':
            result = task_result.result
        else:
            logger.info('celery task failed: %s %s %s', repr(task_result),
                        task_result.status, task_result.result)
            result = {}

        return result

    return dump_logger_tree(include_all=includeAll)

