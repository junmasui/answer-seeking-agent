"""
Instrumentation utilities for the ingestion pipeline.

This module provides OpenTelemetry instrumentation for document ingestion,
processing, and vector store operations.
"""

import logging
import time
from contextlib import contextmanager
from typing import Optional
from uuid import UUID

from opentelemetry.trace import Status, StatusCode

from .tracing import get_tracer
from .llm_metrics import get_llm_metrics

logger = logging.getLogger(__name__)


class IngestionInstrumentation:
    """
    Instrumentation for document ingestion operations.

    This class provides methods to instrument the ingestion pipeline,
    including document loading, processing, and vector storage.
    """

    def __init__(self):
        """Initialize ingestion instrumentation."""
        self.tracer = get_tracer()
        self.metrics = get_llm_metrics()

    @contextmanager
    def trace_document_ingestion(self, document_id: UUID, document_set_id: UUID, source_url: str, content_type: str):
        """
        Trace a complete document ingestion operation.

        Args:
            document_id: Unique document identifier
            document_set_id: Document set identifier
            source_url: Source URL of the document
            content_type: MIME type of the document

        """
        with self.tracer.start_as_current_span(
            'ingestion.document',
            attributes={
                'document.id': str(document_id),
                'document.set_id': str(document_set_id),
                'document.source_url': source_url,
                'document.content_type': content_type,
            },
        ) as span:
            start_time = time.time()

            class IngestionTracker:
                def __init__(self, span, metrics, tracer):
                    self.span = span
                    self.metrics = metrics
                    self.tracer = tracer
                    self.start_time = start_time
                    self.chunk_count = 0
                    self.vector_count = 0

                def record_download(self, file_size_bytes: int, download_duration: float):
                    """Record file download metrics."""
                    self.span.set_attribute('document.size_bytes', file_size_bytes)
                    self.span.set_attribute('ingestion.download_duration_seconds', download_duration)

                def record_processing(self, chunk_count: int, processing_duration: float):
                    """Record document processing metrics."""
                    self.chunk_count = chunk_count
                    self.span.set_attribute('document.chunks_generated', chunk_count)
                    self.span.set_attribute('ingestion.processing_duration_seconds', processing_duration)

                def record_vectorization(self, vector_count: int, vectorization_duration: float):
                    """Record vectorization metrics."""
                    self.vector_count = vector_count
                    self.span.set_attribute('document.vectors_generated', vector_count)
                    self.span.set_attribute('ingestion.vectorization_duration_seconds', vectorization_duration)

                def record_storage(self, storage_duration: float, success: bool = True):
                    """Record vector storage metrics."""
                    self.span.set_attribute('ingestion.storage_duration_seconds', storage_duration)
                    self.span.set_attribute('ingestion.storage_success', success)

                def record_error(self, error: Exception):
                    """Record an ingestion error."""
                    self.span.set_status(Status(StatusCode.ERROR, str(error)))
                    self.span.set_attribute('error.type', type(error).__name__)
                    self.span.set_attribute('error.message', str(error))

                def finalize(self, success: bool = True):
                    """Finalize the ingestion tracking."""
                    total_duration = time.time() - self.start_time
                    self.span.set_attribute('ingestion.total_duration_seconds', total_duration)
                    self.span.set_attribute('ingestion.success', success)

                    # Record metrics
                    self.metrics.record_document_processing(
                        document_count=1,
                        document_type=content_type.split('/')[-1] if content_type else 'unknown',
                        processing_duration=total_duration,
                        success=success,
                    )

                    if self.vector_count > 0:
                        self.metrics.record_vector_operation(
                            operation='add', vector_count=self.vector_count, duration=total_duration, success=success
                        )

                    if success:
                        self.span.set_status(Status(StatusCode.OK))

            tracker = IngestionTracker(span, self.metrics, self.tracer)

            try:
                yield tracker
                tracker.finalize(success=True)
            except Exception as e:
                tracker.record_error(e)
                tracker.finalize(success=False)
                raise

    @contextmanager
    def trace_document_loading(self, file_path: str, strategy: str = 'fast'):
        """
        Trace document loading operation.

        Args:
            file_path: Path to the document file
            strategy: Loading strategy (fast, accurate, etc.)

        """
        with self.tracer.start_as_current_span(
            'ingestion.document_loading',
            attributes={'document.file_path': str(file_path), 'document.loading_strategy': strategy},
        ) as span:
            start_time = time.time()

            class LoadingTracker:
                def __init__(self, span):
                    self.span = span
                    self.start_time = start_time
                    self.chunks_loaded = 0

                def record_chunk(self):
                    """Record a loaded chunk."""
                    self.chunks_loaded += 1

                def finalize(self, success: bool = True):
                    """Finalize loading tracking."""
                    duration = time.time() - self.start_time
                    self.span.set_attribute('document.chunks_loaded', self.chunks_loaded)
                    self.span.set_attribute('ingestion.loading_duration_seconds', duration)
                    self.span.set_attribute('ingestion.loading_success', success)

                    if success:
                        self.span.set_status(Status(StatusCode.OK))
                    else:
                        self.span.set_status(Status(StatusCode.ERROR))

            tracker = LoadingTracker(span)

            try:
                yield tracker
                tracker.finalize(success=True)
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute('error.type', type(e).__name__)
                span.set_attribute('error.message', str(e))
                tracker.finalize(success=False)
                raise

    @contextmanager
    def trace_vector_store_operation(
        self, operation: str, collection_name: Optional[str] = None, vector_count: Optional[int] = None
    ):
        """
        Trace vector store operations.

        Args:
            operation: Type of operation (add, search, delete, etc.)
            collection_name: Name of the vector collection
            vector_count: Number of vectors involved

        """
        with self.tracer.start_as_current_span(
            f'vector_store.{operation}',
            attributes={
                'vector_store.operation': operation,
                'vector_store.collection': collection_name or 'unknown',
                'vector_store.vector_count': vector_count or 0,
            },
        ) as span:
            start_time = time.time()

            class VectorStoreTracker:
                def __init__(self, span, metrics):
                    self.span = span
                    self.metrics = metrics
                    self.start_time = start_time

                def record_result(self, result_count: int, success: bool = True):
                    """Record operation results."""
                    self.span.set_attribute('vector_store.result_count', result_count)
                    self.span.set_attribute('vector_store.success', success)

                def finalize(self, success: bool = True):
                    """Finalize vector store operation tracking."""
                    duration = time.time() - self.start_time
                    self.span.set_attribute('vector_store.duration_seconds', duration)

                    # Record metrics
                    self.metrics.record_vector_operation(
                        operation=operation, vector_count=vector_count or 0, duration=duration, success=success
                    )

                    if success:
                        self.span.set_status(Status(StatusCode.OK))
                    else:
                        self.span.set_status(Status(StatusCode.ERROR))

            tracker = VectorStoreTracker(span, self.metrics)

            try:
                yield tracker
                tracker.finalize(success=True)
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute('error.type', type(e).__name__)
                span.set_attribute('error.message', str(e))
                tracker.finalize(success=False)
                raise

    def trace_celery_task(self, task_name: str, task_id: str, **kwargs):
        """
        Create a span for a Celery task.

        Args:
            task_name: Name of the Celery task
            task_id: Unique task identifier
            **kwargs: Additional task attributes

        """
        attributes = {'celery.task_name': task_name, 'celery.task_id': task_id}
        attributes.update(kwargs)

        return self.tracer.start_as_current_span(f'celery.{task_name}', attributes=attributes)

    def record_s3_operation(
        self,
        operation: str,
        bucket: str,
        key: str,
        size_bytes: Optional[int] = None,
        duration: Optional[float] = None,
        success: bool = True,
    ):
        """
        Record S3 operation metrics.

        Args:
            operation: Type of operation (upload, download, delete, etc.)
            bucket: S3 bucket name
            key: S3 object key
            size_bytes: Size of the object in bytes
            duration: Operation duration in seconds
            success: Whether the operation was successful

        """
        with self.tracer.start_as_current_span(
            f's3.{operation}',
            attributes={
                's3.operation': operation,
                's3.bucket': bucket,
                's3.key': key[:100],  # Limit key length
                's3.size_bytes': size_bytes,
                's3.duration_seconds': duration,
                's3.success': success,
            },
        ) as span:
            if success:
                span.set_status(Status(StatusCode.OK))
            else:
                span.set_status(Status(StatusCode.ERROR))


# Global instrumentation instance
_ingestion_instrumentation = None


def get_ingestion_instrumentation() -> IngestionInstrumentation:
    """Get the global ingestion instrumentation instance."""
    global _ingestion_instrumentation
    if _ingestion_instrumentation is None:
        _ingestion_instrumentation = IngestionInstrumentation()
    return _ingestion_instrumentation
