"""
This is a small stand-alone module that
provides a global configuration object.
"""

from functools import cache
from pathlib import Path
import os

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
            Path(env_var_value) 
            if (env_var_value := os.environ.get('CONFIG_TOML_FILE')) 
            else Path('./config.toml')
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
    Get the cached global authentication configuration instance.

    Returns the singleton AuthSettings object that contains authentication-related
    configuration loaded from environment variables, TOML files, and other sources.
    Uses functools.cache to ensure the configuration is loaded only once per
    application lifecycle for optimal performance.

    Returns:
        AuthSettings: The authentication configuration object containing JWT secrets
                     and other authentication-related settings.
    """
    return AuthLibrarySettings()
