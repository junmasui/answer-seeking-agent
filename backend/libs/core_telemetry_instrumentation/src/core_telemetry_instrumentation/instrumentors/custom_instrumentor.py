"""
OpenLLMetry integration for the application.

This module provides integration with OpenLLMetry (Traceloop's LLM observability framework)
which is built on top of OpenTelemetry and provides automatic instrumentation for
LLM applications including LangChain, vector stores, and LLM providers.
"""

import importlib
import inspect
import logging
import typing
from functools import partial
from timeit import default_timer

from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.trace import SpanKind, Tracer, get_tracer
from wrapt import wrap_function_wrapper

from .langchain_handler import OpenTelemetryCallbackHandler, get_callback_handler

logger = logging.getLogger(__name__)

__version__ = '0.1.0'


def safe_set_span_attributes(span, attributes: dict):
    """
    Safely set span attributes, filtering out None values and logging when they occur.
    
    Args:
        span: The OpenTelemetry span
        attributes: Dictionary of attributes to set
    """
    if not attributes:
        return
    
    none_keys = [k for k, v in attributes.items() if v is None]
    if none_keys:
        logger.warning(
            "Attempting to set span attributes with None values. Keys with None: %s. "
            "These will be filtered out.",
            none_keys
        )
    
    # Only set non-None attributes
    for key, value in attributes.items():
        if value is not None:
            span.set_attribute(key, value)


def _handle_request_wrapper(
    wrapped: typing.Callable[..., typing.Any],
    instance: typing.Any,
    args: tuple[typing.Any, ...],
    kwargs: dict[str, typing.Any],
    get_tracer: typing.Callable[[], Tracer],
    span_name: str,
):
    span_attributes = {}
    metric_attributes = {}

    tracer = get_tracer()

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
                safe_set_span_attributes(span, {ERROR_TYPE: type(exception).__qualname__})
                metric_attributes[ERROR_TYPE] = type(exception).__qualname__
            raise exception.with_traceback(exception.__traceback__)

    return response


async def _handle_async_request_wrapper(
    wrapped: typing.Callable[..., typing.Awaitable[typing.Any]],
    instance: typing.Any,
    args: tuple[typing.Any, ...],
    kwargs: dict[str, typing.Any],
    get_tracer: typing.Callable[[], Tracer],
    span_name: str,
):
    span_attributes = {}
    metric_attributes = {}

    tracer = get_tracer()

    with tracer.start_as_current_span(span_name, kind=SpanKind.INTERNAL, attributes=span_attributes) as span:
        exception = None

        logger.info('WRAPPED ASYNC REQUEST %s', wrapped.__name__)

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
                safe_set_span_attributes(span, {ERROR_TYPE: type(exception).__qualname__})
            raise exception.with_traceback(exception.__traceback__)

    return response


def _handle_gen_wrapper(
    wrapped: typing.Callable[..., typing.Generator[typing.Any, None, None]],
    instance: typing.Any,
    args: tuple[typing.Any, ...],
    kwargs: dict[str, typing.Any],
    get_tracer: typing.Callable[[], Tracer],
    span_name: str,
):
    """Wrapper for sync generator functions (functions that yield)."""
    span_attributes = {}
    metric_attributes = {}

    tracer = get_tracer()

    with tracer.start_as_current_span(span_name, kind=SpanKind.INTERNAL, attributes=span_attributes) as span:
        exception = None

        logger.info('WRAPPED GEN %s', wrapped.__name__)

        start_time = default_timer()

        try:
            for item in wrapped(*args, **kwargs):
                yield item
        except Exception as exc:
            exception = exc
        finally:
            elapsed_time = max(default_timer() - start_time, 0)

        if exception:
            if span.is_recording():
                safe_set_span_attributes(span, {ERROR_TYPE: type(exception).__qualname__})
            raise exception.with_traceback(exception.__traceback__)


