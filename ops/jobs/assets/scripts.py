"""Script-based operation assets."""

from typing import Dict

from dagster import asset

from ..helpers import _run_script_job
from .images import ALL_IMAGE_ASSETS


@asset(required_resource_keys={"compose_env"}, deps=ALL_IMAGE_ASSETS)
def initialize_environment_asset(context) -> Dict[str, str]:
    """Initialize environment by running certificate generation."""
    _run_script_job(context, "initialize_environment", "scripts/make_certs.sh")
    return {"status": "completed"}
