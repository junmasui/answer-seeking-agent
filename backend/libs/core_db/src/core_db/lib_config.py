"""
Library Configuration Management Module.

This module provides centralized configuration management for the application using Pydantic
settings. It handles loading configuration from multiple sources including environment variables,
TOML files, and secrets, with a hierarchical precedence system.

The module defines:
- Custom string types with validation constraints for various configuration values
- LibrarySettings class that encapsulates all application configuration
- A cached factory function for accessing the global configuration instance

Configuration sources are processed in order of precedence:
1. Initialization parameters (highest precedence)
2. Environment variables
3. Secret files
4. TOML configuration files (lowest precedence)
"""

import os
from functools import cache
from pathlib import Path
from typing import Union

from pydantic import (
    Field,
    FilePath,
    PostgresDsn,
    StringConstraints,
)

# See https://docs.pydantic.dev/latest/api/types/#pydantic.types.StringConstraints
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict, TomlConfigSettingsSource
from typing_extensions import Annotated

# Regular expression should match between 32 to 160 hexdecimal characters ( [0-9a-f] )
JwtSecretStr = Annotated[str, StringConstraints(pattern='[0-9a-f]{32,160}')]

MinimalStr = Annotated[str, StringConstraints(to_lower=True, min_length=3)]
LowerCaseStr = Annotated[str, StringConstraints(to_lower=True)]
PasswordOrKeyStr = Annotated[str, StringConstraints(min_length=8)]


class LibrarySettings(BaseSettings):
    """
    Library-wide configuration settings loaded from environment variables and TOML files.

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

    alembic_ini_path: Union[FilePath] = Field(default='./alembic.ini', validation_alias='ALEMBIC_INI_PATH')

    postgres_answers_connection_url: PostgresDsn = Field(default='', validation_alias='POSTGRES_ANSWERS_CONNECTION_URL')
    postgres_vectors_schema: str = Field(default='vectors', validation_alias='POSTGRES_VECTORS_SCHEMA')

    postgres_checkpoints_connection_url: PostgresDsn = Field(
        default='', validation_alias='POSTGRES_CHECKPOINTS_CONNECTION_URL'
    )


@cache
def get_lib_config():
    """
    Get the cached global library configuration instance.

    Returns the singleton Settings object that contains all library
    configuration loaded from environment variables, TOML files, and secrets.
    This serves as the central configuration access point used throughout
    the library for database connections, provider settings, worker
    configuration, and other runtime parameters.

    Returns:
        Settings: The global configuration instance containing all app settings.

    """
    return LibrarySettings()
