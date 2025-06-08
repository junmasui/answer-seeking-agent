"""
Simple authentication library configuration module.

This module provides a centralized configuration management system for the simple authentication
library. It uses Pydantic settings to load configuration from multiple sources including
environment variables, TOML files, and secret files, with a well-defined precedence order.

The module defines type annotations for various string constraints used throughout the
authentication system and provides a singleton pattern for accessing configuration.

Classes:
    AuthLibrarySettings: Main configuration class that handles loading settings from multiple sources.

Functions:
    get_lib_config: Factory function that returns a cached configuration instance.

Type Annotations:
    JwtSecretStr: String constraint for JWT secrets (32-160 hex characters).
    MinimalStr: String constraint for minimal strings (lowercase, min 3 chars).
    LowerCaseStr: String constraint for lowercase strings.
    PasswordOrKeyStr: String constraint for passwords/keys (min 8 chars).
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


class AuthLibrarySettings(BaseSettings):
    """
    Configuration settings for the simple authentication library.

    This class manages configuration loading from multiple sources with a defined precedence:
    1. Initialization arguments (highest priority)
    2. Environment variables
    3. Secret files
    4. TOML configuration files (lowest priority)

    The class uses Pydantic's BaseSettings to provide validation, type conversion,
    and automatic loading from various sources. Configuration files are expected
    to be loaded into environment variables in an earlier initialization step.

    Attributes:
        application_jwt_secret (JwtSecretStr): The JWT secret key for token signing and verification.
                                             Must be 32-160 hexadecimal characters.

    Configuration:
        - Disables automatic .env file loading (assumes pre-loaded environment)
        - Supports nested model partial updates
        - Custom source ordering via settings_customise_sources

    Example:
        >>> settings = AuthLibrarySettings(application_jwt_secret='a' * 32)
        >>> print(settings.application_jwt_secret)
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
        Define the sources and their precedence order for loading configuration values.

        This method customizes how Pydantic loads settings by specifying the order
        and types of configuration sources. Sources are evaluated in order, with
        earlier sources taking precedence over later ones.

        Args:
            settings_cls: The settings class being configured.
            init_settings: Values provided during class instantiation.
            env_settings: Values loaded from environment variables.
            dotenv_settings: Values from .env files (unused in this configuration).
            file_secret_settings: Values from secret files in configured directories.

        Returns:
            tuple[PydanticBaseSettingsSource, ...]: Ordered tuple of configuration sources
                in precedence order (highest to lowest):
                1. init_settings - Direct instantiation arguments
                2. env_settings - Environment variables
                3. file_secret_settings - Secret files
                4. TomlConfigSettingsSource - TOML configuration file

        Note:
            The TOML file path is determined by the CONFIG_TOML_FILE environment
            variable, defaulting to './config.toml' if not specified.
        """
        # We assume that the .env files were loaded into the environment
        # on an earlier step.

        toml_file_path = (
            Path(env_var_value) if (env_var_value := os.environ.get('CONFIG_TOML_FILE')) else Path('./config.toml')
        )

        # init_settings: setting values provided as keyword arguments when initialization
        #     an instance of this Settings class.
        # env_settings: settings values loaded from environment variables.
        # dotenv_settings: settings values loaded from env files, whose paths are specified in `env_file`
        #     config value.
        # file_secret_settings: settings values loaded from secret files, which are files in the
        #     directories specified in the `secrets_dir` config value.

        return (
            init_settings,
            env_settings,
            file_secret_settings,
            TomlConfigSettingsSource(settings_cls, toml_file=toml_file_path),
        )

    application_jwt_secret: JwtSecretStr = Field(default='', validation_alias='APPLICATION_JWT_SECRET')


@cache
def get_lib_config():
    """
    Get the singleton authentication configuration instance.

    This function provides a cached instance of the AuthLibrarySettings class,
    ensuring that configuration is loaded only once per application lifecycle.
    The caching improves performance by avoiding repeated file I/O and validation
    operations.

    The configuration is loaded from multiple sources in the following precedence order:
    1. Environment variables (highest priority)
    2. Secret files
    3. TOML configuration files (lowest priority)

    Returns:
        AuthLibrarySettings: A singleton configuration object containing all
                           authentication-related settings including JWT secrets
                           and other authentication parameters.

    Example:
        >>> config = get_lib_config()
        >>> jwt_secret = config.application_jwt_secret
        >>> # Subsequent calls return the same cached instance
        >>> config2 = get_lib_config()
        >>> assert config is config2

    Note:
        The function uses functools.cache, so the configuration is immutable
        after the first call. Changes to environment variables or configuration
        files after the first call will not be reflected unless the application
        is restarted.
    """
    return AuthLibrarySettings()
