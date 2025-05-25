import os
from pathlib import Path

from dotenv import load_dotenv


def configure_env():
    """Configure environment variables by loading from .env files.

    Loads environment variables from base and override .env files specified
    by DOTENV_FILE and DOTENV_OVERRIDES_FILE environment variables.
    Override values take precedence over base values.
    """
    base_env = os.getenv('DOTENV_FILE', '')

    if len(base_env) > 0:
        base_env = Path(base_env)

        if not base_env.exists():
            raise ValueError()

        # NOTES:
        # load_dotenv function parameters:
        # - interpolate=False will provent the dotenv from interpolating the values
        # - override=True will allow .env file values to override existing environment variables
        load_dotenv(dotenv_path=str(base_env), interpolate=False, override=True)

    overrides_env = os.getenv('DOTENV_OVERRIDES_FILE', '')
    if len(overrides_env) > 0:
        overrides_env = Path(overrides_env)

        if not overrides_env.exists():
            raise ValueError()

        load_dotenv(dotenv_path=overrides_env, interpolate=False, override=True)


configure_env()
