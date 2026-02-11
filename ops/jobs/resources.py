"""Dagster resources for service orchestration."""

import os
import subprocess
from dataclasses import dataclass
from typing import Dict

from dagster import Field, String, resource

from .constants import SCRIPTS_DIR


@dataclass
class ComposeEnv:
    """Environment configuration for docker compose operations."""

    gpu_mode: str
    compose_file: str
    env: Dict[str, str]


class ProcessChecker:
    """Helper to check service readiness."""

    def __init__(self) -> None:
        self.script_path = SCRIPTS_DIR / "display_processes.sh"
        if not self.script_path.exists():
            raise FileNotFoundError(f"Display helper not found: {self.script_path}")

    def check(self, gpu_mode: str) -> subprocess.CompletedProcess:
        """Check if services are ready."""
        cmd = [str(self.script_path), f"--gpu-mode={gpu_mode}"]
        return subprocess.run(cmd, capture_output=True, text=True)


@resource(config_schema={"gpu_mode": Field(String, default_value="cuda12")})
def compose_env_resource(context) -> ComposeEnv:
    """Resource providing docker compose environment configuration."""
    gpu_mode = os.environ.get("GPU_MODE") or context.resource_config.get("gpu_mode", "cuda12")
    compose_file = os.environ.get("COMPOSE_FILE")
    if compose_file is None or compose_file.strip() == "":
        compose_file = ":".join(
            [
                "common.compose.yml",
                "cuda.compose.yml" if gpu_mode == "cuda12" else "cpu-only.compose.yml",
            ]
        )
    env = os.environ.copy()
    env["COMPOSE_FILE"] = compose_file
    env["GPU_MODE"] = gpu_mode
    return ComposeEnv(gpu_mode=str(gpu_mode), compose_file=compose_file, env=env)


@resource
def process_checker_resource(_):
    """Resource providing process readiness checking."""
    return ProcessChecker()
