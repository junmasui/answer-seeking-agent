from functools import cache
from typing import Any, Dict, Optional
import time


from opentelemetry import trace
from opentelemetry.trace import Status

from .custom_otel import get_meter, get_tracer

@cache
def get_span_tracker():
    # Initialize telemetry
    tracer = get_tracer()

    return SpanTracker(tracer)

class SpanTracker:
    """
    Tracks active OpenTelemetry spans and their start times.
    Encapsulates span creation and ending logic.
    """
    def __init__(self, tracer: trace.Tracer):
        self.tracer = tracer
        self._spans: Dict[str, trace.Span] = {}
        self._run_start_times: Dict[str, float] = {}

    def start_span(
        self,
        name: str,
        attributes: Dict[str, Any],
        run_id: str,
        parent_run_id: Optional[str] = None,
    ) -> trace.Span:
        """
        Create and store a new span for the given run_id.
        """
        parent_span = self._spans.get(parent_run_id) if parent_run_id else None
        parent_context = trace.set_span_in_context(parent_span) if parent_span else None
        span = self.tracer.start_span(
            name=name,
            attributes=attributes,
            context=parent_context,
        )
        self._spans[run_id] = span
        self._run_start_times[run_id] = time.time()
        return span

    def get_span(self, run_id: str) -> Optional[trace.Span]:
        return self._spans.get(run_id)

    def get_start_time(self, run_id: str) -> Optional[float]:
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
        Returns the duration in seconds if available.
        """
        span = self._spans.get(run_id)
        start_time = self._run_start_times.get(run_id)
        duration = time.time() - start_time if start_time else None
        if span:
            if extra_attributes:
                for k, v in extra_attributes.items():
                    span.set_attribute(k, v)
            if status:
                span.set_status(status)
            if error:
                span.set_attribute('error.type', type(error).__name__)
                span.set_attribute('error.message', str(error))
            if duration is not None:
                span.set_attribute('duration_seconds', duration)
            span.end()
            self._spans.pop(run_id, None)
            self._run_start_times.pop(run_id, None)
        return duration