async def _handle_async_gen_wrapper(
    wrapped: typing.Callable[..., typing.AsyncGenerator[typing.Any, None]],
    instance: typing.Any,
    args: tuple[typing.Any, ...],
    kwargs: dict[str, typing.Any],
    get_tracer: typing.Callable[[], Tracer],
    span_name: str,
):
    """Wrapper for async generator functions (async functions that yield)."""
    span_attributes = {}
    metric_attributes = {}

    tracer = get_tracer()

    with tracer.start_as_current_span(span_name, kind=SpanKind.INTERNAL, attributes=span_attributes) as span:
        exception = None

        logger.info('WRAPPED ASYNC GEN %s', wrapped.__name__)

        start_time = default_timer()

        try:
            async for item in wrapped(*args, **kwargs):
                yield item
        except Exception as exc:
            exception = exc
        finally:
            elapsed_time = max(default_timer() - start_time, 0)

        if exception:
            if span.is_recording():
                safe_set_span_attributes(span, {ERROR_TYPE: type(exception).__qualname__})
            raise exception.with_traceback(exception.__traceback__)




def _ensure_telemetry_in_config(args, kwargs, span_name):

    logger.info(f"ENSURE TELEMETRY for {span_name}")

    # When Pregel.stream is called, its `config` argument will be positional with
    # index 2 or key-word.
    if len(args) > 2:
        config = args[2]
    else:
        config = kwargs.get('config', None)

    # Context management in async generators/coroutines is tricky with manual spans.
    # We rely on the CustomMlflowLangchainTracer injected into callbacks to handle the trace hierarchy.
    if config:
        extra_data = config.get('configurable', {}) or {}
        session_id = extra_data.get('thread_id', None)
        user_id = extra_data.get('user_id', None)

        callbacks = config.get('callbacks', None)
        if callbacks is None:
            config['callbacks'] = []
            callbacks = config.get('callbacks')

        # Check if our custom tracer is present
        has_telemetry = any(isinstance(handler, OpenTelemetryCallbackHandler) for handler in callbacks)
        
        if not has_telemetry:
            # We need to configure the tracer. 
            # MLFlow tracer usually doesn't need args, but we might want to pass session_id if needed separately?
            # Creating a fresh instance.
            callback = get_callback_handler(session_id=session_id, user_id=user_id)
            callbacks.append(callback)
            config['callbacks'] = callbacks
            logger.info(f"WRAPPER: Added OpenTelemetryCallbackHandler to {span_name}")


def _handle_lang_graph_wrapper(
    wrapped: typing.Callable[..., typing.Any],
    instance: typing.Any,
    args: tuple[typing.Any, ...],
    kwargs: dict[str, typing.Any],
    get_tracer: typing.Callable[[], Tracer],
    span_name: str,
):
    span_attributes = {}

    _ensure_telemetry_in_config(args, kwargs, span_name)

    return _handle_request_wrapper(
        wrapped=wrapped,
        instance=instance,
        args=args,
        kwargs=kwargs,
        get_tracer=get_tracer,
        span_name=span_name)


def _handle_lang_graph_gen_wrapper(
    wrapped: typing.Callable[..., typing.Any],
    instance: typing.Any,
    args: tuple[typing.Any, ...],
    kwargs: dict[str, typing.Any],
    get_tracer: typing.Callable[[], Tracer],
    span_name: str,
):
    _ensure_telemetry_in_config(args, kwargs, span_name)

    for x in _handle_gen_wrapper(
        wrapped=wrapped,
        instance=instance,
        args=args,
        kwargs=kwargs,
        get_tracer=get_tracer,
        span_name=span_name):
        yield x


async def _handle_async_lang_graph_wrapper(
    wrapped: typing.Callable[..., typing.Awaitable[typing.Any]],
    instance: typing.Any,
    args: tuple[typing.Any, ...],
    kwargs: dict[str, typing.Any],
    get_tracer: typing.Callable[[], Tracer],
    span_name: str,
):
    """Wrapper for async methods that return a coroutine (ainvoke, abatch)."""
    _ensure_telemetry_in_config(args, kwargs, span_name)

    return await _handle_async_request_wrapper(
        wrapped=wrapped,
        instance=instance,
        args=args,
        kwargs=kwargs,
        get_tracer=get_tracer,
        span_name=span_name)


async def _handle_async_lang_graph_gen_wrapper(
    wrapped: typing.Callable[..., typing.AsyncIterator[typing.Any]],
    instance: typing.Any,
    args: tuple[typing.Any, ...],
    kwargs: dict[str, typing.Any],
    get_tracer: typing.Callable[[], Tracer],
    span_name: str,
):
    """Wrapper for async methods that return an async generator (astream)."""
    _ensure_telemetry_in_config(args, kwargs, span_name)

    async for x in _handle_async_gen_wrapper(
        wrapped=wrapped,
        instance=instance,
        args=args,
        kwargs=kwargs,
        get_tracer=get_tracer,
        span_name=span_name):
        yield x


