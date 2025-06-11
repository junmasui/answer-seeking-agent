"""
Application Configuration Module.

This module provides centralized configuration management for the core application.
It defines the ApplicationSettings class that handles loading configuration values
from multiple sources including environment variables, TOML files, and secrets.

The module uses Pydantic BaseSettings for type validation and supports hierarchical
configuration loading with customizable source priority. Configuration values are
cached for performance using the @cache decorator.

Key Features:
    - Multi-source configuration loading (env vars, TOML files, secrets)
    - Type validation using Pydantic models
    - JWT secret validation with hexadecimal pattern matching
    - String constraints for minimal length and case conversion
    - Cached configuration access for improved performance

Type Definitions:
    JwtSecretStr: String type for JWT secrets (32-160 hex characters)
    MinimalStr: String type with minimum 3 characters, converted to lowercase
    LowerCaseStr: String type automatically converted to lowercase
    PasswordOrKeyStr: String type with minimum 8 characters for passwords/keys

Example:
    >>> config = get_app_config()
    >>> jwt_secret = config.application_jwt_secret
    >>> write_claim_ok = config.jwt_write_claim_missing_ok

Environment Variables:
    CONFIG_TOML_FILE: Path to TOML configuration file (default: './config.toml')
    APPLICATION_JWT_SECRET: JWT secret key for token signing/verification
    JWT_WRITE_CLAIM_MISSING_OK: Boolean flag for handling missing write claims

Dependencies:
    - pydantic: For data validation and settings management
    - pydantic-settings: For configuration source management
"""

import os
from functools import cache
from pathlib import Path

from pydantic import Field, StringConstraints

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

    This class provides centralized configuration management with support for multiple sources
    including environment variables, TOML configuration files, and secrets. It uses Pydantic
    for type validation and automatic conversion of configuration values.

    The configuration sources are loaded in the following priority order:
        1. init_settings: Values provided during class initialization
        2. env_settings: Values from environment variables
        3. file_secret_settings: Values from secret files
        4. TomlConfigSettingsSource: Values from TOML configuration file

    Attributes:
        jwt_write_claim_missing_ok (bool): Flag indicating whether missing JWT write claims
            are acceptable. Defaults to False. Loaded from JWT_WRITE_CLAIM_MISSING_OK.
        application_jwt_secret (JwtSecretStr): JWT secret key for token signing and
            verification. Must be 32-160 hexadecimal characters. Loaded from
            APPLICATION_JWT_SECRET environment variable.

    Configuration:
        The class uses SettingsConfigDict with env_file=None and toml_file=None since
        environment files are assumed to be loaded in an earlier initialization step.
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
        """
        Define the sources and their priority order for loading configuration values.

        This method customizes how Pydantic loads configuration settings by specifying
        the order and types of configuration sources. The method assumes that .env files
        have been loaded into the environment in an earlier initialization step.

        The TOML configuration file path is determined by the CONFIG_TOML_FILE environment
        variable, defaulting to './config.toml' if not specified.

        Args:
            settings_cls: The Settings class being configured
            init_settings: Settings values provided as keyword arguments during
                class initialization
            env_settings: Settings values loaded from environment variables
            dotenv_settings: Settings values loaded from .env files (unused here)
            file_secret_settings: Settings values loaded from secret files in
                directories specified by secrets_dir config

        Returns:
            tuple[PydanticBaseSettingsSource, ...]: Ordered tuple of configuration
                sources in priority order (highest to lowest priority):
                1. init_settings
                2. env_settings
                3. file_secret_settings
                4. TomlConfigSettingsSource

        Note:
            The dotenv_settings source is not included in the returned tuple since
            .env files are assumed to be pre-loaded into the environment.
        """
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

    jwt_write_claim_missing_ok: bool = Field(default=False, validation_alias='JWT_WRITE_CLAIM_MISSING_OK')

    application_jwt_secret: JwtSecretStr = Field(default='', validation_alias='APPLICATION_JWT_SECRET')


@cache
def get_app_config():
    """
    Get the cached global application configuration instance.

    This function provides a singleton-like access pattern to the application
    configuration. The configuration is cached using Python's @cache decorator
    to improve performance by avoiding repeated initialization and validation.

    The function creates and returns an ApplicationSettings instance that loads
    configuration from environment variables, TOML files, and other sources as
    defined in the ApplicationSettings class.

    Returns:
        ApplicationSettings: A cached instance of the application configuration
            with all settings loaded and validated.

    Performance:
        Subsequent calls to this function return the same cached instance,
        avoiding the overhead of re-reading configuration sources.

    Note:
        Due to caching, configuration changes made after the first call to this
        function will not be reflected until the cache is cleared or the
        application is restarted.
    """
    return ApplicationSettings()
