"""
Test Configuration Module.

This module provides a centralized configuration management system for testing environments.
It defines configuration classes and utilities that handle loading application settings
from multiple sources including environment variables, TOML configuration files, and secrets.

The module is designed to support integration testing by providing access to database
connection strings, API credentials, and other infrastructure settings needed for
comprehensive test execution.

Key Components:
    - RuntimeSettings: Main configuration class with Pydantic validation
    - Custom type annotations for secure string handling
    - Cached configuration retrieval for optimal performance
    - Multi-source configuration loading with precedence handling

Usage:
    config = get_test_config()
    db_url = config.postgres_answers_connection_url
"""

import os
from functools import cache
from pathlib import Path

from pydantic import AnyHttpUrl, Field, PostgresDsn, StringConstraints

# See https://docs.pydantic.dev/latest/api/types/#pydantic.types.StringConstraints
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict, TomlConfigSettingsSource
from typing_extensions import Annotated

# Regular expression should match between 32 to 160 hexdecimal characters ( [0-9a-f] )
JwtSecretStr = Annotated[str, StringConstraints(pattern='[0-9a-f]{32,160}')]

MinimalStr = Annotated[str, StringConstraints(to_lower=True, min_length=3)]
LowerCaseStr = Annotated[str, StringConstraints(to_lower=True)]
PasswordOrKeyStr = Annotated[str, StringConstraints(min_length=8)]


class RuntimeSettings(BaseSettings):
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

    postgres_answers_connection_url: PostgresDsn = Field(default='', validation_alias='POSTGRES_ANSWERS_CONNECTION_URL')

    minio_endpoint_url: AnyHttpUrl = Field(default='', validation_alias='MINIO_ENDPOINT_URL')
    minio_bucket_name: MinimalStr = Field(default='', validation_alias='ANSWERS_MINIO_BUCKET')
    minio_user_name: MinimalStr = Field(default='', validation_alias='ANSWERS_MINIO_USER_NAME')
    minio_user_password: PasswordOrKeyStr = Field(default='', validation_alias='ANSWERS_MINIO_USER_PASSWORD')


@cache
def get_test_config():
    """
    Get the cached global application configuration instance for testing.

    This function provides access to the singleton Settings object that contains all
    application configuration values loaded from environment variables, TOML files,
    and other configuration sources. It's primarily used by test fixtures to access
    database connection strings, API credentials, and other infrastructure settings
    needed for integration testing.

    The configuration is cached using functools.cache to ensure it's loaded only once
    per test session, improving performance and ensuring consistency across all tests.

    Returns:
        Settings: The singleton configuration object containing all application settings.
    """
    return RuntimeSettings()
