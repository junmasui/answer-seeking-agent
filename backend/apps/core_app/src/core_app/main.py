import logging
# Standard Library
# ...
import os

# Configure MLFlow to use the global OTel TracerProvider (from our Distro)
os.environ['MLFLOW_USE_DEFAULT_TRACER_PROVIDER'] = 'false'
# Enable Exemplars in OTel Metrics for trace correlation
os.environ['OTEL_METRICS_EXEMPLAR_FILTER'] = 'trace_based'

from contextlib import asynccontextmanager

from core.signals import configure_sender, send_start_up
from core_telemetry_distro.verifier import verify_distro
from fastapi import FastAPI
from log_config_monitor import get_logging_conf_monitor

from .middlewares import ErrorLoggingMiddleware
from .middlewares.dynamic_root_path import DynamicRootPathMiddleware
from .routers import admin, answer, document_sets, documents, health, prompt_versions, prompts, status, tasks

logger = logging.getLogger(__name__)


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

    ## load_custom_distro_by_entry_point('distro')
    ## load_custom_distro_by_entry_point('custom_otel')
    verify_distro()

    logger.info('Application is starting up...')
    configure_sender(is_worker=False)
    await send_start_up()

    yield

    logger.info('Logging config watcher stopping')
    get_logging_conf_monitor().stop()


app = FastAPI(lifespan=lifespan, title='Seeking Answers', version='1.0.0')

app.add_middleware(DynamicRootPathMiddleware)
app.add_middleware(ErrorLoggingMiddleware)

app.include_router(router=admin.router, prefix='/admin')
app.include_router(router=answer.router, prefix='/answer')
app.include_router(router=document_sets.router, prefix='/document-sets')
app.include_router(router=documents.router, prefix='/documents')
app.include_router(router=health.router, prefix='/health')
app.include_router(router=status.router, prefix='/status')
app.include_router(router=prompts.router)
app.include_router(router=prompt_versions.router)
app.include_router(router=tasks.router, prefix='/tasks')


@app.get('')  # Empty path handles no trailing slash without using 307 redirect.
@app.get('/')
async def handle_root():
    """
    Handle requests to the root path.

    Returns a simple tag line.
    """
    return {'Tag': 'Seeking answers'}
