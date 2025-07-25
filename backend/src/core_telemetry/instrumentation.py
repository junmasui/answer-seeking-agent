import importlib
import logging
import typing
from functools import partial
from timeit import default_timer

from opentelemetry import context as context_api
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.utils import _SUPPRESS_INSTRUMENTATION_KEY, unwrap
from opentelemetry.trace import SpanKind, Tracer, get_tracer
from wrapt import wrap_function_wrapper

__version__ = '0.1.0'

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

    try:
        # Instrument Botocore requests
        BotocoreInstrumentor().instrument()
        logger.debug('Botocore instrumentation enabled')
    except Exception as e:
        logger.warning(f'Failed to instrument Botocore: {e}')

    try:
        # Instrument HTTP requests
        RequestsInstrumentor().instrument()
        logger.debug('Requests instrumentation enabled')
    except Exception as e:
        logger.warning(f'Failed to instrument Requests: {e}')

    try:
        # Instrument HTTPX requests
        HTTPXClientInstrumentor().instrument()
        logger.debug('Requests instrumentation enabled')
    except Exception as e:
        logger.warning(f'Failed to instrument Requests: {e}')

    try:
        # Instrument SQLAlchemy requests
        SQLAlchemyInstrumentor().instrument()
        logger.debug('SQLAlchemy instrumentation enabled')
    except Exception as e:
        logger.warning(f'Failed to instrument SQLAlchemy: {e}')

    try:
        # Instrument Redis requests
        RedisInstrumentor().instrument()
        logger.debug('Redis instrumentation enabled')
    except Exception as e:
        logger.warning(f'Failed to instrument Redis: {e}')
    logger.info('INSTRUMENTING')

    try:
        CustomInstrumentor().instrument(skip_dep_check=True)
        logger.debug('Custom instrumentation enabled')
    except Exception as e:
        logger.warning(f'Failed to instrument Custom:', exc_info=e)

    logger.info('INSTRUMENTED')


ERROR_TYPE: str = 'error.type'


WRAPPED_METHODS = [
    {'module': 'core.ingest.ingest', 'object': '_ingest_one_document', 'method': None, 'span_name': '_ingest_one_document'},
    {'module': 'langchain_core.vectorstores.base', 'object': 'VectorStore', 'method': 'add_documents', 'span_name': 'vectorstore.add_documents'},
    {'module': 'langchain_core.vectorstores.base', 'object': 'VectorStore', 'method': 'search', 'span_name': 'vector.search'},
    {'module': 'langchain_core.vectorstores.base', 'object': 'VectorStore', 'method': 'similarity_search', 'span_name': 'vector.similarity_search'},
    {'module': 'langchain_core.vectorstores.base', 'object': 'VectorStore', 'method': 'similarity_search_with_score', 'span_name': 'vector.similarity_search_with_score'},
    {'module': 'langchain_core.vectorstores.base', 'object': 'VectorStore', 'method': 'similarity_search_with_relevance_scores', 'span_name': 'vector.similarity_search_with_relevance_scores'},

    {'module': 'langchain_core.vectorstores.base', 'object': 'VectorStore', 'method': 'similarity_search_by_vector', 'span_name': 'vector.similarity_search_by_vector'},
    {'module': 'langchain_core.vectorstores.base', 'object': 'VectorStore', 'method': 'max_marginal_relevance_search', 'span_name': 'vector.max_marginal_relevance_search'},
    {'module': 'langchain_core.vectorstores.base', 'object': 'VectorStore', 'method': 'max_marginal_relevance_search_by_vector', 'span_name': 'vector.max_marginal_relevance_search_by_vector'},

    {'module': 'langchain_core.retrievers', 'object': 'BaseRetriever', 'method': 'invoke', 'span_name': 'retriever.invoke'},

    {'module': 'langchain_unstructured.document_loaders', 'object': '_SingleDocumentLoader', 'method': 'lazy_load', 'span_name': 'doc_loader.lazy_load'},

    {'module': 'langchain_huggingface.embeddings.huggingface', 'object': 'HuggingFaceEmbeddings', 'method': 'embed_documents', 'span_name': 'hf_embeddings_model.embed_documents'},
    {'module': 'langchain_huggingface.embeddings.huggingface', 'object': 'HuggingFaceEmbeddings', 'method': 'embed_query', 'span_name': 'hf_embeddings_model.embed_query'},
]



