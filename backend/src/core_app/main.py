import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

import sim_auth_app
from core.signals import configure_sender, send_start_up
from log_config_monitor import get_logging_conf_monitor

from .middlewares import ErrorLoggingMiddleware
from .routers import admin, answer, document_sets, documents, live, prompts, tasks

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """
    Manage the application's lifespan events.
    Starts the logging configuration monitor and exposes Prometheus metrics on startup.
    Configures the signal sender and sends the start_up signal.
    Stops the logging configuration monitor on shutdown.
    """
    logger.info('Logging config watcher starting')
    get_logging_conf_monitor().start()

    instrumentator.expose(fastapi_app, include_in_schema=False, should_gzip=False)

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
app.include_router(router=live.router, prefix='/live')
app.include_router(router=prompts.router, prefix='/prompts')
app.include_router(router=tasks.router, prefix='/tasks')

app.mount('/sim_auth', sim_auth_app.app)


@app.get('/')
async def handle_root():
    """Handle requests to the root path. Returns a simple tag line."""
    return {'Tag': 'Seeking answers'}
