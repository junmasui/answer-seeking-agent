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


ERROR_TYPE: str = 'error.type'


WRAPPED_METHODS = [
    {'module': 'weaviate.schema', 'object': 'Schema', 'method': 'get', 'span_name': 'db.weaviate.schema.get'}
]


def _with_tracer_wrapper(func):
    """Helper for providing tracer for wrapper functions."""

    def _with_tracer(tracer, to_wrap):
        def wrapper(wrapped, instance, args, kwargs):
            return func(tracer, to_wrap, wrapped, instance, args, kwargs)

        return wrapper

    return _with_tracer


@_with_tracer_wrapper
def _wrap(tracer, to_wrap, wrapped, instance, args, kwargs):
    """Instruments and calls every function defined in TO_WRAP."""
    if context_api.get_value(_SUPPRESS_INSTRUMENTATION_KEY):
        return wrapped(*args, **kwargs)

    name = to_wrap.get('span_name')
    with tracer.start_as_current_span(name) as span:
        # span.set_attribute(SpanAttributes.DB_SYSTEM, "weaviate")
        # span.set_attribute(SpanAttributes.DB_OPERATION, to_wrap.get("method"))

        obj = to_wrap.get('object')

        return_value = wrapped(*args, **kwargs)

    return return_value


class CustomInstrumentor(BaseInstrumentor):
    # pylint: disable=protected-access,attribute-defined-outside-init
    """
    An instrumentor for httpx Client and AsyncClient

    See `BaseInstrumentor`
    """

    def instrumentation_dependencies(self) -> typing.Collection[str]:
        return ('core >= 0.1.0, <5',)

    def _instrument(self, **kwargs):
        tracer_provider = kwargs.get('tracer_provider')
        tracer = get_tracer(__name__, __version__, tracer_provider)
        for wrapped_method in WRAPPED_METHODS:
            wrap_module = wrapped_method.get('module')
            wrap_object = wrapped_method.get('object')
            wrap_method = wrapped_method.get('method')
            module = importlib.import_module(wrap_module)
            if getattr(module, wrap_object, None):
                wrap_function_wrapper(wrap_module, f'{wrap_object}.{wrap_method}', _wrap(tracer, wrapped_method))

    def _uninstrument(self, **kwargs):
        for wrapped_method in WRAPPED_METHODS:
            wrap_module = wrapped_method.get('module')
            wrap_object = wrapped_method.get('object')
            module = importlib.import_module(wrap_module)
            wrapped = getattr(module, wrap_object, None)
            if wrapped:
                unwrap(wrapped, wrapped_method.get('method'))

    def _instrument(self, **kwargs: typing.Any):
        """
        Instruments httpx Client and AsyncClient

        Args:
            **kwargs: Optional arguments
                ``tracer_provider``: a TracerProvider, defaults to global
                ``meter_provider``: a MeterProvider, defaults to global

        """
        tracer_provider = kwargs.get('tracer_provider')
        meter_provider = kwargs.get('meter_provider')

        tracer = get_tracer(
            __name__,
            # instrumenting_library_version=__version__,
            tracer_provider=tracer_provider,
            # schema_url=schema_url,
        )

        wrap_function_wrapper(
            'httpx', 'HTTPTransport.handle_request', partial(self._handle_request_wrapper, tracer=tracer)
        )
        wrap_function_wrapper(
            'httpx',
            'AsyncHTTPTransport.handle_async_request',
            partial(self._handle_async_request_wrapper, tracer=tracer),
        )

    def _uninstrument(self, **kwargs: typing.Any):
        """ """
        # FIXME unwrap(httpx.HTTPTransport, "handle_request")
        # FIXME unwrap(httpx.AsyncHTTPTransport, "handle_async_request")

    @staticmethod
    def _handle_request_wrapper(
        wrapped: typing.Callable[..., typing.Any],
        instance: typing.Any,
        args: tuple[typing.Any, ...],
        kwargs: dict[str, typing.Any],
        tracer: Tracer,
    ):
        span_name = 'fixme'
        span_attributes = {}
        metric_attributes = {}

        with tracer.start_as_current_span(span_name, kind=SpanKind.INTERNAL, attributes=span_attributes) as span:
            exception = None

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
    ):
        span_name = 'fixme'
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
