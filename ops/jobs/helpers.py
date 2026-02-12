"""Helper functions for service orchestration."""

import json
import subprocess
from typing import Dict, List

from dagster import Failure

from .constants import SERVICES_ROOT


def _run_subprocess(
    cmd: List[str], env: Dict[str, str], cwd: str | None = None
) -> subprocess.CompletedProcess:
    """Run a subprocess with the given command and environment."""
    return subprocess.run(cmd, env=env, cwd=cwd, capture_output=True, text=True)


def _get_container_logs(env: Dict[str, str], service: str, tail: int = 50) -> str:
    """Retrieve recent logs from a container for debugging."""
    result = _run_subprocess(["docker", "compose", "logs", "--tail", str(tail), service], env, cwd=str(SERVICES_ROOT))
    return result.stdout or result.stderr or "(no logs)"


def _start_service(context, service: str) -> None:
    """Start a long-running service and wait for it to become healthy.

    Use this for services that stay running (e.g., postgres, redis, api-server).
    The service is started in detached mode and readiness is verified via the
    process_checker resource.
    """
    compose_env = context.resources.compose_env
    env = compose_env.env

    cmd = ["docker", "compose", "up", "-d", service]
    result = _run_subprocess(cmd, env, cwd=str(SERVICES_ROOT))
    context.log.info("started service %s (exit=%s)", service, result.returncode)

    if result.returncode != 0:
        context.log.error("docker compose up failed: %s", result.stderr.strip())
        raise Failure(f"failed to start service {service} (code={result.returncode})")

    check_result = context.resources.process_checker.check(compose_env.gpu_mode)
    context.log.info(
        "readiness check exit=%s stdout=%s",
        check_result.returncode,
        check_result.stdout.strip(),
    )

    if check_result.returncode != 0:
        context.log.error("readiness check failed: %s", check_result.stderr.strip())
        raise Failure(
            f"readiness check failed for service {service} (code={check_result.returncode})"
        )


def _run_init_container(context, service: str) -> None:
    """Run an init container and wait for it to exit successfully.

    Use this for run-and-done containers (e.g., postgres-init, keycloak-init).
    The container is started and we wait for it to exit, then check the exit code.
    """
    compose_env = context.resources.compose_env
    env = compose_env.env

    # Start the init container
    up_cmd = ["docker", "compose", "up", "-d", service]
    up_result = _run_subprocess(up_cmd, env, cwd=str(SERVICES_ROOT))
    context.log.info("started init container %s (exit=%s)", service, up_result.returncode)

    if up_result.returncode != 0:
        context.log.error("docker compose up failed: %s", up_result.stderr.strip())
        raise Failure(f"failed to start init container {service} (code={up_result.returncode})")

    # Wait for the container to exit (docker compose wait returns the container's exit code)
    wait_cmd = ["docker", "compose", "wait", service]
    wait_result = _run_subprocess(wait_cmd, env, cwd=str(SERVICES_ROOT))
    context.log.info("init container %s completed (exit=%s)", service, wait_result.returncode)

    if wait_result.returncode != 0:
        # Fallback: check if container actually succeeded (workaround for flaky compose wait)
        try:
            # Get container ID
            ps_cmd = ["docker", "compose", "ps", "-q", "-a", service]
            ps_result = _run_subprocess(ps_cmd, env, cwd=str(SERVICES_ROOT))
            if ps_result.returncode == 0 and ps_result.stdout.strip():
                container_id = ps_result.stdout.strip()
                inspect_cmd = ["docker", "inspect", container_id]
                inspect_result = _run_subprocess(inspect_cmd, env, cwd=str(SERVICES_ROOT))
                if inspect_result.returncode == 0:
                    info = json.loads(inspect_result.stdout)[0]
                    exit_code = info["State"]["ExitCode"]
                    if exit_code == 0:
                        context.log.warning(
                            "docker compose wait failed (%s) but container exited with 0. Proceeding.",
                            wait_result.stderr.strip(),
                        )
                        return
        except Exception:
            pass  # Failed to verify, proceed to error logging

        logs = _get_container_logs(env, service)
        context.log.error("init container failed, logs:\n%s", logs)
        # Log stderr to help debugging
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
