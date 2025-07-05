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
    app_name: str = "answers-agent",
    telemetry_enabled: bool = False,
    **kwargs
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
        **kwargs: Additional configuration options for Traceloop.init()
    """
    global _openllmetry_initialized
    
    if _openllmetry_initialized:
        logger.debug("OpenLLMetry already initialized")
        return
    
    try:
        from traceloop.sdk import Traceloop
        
        # Set environment variables if provided
        if api_key:
            os.environ['TRACELOOP_API_KEY'] = api_key
        if base_url:
            os.environ['TRACELOOP_BASE_URL'] = base_url
        
        # Initialize Traceloop with configuration
        init_kwargs = {
            'app_name': app_name,
            'disable_batch': disable_batch,
            'telemetry_enabled': telemetry_enabled,
            **kwargs
        }
        
        # Remove None values to use defaults
        init_kwargs = {k: v for k, v in init_kwargs.items() if v is not None}
        
        Traceloop.init(**init_kwargs)
        
        _openllmetry_initialized = True
        logger.info(f"OpenLLMetry initialized successfully with app_name='{app_name}'")
        
    except ImportError as e:
        logger.error(
            "OpenLLMetry (traceloop-sdk) not installed. "
            "Install it with: pip install traceloop-sdk"
        )
        raise e
    except Exception as e:
        logger.error(f"Failed to initialize OpenLLMetry: {e}")
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
                logger.warning("OpenLLMetry decorators not available")
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
                logger.warning("OpenLLMetry decorators not available")
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
            logger.warning(f"Failed to add tags: {e}")
    else:
        logger.debug("OpenLLMetry not available, skipping tag addition")


def set_user_id(user_id: str):
    """
    Set the user ID for the current trace context.
    
    Args:
        user_id: User identifier
    """
    if is_openllmetry_available() and is_openllmetry_initialized():
        try:
            from traceloop.sdk import Traceloop
            Traceloop.set_association_properties(user_id=user_id)
        except Exception as e:
            logger.warning(f"Failed to set user ID: {e}")
    else:
        logger.debug("OpenLLMetry not available, skipping user ID setting")


def set_session_id(session_id: str):
    """
    Set the session ID for the current trace context.
    
    Args:
        session_id: Session identifier
    """
    if is_openllmetry_available() and is_openllmetry_initialized():
        try:
            from traceloop.sdk import Traceloop
            Traceloop.set_association_properties(session_id=session_id)
        except Exception as e:
            logger.warning(f"Failed to set session ID: {e}")
    else:
        logger.debug("OpenLLMetry not available, skipping session ID setting")


# Compatibility function for existing code
def get_opentelemetry_callback_handler(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    sample_rate: float = 1.0,
    **kwargs
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
        logger.debug("Using OpenLLMetry auto-instrumentation, no callback handler needed")
        return None
    else:
        # Fallback to custom OpenTelemetry handler if OpenLLMetry not available
        logger.warning("OpenLLMetry not available, falling back to custom OpenTelemetry handler")
        from .langchain_handler import OpenTelemetryCallbackHandler
        return OpenTelemetryCallbackHandler(
            session_id=session_id,
            user_id=user_id,
            sample_rate=sample_rate,
            **kwargs
        )
