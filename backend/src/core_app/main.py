import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.types import ASGIApp, Receive, Scope, Send

import sim_auth_app
from core.signals import configure_sender, send_start_up
from log_config_monitor import get_logging_conf_monitor

from .middlewares import ErrorLoggingMiddleware
from .middlewares.dynamic_root_path import DynamicRootPathMiddleware
from .routers import admin, answer, document_sets, documents, health, prompts, status, tasks

logger = logging.getLogger(__name__)


class SubAppRootPathFixer:
    """
    A middleware that resets the `root_path` for a sub-application.

    This is used to isolate a mounted sub-app from dynamic `root_path`
    changes made by a proxy, ensuring consistent routing behavior.
    """

    def __init__(self, app: ASGIApp, root_path: str):
        self.app = app
        self.root_path = root_path

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope['root_path'] = self.root_path
        await self.app(scope, receive, send)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """
    Manage the application's lifespan events.

    Starts the logging configuration monitor and exposes Prometheus metrics on startup. Configures
    the signal sender and sends the start_up signal. Stops the logging configuration monitor on
    shutdown.
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


app = FastAPI(lifespan=lifespan, title='Seeking Answers', version='1.0.0')

app.add_middleware(DynamicRootPathMiddleware)
app.add_middleware(ErrorLoggingMiddleware)

instrumentator = Instrumentator().instrument(app)

FastAPIInstrumentor.instrument_app(app, excluded_urls="health,status")

app.include_router(router=admin.router, prefix='/admin')
app.include_router(router=answer.router, prefix='/answer')
app.include_router(router=document_sets.router, prefix='/document-sets')
app.include_router(router=documents.router, prefix='/documents')
app.include_router(router=health.router, prefix='/health')
app.include_router(router=status.router, prefix='/status')
app.include_router(router=prompts.router, prefix='/prompts')
app.include_router(router=tasks.router, prefix='/tasks')

app.mount('/sim_auth/', SubAppRootPathFixer(sim_auth_app.app, root_path='/sim_auth'))


@app.get('')  # Empty path handles no trailing slash without using 307 redirect.
@app.get('/')
async def handle_root():
    """
    Handle requests to the root path.

    Returns a simple tag line.
    """
    return {'Tag': 'Seeking answers'}
