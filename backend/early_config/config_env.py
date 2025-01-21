import os
from dotenv import load_dotenv


def configure_env(base_env, secrets_env, overrides_env):
    # NOTES:
    # load_dotenv function parameters:
    # - interpolate=False will provent the dotenv from interpolating the values
    # - override=True will allow .env file values to override existing environment variables
    load_dotenv(dotenv_path=base_env, interpolate=False, override=True)
    if overrides_env is not None:
        load_dotenv(dotenv_path=overrides_env,
                    interpolate=False, override=True)
    if secrets_env is not None:
        load_dotenv(dotenv_path=secrets_env, interpolate=False, override=True)
