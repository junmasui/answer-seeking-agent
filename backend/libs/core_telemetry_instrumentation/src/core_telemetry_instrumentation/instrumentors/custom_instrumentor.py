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
import mlflow

from ..tracing.custom_tracer import CustomMlflowLangchainTracer

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

    # When Pregel.stream is called, its `config` argument will be positional with
    # index 2 or key-word.
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

        # Check if our custom tracer is present
        has_custom_tracer = any(isinstance(handler, CustomMlflowLangchainTracer) for handler in callbacks)

        if not has_custom_tracer:
            # We need to configure the tracer. 
            # MLFlow tracer usually doesn't need args, but we might want to pass session_id if needed separately?
            # Creating a fresh instance.
            tracer_instance = CustomMlflowLangchainTracer()
            callbacks.append(tracer_instance)
            config['callbacks'] = callbacks

    # We NO LONGER wrap the execution in a manual span here manually if MLFlow handles it?
    # Actually, `_handle_lang_graph_wrapper` was originally WRAPPING the `stream` call with a span.
    # MLFlow autolog (even with log_traces=False) might NOT wrap `stream` automatically if we disabled it?
    # Wait, `log_traces=False` disables the *injection* of the tracer. It doesn't disable the patching of methods?
    # Actually, MLFlow's `safe_patch` is what does the wrapping.
    # If we use `autolog(log_traces=False)`, the patches are applied, but the callback manager logic depends on `log_traces`?
    # Looking at `autolog.py`:
    # `if not AutoLoggingConfig.init(FLAVOR_NAME).log_traces: return` inside `_patched_callback_manager_init`.
    # So if `log_traces=False`, MLFlow will NOT inject its tracer.
    # But we are manually injecting OUR tracer.
    # So we don't need to manually start a span here anymore?
    # The original wrapper started a "langgraph.stream" span.
    # Our Custom Tracer will rely on LangChain callbacks to create spans *inside* the execution.
    # But does LangGraph emit a start event that creates a root span *around* the stream?
    # LangGraph usually does.
    
    # Let's keep the manual span wrapper for now to ensure we have a "parent" span if LangGraph doesn't create one immediately?
    # Or cleaner: Just return wrapped(*args, **kwargs) without extra span, relying on `CustomMlflowLangchainTracer`?
    # Use standard OTel context propagation.
    
    return wrapped(*args, **kwargs)


async def _handle_async_lang_graph_wrapper(
    wrapped: typing.Callable[..., typing.Awaitable[typing.Any]],
    instance: typing.Any,
    args: tuple[typing.Any, ...],
    kwargs: dict[str, typing.Any],
    tracer: Tracer,
    span_name: str,
):
    """Wrapper for async methods that return a coroutine (ainvoke, abatch)."""
    # When Pregel.stream is called, its `config` argument will be positional with
    # index 2 or key-word.
    if len(args) > 2:
        config = args[2]
    else:
        config = kwargs.get('config', None)

    if config:
        extra_data = config.get('configurable', None)
        # session_id = extra_data.get('thread_id', None)
        # user_id = extra_data.get('user_id', None)

        callbacks = config.get('callbacks', None)
        if callbacks is None:
            config['callbacks'] = []
            callbacks = config.get('callbacks')

        # Check if our custom tracer is present
        has_custom_tracer = any(isinstance(handler, CustomMlflowLangchainTracer) for handler in callbacks)

        if not has_custom_tracer:
            # We need to configure the tracer.
             tracer_instance = CustomMlflowLangchainTracer()
             callbacks.append(tracer_instance)
             config['callbacks'] = callbacks

    return await wrapped(*args, **kwargs)


