from typing import Dict, List

from dagster import AssetsDefinition, Failure, RetryPolicy, asset

from ..constants import SERVICES_ROOT
from ..helpers import _run_subprocess


def _make_image_build_asset(directory: str, deps: List[AssetsDefinition] = None) -> AssetsDefinition:
    """Create an asset for building a specific service image."""
    asset_name = f"{directory.replace('-', '_')}_image"
    
    @asset(
        name=asset_name,
        required_resource_keys={"compose_env"},
        retry_policy=RetryPolicy(max_retries=3),
        deps=deps,
        op_tags={"dagster/concurrency_key": "image_build"},
    )
    def _asset(context) -> Dict[str, str]:
        env = context.resources.compose_env.env
        build_dir = SERVICES_ROOT / directory / "build"
        script_path = build_dir / "build_images.sh"
        
        if not script_path.exists():
            raise Failure(f"missing build script: {script_path}")
            
        result = _run_subprocess(["bash", "build_images.sh"], env, cwd=str(build_dir))
        if result.stdout:
            context.log.info("stdout:\n%s", result.stdout.strip())
        if result.stderr:
            context.log.info("stderr:\n%s", result.stderr.strip())
        context.log.info("built %s exit=%s", directory, result.returncode)

        if result.returncode != 0:
            raise Failure(f"image build failed for {directory} (code={result.returncode})")
            
        return {"status": "built"}

    return _asset


# Group 1: Independent images
# "slim-util", "seaweedfs", "redis", "opensearch", "traefik", "weaviate", "api-server"
slim_util_image = _make_image_build_asset("slim-util")
seaweedfs_image = _make_image_build_asset("seaweedfs")
redis_image = _make_image_build_asset("redis")
opensearch_image = _make_image_build_asset("opensearch")
traefik_image = _make_image_build_asset("traefik")
weaviate_image = _make_image_build_asset("weaviate")
api_server_image = _make_image_build_asset("api-server")

group_1_assets = [
    slim_util_image,
    seaweedfs_image,
    redis_image,
    opensearch_image,
    traefik_image,
    weaviate_image,
    api_server_image,
]


@asset(
    required_resource_keys={"compose_env"},
    retry_policy=RetryPolicy(max_retries=3),
    deps=group_1_assets,
    op_tags={"dagster/concurrency_key": "image_build"},
)
def build_python_packages_asset(context) -> Dict[str, str]:
    """Build Python packages for the project."""
    script_path = SERVICES_ROOT / "scripts" / "build_python_packages.sh"
    if not script_path.exists():
        raise Failure(f"missing build script: {script_path}")
    
    env = context.resources.compose_env.env
    cmd = ["bash", "scripts/build_python_packages.sh"]
    result = _run_subprocess(cmd, env, cwd=str(SERVICES_ROOT))
    context.log.info("built python packages exit=%s", result.returncode)
    
    if result.returncode != 0:
        context.log.error("python build failed: %s", result.stderr.strip())
        raise Failure(f"python build failed (code={result.returncode})")
        
    return {"status": "built"}


# Group 2: Depend on Python packages
# "nemo", "webui-server", "dev-server"
nemo_image = _make_image_build_asset("nemo", deps=[build_python_packages_asset])
webui_server_image = _make_image_build_asset("webui-server", deps=[build_python_packages_asset])
# dev_server_image = _make_image_build_asset("dev-server", deps=[build_python_packages_asset])

group_2_assets = [
    nemo_image,
    webui_server_image,
    # dev_server_image,
]

# Collection of all image assets for external dependencies
ALL_IMAGE_ASSETS = group_1_assets + [build_python_packages_asset] + group_2_assets
