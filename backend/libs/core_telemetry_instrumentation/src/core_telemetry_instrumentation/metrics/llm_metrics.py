"""
LLM-specific metrics collection utilities.

This module provides specialized metrics for tracking LLM operations,
including token usage, costs, quality metrics, and performance indicators.
"""

import logging
import time
from contextlib import contextmanager
from typing import Optional

from opentelemetry.metrics import get_meter

logger = logging.getLogger(__name__)


class LLMMetrics:
    """
    Centralized metrics collection for LLM operations.

    This class provides high-level metrics collection methods for common
    LLM operations, making it easy to track performance and usage across
    different parts of the application.
    """

    def __init__(self):
        """Initialize LLM metrics with OpenTelemetry meter."""
        self.meter = get_meter(__name__)
        self._init_metrics()

    def _init_metrics(self):
        """Initialize all LLM-related metrics."""
        # Token usage metrics
        self.token_counter = self.meter.create_counter(
            name='llm_tokens_processed_total', description='Total number of tokens processed by LLMs', unit='1'
        )

        # Cost tracking
        self.cost_counter = self.meter.create_counter(
            name='llm_cost_usd_total', description='Total cost of LLM operations in USD', unit='USD'
        )

        # Performance metrics
        self.latency_histogram = self.meter.create_histogram(
            name='llm_request_latency_seconds', description='Latency of LLM requests', unit='s'
        )

        # Quality metrics
        self.response_length_histogram = self.meter.create_histogram(
            name='llm_response_length_chars', description='Length of LLM responses in characters', unit='1'
        )

        # Error tracking
        self.error_counter = self.meter.create_counter(
            name='llm_errors_total', description='Total number of LLM errors', unit='1'
        )

        # Document processing metrics
        self.document_processing_counter = self.meter.create_counter(
            name='document_processing_total', description='Total number of documents processed', unit='1'
        )

        self.document_processing_duration = self.meter.create_histogram(
            name='document_processing_duration_seconds', description='Time taken to process documents', unit='s'
        )

        # Vector store metrics
        self.vector_operations_counter = self.meter.create_counter(
            name='vector_store_operations_total', description='Total number of vector store operations', unit='1'
        )

        self.vector_search_duration = self.meter.create_histogram(
            name='vector_search_duration_seconds', description='Time taken for vector searches', unit='s'
        )

    def record_token_usage(
        self, prompt_tokens: int, completion_tokens: int, model: str, provider: str, session_id: Optional[str] = None
    ):
        """
        Record token usage for an LLM operation.

        Args:
            prompt_tokens: Number of tokens in the prompt
            completion_tokens: Number of tokens in the completion
            model: Model name (e.g., "gpt-4", "claude-3")
            provider: Provider name (e.g., "openai", "anthropic")
            session_id: Optional session identifier

        """
        attributes = {'model': model, 'provider': provider, 'session_id': session_id or 'unknown'}

        if prompt_tokens > 0:
            self.token_counter.add(prompt_tokens, {**attributes, 'token_type': 'prompt'})

        if completion_tokens > 0:
            self.token_counter.add(completion_tokens, {**attributes, 'token_type': 'completion'})

    def record_cost(
        self,
        cost_usd: float,
        model: str,
        provider: str,
        operation_type: str = 'inference',
        session_id: Optional[str] = None,
    ):
        """
        Record the cost of an LLM operation.

        Args:
            cost_usd: Cost in USD
            model: Model name
            provider: Provider name
            operation_type: Type of operation (inference, fine-tuning, etc.)
            session_id: Optional session identifier

        """
        self.cost_counter.add(
            cost_usd,
            attributes={
                'model': model,
                'provider': provider,
                'operation_type': operation_type,
                'session_id': session_id or 'unknown',
            },
        )

    def record_latency(
        self,
        duration_seconds: float,
        model: str,
        provider: str,
        operation_type: str = 'inference',
        session_id: Optional[str] = None,
    ):
        """
        Record the latency of an LLM operation.

        Args:
            duration_seconds: Duration in seconds
            model: Model name
            provider: Provider name
            operation_type: Type of operation
            session_id: Optional session identifier

        """
        self.latency_histogram.record(
            duration_seconds,
            attributes={
                'model': model,
                'provider': provider,
                'operation_type': operation_type,
                'session_id': session_id or 'unknown',
            },
        )

    def record_response_quality(
        self,
        response_length: int,
        model: str,
        provider: str,
        quality_score: Optional[float] = None,
        session_id: Optional[str] = None,
    ):
        """
        Record response quality metrics.

        Args:
            response_length: Length of response in characters
            model: Model name
            provider: Provider name
            quality_score: Optional quality score (0.0-1.0)
            session_id: Optional session identifier

        """
        attributes = {'model': model, 'provider': provider, 'session_id': session_id or 'unknown'}

        self.response_length_histogram.record(response_length, attributes=attributes)

        if quality_score is not None:
            # Create quality metric if it doesn't exist
            if not hasattr(self, 'quality_histogram'):
                self.quality_histogram = self.meter.create_histogram(
                    name='llm_response_quality_score', description='Quality score of LLM responses (0.0-1.0)', unit='1'
                )

            self.quality_histogram.record(quality_score, attributes=attributes)

    def record_error(
        self,
        error_type: str,
        model: str,
        provider: str,
        error_message: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """
        Record an LLM error.

        Args:
            error_type: Type of error (e.g., "timeout", "rate_limit", "auth")
            model: Model name
            provider: Provider name
            error_message: Optional error message
            session_id: Optional session identifier

        """
        attributes = {
            'error_type': error_type,
            'model': model,
            'provider': provider,
            'session_id': session_id or 'unknown',
        }

        if error_message:
            attributes['error_message'] = error_message[:100]  # Limit length

        self.error_counter.add(1, attributes=attributes)

    def record_document_processing(
        self,
        document_count: int,
        document_type: str,
        processing_duration: float,
        success: bool = True,
        session_id: Optional[str] = None,
    ):
        """
        Record document processing metrics.

        Args:
            document_count: Number of documents processed
            document_type: Type of documents (pdf, html, txt, etc.)
            processing_duration: Duration in seconds
            success: Whether processing was successful
            session_id: Optional session identifier

        """
        attributes = {
            'document_type': document_type,
            'success': str(success).lower(),
            'session_id': session_id or 'unknown',
        }

        self.document_processing_counter.add(document_count, attributes=attributes)
        self.document_processing_duration.record(processing_duration, attributes=attributes)

    def record_vector_operation(
        self,
        operation: str,
        vector_count: int,
        duration: float,
        success: bool = True,
        vector_store_type: str = 'unknown',
    ):
        """
        Record vector store operation metrics.

        Args:
            operation: Type of operation (add, search, delete, etc.)
            vector_count: Number of vectors involved
            duration: Duration in seconds
            success: Whether operation was successful
            vector_store_type: Type of vector store (weaviate, pinecone, etc.)

        """
        attributes = {'operation': operation, 'vector_store_type': vector_store_type, 'success': str(success).lower()}

        self.vector_operations_counter.add(vector_count, attributes=attributes)

        if operation == 'search':
            self.vector_search_duration.record(duration, attributes=attributes)

    @contextmanager
    def track_operation(self, operation_name: str, model: str, provider: str, session_id: Optional[str] = None):
        """
        Context manager for tracking an LLM operation.

        Usage:
            with metrics.track_operation("chat_completion", "gpt-4", "openai") as tracker:
                result = llm.invoke(prompt)
                tracker.record_tokens(100, 50)
                tracker.record_cost(0.002)

        Args:
            operation_name: Name of the operation
            model: Model name
            provider: Provider name
            session_id: Optional session identifier

        """
        start_time = time.time()

        class OperationTracker:
            def __init__(self, metrics_instance):
                self.metrics = metrics_instance
                self.model = model
                self.provider = provider
                self.session_id = session_id
                self.start_time = start_time

            def record_tokens(self, prompt_tokens: int, completion_tokens: int):
                self.metrics.record_token_usage(
                    prompt_tokens, completion_tokens, self.model, self.provider, self.session_id
                )

            def record_cost(self, cost_usd: float):
                self.metrics.record_cost(cost_usd, self.model, self.provider, operation_name, self.session_id)

            def record_error(self, error_type: str, error_message: Optional[str] = None):
                self.metrics.record_error(error_type, self.model, self.provider, error_message, self.session_id)

        tracker = OperationTracker(self)

        try:
            yield tracker
        except Exception as e:
            tracker.record_error(type(e).__name__, str(e))
            raise
        finally:
            duration = time.time() - start_time
            self.record_latency(duration, model, provider, operation_name, session_id)


# Global metrics instance
_llm_metrics = None


def get_llm_metrics() -> LLMMetrics:
    """Get the global LLM metrics instance."""
    global _llm_metrics
    if _llm_metrics is None:
        _llm_metrics = LLMMetrics()
    return _llm_metrics
