"""
OpenTelemetry configuration and initialization for LLM observability.

This module provides centralized configuration for OpenTelemetry instrumentation,
supporting multiple approaches:
1. OpenLLMetry (recommended) - Automatic LLM-specific instrumentation
2. Custom OpenTelemetry - Manual instrumentation with custom exporters

Preference is given to OpenLLMetry when available as it provides better
LLM-specific observability out of the box.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Global telemetry configuration
_telemetry_initialized = False
_telemetry_method = None  # 'openllmetry' or 'custom'


def initialize_telemetry(method: str = 'custom', **kwargs):
    """
    Initialize telemetry with the best available method.

    Args:
        method: Telemetry method ('auto', 'openllmetry', 'custom')
        **kwargs: Configuration options passed to the chosen method

    """
    global _telemetry_initialized, _telemetry_method

    if _telemetry_initialized:
        logger.debug(f'Telemetry already initialized with method: {_telemetry_method}')
        return

    if method == 'auto':
        # Try OpenLLMetry first, fallback to custom
        if _try_initialize_openllmetry(**kwargs):
            _telemetry_method = 'openllmetry'
        else:
            _initialize_custom_telemetry(**kwargs)
            _telemetry_method = 'custom'
    elif method == 'openllmetry':
        if not _try_initialize_openllmetry(**kwargs):
            raise RuntimeError('OpenLLMetry initialization failed')
        _telemetry_method = 'openllmetry'
    elif method == 'custom':
        _initialize_custom_telemetry(**kwargs)
        _telemetry_method = 'custom'
    else:
        raise ValueError(f'Unknown telemetry method: {method}')

    _telemetry_initialized = True
    logger.info(f'Telemetry initialized successfully with method: {_telemetry_method}')


def _try_initialize_openllmetry(**kwargs) -> bool:
    """
    Try to initialize OpenLLMetry.

    Returns:
        bool: True if successful, False otherwise

    """
    try:
        from .openllmetry import initialize_openllmetry, is_openllmetry_available

        if not is_openllmetry_available():
            logger.info('OpenLLMetry not available, will use custom telemetry')
            return False

        # Extract OpenLLMetry-specific config
        openllmetry_config = {
            'disable_batch': kwargs.get('disable_batch', False),
            'app_name': kwargs.get('service_name', 'answers-agent'),
            'telemetry_enabled': kwargs.get('telemetry_enabled', False),
            'endpoint': kwargs.get('otel_jaeger_endpoint'),
        }

        initialize_openllmetry(**openllmetry_config)
        logger.info('Successfully initialized OpenLLMetry')
        return True

    except Exception as e:
        logger.warning(f'Failed to initialize OpenLLMetry: {e}')
        return False


def _initialize_custom_telemetry(**kwargs):
    """Initialize custom OpenTelemetry setup."""
    from .custom_otel import initialize_custom_telemetry

    initialize_custom_telemetry(**kwargs)
    logger.info('Successfully initialized custom OpenTelemetry')


def get_callback_handler(session_id: Optional[str] = None, user_id: Optional[str] = None, **kwargs):
    """
    Get appropriate callback handler for LangChain integration.

    Returns:
        Callback handler or None (if using auto-instrumentation)

    """
    if not _telemetry_initialized:
        raise RuntimeError()

    if _telemetry_method == 'openllmetry':
        from .openllmetry import get_opentelemetry_callback_handler

        return get_opentelemetry_callback_handler(session_id=session_id, user_id=user_id, **kwargs)
    else:
        from .langchain_handler import OpenTelemetryCallbackHandler

        return OpenTelemetryCallbackHandler(session_id=session_id, user_id=user_id, **kwargs)
