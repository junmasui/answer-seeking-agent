"""Helper functions for service orchestration."""

import json
import subprocess
import time
from dataclasses import dataclass
from typing import Dict, List

from dagster import Failure

from .constants import SERVICES_ROOT

# How long to poll for a container health-check that is still "starting"
_HEALTH_CHECK_TIMEOUT = 120  # seconds
_HEALTH_CHECK_INTERVAL = 4  # seconds between polls


def _run_subprocess(
    cmd: List[str], env: Dict[str, str], cwd: str | None = None
) -> subprocess.CompletedProcess:
    """Run a subprocess with the given command and environment."""
    return subprocess.run(cmd, env=env, cwd=cwd, capture_output=True, text=True)


def _get_container_logs(env: Dict[str, str], service: str, tail: int = 50) -> str:
    """Retrieve recent logs from a container for debugging."""
    result = _run_subprocess(["docker", "compose", "logs", "--tail", str(tail), service], env, cwd=str(SERVICES_ROOT))
    return result.stdout or result.stderr or "(no logs)"


@dataclass
class ServiceState:
    """Current state of a Docker Compose service container."""

    exists: bool
    state: str  # running, exited, paused, restarting, dead, created
    health: str  # healthy, unhealthy, starting, empty-string
    exit_code: int
    name: str


def _get_service_state(env: Dict[str, str], service: str) -> ServiceState:
    """Query Docker for the current state of a specific service container."""
    cmd = ["docker", "compose", "ps", "--format", "json", "-a", service]
    result = _run_subprocess(cmd, env, cwd=str(SERVICES_ROOT))
    if result.returncode != 0 or not result.stdout.strip():
        return ServiceState(exists=False, state="", health="", exit_code=-1, name=service)

    try:
        for line in result.stdout.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            return ServiceState(
                exists=True,
                state=data.get("State", ""),
                health=data.get("Health", ""),
                exit_code=data.get("ExitCode", -1),
                name=data.get("Name", service),
            )
    except (json.JSONDecodeError, IndexError, KeyError):
        pass

    return ServiceState(exists=False, state="", health="", exit_code=-1, name=service)


def _is_service_running_ok(state: ServiceState) -> bool:
    """Check if a long-running service is in an acceptable running state.

    Returns True when the container is running and either has a passing
    health-check or has no health-check configured (running is sufficient).
    """
    if not state.exists or state.state != "running":
        return False
    return state.health in ("", "healthy")


def _force_remove_service(env: Dict[str, str], service: str) -> None:
    """Force-stop and remove a service container."""
    _run_subprocess(
        ["docker", "compose", "rm", "-f", "-s", service], env, cwd=str(SERVICES_ROOT)
    )


def _start_service(context, service: str) -> None:
    """Start a long-running service with idempotent health-checking.

    1. Query the current container state for *this specific service*.
    2. If already running and healthy -> skip (no restart).
    3. If unhealthy / exited-non-zero / dead -> force-remove, then start fresh.
    4. If cleanly exited or not found -> start fresh.
    5. After starting, verify the service is running via a per-service check.
    """
    compose_env = context.resources.compose_env
    env = compose_env.env

    # -- Pre-check: active query of actual container state --
    pre = _get_service_state(env, service)
    context.log.info(
        "pre-check %s: exists=%s state=%s health=%s exit_code=%s",
        service, pre.exists, pre.state, pre.health, pre.exit_code,
    )

    if _is_service_running_ok(pre):
        context.log.info("service %s already running and healthy -- skipping start", service)
        return

    # Clean up containers in bad states before starting
    if pre.exists and (
        pre.health == "unhealthy"
        or (pre.state == "exited" and pre.exit_code != 0)
        or pre.state in ("dead", "paused", "restarting")
    ):
        context.log.warning(
            "service %s in bad state (state=%s health=%s exit=%s) -- force-removing",
            service, pre.state, pre.health, pre.exit_code,
        )
        _force_remove_service(env, service)

    # -- Start --
    cmd = ["docker", "compose", "up", "-d", service]
    result = _run_subprocess(cmd, env, cwd=str(SERVICES_ROOT))
    context.log.info("docker compose up -d %s (exit=%s)", service, result.returncode)

    if result.returncode != 0:
        context.log.error("docker compose up failed: %s", result.stderr.strip())
        raise Failure(f"failed to start service {service} (code={result.returncode})")

    # -- Post-check: poll until the service is healthy or timeout --
    deadline = time.monotonic() + _HEALTH_CHECK_TIMEOUT
    while True:
        post = _get_service_state(env, service)
        context.log.info(
            "post-check %s: state=%s health=%s", service, post.state, post.health,
        )

        if _is_service_running_ok(post):
            context.log.info("service %s is running and healthy", service)
            return

        if post.state == "running" and post.health == "starting":
            if time.monotonic() < deadline:
                context.log.info(
                    "service %s health-check still starting -- waiting %ds",
                    service, _HEALTH_CHECK_INTERVAL,
                )
                time.sleep(_HEALTH_CHECK_INTERVAL)
                continue
            raise Failure(
                f"service {service} health-check did not pass within {_HEALTH_CHECK_TIMEOUT}s"
            )

        logs = _get_container_logs(env, service)
        context.log.error("service %s not ready after start, logs:\n%s", service, logs)
        raise Failure(
            f"service {service} not ready (state={post.state} health={post.health})"
        )


