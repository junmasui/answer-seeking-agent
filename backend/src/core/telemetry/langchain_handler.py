"""
OpenTelemetry-based callback handler for LangChain/LangGraph operations.

This module provides a drop-in replacement for Langfuse's CallbackHandler,
using OpenTelemetry for distributed tracing and metrics collection.
"""

import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.documents import Document
from langchain_core.outputs import ChatGeneration, Generation, LLMResult
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from .custom_otel import get_meter, get_tracer

logger = logging.getLogger(__name__)


class OpenTelemetryCallbackHandler(BaseCallbackHandler):
    """
    OpenTelemetry-based callback handler for LangChain operations.

    This handler captures:
    - Distributed traces for LLM operations
    - Metrics for token usage, latency, and costs
    - Session and user tracking
    - Error handling and debugging information
    """

    def __init__(
        self, session_id: Optional[str] = None, user_id: Optional[str] = None, sample_rate: float = 1.0, **kwargs
    ):
        """
        Initialize the OpenTelemetry callback handler.

        Args:
            session_id: Session identifier for grouping related operations
            user_id: User identifier for attribution
            sample_rate: Sampling rate for trace collection (0.0-1.0)
            **kwargs: Additional configuration options

        """
        super().__init__()
        self.session_id = session_id or str(uuid.uuid4())
        self.user_id = user_id
        self.sample_rate = sample_rate

        # Initialize telemetry
        self.tracer = get_tracer()
        self.meter = get_meter()

        # Create metrics
        self._init_metrics()

        # Active spans tracking
        self._spans: Dict[str, trace.Span] = {}
        self._run_start_times: Dict[str, float] = {}

        logger.debug(f'OpenTelemetryCallbackHandler initialized with session_id={self.session_id}')

    def _init_metrics(self):
        """Initialize OpenTelemetry metrics."""
        self.llm_request_counter = self.meter.create_counter(
            name='llm_requests_total', description='Total number of LLM requests', unit='1'
        )

        self.llm_request_duration = self.meter.create_histogram(
            name='llm_request_duration_seconds', description='Duration of LLM requests', unit='s'
        )

        self.llm_token_usage = self.meter.create_counter(
            name='llm_tokens_total', description='Total number of tokens processed', unit='1'
        )

        self.llm_cost_metric = self.meter.create_counter(
            name='llm_cost_total', description='Total cost of LLM operations', unit='1'
        )

        self.retrieval_counter = self.meter.create_counter(
            name='retrieval_requests_total', description='Total number of retrieval requests', unit='1'
        )

        self.retrieval_duration = self.meter.create_histogram(
            name='retrieval_duration_seconds', description='Duration of retrieval operations', unit='s'
        )

    def on_llm_start(
        self,
        serialized: Optional[Dict[str, Any]],
        prompts: List[str],
        *,
        run_id: uuid.UUID,
        parent_run_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """Handle LLM start event."""
        run_id_str = str(run_id)

        # Handle None serialized parameter (common with LCEL Runnables)
        llm_name = 'unknown'
        llm_vendor = 'unknown' 
        llm_model = 'unknown'
        llm_temperature = None
        llm_max_tokens = None
        
        if serialized is not None:
            llm_name = serialized.get('name', 'unknown')
            llm_vendor = serialized.get('_type', 'unknown')
            llm_model = serialized.get('model_name', 'unknown')
            llm_temperature = serialized.get('temperature')
            llm_max_tokens = serialized.get('max_tokens')

        # Create span for LLM operation
        span_name = f'llm.{llm_name}'
        span_attributes = {
                'llm.vendor': llm_vendor,
                'llm.model': llm_model,
                'llm.temperature': llm_temperature,
                'llm.max_tokens': llm_max_tokens,
                'session.id': self.session_id,
                'user.id': self.user_id,
                'run.id': run_id_str,
                'llm.prompts.count': len(prompts),
            }
        if parent_run_id is not None:
            span_attributes['run.parent_id'] = str(parent_run_id)

        parent_span = self._spans.get(str(parent_run_id)) if parent_run_id else None
        parent_context = trace.set_span_in_context(parent_span) if parent_span else None

        span = self.tracer.start_span(
            name=span_name,
            attributes=span_attributes,
            context=parent_context,
        )
        logger.info('--- ON_LLM_START %s\nserialized: %r\nspan: %r\nmetadata: %r', run_id, serialized, span, metadata)

        # Add prompt content to span (with size limits)
        for i, prompt in enumerate(prompts[:3]):  # Limit to first 3 prompts
            prompt_preview = prompt[:500] + '...' if len(prompt) > 500 else prompt
            span.set_attribute(f'llm.prompt.{i}', prompt_preview)

        # Add tags and metadata
        if tags:
            span.set_attribute('llm.tags', json.dumps(tags))
        if metadata:
            span.set_attribute('llm.metadata', json.dumps(metadata, default=str))

        self._spans[run_id_str] = span
        self._run_start_times[run_id_str] = time.time()

        # Record metrics
        self.llm_request_counter.add(
            1,
            attributes={
                'model': llm_model,
                'vendor': llm_vendor,
                'session_id': self.session_id,
            },
        )

    def on_llm_end(
        self, response: LLMResult, *, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None, **kwargs: Any
    ) -> Any:
        """Handle LLM end event."""
        run_id_str = str(run_id)
        span = self._spans.get(run_id_str)
        start_time = self._run_start_times.get(run_id_str)

        logger.info('--- ON_LLM_END %s\nspan: %r', run_id, span)

        if not span:
            logger.warning(f'No span found for LLM run {run_id_str}')
            return

        try:
            # Calculate duration
            duration = time.time() - start_time if start_time else 0

            # Extract token usage
            token_usage = response.llm_output.get('token_usage', {}) if response.llm_output else {}
            prompt_tokens = token_usage.get('prompt_tokens', 0)
            completion_tokens = token_usage.get('completion_tokens', 0)
            total_tokens = token_usage.get('total_tokens', 0)

            # Update span attributes
            span.set_attribute('llm.usage.prompt_tokens', prompt_tokens)
            span.set_attribute('llm.usage.completion_tokens', completion_tokens)
            span.set_attribute('llm.usage.total_tokens', total_tokens)
            span.set_attribute('llm.response.generations_count', len(response.generations))
            span.set_attribute('llm.duration_seconds', duration)

            # Add response content (limited)
            for i, generation_list in enumerate(response.generations[:2]):
                for j, generation in enumerate(generation_list[:2]):
                    if isinstance(generation, ChatGeneration):
                        content = generation.message.content
                    elif isinstance(generation, Generation):
                        content = generation.text
                    else:
                        content = str(generation)

                    content_preview = content[:300] + '...' if len(content) > 300 else content
                    span.set_attribute(f'llm.response.{i}.{j}', content_preview)

            # Record metrics
            attributes = {
                'model': span.attributes.get('llm.model', 'unknown'),
                'vendor': span.attributes.get('llm.vendor', 'unknown'),
                'session_id': self.session_id,
            }

            self.llm_request_duration.record(duration, attributes=attributes)

            if prompt_tokens > 0:
                self.llm_token_usage.add(prompt_tokens, {**attributes, 'token_type': 'prompt'})
            if completion_tokens > 0:
                self.llm_token_usage.add(completion_tokens, {**attributes, 'token_type': 'completion'})

            span.set_status(Status(StatusCode.OK))

        except Exception as ex:
            logger.warning('Error in on_llm_end', exc_info=ex)
            span.set_status(Status(StatusCode.ERROR, str(ex)))
        finally:
            span.end()
            self._spans.pop(run_id_str, None)
            self._run_start_times.pop(run_id_str, None)

    def on_llm_error(
        self, error: BaseException, *, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None, **kwargs: Any
    ) -> Any:
        """Handle LLM error event."""
        run_id_str = str(run_id)
        span = self._spans.get(run_id_str)

        if span:
            span.set_status(Status(StatusCode.ERROR, str(error)))
            span.set_attribute('error.type', type(error).__name__)
            span.set_attribute('error.message', str(error))
            span.end()

            self._spans.pop(run_id_str, None)
            self._run_start_times.pop(run_id_str, None)

    def on_retriever_start(
        self,
        serialized: Optional[Dict[str, Any]],
        query: str,
        *,
        run_id: uuid.UUID,
        parent_run_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """Handle retriever start event."""
        run_id_str = str(run_id)

        # Handle None serialized parameter (common with LCEL Runnables)
        retriever_type = 'unknown'
        if serialized is not None:
            retriever_type = serialized.get('_type', 'unknown')

        span_attributes = {
                'retrieval.query': query[:200] + '...' if len(query) > 200 else query,
                'retrieval.query_length': len(query),
                'session.id': self.session_id,
                'user.id': self.user_id,
                'run.id': run_id_str,
            }
        if parent_run_id is not None:
            span_attributes['run.parent_id'] = str(parent_run_id)

        parent_span = self._spans.get(str(parent_run_id)) if parent_run_id else None
        parent_context = trace.set_span_in_context(parent_span) if parent_span else None

        span = self.tracer.start_span(
            name='retrieval.search',
            attributes=span_attributes,
            context=parent_context,
        )
        logger.info('--- ON_RETRIEVER_START %s\nserialized: %r\nspan: %r\nmetadata: %r', run_id, serialized, span, metadata)

        # Add tags and metadata
        if tags:
            span.set_attribute('retrieval.tags', json.dumps(tags))
        if metadata:
            span.set_attribute('retrieval.metadata', json.dumps(metadata, default=str))

        self._spans[run_id_str] = span
        self._run_start_times[run_id_str] = time.time()

        # Record metrics
        self.retrieval_counter.add(
            1, attributes={'session_id': self.session_id, 'retriever_type': retriever_type}
        )

    def on_retriever_end(
        self, documents: List[Document], *, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None, **kwargs: Any
    ) -> Any:
        """Handle retriever end event."""
        run_id_str = str(run_id)
        span = self._spans.get(run_id_str)
        start_time = self._run_start_times.get(run_id_str)

        logger.info('--- ON_RETRIEVER_END %s\nspan: %r', run_id, span)

        if not span:
            return

        try:
            duration = time.time() - start_time if start_time else 0

            span.set_attribute('retrieval.documents_count', len(documents))
            span.set_attribute('retrieval.duration_seconds', duration)

            # Add document metadata (limited)
            for i, doc in enumerate(documents[:5]):  # Limit to first 5 documents
                span.set_attribute(f'retrieval.document.{i}.source', str(doc.metadata.get('source', '')))
                span.set_attribute(f'retrieval.document.{i}.length', len(doc.page_content))

            # Record metrics
            self.retrieval_duration.record(
                duration, attributes={'session_id': self.session_id, 'documents_found': len(documents)}
            )

            span.set_status(Status(StatusCode.OK))

        except Exception as ex:
            logger.warning('Error in on_retriever_end', exc_info=ex)
            span.set_status(Status(StatusCode.ERROR, str(ex)))
        finally:
            span.end()
            self._spans.pop(run_id_str, None)
            self._run_start_times.pop(run_id_str, None)

    def on_retriever_error(
        self, error: BaseException, *, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None, **kwargs: Any
    ) -> Any:
        """Handle retriever error event."""
        run_id_str = str(run_id)
        span = self._spans.get(run_id_str)

        if span:
            span.set_status(Status(StatusCode.ERROR, str(error)))
            span.set_attribute('error.type', type(error).__name__)
            span.set_attribute('error.message', str(error))
            span.end()

            self._spans.pop(run_id_str, None)
            self._run_start_times.pop(run_id_str, None)

    def on_tool_start(
        self,
        serialized: Optional[Dict[str, Any]],
        input_str: str,
        *,
        run_id: uuid.UUID,
        parent_run_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        inputs: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """Handle tool start event."""
        run_id_str = str(run_id)

        # Handle None serialized parameter (common with LCEL Runnables)
        tool_name = 'unknown'
        if serialized is not None:
            tool_name = serialized.get('name', 'unknown')

        span_attributes = {
                'tool.name': tool_name,
                'tool.input': input_str[:200] + '...' if len(input_str) > 200 else input_str,
                'session.id': self.session_id,
                'user.id': self.user_id,
                'run.id': run_id_str,
            }
        if parent_run_id is not None:
            span_attributes['run.parent_id'] = str(parent_run_id)

        parent_span = self._spans.get(str(parent_run_id)) if parent_run_id else None
        parent_context = trace.set_span_in_context(parent_span) if parent_span else None

        span = self.tracer.start_span(
            name=f'tool.{tool_name}',
            attributes=span_attributes,
            context=parent_context,
        )
        logger.info('--- ON_TOOL_START %s\nserialized: %r\nspan: %r\nmetadata: %r', run_id, serialized, span, metadata)

        # Add tags and metadata
        if tags:
            span.set_attribute('tool.tags', json.dumps(tags))
        if metadata:
            span.set_attribute('tool.metadata', json.dumps(metadata, default=str))

        self._spans[run_id_str] = span
        self._run_start_times[run_id_str] = time.time()

    def on_tool_end(
        self, output: str, *, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None, **kwargs: Any
    ) -> Any:
        """Handle tool end event."""
        run_id_str = str(run_id)
        span = self._spans.get(run_id_str)
        start_time = self._run_start_times.get(run_id_str)

        if not span:
            return

        try:
            duration = time.time() - start_time if start_time else 0

            span.set_attribute('tool.output', output[:200] + '...' if len(output) > 200 else output)
            span.set_attribute('tool.duration_seconds', duration)
            span.set_status(Status(StatusCode.OK))

        except Exception as ex:
            logger.warning('Error in on_tool_end', exc_info=ex)
            span.set_status(Status(StatusCode.ERROR, str(ex)))
        finally:
            span.end()
            self._spans.pop(run_id_str, None)
            self._run_start_times.pop(run_id_str, None)

    def on_tool_error(
        self, error: BaseException, *, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None, **kwargs: Any
    ) -> Any:
        """Handle tool error event."""
        run_id_str = str(run_id)
        span = self._spans.get(run_id_str)

        if span:
            span.set_status(Status(StatusCode.ERROR, str(error)))
            span.set_attribute('error.type', type(error).__name__)
            span.set_attribute('error.message', str(error))
            span.end()

            self._spans.pop(run_id_str, None)
            self._run_start_times.pop(run_id_str, None)

    def on_chain_start(
        self,
        serialized: Optional[Dict[str, Any]],
        inputs: Dict[str, Any],
        *,
        run_id: uuid.UUID,
        parent_run_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """Handle chain start event."""
        run_id_str = str(run_id)

        # Handle None serialized parameter (common with LCEL Runnables)
        chain_name = 'unknown'
        chain_type = 'unknown'
        logger.info('--- ON_CHAIN_START SERIALIZED %s\nserialized: %r', run_id, serialized)
        logger.info('--- ON_CHAIN_START TAGS %s\nmetadata: %r', run_id, tags)
        logger.info('--- ON_CHAIN_START METADATA %s\nmetadata: %r', run_id, metadata)
        logger.info('--- ON_CHAIN_START KWARGS %s\nkwargs: %r', run_id, kwargs)
        if serialized is not None:
            chain_name = serialized.get('name', 'unknown')
            chain_type = serialized.get('_type', 'unknown')
        else:
            if metadata is not None:
                langgraph_node = metadata.get('langgraph_node', None)
                # The node will be a StrEnum type: see our agent graph definitions.
                chain_name = str(langgraph_node)

        span_attributes = {
                'chain.name': chain_name,
                'chain.type': chain_type,
                'session.id': self.session_id,
                'user.id': self.user_id,
                'run.id': run_id_str,
            }
        if parent_run_id is not None:
            span_attributes['run.parent_id'] = str(parent_run_id)

        # Add metadata to span attributes
        if metadata:
            for key, value in metadata.items():
                span_attributes[f'meta.{key}'] = str(value)

        parent_span = self._spans.get(str(parent_run_id)) if parent_run_id else None
        parent_context = trace.set_span_in_context(parent_span) if parent_span else None

        span = self.tracer.start_span(
            name=f'chain.{chain_name}',
            attributes=span_attributes,
            context=parent_context,
        )
        logger.info('--- ON_CHAIN_START %s\nserialized: %r\nspan: %r\nmetadata: %r', run_id, serialized, span, metadata)

        # Add input information (limited)
        input_summary = {}
        if hasattr(inputs, 'items'):
            for key, value in inputs.items():
                if isinstance(value, str):
                    input_summary[key] = value[:100] + '...' if len(value) > 100 else value
                else:
                    input_summary[key] = str(value)[:100]
        else:
            if isinstance(inputs, str):
                input_summary = inputs[:100] + '...' if len(inputs) > 100 else inputs
            else:
                input_summary = str(inputs)[:100]

        span.set_attribute('chain.inputs', json.dumps(input_summary))

        # Add tags and metadata
        if tags:
            span.set_attribute('chain.tags', json.dumps(tags))
        if metadata:
            span.set_attribute('chain.metadata', json.dumps(metadata, default=str))

        self._spans[run_id_str] = span
        self._run_start_times[run_id_str] = time.time()

    def on_chain_end(
        self, outputs: Dict[str, Any], *, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None, **kwargs: Any
    ) -> Any:
        """Handle chain end event."""
        run_id_str = str(run_id)
        span = self._spans.get(run_id_str)
        start_time = self._run_start_times.get(run_id_str)

        logger.info('--- ON_CHAIN_END %s\nspan: %r', run_id, span)

        if not span:
            return

        try:
            duration = time.time() - start_time if start_time else 0

            # Add output information (limited)
            output_summary = {}
            if hasattr(outputs, 'items'):
                for key, value in outputs.items():
                    if isinstance(value, str):
                        output_summary[key] = value[:100] + '...' if len(value) > 100 else value
                    else:
                        output_summary[key] = str(value)[:100]
            else:
                if isinstance(outputs, str):
                    output_summary = outputs[:100] + '...' if len(outputs) > 100 else outputs
                else:
                    output_summary = str(outputs)[:100]

            span.set_attribute('chain.outputs', json.dumps(output_summary))
            span.set_attribute('chain.duration_seconds', duration)
            span.set_status(Status(StatusCode.OK))

        except Exception as ex:
            logger.warning('Error in on_chain_end', exc_info=ex)
            span.set_status(Status(StatusCode.ERROR, str(ex)))
        finally:
            span.end()
            self._spans.pop(run_id_str, None)
            self._run_start_times.pop(run_id_str, None)

    def on_chain_error(
        self, error: BaseException, *, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None, **kwargs: Any
    ) -> Any:
        """Handle chain error event."""
        run_id_str = str(run_id)
        span = self._spans.get(run_id_str)

        if span:
            span.set_status(Status(StatusCode.ERROR, str(error)))
            span.set_attribute('error.type', type(error).__name__)
            span.set_attribute('error.message', str(error))
            span.end()

            self._spans.pop(run_id_str, None)
            self._run_start_times.pop(run_id_str, None)

    def on_chat_model_start(
        self,
        serialized: Optional[Dict[str, Any]],
        messages: List[List[Any]],
        *,
        run_id: uuid.UUID,
        tags: Optional[List[str]] = None,
        parent_run_id: Optional[uuid.UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """Handle Chat Model start event."""
        run_id_str = str(run_id)
        
        # Handle None serialized parameter (common with LCEL Runnables)
        chat_model_name = 'unknown'
        chat_model_vendor = 'unknown'
        chat_model_model = 'unknown'
        
        if serialized is not None:
            chat_model_name = serialized.get('name', 'unknown')
            chat_model_vendor = serialized.get('_type', 'unknown')
            chat_model_model = serialized.get('model_name', 'unknown')
        
        span_name = f'chat_model.{chat_model_name}'
        span_attributes = {
                'chat_model.vendor': chat_model_vendor,
                'chat_model.model': chat_model_model,
                'session.id': self.session_id,
                'user.id': self.user_id,
                'run.id': run_id_str,
                'chat_model.messages.count': sum(len(m) for m in messages),
            }
        if parent_run_id is not None:
            span_attributes['run.parent_id'] = str(parent_run_id)

        parent_span = self._spans.get(str(parent_run_id)) if parent_run_id else None
        parent_context = trace.set_span_in_context(parent_span) if parent_span else None

        span = self.tracer.start_span(
            name=span_name,
            attributes=span_attributes,
            context=parent_context,
        )
        logger.info('--- ON_CHAT_MODEL_START %s\nserialized: %r\nspan: %r\nmetadata: %r', run_id, serialized, span, metadata)

        # Add message content (limit to first 3 messages)
        msg_idx = 0
        for message_list in messages[:3]:
            for msg in message_list[:3]:
                content = getattr(msg, 'content', str(msg))
                preview = content[:500] + '...' if isinstance(content, str) and len(content) > 500 else content
                span.set_attribute(f'chat_model.message.{msg_idx}', preview)
                msg_idx += 1

        # Add tags and metadata
        if tags:
            span.set_attribute('chat_model.tags', json.dumps(tags))
        if metadata:
            span.set_attribute('chat_model.metadata', json.dumps(metadata, default=str))

        self._spans[run_id_str] = span
        self._run_start_times[run_id_str] = time.time()



    def on_chat_model_end(
        self, response: LLMResult, *, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None, **kwargs: Any
    ) -> Any:
        """Handle Chat Model end event."""
        run_id_str = str(run_id)
        span = self._spans.get(run_id_str)
        logger.info('--- ON_CHAT_MODEL_END %s\nspan: %r', run_id, span)
        start_time = self._run_start_times.get(run_id_str)
        if not span:
            logger.warning(f'No span found for Chat Model run {run_id_str}')
            return
        try:
            duration = time.time() - start_time if start_time else 0
            # Token usage (if available)
            token_usage = response.llm_output.get('token_usage', {}) if response.llm_output else {}
            prompt_tokens = token_usage.get('prompt_tokens', 0)
            completion_tokens = token_usage.get('completion_tokens', 0)
            total_tokens = token_usage.get('total_tokens', 0)
            span.set_attribute('chat_model.usage.prompt_tokens', prompt_tokens)
            span.set_attribute('chat_model.usage.completion_tokens', completion_tokens)
            span.set_attribute('chat_model.usage.total_tokens', total_tokens)
            span.set_attribute('chat_model.response.generations_count', len(response.generations))
            span.set_attribute('chat_model.duration_seconds', duration)
            # Add response content (limited)
            for i, generation_list in enumerate(response.generations[:2]):
                for j, generation in enumerate(generation_list[:2]):
                    content = getattr(getattr(generation, 'message', generation), 'content', str(generation))
                    preview = content[:300] + '...' if isinstance(content, str) and len(content) > 300 else content
                    span.set_attribute(f'chat_model.response.{i}.{j}', preview)
            span.set_status(Status(StatusCode.OK))
        except Exception as ex:
            logger.warning('Error in on_chat_model_end', exc_info=ex)
            span.set_status(Status(StatusCode.ERROR, str(ex)))
        finally:
            span.end()
            self._spans.pop(run_id_str, None)
            self._run_start_times.pop(run_id_str, None)

    def on_agent_error(
        self, error: BaseException, *, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None, **kwargs: Any
    ) -> Any:
        """Handle agent error event."""
        run_id_str = str(run_id)
        span = self._spans.get(run_id_str)
        if span:
            span.set_status(Status(StatusCode.ERROR, str(error)))
            span.set_attribute('error.type', type(error).__name__)
            span.set_attribute('error.message', str(error))
            span.end()
            self._spans.pop(run_id_str, None)
            self._run_start_times.pop(run_id_str, None)