class CustomInstrumentor(BaseInstrumentor):
    # pylint: disable=protected-access,attribute-defined-outside-init
    """
    An instrumentor for httpx Client and AsyncClient

    See `BaseInstrumentor`
    """

    def instrumentation_dependencies(self) -> typing.Collection[str]:
        return []

    def instrument(self, **kwargs):
        logger.info('CUSTOM INSTRUMENTING')
        tracer_provider = kwargs.get('tracer_provider')
        tracer = get_tracer(__name__, __version__, tracer_provider)
        for wrapped_method in WRAPPED_METHODS:
            wrap_module = wrapped_method.get('module')
            wrap_object = wrapped_method.get('object')
            wrap_method = wrapped_method.get('method')
            span_name = wrapped_method.get('span_name')
            logger.info('WRAPPING %s', wrap_module)
            module = importlib.import_module(wrap_module)
            if getattr(module, wrap_object, None):
                fname = f'{wrap_object}.{wrap_method}' if wrap_method is not None else wrap_object
                logger.info('WRAPPING %s', fname)
                wrap_function_wrapper(wrap_module, fname,
                                      partial(self._handle_request_wrapper, tracer=tracer, span_name=span_name))
        logger.info('CUSTOM INSTRUMENTED')

    def _uninstrument(self, **kwargs):
        for wrapped_method in WRAPPED_METHODS:
            wrap_module = wrapped_method.get('module')
            wrap_object = wrapped_method.get('object')
            module = importlib.import_module(wrap_module)
            wrapped = getattr(module, wrap_object, None)

            # if wrapped:
            #     unwrap(wrapped, wrapped_method.get('method'))


    @staticmethod
    def _handle_request_wrapper(
        wrapped: typing.Callable[..., typing.Any],
        instance: typing.Any,
        args: tuple[typing.Any, ...],
        kwargs: dict[str, typing.Any],
        tracer: Tracer,
        span_name: str,
    ):
        span_attributes = {}
        metric_attributes = {}

        with tracer.start_as_current_span(span_name, kind=SpanKind.INTERNAL, attributes=span_attributes) as span:
            exception = None

            logger.info('WRAPPED REQUEST %s', wrapped.__name__)

            start_time = default_timer()

            try:
                response = wrapped(*args, **kwargs)
            except Exception as exc:
                exception = exc
                response = getattr(exc, 'response', None)
            finally:
                elapsed_time = max(default_timer() - start_time, 0)

            if exception:
                if span.is_recording():
                    span.set_attribute(ERROR_TYPE, type(exception).__qualname__)
                    metric_attributes[ERROR_TYPE] = type(exception).__qualname__
                raise exception.with_traceback(exception.__traceback__)

        return response

    @staticmethod
    async def _handle_async_request_wrapper(
        wrapped: typing.Callable[..., typing.Awaitable[typing.Any]],
        instance: typing.Any,
        args: tuple[typing.Any, ...],
        kwargs: dict[str, typing.Any],
        tracer: Tracer,
        span_name: str,
    ):
        span_attributes = {}
        metric_attributes = {}

        with tracer.start_as_current_span(span_name, kind=SpanKind.INTERNAL, attributes=span_attributes) as span:
            exception = None

            start_time = default_timer()

            try:
                response = await wrapped(*args, **kwargs)
            except Exception as exc:
                exception = exc
                response = getattr(exc, 'response', None)
            finally:
                elapsed_time = max(default_timer() - start_time, 0)

            if exception:
                if span.is_recording():
                    span.set_attribute(ERROR_TYPE, type(exception).__qualname__)
                raise exception.with_traceback(exception.__traceback__)

        return response
