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

logger = logging.getLogger(__name__)


def init_telemetry():
    """Initialize telemetry."""
    from .lib_config import get_lib_config
