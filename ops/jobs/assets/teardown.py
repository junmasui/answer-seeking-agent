"""Teardown assets for stopping Docker Compose services."""

from typing import Dict

from dagster import asset

from ..constants import ALL_APP_SERVICES, AUTOTEST_AND_TEST_SERVICES
from ..helpers import _stop_all_services, _stop_services


@asset(name="stop-all-services", required_resource_keys={"compose_env"})
def stop_all_services_asset(context) -> Dict[str, str]:
    """Stop all Docker Compose services, remove containers and orphans."""
    _stop_all_services(context)
    return {"status": "stopped"}


@asset(name="stop-app-services", required_resource_keys={"compose_env"})
def stop_app_services_asset(context) -> Dict[str, str]:
    """Stop frontend and backend services (prod-like, autotest, and automated tests)."""
    _stop_services(context, list(ALL_APP_SERVICES))
    return {"status": "stopped"}


@asset(name="stop-autotest-services", required_resource_keys={"compose_env"})
def stop_autotest_services_asset(context) -> Dict[str, str]:
    """Stop frontend and backend autotest and automated test services."""
    _stop_services(context, list(AUTOTEST_AND_TEST_SERVICES))
    return {"status": "stopped"}
