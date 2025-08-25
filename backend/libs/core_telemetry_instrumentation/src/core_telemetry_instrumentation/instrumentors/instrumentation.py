import logging

from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

from .custom_instrumentor import CustomInstrumentor

logger = logging.getLogger(__name__)


def setup_auto_instrumentation():
    """
    Set up auto-instrumentation for common libraries (FastAPI, Celery, Requests).

    Attempts to instrument supported libraries and logs any failures.
    """
    # try:
    #     # Instrument FastAPI
    #     FastAPIInstrumentor().instrument()
    #     logger.debug('FastAPI instrumentation enabled')
    # except Exception as e:
    #     logger.warning(f'Failed to instrument FastAPI: {e}')

    # try:
    #     # Instrument Celery
    #     CeleryInstrumentor().instrument()
    #     logger.debug('Celery instrumentation enabled')
    # except Exception as e:
    #     logger.warning(f'Failed to instrument Celery: {e}')

    # try:
    #     # Instrument Botocore requests
    #     BotocoreInstrumentor().instrument()
    #     logger.debug('Botocore instrumentation enabled')
    # except Exception as e:
    #     logger.warning(f'Failed to instrument Botocore: {e}')

    # try:
    #     # Instrument HTTP requests
    #     RequestsInstrumentor().instrument()
    #     logger.debug('Requests instrumentation enabled')
    # except Exception as e:
    #     logger.warning(f'Failed to instrument Requests: {e}')

    # try:
    #     # Instrument HTTPX requests
    #     HTTPXClientInstrumentor().instrument()
    #     logger.debug('Requests instrumentation enabled')
    # except Exception as e:
    #     logger.warning(f'Failed to instrument Requests: {e}')

    # try:
    #     # Instrument SQLAlchemy requests
    #     SQLAlchemyInstrumentor().instrument()
    #     logger.debug('SQLAlchemy instrumentation enabled')
    # except Exception as e:
    #     logger.warning(f'Failed to instrument SQLAlchemy: {e}')

    # try:
    #     # Instrument Redis requests
    #     RedisInstrumentor().instrument()
    #     logger.debug('Redis instrumentation enabled')
    # except Exception as e:
    #     logger.warning(f'Failed to instrument Redis: {e}')

    logger.info('INSTRUMENTING')

    try:
        CustomInstrumentor().instrument(skip_dep_check=True)
        logger.debug('Custom instrumentation enabled')
    except Exception as e:
        logger.warning(f'Failed to instrument Custom:', exc_info=e)

    logger.info('INSTRUMENTED')







