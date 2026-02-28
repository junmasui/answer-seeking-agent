
import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from langchain_core.outputs import ChatGeneration, Generation, LLMResult
from mlflow.langchain.langchain_tracer import MlflowLangchainTracer
from opentelemetry.metrics import get_meter

from .span_tracker import get_span_tracker

logger = logging.getLogger(__name__)

class CustomMlflowLangchainTracer(MlflowLangchainTracer):
    """
    Custom MLFlow Tracer that also records Prometheus metrics.
    Inherits from MlflowLangchainTracer to get all the standard tracing behavior,
    but adds metric recording hooks.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.meter = get_meter(__name__)
        self._init_metrics()
        # We still need SpanTracker? MLFlow handles spans now.
        # But we might need it if other parts of the system rely on it.
        # For now, let's assume we don't need SpanTracker for *new* spans,
        # but we might need to read from it if legacy code exists.
        # Actually, MLflow tracer manages its own spans.

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
        # Call parent to start the span
        super().on_llm_start(
            serialized, prompts, run_id=run_id, parent_run_id=parent_run_id, tags=tags, metadata=metadata, **kwargs
        )

        # Record start metric
        llm_model = 'unknown'
        llm_vendor = 'unknown'
        if serialized:
            llm_model = serialized.get('model_name', 'unknown')
            llm_vendor = serialized.get('_type', 'unknown')

        # We need to extract session_id from metadata or tags if available
        session_id = 'unknown'
        if metadata:
            session_id = metadata.get('session_id', 'unknown')

        self.llm_request_counter.add(
            1, attributes={'model': llm_model, 'vendor': llm_vendor, 'session_id': session_id}
        )

    def on_llm_end(
        self, response: LLMResult, *, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None, **kwargs: Any
    ) -> Any:
        """Handle LLM end event."""
        # Call parent to end the span
        super().on_llm_end(response, run_id=run_id, parent_run_id=parent_run_id, **kwargs)

        # Record metrics
        try:
            # We don't have easy access to the start time here unless we track it ourselves,
            # or rely on the parent's internal state.
            # MLFlow's _run_span_mapping might have it, but it's internal.
            # For simplicity, we might skip duration if it's hard to get, or use a separate tracker.
            # However, `response.llm_output` might have execution info?
            
            token_usage = response.llm_output.get('token_usage', {}) if response.llm_output else {}
            prompt_tokens = token_usage.get('prompt_tokens', 0)
            completion_tokens = token_usage.get('completion_tokens', 0)
            
            # Helper to get session_id? It's not passed to on_llm_end.
            # We might need to store it in `_run_span_mapping` or similar if we were implementing from scratch.
            # But since we are subclassing, we might not have easy access to the attributes set in start.
            
            # This is a limitation of the "Combined Tracer" approach if the parent class doesn't expose state.
            # Let's inspect `self._run_span_mapping` (which we saw in the source code earlier).
            
            span_with_token = self._run_span_mapping.get(str(run_id))
            if span_with_token and span_with_token.span:
                # We can get attributes from the span!
                 attributes = span_with_token.span.attributes or {}
                 # But standard OTel span attributes might not be directly accessible as a dict depending on implementation.
                 # Assuming it is a ReadableSpan or similar.
                 pass

            # For now, let's record what we can (Tokens)
            attributes = {
                 # We'd need to reconstruct these or rely on what's available
            }
            
            # If we really need robust metrics matching the old handler, 
            # we might need to duplicate some state tracking.
            
            if prompt_tokens > 0:
                self.llm_token_usage.add(prompt_tokens, {'token_type': 'prompt'})
            if completion_tokens > 0:
                self.llm_token_usage.add(completion_tokens, {'token_type': 'completion'})

        except Exception as e:
            logger.warning(f"Failed to record metrics in on_llm_end: {e}")

    def on_retriever_start(self, serialized: Optional[Dict[str, Any]], query: str, *, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None, tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Any:
        super().on_retriever_start(serialized, query, run_id=run_id, parent_run_id=parent_run_id, tags=tags, metadata=metadata, **kwargs)
        
        retriever_type = serialized.get('_type', 'unknown') if serialized else 'unknown'
        session_id = metadata.get('session_id', 'unknown') if metadata else 'unknown'
        
        self.retrieval_counter.add(1, attributes={'session_id': session_id, 'retriever_type': retriever_type})

