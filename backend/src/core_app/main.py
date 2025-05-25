import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Union

from celery.result import AsyncResult
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

import sim_auth_app
from core import status_check
from core.signals import configure_sender, send_start_up
from core_worker import get_worker_logger_tree
from log_config_monitor import dump_logger_tree, get_logging_conf_monitor

from .middlewares import ErrorLoggingMiddleware
from .routers import admin, answer, document_sets, documents, prompts

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage the application's lifespan events.
    Starts the logging configuration monitor and exposes Prometheus metrics on startup.
    Configures the signal sender and sends the start_up signal.
    Stops the logging configuration monitor on shutdown.
    """
    logger.info('Logging config watcher starting')
    get_logging_conf_monitor().start()

    instrumentator.expose(app, include_in_schema=False, should_gzip=False)

    logger.info('Application is starting up...')
    configure_sender(is_worker=False)
    send_start_up()

    yield

    logger.info('Logging config watcher stopping')
    get_logging_conf_monitor().stop()


app = FastAPI(lifespan=lifespan)

app.add_middleware(ErrorLoggingMiddleware)

instrumentator = Instrumentator().instrument(app)

app.include_router(router=admin.router, prefix='/admin')
app.include_router(router=answer.router, prefix='/answer')
app.include_router(router=document_sets.router, prefix='/document-sets')
app.include_router(router=documents.router, prefix='/documents')
app.include_router(router=prompts.router, prefix='/prompts')

app.mount('/sim_auth', sim_auth_app.app)


@app.get('/')
async def handle_root():
    """Handle requests to the root path. Returns a simple tag line."""
    return {'Tag': 'Seeking answers'}


@app.get('/status')
async def handle_status_check():
    """Handle requests to the status path. Returns the application status."""
    return status_check()


@app.get('/tasks/{task_id}')
def get_status(
    task_id,
    # current_user: Annotated[User, Depends(get_scoped_current_user(Scope.ADMIN))] = None
):
    """Return the status of specified task."""
    task_result = AsyncResult(task_id)
    result = {'taskId': task_id, 'taskStatus': task_result.status, 'taskResult': task_result.result}
    return result


@app.get('/loggers')
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
