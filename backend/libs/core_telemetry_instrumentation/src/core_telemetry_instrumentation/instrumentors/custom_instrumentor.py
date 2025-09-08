"""
OpenLLMetry integration for the application.

This module provides integration with OpenLLMetry (Traceloop's LLM observability framework)
which is built on top of OpenTelemetry and provides automatic instrumentation for
LLM applications including LangChain, vector stores, and LLM providers.
"""

from functools import partial
import logging
import os
from timeit import default_timer
import typing
import importlib
import importlib_metadata

from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.trace import SpanKind, Tracer, get_tracer
from wrapt import wrap_function_wrapper

from .langchain_handler import OpenTelemetryCallbackHandler, get_callback_handler

logger = logging.getLogger(__name__)

__version__ = '0.1.0'


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


def _handle_lang_graph_wrapper(
    wrapped: typing.Callable[..., typing.Any],
    instance: typing.Any,
    args: tuple[typing.Any, ...],
    kwargs: dict[str, typing.Any],
    tracer: Tracer,
    span_name: str,
):
    span_attributes = {}
    metric_attributes = {}

    # When Pregel.stream is called, its `config` argument will be positional with index 2 or key-word.
    # The `config` arugment will have type RunnableConfig
    if len(args) > 2:
        config = args[2]
    else:
        config = kwargs.get('config', None)

    if config:
        extra_data = config.get('configurable', None)
        session_id = extra_data.get('thread_id', None)
        user_id = extra_data.get('user_id', None)

        callbacks = config.get('callbacks', None)
        if callbacks is None:
            config['callbacks'] = []
            callbacks = config.get('callbacks')

        has_telemetry = any(isinstance(handler, OpenTelemetryCallbackHandler) for handler in callbacks)

        if not has_telemetry:
            callback = get_callback_handler(session_id=session_id, user_id=user_id)
            callbacks.append(callback)
            config['callbacks'] = callbacks


    with tracer.start_as_current_span(span_name, kind=SpanKind.INTERNAL, attributes=span_attributes) as span:
        exception = None

        logger.info('WRAPPING LANG GRAPH %s', wrapped.__name__)
        print('WRAPPING LANG GRAPH %s' % wrapped.__name__)

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

        logger.info('WRAPPED LANG GRAPH %s', wrapped.__name__)
        print('WRAPPED LANG GRAPH %s' % wrapped.__name__)

    return response


WRAPPED_METHODS = [
    {'module': 'core.ingest.ingest', 'object': '_ingest_one_document', 'method': None, 'span_name': '_ingest_one_document'},
    {'module': 'langchain_core.vectorstores.base', 'object': 'VectorStore',
        'method': 'add_documents', 'span_name': 'vectorstore.add_documents'},
    {'module': 'langchain_core.vectorstores.base', 'object': 'VectorStore', 'method': 'search', 'span_name': 'vector.search'},
    {'module': 'langchain_core.vectorstores.base', 'object': 'VectorStore',
        'method': 'similarity_search', 'span_name': 'vector.similarity_search'},
    {'module': 'langchain_core.vectorstores.base', 'object': 'VectorStore',
        'method': 'similarity_search_with_score', 'span_name': 'vector.similarity_search_with_score'},
    {'module': 'langchain_core.vectorstores.base', 'object': 'VectorStore',
        'method': 'similarity_search_with_relevance_scores', 'span_name': 'vector.similarity_search_with_relevance_scores'},

    {'module': 'langchain_core.vectorstores.base', 'object': 'VectorStore',
        'method': 'similarity_search_by_vector', 'span_name': 'vector.similarity_search_by_vector'},
    {'module': 'langchain_core.vectorstores.base', 'object': 'VectorStore',
        'method': 'max_marginal_relevance_search', 'span_name': 'vector.max_marginal_relevance_search'},
    {'module': 'langchain_core.vectorstores.base', 'object': 'VectorStore',
        'method': 'max_marginal_relevance_search_by_vector', 'span_name': 'vector.max_marginal_relevance_search_by_vector'},

    {'module': 'langchain_core.retrievers', 'object': 'BaseRetriever', 'method': 'invoke', 'span_name': 'retriever.invoke'},

    {'module': 'langchain_unstructured.document_loaders', 'object': 'UnstructuredLoader',
        'method': 'lazy_load', 'span_name': 'unstructured_loader.lazy_load'},
    {'module': 'langchain_unstructured.document_loaders', 'object': '_SingleDocumentLoader',
        'method': 'lazy_load', 'span_name': 'single_doc_loader.lazy_load'},
    {'module': 'unstructured.partition.auto', 'object': 'partition', 'method': None, 'span_name': 'unstructured.partition'},

    {'module': 'langchain_huggingface.embeddings.huggingface', 'object': 'HuggingFaceEmbeddings',
        'method': 'embed_documents', 'span_name': 'hf_embeddings_model.embed_documents'},
    {'module': 'langchain_huggingface.embeddings.huggingface', 'object': 'HuggingFaceEmbeddings',
        'method': 'embed_query', 'span_name': 'hf_embeddings_model.embed_query'},

    {'module': 'langgraph.pregel', 'object': 'Pregel',
        'method': 'stream', 'span_name': 'graph.stream', 'wrapper': _handle_lang_graph_wrapper},

    {'module': 'langgraph.pregel', 'object': 'Pregel',
        'method': 'stream', 'span_name': 'graph.stream', 'wrapper': _handle_lang_graph_wrapper},

    {'module': 'spacy.language', 'object': 'Language',
        'method': '__call__', 'span_name': 'spacy.language'},
]
ERROR_TYPE: str = 'error.type'


