"""
Span tracking utilities for OpenTelemetry instrumentation.

This module provides the SpanTracker class, which manages the creation, retrieval, and
completion of OpenTelemetry spans. It supports context propagation and error/status handling
for distributed tracing. Use get_span_tracker() to obtain a singleton instance for span
management.
"""

import logging
import time
from functools import cache
from typing import Any, Dict, Optional

from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.trace import Status, get_tracer, set_span_in_context

logger = logging.getLogger(__name__)


@cache
def get_span_tracker():
    """
    Return a cached instance of SpanTracker initialized with the current tracer.

    Returns:
        SpanTracker: A singleton SpanTracker instance.

    """
    tracer = get_tracer(__name__)
    return SpanTracker(tracer)


class SpanTracker:
    """
    Tracks and manages OpenTelemetry spans for distributed tracing.

    This class encapsulates logic for creating, retrieving, and ending spans,
    including context propagation, status, and error handling. It maintains
    internal mappings for active spans, their start times, and explicit Context
    objects. Context is passed explicitly (not via attach/detach) to ensure
    async safety across concurrent tasks.
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
        self._contexts: Dict[str, Context] = {}

    def start_span(
        self, name: str, attributes: Dict[str, Any], run_id: str, parent_run_id: Optional[str] = None
    ) -> trace.Span:
        """
        Create and store a new span for the given run_id.

        Starts a new OpenTelemetry span, optionally as a child of a parent span, and stores
        an explicit Context for child span propagation. Does not attach to the global context,
        making it safe for concurrent async usage.

        Args:
            name (str): The name of the span.
            attributes (Dict[str, Any]): Attributes to associate with the span.
            run_id (str): Unique identifier for the span/run.
            parent_run_id (Optional[str]): Optional run_id of the parent span.

        Returns:
            trace.Span: The created OpenTelemetry span object.

        """
        # Look up the stored parent context (if any) to maintain trace hierarchy
        parent_context = self._contexts.get(parent_run_id) if parent_run_id else None

        # Start a new span using the tracer, with optional parent context and custom attributes
        span = self.tracer.start_span(name=name, attributes=attributes, context=parent_context)
        self._spans[run_id] = span
        self._run_start_times[run_id] = time.time()

        # Store an explicit Context carrying this span so child spans can reference it.
        # This avoids attach/detach which is unsafe across async boundaries.
        self._contexts[run_id] = set_span_in_context(span, parent_context)

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
            Optional[float]: The timestamp (in seconds since epoch) when the span was
                started, or None if not found.

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

        Sets additional attributes, status, and error information on the span before ending it.
        Removes the span and its stored context from internal tracking.

        Args:
            run_id (str): Unique identifier for the span/run.
            status (Optional[Status]): Optional status to set on the span (e.g., OK, ERROR).
            error (Optional[BaseException]): Optional error to record on the span.
            extra_attributes (Optional[Dict[str, Any]]): Optional extra attributes to set on the
                span.

        Returns:
            Optional[float]: The duration of the span in seconds, or None if start time is not
                available.

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

            self._spans.pop(run_id, None)
            self._run_start_times.pop(run_id, None)
            self._contexts.pop(run_id, None)
        return duration