WRAPPED_METHODS = [
    {
        'module': 'core.ingest.ingest',
        'object': '_ingest_one_document',
        'method': None,
        'span_name': '_ingest_one_document',
    },
    {
        'module': 'langchain_core.vectorstores.base',
        'object': 'VectorStore',
        'method': 'add_documents',
        'span_name': 'vectorstore.add_documents',
    },
    {
        'module': 'langchain_core.vectorstores.base',
        'object': 'VectorStore',
        'method': 'search',
        'span_name': 'vector.search',
    },
    {
        'module': 'langchain_core.vectorstores.base',
        'object': 'VectorStore',
        'method': 'similarity_search',
        'span_name': 'vector.similarity_search',
    },
    {
        'module': 'langchain_core.vectorstores.base',
        'object': 'VectorStore',
        'method': 'similarity_search_with_score',
        'span_name': 'vector.similarity_search_with_score',
    },
    {
        'module': 'langchain_core.vectorstores.base',
        'object': 'VectorStore',
        'method': 'similarity_search_with_relevance_scores',
        'span_name': 'vector.similarity_search_with_relevance_scores',
    },
    {
        'module': 'langchain_core.vectorstores.base',
        'object': 'VectorStore',
        'method': 'similarity_search_by_vector',
        'span_name': 'vector.similarity_search_by_vector',
    },
    {
        'module': 'langchain_core.vectorstores.base',
        'object': 'VectorStore',
        'method': 'max_marginal_relevance_search',
        'span_name': 'vector.max_marginal_relevance_search',
    },
    {
        'module': 'langchain_core.vectorstores.base',
        'object': 'VectorStore',
        'method': 'max_marginal_relevance_search_by_vector',
        'span_name': 'vector.max_marginal_relevance_search_by_vector',
    },
    {
        'module': 'langchain_core.retrievers',
        'object': 'BaseRetriever',
        'method': 'invoke',
        'span_name': 'retriever.invoke',
    },
    {
        'module': 'langchain_unstructured.document_loaders',
        'object': 'UnstructuredLoader',
        'method': 'lazy_load',
        'span_name': 'unstructured_loader.lazy_load',
    },
    {
        'module': 'langchain_unstructured.document_loaders',
        'object': '_SingleDocumentLoader',
        'method': 'lazy_load',
        'span_name': 'single_doc_loader.lazy_load',
    },
    {
        'module': 'unstructured.partition.auto',
        'object': 'partition',
        'method': None,
        'span_name': 'unstructured.partition',
    },
    # internal functions decorated with @requires_dependencies
    {
        'module': 'unstructured.partition.pdf',
        'object': '_partition_pdf_or_image_local',
        'method': None,
        'span_name': 'unstructured.pdf._partition_pdf_or_image_local',
    },
    {
        'module': 'unstructured.partition.pdf',
        'object': 'check_pdf_hi_res_max_pages_exceeded',
        'method': None,
        'span_name': 'unstructured.pdf.check_pdf_hi_res_max_pages_exceeded',
    },
    {
        'module': 'unstructured.partition.pdf_image.ocr',
        'object': 'process_data_with_ocr',
        'method': None,
        'span_name': 'unstructured.process_data_with_ocr',
    },
    {
        'module': 'unstructured.partition.pdf_image.ocr',
        'object': 'process_file_with_ocr',
        'method': None,
        'span_name': 'unstructured.process_file_with_ocr',
    },
    {
        'module': 'unstructured.partition.pdf_image.pdfminer_processing',
        'object': 'process_data_with_pdfminer',
        'method': None,
        'span_name': 'unstructured.process_data_with_pdfminer',
    },
    {
        'module': 'unstructured.partition.pdf_image.pdfminer_processing',
        'object': 'process_file_with_pdfminer',
        'method': None,
        'span_name': 'unstructured.process_file_with_pdfminer',
    },
    {
        'module': 'unstructured.partition.utils.ocr_models.paddle_ocr',
        'object': 'OCRAgentPaddle',
        'method': 'get_layout_elements_from_image',
        'span_name': 'unstructured.ocr-agent.get_layout_elements_from_image',
    },
    {
        'module': 'unstructured.partition.utils.ocr_models.paddle_ocr',
        'object': 'OCRAgentPaddle',
        'method': 'get_layout_from_image',
        'span_name': 'unstructured.ocr-agent.get_layout_from_image',
    },
    {
        'module': 'unstructured.partition.utils.ocr_models.paddle_ocr',
        'object': 'OCRAgentPaddle',
        'method': 'get_text_from_image',
        'span_name': 'unstructured.ocr-agent.get_text_from_image',
    },
    {
        'module': 'unstructured.partition.utils.ocr_models.tesseract_ocr',
        'object': 'OCRAgentTesseract',
        'method': 'get_layout_elements_from_image',
        'span_name': 'unstructured.ocr-agent.get_layout_elements_from_image',
    },
    {
        'module': 'unstructured.partition.utils.ocr_models.tesseract_ocr',
        'object': 'OCRAgentTesseract',
        'method': 'get_layout_from_image',
        'span_name': 'unstructured.ocr-agent.get_layout_from_image',
    },
    {
        'module': 'unstructured.partition.utils.ocr_models.tesseract_ocr',
        'object': 'OCRAgentTesseract',
        'method': 'get_text_from_image',
        'span_name': 'unstructured.ocr-agent.get_text_from_image',
    },
    {
        'module': 'unstructured_inference.inference.layout',
        'object': 'process_data_with_model',
        'method': None,
        'span_name': 'unstructured.process_data_with_model',
    },
    {
        'module': 'unstructured_inference.inference.layout',
        'object': 'process_file_with_model',
        'method': None,
        'span_name': 'unstructured.process_file_with_model',
    },
    {
        'module': 'unstructured_inference.models.detectron2onnx',
        'object': 'UnstructuredDetectronONNXModel',
        'method': 'initialize',
        'span_name': 'UnstructuredDetectronONNXModel.initialize',
    },
    {
        'module': 'unstructured_inference.models.detectron2onnx',
        'object': 'UnstructuredDetectronONNXModel',
        'method': 'predict',
        'span_name': 'UnstructuredDetectronONNXModel.predict',
    },
    {
        'module': 'unstructured_inference.models.yolox',
        'object': 'UnstructuredYoloXModel',
        'method': 'initialize',
        'span_name': 'UnstructuredYoloXModel.initialize',
    },
    {
        'module': 'unstructured_inference.models.yolox',
        'object': 'UnstructuredYoloXModel',
        'method': 'image_processing',
        'span_name': 'UnstructuredYoloXModel.image_processing',
    },
    {
        'module': 'unstructured_pytesseract.pytesseract',
        'object': 'image_to_pdf_or_hocr',
        'method': None,
        'span_name': 'unstructured_pytesseract.image_to_pdf_or_hocr',
    },
    {
        'module': 'unstructured_pytesseract.pytesseract',
        'object': 'image_to_string',
        'method': None,
        'span_name': 'unstructured_pytesseract.image_to_string',
    },
    {
        'module': 'unstructured_pytesseract.pytesseract',
        'object': 'run_tesseract',
        'method': None,
        'span_name': 'unstructured_pytesseract.run_tesseract',
    },
    # {
    #     'module': 'pdfminer.pdfinterp',
    #     'object': 'PDFPageInterpreter',
    #     'method': 'process_page',
    #     'span_name': 'pdfminer.PDFPageInterpreter.process_page'
    # },
    # {
    #     'module': 'pdfminer.converter',
    #     'object': 'PDFPageAggregator',
    #     'method': 'get_result',
    #     'span_name': 'pdfminer.PDFPageAggregator.get_result'
    # },
    {
        'module': 'langchain_huggingface.embeddings.huggingface',
        'object': 'HuggingFaceEmbeddings',
        'method': 'embed_documents',
        'span_name': 'hf_embeddings_model.embed_documents',
    },
    {
        'module': 'langchain_huggingface.embeddings.huggingface',
        'object': 'HuggingFaceEmbeddings',
        'method': 'embed_query',
        'span_name': 'hf_embeddings_model.embed_query',
    },
    {
        'module': 'langchain_weaviate.vectorstores',
        'object': 'WeaviateVectorStore',
        'method': 'add_texts',
        'span_name': 'WeaviateVectorStore.add_texts',
    },
    {
        'module': 'langchain_weaviate.vectorstores',
        'object': 'WeaviateVectorStore',
        'method': 'similarity_search',
        'span_name': 'WeaviateVectorStore.similarity_search',
    },
    {
        'module': 'langchain_weaviate.vectorstores',
        'object': 'WeaviateVectorStore',
        'method': 'similarity_search_with_score',
        'span_name': 'WeaviateVectorStore.similarity_search_with_score',
    },
    {
        'module': 'langchain_weaviate.vectorstores',
        'object': 'WeaviateVectorStore',
        'method': 'max_marginal_relevance_search',
        'span_name': 'WeaviateVectorStore.max_marginal_relevance_search',
    },
    {
        'module': 'langchain_weaviate.vectorstores',
        'object': 'WeaviateVectorStore',
        'method': 'max_marginal_relevance_search_by_vector',
        'span_name': 'WeaviateVectorStore.max_marginal_relevance_search_by_vector',
    },
    {
        'module': 'langchain_weaviate.vectorstores',
        'object': 'WeaviateVectorStore',
        'method': 'delete',
        'span_name': 'WeaviateVectorStore.delete',
    },
    {
        'module': 'langgraph.pregel',
        'object': 'Pregel',
        'method': 'invoke',
        'span_name': 'graph.invoke',
        'wrapper': _handle_lang_graph_wrapper,
    },
    {
        'module': 'langgraph.pregel',
        'object': 'Pregel',
        'method': 'ainvoke',
        'span_name': 'graph.ainvoke',
        'wrapper': _handle_async_lang_graph_wrapper,
    },
    {
        'module': 'langgraph.pregel',
        'object': 'Pregel',
        'method': 'stream',
        'span_name': 'graph.stream',
        'wrapper': _handle_lang_graph_gen_wrapper,
    },
    {
        'module': 'langgraph.pregel',
        'object': 'Pregel',
        'method': 'astream',
        'span_name': 'graph.astream',
        'wrapper': _handle_async_lang_graph_gen_wrapper, 
    },
    {
        'module': 'langgraph.pregel',
        'object': 'Pregel',
        'method': 'batch',
        'span_name': 'graph.batch',
        'wrapper': _handle_lang_graph_wrapper,
    },
    {
        'module': 'langgraph.pregel',
        'object': 'Pregel',
        'method': 'abatch',
        'span_name': 'graph.abatch',
        'wrapper': _handle_async_lang_graph_wrapper,
    },

    {
        'module': 'presidio_analyzer.nlp_engine.spacy_nlp_engine',
        'object': 'SpacyNlpEngine',
        'method': 'process_text',
        'span_name': 'spacy_nlp_engine.process_text',
    },
    {
        'module': 'presidio_analyzer.nlp_engine.spacy_nlp_engine',
        'object': 'SpacyNlpEngine',
        'method': 'process_batch',
        'span_name': 'spacy_nlp_engine.process_batch',
    },
    # {'module': 'transformers', 'object': 'TextGenerationPipeline',
    #     'method': '__call__', 'span_name': 'transformers_text_generation_pipeline.call'},
    {'module': 'spacy.language', 'object': 'Language', 'method': '__call__', 'span_name': 'spacy.language'},
]
ERROR_TYPE: str = 'error.type'


