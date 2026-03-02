#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# healthcheck.sh — Two-phase Docker health check
#
# Phase 1 (startup / sync):
#   The sentinel file does not yet exist.  The container is still installing
#   dependencies or starting the application.  We return exit 0 so that
#   Docker does not mark the container as unhealthy during normal startup.
#
# Phase 2 (application running):
#   Once the application signals readiness by creating the sentinel file,
#   we perform an HTTP health check with the X-Health-Check header.
#   If no HEALTHCHECK_URL is configured, the sentinel file alone is
#   sufficient proof of health.
#
# Environment variables (set in the compose service):
#   HEALTHCHECK_URL        — URL to curl  (e.g. http://127.0.0.1:8000/)
#   HEALTHCHECK_READY_FILE — Path to sentinel file  (default: /tmp/app-ready)
# ---------------------------------------------------------------------------

READY_FILE="${HEALTHCHECK_READY_FILE:-/tmp/app-ready}"
HEALTH_URL="${HEALTHCHECK_URL:-}"

# Phase 1: If the application has not signalled readiness, assume it is still
# syncing workspaces / installing packages.
if [ ! -f "$READY_FILE" ]; then
    exit 0
fi

# Phase 2: Application is ready — perform a real health check.
if [ -n "$HEALTH_URL" ]; then
    exec curl -sf -H 'X-Health-Check: true' "$HEALTH_URL"
fi

# No URL configured but sentinel exists — healthy.
exit 0