async def _handle_async_lang_graph_gen_wrapper(
    wrapped: typing.Callable[..., typing.AsyncIterator[typing.Any]],
    instance: typing.Any,
    args: tuple[typing.Any, ...],
    kwargs: dict[str, typing.Any],
    tracer: Tracer,
    span_name: str,
):
    """Wrapper for async methods that return an async generator (astream)."""
    # When Pregel.stream is called, its `config` argument will be positional with
    # index 2 or key-word.
    if len(args) > 2:
        config = args[2]
    else:
        config = kwargs.get('config', None)

    if config:
        extra_data = config.get('configurable', None)
        callbacks = config.get('callbacks', None)
        if callbacks is None:
            config['callbacks'] = []
            callbacks = config.get('callbacks')

        # Check if our custom tracer is present
        has_custom_tracer = any(isinstance(handler, CustomMlflowLangchainTracer) for handler in callbacks)

        if not has_custom_tracer:
             tracer_instance = CustomMlflowLangchainTracer()
             callbacks.append(tracer_instance)
             config['callbacks'] = callbacks

    async for item in wrapped(*args, **kwargs):
        yield item






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
        'wrapper': _handle_lang_graph_wrapper,
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
        print('MONKEY PATCH: Starting...', flush=True)

        # Monkey patch opentelemetry.sdk.trace.Span.set_attribute to debug span_type=None
        try:
            import traceback
            from opentelemetry.sdk.trace import Span as SdkSpan
            from opentelemetry.trace import Tracer as ApiTracer
            
            original_init = SdkSpan.__init__
            original_set_attribute = SdkSpan.set_attribute
            original_set_attributes = SdkSpan.set_attributes
            original_start_span = ApiTracer.start_span

            def log_none_attribute(key, value):
                if value is None:
                    stack = "".join(traceback.format_stack()[:-1])
                    msg = f"MONKEY PATCH: Attribute '{key}' set to None. Traceback:\n{stack}"
                    logger.warning(msg)
                    print(msg, flush=True)

            def version_wrapper(name):
                try:
                    return original_version(name)
                except Exception as e:
                    stack = "".join(traceback.format_stack()[:-1])
                    msg = f"MONKEY PATCH: CRASH in importlib.metadata.version('{name}'): {e}\nTraceback:\n{stack}"
                    print(msg, flush=True)
                    raise e

            from importlib import metadata as py_metadata
            original_version = py_metadata.version
            py_metadata.version = version_wrapper

            def init_wrapper(self, *args, **kwargs):
                attributes = kwargs.get("attributes")
                if attributes:
                    for k, v in attributes.items():
                        log_none_attribute(k, v)
                return original_init(self, *args, **kwargs)

            def set_attribute_wrapper(self, key, value):
                log_none_attribute(key, value)
                return original_set_attribute(self, key, value)

            def set_attributes_wrapper(self, attributes):
                if attributes:
                    for k, v in attributes.items():
                        log_none_attribute(k, v)
                return original_set_attributes(self, attributes)

            def start_span_wrapper(self, name, *args, **kwargs):
                # Check for None in attributes passed to start_span
                attributes = kwargs.get("attributes")
                if attributes:
                    for k, v in attributes.items():
                        log_none_attribute(k, v)
                return original_start_span(self, name, *args, **kwargs)

            SdkSpan.__init__ = init_wrapper
            SdkSpan.set_attribute = set_attribute_wrapper
            SdkSpan.set_attributes = set_attributes_wrapper
            ApiTracer.start_span = start_span_wrapper
            
            msg = "MONKEY PATCH: Applied to Span.__init__, set_attribute, set_attributes, Tracer.start_span"
            logger.info(msg)
            print(msg, flush=True)
        except Exception as e:
            logger.error(f"Failed to monkey patch: {e}")

        # Enable MLFlow Autologging but DISABLE default tracer injection
        # This allows us to inject our CustomMlflowLangchainTracer manually
        try:
             mlflow.langchain.autolog(log_traces=False, silent=False)
             logger.info('Enabled mlflow.langchain.autolog(log_traces=False)')
        except Exception as e:
             logger.error(f'Failed to enable mlflow autolog: {e}')

        tracer_provider = kwargs.get('tracer_provider')
        tracer = get_tracer(__name__, __version__, tracer_provider)
        for wrapped_method in WRAPPED_METHODS:
            module_name = wrapped_method.get('module')
            object_name = wrapped_method.get('object')
            method_name = wrapped_method.get('method')
            span_name = wrapped_method.get('span_name')

            logger.info('WRAPPING %s', module_name)
            try:
                wrap_module = importlib.import_module(module_name)
                print(f'WRAPPED {module_name}')
            except ModuleNotFoundError:
                print(f'CANNOT WRAP MODULE {module_name}')
                logger.info('Module not found %s', module_name)
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

            logger.info('WRAPPING %s', fname)

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
                    is_async = False
                    is_gen = False
                    is_asyncgen = False

            # choose provided wrapper if present, otherwise pick async/sync handler
            wrapper_func = wrapped_method.get('wrapper')
            if wrapper_func is None:
                wrapper_func = _handle_async_request_wrapper if is_async else _handle_request_wrapper

            wrapper_func = partial(wrapper_func, tracer=tracer, span_name=span_name)

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
