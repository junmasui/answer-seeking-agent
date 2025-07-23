"""
OpenLLMetry integration for the application.

This module provides integration with OpenLLMetry (Traceloop's LLM observability framework)
which is built on top of OpenTelemetry and provides automatic instrumentation for
LLM applications including LangChain, vector stores, and LLM providers.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Global initialization flag
_openllmetry_initialized = False


def initialize_openllmetry(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    disable_batch: bool = False,
    app_name: str = 'answers-agent',
    telemetry_enabled: bool = False,
    endpoint: Optional[str] = None,
    **kwargs,
):
    """
    Initialize OpenLLMetry (Traceloop SDK) for automatic LLM observability.

    This function sets up OpenLLMetry which automatically instruments:
    - LangChain/LangGraph operations
    - LLM provider calls (OpenAI, Anthropic, etc.)
    - Vector store operations (Weaviate, Pinecone, etc.)
    - General OpenTelemetry instrumentations

    Args:
        api_key: Traceloop API key (can also be set via TRACELOOP_API_KEY env var)
        base_url: Traceloop base URL (can also be set via TRACELOOP_BASE_URL env var)
        disable_batch: Whether to disable batch sending for immediate traces
        app_name: Application name for resource identification
        telemetry_enabled: Whether to enable Traceloop's own telemetry
        endpoint: The OTLP endpoint for sending traces.
        **kwargs: Additional configuration options for Traceloop.init()

    """
    global _openllmetry_initialized

    if _openllmetry_initialized:
        logger.debug('OpenLLMetry already initialized')
        return

    try:
        from traceloop.sdk import Traceloop

        # Set environment variables if provided
        if api_key:
            os.environ['TRACELOOP_API_KEY'] = api_key
        if base_url:
            os.environ['TRACELOOP_BASE_URL'] = base_url
        if endpoint:
            os.environ['OTEL_EXPORTER_OTLP_TRACES_ENDPOINT'] = endpoint
            # When using a local OTLP endpoint like Jaeger, TRACELOOP_API_KEY should not be set.
            # The SDK will then use an insecure connection by default.
            if 'TRACELOOP_API_KEY' in os.environ:
                del os.environ['TRACELOOP_API_KEY']

        def temp_callback(span):
            logger.info('--- SPAN: %r', span)

        # Initialize Traceloop with configuration
        init_kwargs = {
            'app_name': app_name,
            'api_endpoint': None,
            'disable_batch': disable_batch,
            'telemetry_enabled': telemetry_enabled,
            'span_postprocess_callback': temp_callback,
            **kwargs,
        }

        # Remove None values to use defaults
        init_kwargs = {k: v for k, v in init_kwargs.items() if v is not None}

        Traceloop.init(**init_kwargs)

        _openllmetry_initialized = True
        logger.info(f"OpenLLMetry initialized successfully with app_name='{app_name}'")

    except ImportError as e:
        logger.error('OpenLLMetry (traceloop-sdk) not installed. Install it with: pip install traceloop-sdk', exc_info=e)
        raise e
    except Exception as e:
        logger.error('Failed to initialize OpenLLMetry:', exc_info=e)
        raise e


def get_openllmetry_config():
    """
    Get OpenLLMetry configuration from environment variables.

    Returns:
        dict: Configuration dictionary with OpenLLMetry settings

    """
    return {
        'api_key': os.getenv('TRACELOOP_API_KEY'),
        'base_url': os.getenv('TRACELOOP_BASE_URL'),
        'disable_batch': os.getenv('TRACELOOP_DISABLE_BATCH', 'false').lower() == 'true',
        'app_name': os.getenv('TRACELOOP_APP_NAME', 'answers-agent'),
        'telemetry_enabled': os.getenv('TRACELOOP_TELEMETRY', 'false').lower() == 'true',
    }


def is_openllmetry_available() -> bool:
    """
    Check if OpenLLMetry (traceloop-sdk) is available.

    Returns:
        bool: True if OpenLLMetry is available, False otherwise

    """
    try:
        import traceloop.sdk

        return True
    except ImportError:
        return False


def is_openllmetry_initialized() -> bool:
    """
    Check if OpenLLMetry has been initialized.

    Returns:
        bool: True if OpenLLMetry is initialized, False otherwise

    """
    return _openllmetry_initialized


def annotate_workflow(name: str):
    """
    Decorator to annotate workflows for better tracing.

    This is a wrapper around OpenLLMetry's @workflow decorator that provides
    a fallback if OpenLLMetry is not available.

    Args:
        name: Name of the workflow

    Returns:
        Decorator function

    """

    def decorator(func):
        if is_openllmetry_available():
            try:
                from traceloop.sdk.decorators import workflow

                return workflow(name=name)(func)
            except ImportError:
                logger.warning('OpenLLMetry decorators not available')
                return func
        else:
            logger.debug(f"OpenLLMetry not available, skipping workflow annotation for '{name}'")
            return func

    return decorator


def annotate_task(name: str):
    """
    Decorator to annotate tasks for better tracing.

    This is a wrapper around OpenLLMetry's @task decorator that provides
    a fallback if OpenLLMetry is not available.

    Args:
        name: Name of the task

    Returns:
        Decorator function

    """

    def decorator(func):
        if is_openllmetry_available():
            try:
                from traceloop.sdk.decorators import task

                return task(name=name)(func)
            except ImportError:
                logger.warning('OpenLLMetry decorators not available')
                return func
        else:
            logger.debug(f"OpenLLMetry not available, skipping task annotation for '{name}'")
            return func

    return decorator


def add_tags(**tags):
    """
    Add tags to the current trace context.

    Args:
        **tags: Key-value pairs to add as tags

    """
    if is_openllmetry_available() and is_openllmetry_initialized():
        try:
            from traceloop.sdk import Traceloop

            Traceloop.set_association_properties(**tags)
        except Exception as e:
            logger.warning(f'Failed to add tags: {e}')
    else:
        logger.debug('OpenLLMetry not available, skipping tag addition')


def set_user_id(user_id: str):
    """
    Set user ID for OpenLLMetry context.

    Args:
        user_id: The user identifier.

    """
    try:
        from traceloop.sdk import Traceloop

        if is_openllmetry_initialized():
            Traceloop.set_correlation_id(user_id=user_id)
            logger.debug(f'Set user_id to {user_id}')

    except Exception as e:
        logger.warning(f'Failed to set user ID: {e}')


def set_session_id(session_id: str):
    """
    Set session ID for OpenLLMetry context.

    Args:
        session_id: The session identifier.

    """
    try:
        from traceloop.sdk import Traceloop

        if is_openllmetry_initialized():
            Traceloop.set_correlation_id(session_id=session_id)
            logger.debug(f'Set session_id to {session_id}')

    except Exception as e:
        logger.warning(f'Failed to set session ID: {e}')


# Compatibility function for existing code
def get_opentelemetry_callback_handler(
    session_id: Optional[str] = None, user_id: Optional[str] = None, sample_rate: float = 1.0, **kwargs
):
    """
    Get a callback handler for LangChain integration.

    When using OpenLLMetry, this returns None because OpenLLMetry automatically
    instruments LangChain operations. This function is provided for compatibility
    with existing code that expects a callback handler.

    Args:
        session_id: Session identifier
        user_id: User identifier
        sample_rate: Sampling rate (not used with OpenLLMetry auto-instrumentation)
        **kwargs: Additional arguments (ignored)

    Returns:
        None (OpenLLMetry uses auto-instrumentation)

    """
    if is_openllmetry_available() and is_openllmetry_initialized():
        # Set context properties for this session
        if session_id:
            set_session_id(session_id)
        if user_id:
            set_user_id(user_id)

        # OpenLLMetry auto-instruments LangChain, so no callback handler needed
        logger.debug('Using OpenLLMetry auto-instrumentation, no callback handler needed')
        return None
    else:
        # Fallback to custom OpenTelemetry handler if OpenLLMetry not available
        logger.warning('OpenLLMetry not available, falling back to custom OpenTelemetry handler')
        from .langchain_handler import OpenTelemetryCallbackHandler

        return OpenTelemetryCallbackHandler(session_id=session_id, user_id=user_id, sample_rate=sample_rate, **kwargs)
