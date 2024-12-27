import os
from dotenv import load_dotenv

def configure_env(base_env, secrets_env):
    # NOTES:
    # interpolate=False will provent the dotenv from interpolating the values
    # override=True will allow .env file values to override existing environment variables
    load_dotenv(dotenv_path=base_env, interpolate=False, override=True)
    load_dotenv(dotenv_path=secrets_env, interpolate=False, override=True)

