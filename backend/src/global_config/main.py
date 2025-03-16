"""
This is a small stand-alone module that
provides a global configuration object.
"""
from typing import Union
from typing_extensions import Annotated
from functools import cache

from pydantic import (
    BaseModel,
    Field,
    PostgresDsn,
    RedisDsn,
    AnyHttpUrl,
    StringConstraints,
    DirectoryPath,
    FilePath,
    NewPath
)

# See https://docs.pydantic.dev/latest/api/types/#pydantic.types.StringConstraints

from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict, TomlConfigSettingsSource

# Regular expression should match between 32 to 160 hexdecimal characters ( [0-9a-f] )
JwtSecretStr = Annotated[str, StringConstraints(pattern='[0-9a-f]{32,160}')]

MinimalStr = Annotated[str, StringConstraints(to_lower=True, min_length=3)]
LowerCaseStr = Annotated[str, StringConstraints(to_lower=True)]
PasswordOrKeyStr = Annotated[str, StringConstraints(min_length=8)]


class DocManagerConfig(BaseModel):
    chunk_root_dir: str = Field(default='upload_chunks')
    doc_root_dir: str = Field(default='documents')


class Settings(BaseSettings):
    # We assume that the .env files were loaded into the environment
    # in an earlier initialization step.
    model_config = SettingsConfigDict(env_file=None, toml_file=None,
                                      nested_model_default_partial_update=True)


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
        Define the sources and their order for loading the settings values.
        """
        # We assume that the .env files were loaded into the environment
        # on an earlier step.

        # init_settings: setting values provided as keyword arguments when initialization
        #     an instance of this Settings class.
        # env_settings: settings values loaded from environment variables.
        # dotenv_settings: settings values loaded from env files, whose paths are specified in `env_file`
        #     config value.
        # file_secret_settings: settings values loaded from secret files, which are files in the
        #     directories specified in the `secrets_dir` config value.

        return init_settings, env_settings, file_secret_settings, TomlConfigSettingsSource(settings_cls)

    logging_config_path: Union[FilePath, NewPath] = Field(default='./logging.toml', validation_alias='LOGGING_CONFIG_PATH')

    staging_dir: Union[DirectoryPath, NewPath] = Field(default='/staging', validation_alias='WORKER_STAGING_DIR')

    redis_dsn: RedisDsn = Field(default='', validation_alias='REDIS_URL')

    postgres_connection_url: PostgresDsn = Field(default='',
                                validation_alias='POSTGRES_CONNECTION_URL')    

    application_jwt_secret: JwtSecretStr = Field(default='', validation_alias='APPLICATION_JWT_SECRET')

    use_unstructured_cloud_api: bool = Field(default=False,
                      validation_alias='USE_UNSTRUCTURED_API')

    unstructured_api_key: str = Field(default='', validation_alias='UNSTRUCTURED_API_KEY')


    chat_llm_type: LowerCaseStr = Field(default='', validation_alias='CHAT_LLM_TYPE')
    llm_has_structured_output: bool = Field(default=False, validation_alias='LLM_HAS_STRUCTURED_OUTPUT')


    minio_endpoint_url: AnyHttpUrl =Field(default='', validation_alias='MINIO_ENDPOINT_URL')
    minio_bucket_name: MinimalStr = Field(default='', validation_alias='BACKEND_MINIO_BUCKET')
    minio_user_name: MinimalStr = Field(default='', validation_alias='BACKEND_MINIO_USER_NAME')
    minio_user_password: PasswordOrKeyStr = Field(default='', validation_alias='BACKEND_MINIO_USER_PASSWORD')

    doc_manager: DocManagerConfig = DocManagerConfig()

@cache
def get_global_config():
    return Settings()
