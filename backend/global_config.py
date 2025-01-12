"""
This is a small stand-alone module that
provides a global configuration object.
"""
from typing_extensions import Annotated

from functools import cache

from pydantic import (
    Field,
    PostgresDsn,
    RedisDsn,
    AnyHttpUrl,
    StringConstraints
)

# See https://docs.pydantic.dev/latest/api/types/#pydantic.types.StringConstraints

from pydantic_settings import BaseSettings, SettingsConfigDict

MinimalStr = Annotated[str, StringConstraints(to_lower=True, min_length=3)]
LowerCaseStr = Annotated[str, StringConstraints(to_lower=True)]
PasswordOrKeyStr = Annotated[str, StringConstraints(min_length=8)]

class Settings(BaseSettings):
    # We assume that the .env files were loaded into the environment
    # on an earlier step.
    model_config = SettingsConfigDict(env_file=None)

    # auth_key: str = Field(validation_alias='my_auth_key')

    # api_key: str = Field(alias='my_api_key')  

    redis_dsn: RedisDsn = Field(
        default='',
        validation_alias='REDIS_URL',  
    )

    postgres_connection_url: PostgresDsn = Field(default='',
                                validation_alias='POSTGRES_CONNECTION_URL')    
    postgres_user_name: MinimalStr = Field(default='',
                                    validation_alias='BACKEND_POSTGRES_USER_NAME')
    postgres_user_password: PasswordOrKeyStr = Field(default='',
                                    validation_alias='BACKEND_POSTGRES_USER_PASSWORD')


    use_unstructured_cloud_api: bool = Field(default=False,
                      validation_alias='USE_UNSTRUCTURED_API')

    unstructured_api_key: str = Field(default='', validation_alias='UNSTRUCTURED_API_KEY')


    chat_llm_type: LowerCaseStr = Field(default='', validation_alias='CHAT_LLM_TYPE')
    llm_has_structured_output: bool = Field(default=False, validation_alias='LLM_HAS_STRUCTURED_OUTPUT')


    minio_endpoint_url: AnyHttpUrl =Field(default='', validation_alias='MINIO_ENDPOINT_URL')
    minio_bucket_name: MinimalStr = Field(default='', validation_alias='BACKEND_MINIO_BUCKET')
    minio_user_name: MinimalStr = Field(default='', validation_alias='BACKEND_MINIO_USER_NAME')
    minio_user_password: PasswordOrKeyStr = Field(default='', validation_alias='BACKEND_MINIO_USER_PASSWORD')

@cache
def get_global_config():
    return Settings()
