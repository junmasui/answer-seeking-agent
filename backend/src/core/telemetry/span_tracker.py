from functools import cache
from typing import Any, Dict, Optional
import time


from opentelemetry import context as context_api
from opentelemetry import trace
from opentelemetry.trace import Status
from opentelemetry.trace.propagation import (
    _SPAN_KEY,  # Internal key used by OpenTelemetry to store the current span in the context
    get_current_span,
    set_span_in_context,
)

from .custom_otel import get_meter, get_tracer

@cache
def get_span_tracker():
    # Initialize telemetry
    tracer = get_tracer()

    return SpanTracker(tracer)

class SpanTracker:
    """
    Tracks active OpenTelemetry spans and their start times.
    Encapsulates span creation and ending logic for distributed tracing.
    Provides methods to start, retrieve, and end spans, as well as manage their context propagation.
    """
    def __init__(self, tracer: trace.Tracer):
        """
        Initialize a SpanTracker instance.

        Args:
            tracer (trace.Tracer): The OpenTelemetry tracer used to create spans.
        """
        self.tracer = tracer
        self._spans: Dict[str, trace.Span] = {}
        self._run_start_times: Dict[str, float] = {}
        self._tokens: Dict[str, trace.Span] = {}


    def start_span(
        self,
        name: str,
        attributes: Dict[str, Any],
        run_id: str,
        parent_run_id: Optional[str] = None,
    ) -> trace.Span:
        """
        Create and store a new span for the given run_id.

        Starts a new OpenTelemetry span, optionally as a child of a parent span, and attaches it to the current context for propagation.
        Stores the span and its start time for later reference.

        Args:
            name (str): The name of the span.
            attributes (Dict[str, Any]): Attributes to associate with the span.
            run_id (str): Unique identifier for the span/run.
            parent_run_id (Optional[str]): Optional run_id of the parent span.

        Returns:
            trace.Span: The created OpenTelemetry span object.
        """
        # Retrieve parent span if available, to maintain trace hierarchy
        parent_span = self._spans.get(parent_run_id) if parent_run_id else None
        # Set parent context for child span propagation
        parent_context = trace.set_span_in_context(parent_span) if parent_span else None
        # Start a new span using the tracer, with optional parent context and custom attributes
        span = self.tracer.start_span(
            name=name,
            attributes=attributes,
            context=parent_context,
        )
        self._spans[run_id] = span
        self._run_start_times[run_id] = time.time()

        # Attach the span to the OpenTelemetry context, so it becomes the current active span
        # This is necessary for context propagation across async boundaries and threads
        # _SPAN_KEY is the internal key used by OpenTelemetry to store the current span in the context object
        token = context_api.attach(context_api.set_value(trace.propagation._SPAN_KEY, span))
        self._tokens[run_id] = token

        return span
    
    def get_span(self, run_id: str) -> Optional[trace.Span]:
        """
        Retrieve the span object for a given run_id.

        Args:
            run_id (str): Unique identifier for the span/run.

        Returns:
            Optional[trace.Span]: The OpenTelemetry span object, or None if not found.
        """
        return self._spans.get(run_id)

    def get_start_time(self, run_id: str) -> Optional[float]:
        """
        Retrieve the start time for a given run_id.

        Args:
            run_id (str): Unique identifier for the span/run.

        Returns:
            Optional[float]: The timestamp (in seconds since epoch) when the span was started, or None if not found.
        """
        return self._run_start_times.get(run_id)

    def end_span(
        self,
        run_id: str,
        status: Optional[Status] = None,
        error: Optional[BaseException] = None,
        extra_attributes: Optional[Dict[str, Any]] = None,
    ) -> Optional[float]:
        """
        End the span for the given run_id, set status and error attributes, and remove tracking.

        Sets additional attributes, status, and error information on the span before ending it. Detaches the span from the context to clean up propagation state.

        Args:
            run_id (str): Unique identifier for the span/run.
            status (Optional[Status]): Optional status to set on the span (e.g., OK, ERROR).
            error (Optional[BaseException]): Optional error to record on the span.
            extra_attributes (Optional[Dict[str, Any]]): Optional extra attributes to set on the span.

        Returns:
            Optional[float]: The duration of the span in seconds, or None if start time is not available.
        """
        span = self._spans.get(run_id)
        start_time = self._run_start_times.get(run_id)
        duration = time.time() - start_time if start_time else None
        if span:
            # Add any extra attributes to the span for richer telemetry
            if extra_attributes:
                for k, v in extra_attributes.items():
                    span.set_attribute(k, v)
            # Set the status of the span (OK, ERROR, etc.) for trace analysis
            if status:
                span.set_status(status)
            # Record error details in the span for observability
            if error:
                span.set_attribute('error.type', type(error).__name__)
                span.set_attribute('error.message', str(error))
            # Record the duration of the span for performance monitoring
            if duration is not None:
                span.set_attribute('duration_seconds', duration)
            # End the span to signal completion to OpenTelemetry
            span.end()
            span = self._spans.pop(run_id, None)
            self._run_start_times.pop(run_id, None)

            # Detach the span from the OpenTelemetry context to clean up context propagation
            token = self._tokens.pop(run_id, None)
            context_api.detach(token)
        return duration
