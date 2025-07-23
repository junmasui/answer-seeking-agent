from .agent import get_mermaid_graph, seek_answer
from .db_models import event_handlers
from .doc_mgr import (
    delete_document,
    get_document_set_statistics,
    get_document_statistics,
    list_document_sets,
    list_documents,
    merge_chunked_document,
    update_document,
    update_document_set,
    update_document_status,
    upload_chunk,
    upload_document,
)
from .health import health_check, status_check
from .ingest import ingest_documents, reset_worker_data

# Explicitly define the exported names: these names are the contract of this module.
__all__ = [
    'get_mermaid_graph',
    'seek_answer',
    'event_handlers',
    'delete_document',
    'get_document_set_statistics',
    'get_document_statistics',
    'health_check',
    'list_document_sets',
    'list_documents',
    'merge_chunked_document',
    'update_document',
    'update_document_set',
    'update_document_status',
    'upload_chunk',
    'upload_document',
    'ingest_documents',
    'reset_worker_data',
    'status_check',
]


def init_telemetry():
    from .lib_config import get_lib_config

    config = get_lib_config()
    # OpenTelemetry/OpenLLMetry handler (new implementation)
    if config.enable_opentelemetry:
        from core.telemetry import initialize_telemetry

        # Initialize telemetry (will choose best available method)
        initialize_telemetry(
            method='custom',  # Will prefer OpenLLMetry if available
            disable_batch=True,  # For immediate traces in development
            service_name=config.otel_service_name,
            environment=config.otel_environment,
            trace_sample_rate=config.otel_trace_sample_rate,
            otel_jaeger_endpoint=config.otel_jaeger_endpoint,
        )