class CustomInstrumentor(BaseInstrumentor):
    # pylint: disable=protected-access,attribute-defined-outside-init
    """
    An instrumentor for httpx Client and AsyncClient

    See `BaseInstrumentor`
    """

    def instrumentation_dependencies(self) -> typing.Collection[str]:
        logger.info('CUSTOM INSTRUMENTATION DEPENDENCIES')
        print('CUSTOM INSTRUMENTATION DEPENDENCIES')
        return []

    def _instrument(self, **kwargs):
        logger.info('CUSTOM INSTRUMENTING')
        print('CUSTOM INSTRUMENTING')

        tracer_provider = kwargs.get('tracer_provider')
        tracer = get_tracer(__name__, __version__, tracer_provider)
        for wrapped_method in WRAPPED_METHODS:
            wrap_module = wrapped_method.get('module')
            wrap_object = wrapped_method.get('object')
            wrap_method = wrapped_method.get('method')
            span_name = wrapped_method.get('span_name')

            logger.info('WRAPPING %s', wrap_module)
            try:
                module = importlib.import_module(wrap_module)
                if getattr(module, wrap_object, None):
                    fname = f'{wrap_object}.{wrap_method}' if wrap_method is not None else wrap_object
                    logger.info('WRAPPING %s', fname)

                    wrapper_func = wrapped_method.get('wrapper', _handle_request_wrapper)
                    wrapper_func = partial(wrapper_func, tracer=tracer, span_name=span_name)

                    wrap_function_wrapper(wrap_module, fname, wrapper_func)
            except ModuleNotFoundError as ex:
                print(f'CANNOT WRAP MODULE {wrap_module}')
                logger.info('Module not wrapped', exc_info=ex)

        logger.info('CUSTOM INSTRUMENTED')
        print('CUSTOM INSTRUMENTED')

    def _uninstrument(self, **kwargs):
        logger.info('CUSTOM UNINSTRUMENTING')
        print('CUSTOM UNINSTRUMENTING')

        for wrapped_method in WRAPPED_METHODS:
            wrap_module = wrapped_method.get('module')
            wrap_object = wrapped_method.get('object')
            try:
                module = importlib.import_module(wrap_module)
                wrapped = getattr(module, wrap_object, None)

                # if wrapped:
                #     unwrap(wrapped, wrapped_method.get('method'))
            except ModuleNotFoundError as ex:
                print(f'CANNOT FIND MODULE {wrap_module}')
                logger.info('Module not wrapped', exc_info=ex)

        print('CUSTOM UNINSTRUMENTED')