class CustomInstrumentor(BaseInstrumentor):
    # pylint: disable=protected-access,attribute-defined-outside-init
    """
    An instrumentor for httpx Client and AsyncClient.

    See `BaseInstrumentor`
    """

    def instrumentation_dependencies(self) -> typing.Collection[str]:
        """Return a collection of instrumentation dependencies."""
        logger.info('CUSTOM INSTRUMENTATION DEPENDENCIES')
        print('CUSTOM INSTRUMENTATION DEPENDENCIES')
        return []

    def _instrument(self, **kwargs):
        logger.info('CUSTOM INSTRUMENTING')
        print('CUSTOM INSTRUMENTING')

        # Enable MLFlow Autologging but DISABLE default tracer injection
        # This allows us to inject our CustomMlflowLangchainTracer manually
        
        tracer_provider = kwargs.get('tracer_provider')
        def _get_tracer():
            tracer = get_tracer(__name__, __version__, tracer_provider)
            return tracer

        for wrapped_method in WRAPPED_METHODS:
            module_name = wrapped_method.get('module')
            object_name = wrapped_method.get('object')
            method_name = wrapped_method.get('method')
            span_name = wrapped_method.get('span_name')

            wrapped_name = ' '.join([x for x in [module_name, object_name, method_name] if x])
            logger.info('WRAPPING %s', wrapped_name)
            try:
                wrap_module = importlib.import_module(module_name)
                print(f'WRAPPED {wrapped_name}')
            except ModuleNotFoundError:
                print(f'CANNOT WRAP MODULE {wrapped_name}')
                logger.info('Module not found %s', wrapped_name)
                continue

            wrap_object = getattr(wrap_module, object_name, None)
            if wrap_object is None:
                logger.info('Object not found %s', object_name)
                continue

            if method_name is not None:
                fname = f'{object_name}.{method_name}'
                # Wrap object is a function.
                fobj = getattr(wrap_object, method_name, None)
            else:
                fname = object_name
                fobj = wrap_object

            logger.info('WRAPPING %s', wrapped_name)

            # detect if the target object/function is asynchronous
            is_async = False
            is_gen = False
            is_asyncgen = False
            if fobj is not None:
                try:
                    is_async = inspect.iscoroutinefunction(fobj)
                    is_gen = inspect.isgeneratorfunction(fobj)
                    is_asyncgen = inspect.isasyncgenfunction(fobj)
                except Exception:
                    logger.info('Cannot instrument method %s', fname)
                    continue
            is_sync = not is_async and not is_gen and not is_asyncgen

            # choose provided wrapper if present, otherwise pick async/sync handler
            wrapper_func = wrapped_method.get('wrapper')
            if wrapper_func is not None:
                is_async_wrapper = inspect.iscoroutinefunction(wrapper_func)
                is_gen_wrapper = inspect.isgeneratorfunction(wrapper_func)
                is_asyncgen_wrapper = inspect.isasyncgenfunction(wrapper_func)
                is_sync_wrapper = not is_async_wrapper and not is_gen_wrapper and not is_asyncgen_wrapper

                if is_asyncgen:
                    if not is_asyncgen_wrapper:
                        print(f'Wrapper {wrapper_func.__name__} is not an async generator (expected async generator)')
                        logger.warning('Wrapper %s is not an async generator (expected async generator)', wrapper_func.__name__)
                        continue
                elif is_async:
                    if not is_async_wrapper:
                        print(f'Wrapper {wrapper_func.__name__} is not a coroutine function (expected async)')
                        logger.warning('Wrapper %s is not a coroutine function (expected async)', wrapper_func.__name__)
                        continue
                elif is_gen:
                    if not is_gen_wrapper:
                        print(f'Wrapper {wrapper_func.__name__} is not a generator (expected generator)')
                        logger.warning('Wrapper %s is not a generator (expected generator)', wrapper_func.__name__)
                        continue
                elif is_sync:
                    if not is_sync_wrapper:
                        print(f'Wrapper {wrapper_func.__name__} is async/generator (expected sync)')
                        logger.warning('Wrapper %s is async/generator (expected sync)', wrapper_func.__name__)
                        continue
                else:
                    logger.warning('Wrapper %s is not inspected', wrapper_func.__name__)
                    continue

            else:
                # Choose wrapper based on function type:
                # - Async generators need special handling (async for yielding)
                # - Regular async functions (return value)
                # - Sync generators (yield)
                # - Regular sync functions (return value)
                if is_asyncgen:
                    # Async generator - use async gen wrapper
                    wrapper_func = _handle_async_gen_wrapper
                elif is_async:
                    # Regular async function that returns a value
                    wrapper_func = _handle_async_request_wrapper
                elif is_gen:
                    # Sync generator - use gen wrapper
                    wrapper_func = _handle_gen_wrapper
                else:
                    # Regular sync function
                    wrapper_func = _handle_request_wrapper

            wrapper_func = partial(wrapper_func, get_tracer=_get_tracer, span_name=span_name)

            wrap_function_wrapper(wrap_module, fname, wrapper_func)

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
