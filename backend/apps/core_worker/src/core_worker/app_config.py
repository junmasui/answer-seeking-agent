"""
Celery Worker Application Configuration Module.

This module provides centralized configuration management for Celery worker components
through a Pydantic-based settings system. It handles loading configuration values from
multiple sources including environment variables, TOML configuration files, and secrets.

The module defines type constraints for common configuration values like JWT secrets,
passwords, and strings, and provides a singleton pattern for accessing application
configuration throughout the Celery worker application.

Key Features:
    - Multi-source configuration loading (environment, TOML, secrets)
    - Type validation and constraints using Pydantic
    - Cached singleton configuration access
    - Redis and Celery-specific configuration management
    - Prometheus metrics directory configuration
"""

import os
from functools import cache
from pathlib import Path

from pydantic import Field, RedisDsn, StringConstraints

# See https://docs.pydantic.dev/latest/api/types/#pydantic.types.StringConstraints
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict, TomlConfigSettingsSource
from typing_extensions import Annotated

# Regular expression should match between 32 to 160 hexdecimal characters ( [0-9a-f] )
JwtSecretStr = Annotated[str, StringConstraints(pattern='[0-9a-f]{32,160}')]

MinimalStr = Annotated[str, StringConstraints(to_lower=True, min_length=3)]
LowerCaseStr = Annotated[str, StringConstraints(to_lower=True)]
PasswordOrKeyStr = Annotated[str, StringConstraints(min_length=8)]


class ApplicationSettings(BaseSettings):
    """
    Application-wide configuration settings loaded from environment variables and TOML files.

    Provides centralized configuration management with support for multiple sources including
    environment variables, TOML configuration files, and secrets.
    """

    # We assume that the .env files were loaded into the environment
    # in an earlier initialization step.
    model_config = SettingsConfigDict(env_file=None, toml_file=None, nested_model_default_partial_update=True)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Define the sources and their order for loading the settings values."""
        # We assume that the .env files were loaded into the environment
        # on an earlier step.

        toml_file_path = (
            Path(env_var_value) if (env_var_value := os.environ.get('CONFIG_TOML_FILE')) else Path('./config.toml')
        )

        # init_settings: setting values provided as keyword arguments when initialization
        #     an instance of this Settings class.
        # env_settings: settings values loaded from environment variables.
        # dotenv_settings: settings values loaded from env files, whose paths are specified
        #     in `env_file` config value.
        # file_secret_settings: settings values loaded from secret files, which are files in the
        #     directories specified in the `secrets_dir` config value.

        return (
            init_settings,
            env_settings,
            file_secret_settings,
            TomlConfigSettingsSource(settings_cls, toml_file=toml_file_path),
        )

    redis_dsn: RedisDsn = Field(default='', validation_alias='REDIS_URL')

    celery_task_queue: str = Field(default='', validation_alias='CELERY_TASK_QUEUE')
    celery_result_key_prefix: str = Field(default='', validation_alias='CELERY_RESULT_KEY_PREFIX')


@cache
def get_app_config():
    """
    Get the cached global application configuration instance for Celery worker operations.

    This function provides access to the singleton Settings object that contains all
    application configuration values loaded from environment variables, TOML files,
    and other configuration sources. It's specifically used by the Celery worker
    components to access database connections, Redis settings, task queue configurations,
    file storage paths, and other runtime settings required for background task processing.

    Returns:
        Settings: The singleton configuration object containing Celery worker settings,
                 database connections, Redis DSN, task queues, file paths, and other
                 application configuration parameters.

    """
    return ApplicationSettings()