def _run_init_container(context, service: str) -> None:
    """Run an init container with idempotent completion-checking.

    1. Query the current container state.
    2. If already exited with code 0 -> skip (init work already done).
    3. If in any other existing state -> clean up and re-run.
    4. Wait for the container to exit and verify success.
    """
    compose_env = context.resources.compose_env
    env = compose_env.env

    # -- Pre-check: active query of actual container state --
    pre = _get_service_state(env, service)
    context.log.info(
        "pre-check init %s: exists=%s state=%s exit_code=%s",
        service, pre.exists, pre.state, pre.exit_code,
    )

    if pre.exists and pre.state == "exited" and pre.exit_code == 0:
        context.log.info(
            "init container %s already completed successfully -- skipping", service
        )
        return

    # Clean up any old container before re-running
    if pre.exists:
        context.log.info(
            "removing old init container %s (state=%s exit=%s)",
            service, pre.state, pre.exit_code,
        )
        _force_remove_service(env, service)

    # -- Start the init container --
    up_cmd = ["docker", "compose", "up", "-d", service]
    up_result = _run_subprocess(up_cmd, env, cwd=str(SERVICES_ROOT))
    context.log.info("started init container %s (exit=%s)", service, up_result.returncode)

    if up_result.returncode != 0:
        context.log.error("docker compose up failed: %s", up_result.stderr.strip())
        raise Failure(f"failed to start init container {service} (code={up_result.returncode})")

    # -- Wait for the container to exit --
    wait_cmd = ["docker", "compose", "wait", service]
    wait_result = _run_subprocess(wait_cmd, env, cwd=str(SERVICES_ROOT))
    context.log.info("init container %s completed (exit=%s)", service, wait_result.returncode)

    if wait_result.returncode != 0:
        # Fallback: inspect container directly (workaround for flaky compose wait)
        try:
            ps_cmd = ["docker", "compose", "ps", "-q", "-a", service]
            ps_result = _run_subprocess(ps_cmd, env, cwd=str(SERVICES_ROOT))
            if ps_result.returncode == 0 and ps_result.stdout.strip():
                container_id = ps_result.stdout.strip()
                inspect_cmd = ["docker", "inspect", container_id]
                inspect_result = _run_subprocess(inspect_cmd, env, cwd=str(SERVICES_ROOT))
                if inspect_result.returncode == 0:
                    info = json.loads(inspect_result.stdout)[0]
                    actual_exit = info["State"]["ExitCode"]
                    if actual_exit == 0:
                        context.log.warning(
                            "docker compose wait reported failure (%s) but container exited 0 -- proceeding",
                            wait_result.stderr.strip(),
                        )
                        return
        except Exception:
            pass  # Unable to verify, fall through to error

        logs = _get_container_logs(env, service)
        context.log.error("init container failed, logs:\n%s", logs)
        context.log.error("wait stderr: %s", wait_result.stderr)
        raise Failure(f"init container {service} failed (code={wait_result.returncode})")


def _run_script_job(context, job_name: str, script_rel: str) -> None:
    """Run a script job from the services/scripts directory."""
    script_path = SERVICES_ROOT / script_rel
    if not script_path.exists():
        raise Failure(f"script path not found: {script_path}")
    env = context.resources.compose_env.env
    cmd = ["bash", str(script_path)]
    result = _run_subprocess(cmd, env, cwd=str(SERVICES_ROOT))
    context.log.info("running %s exit=%s", job_name, result.returncode)
    if result.returncode != 0:
        context.log.error("job diagnostics: %s", result.stderr.strip())
        raise Failure(f"job {job_name} failed with code {result.returncode}")


def _stop_service(context, service: str) -> None:
    """Stop and remove a single service container (idempotent)."""
    env = context.resources.compose_env.env
    state = _get_service_state(env, service)
    if not state.exists:
        context.log.info("service %s not found -- nothing to stop", service)
        return
    context.log.info("stopping service %s (state=%s)", service, state.state)
    _force_remove_service(env, service)
    context.log.info("service %s stopped and removed", service)


def _stop_services(context, services: List[str]) -> None:
    """Stop and remove a list of service containers."""
    env = context.resources.compose_env.env
    stop_cmd = ["docker", "compose", "stop", *services]
    stop_result = _run_subprocess(stop_cmd, env, cwd=str(SERVICES_ROOT))
    context.log.info("stopped services %s (exit=%s)", services, stop_result.returncode)

    rm_cmd = ["docker", "compose", "rm", "-f", *services]
    rm_result = _run_subprocess(rm_cmd, env, cwd=str(SERVICES_ROOT))
    context.log.info("removed containers %s (exit=%s)", services, rm_result.returncode)

    if stop_result.returncode != 0:
        context.log.error("stop stderr: %s", stop_result.stderr.strip())
        raise Failure(f"failed to stop services (code={stop_result.returncode})")


def _stop_all_services(context) -> None:
    """Stop and remove all Docker Compose services, networks, and orphans."""
    env = context.resources.compose_env.env
    cmd = ["docker", "compose", "down", "--remove-orphans"]
    result = _run_subprocess(cmd, env, cwd=str(SERVICES_ROOT))
    context.log.info("docker compose down (exit=%s)", result.returncode)

    if result.returncode != 0:
        context.log.error("docker compose down failed: %s", result.stderr.strip())
        raise Failure(f"docker compose down failed (code={result.returncode})")
