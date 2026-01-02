import logging

import torch
from core_db.providers.sql_database import DataDomain, ping_async_sql_database
from core_public.status_models import PingResult, PingStatus

from ..providers.chat_llm import ping_chat_llm  # Added import
from ..providers.file_store import ping_file_store
from ..providers.vector_store import ping_vector_store

logger = logging.getLogger(__name__)


async def system_health_check():
    """Perform a comprehensive status check of the system, including database connectivity."""
    # Initialize with a default bad status, to be updated upon successful checks
    system_health = {
        'sql_database': PingResult(status=PingStatus.BAD, message='Check not performed').model_dump(),
        'file_store': PingResult(status=PingStatus.BAD, message='Check not performed').model_dump(),
        'vector_store': PingResult(status=PingStatus.BAD, message='Check not performed').model_dump(),
        'chat_llm': PingResult(status=PingStatus.BAD, message='Check not performed').model_dump(),  # Added chat_llm
    }

    # Ping PostgreSQL 'answers' schema
    try:
        pg_answers_status = await ping_async_sql_database(DataDomain.ANSWERS)
        system_health['sql_database'] = pg_answers_status.model_dump()
    except Exception as e:
        logger.error("Error during PostgreSQL 'answers' schema health check", exc_info=e)
        # Ensure the error is captured in the health status
        system_health['sql_database'] = PingResult(
            status=PingStatus.BAD, message="PostgreSQL 'answers' schema check failed unexpectedly.", error=str(e)
        ).model_dump()

    # Ping MinIO file store
    try:
        # TODO: Make ping_file_store async
        minio_status = ping_file_store()
        system_health['file_store'] = minio_status.model_dump()
    except Exception as e:
        logger.error('Error during MinIO file store health check', exc_info=e)
        system_health['file_store'] = PingResult(
            status=PingStatus.BAD, message='MinIO file store check failed unexpectedly.', error=str(e)
        ).model_dump()

    # Ping Vector Store
    try:
        vector_store_status = await ping_vector_store()
        system_health['vector_store'] = vector_store_status.model_dump()
    except Exception as e:
        logger.error('Error during vector store health check', exc_info=e)
        system_health['vector_store'] = PingResult(
            status=PingStatus.BAD, message='Vector store check failed unexpectedly.', error=str(e)
        ).model_dump()

    # Ping Chat LLM Provider
    try:
        # TODO: Make ping_chat_llm async
        chat_llm_status = ping_chat_llm()
        system_health['chat_llm'] = chat_llm_status.model_dump()
    except Exception as e:
        logger.error('Error during Chat LLM provider health check', exc_info=e)
        system_health['chat_llm'] = PingResult(
            status=PingStatus.BAD, message='Chat LLM provider check failed unexpectedly.', error=str(e)
        ).model_dump()

    return system_health


async def health_check():
    """
    Perform a system status check and return health information.

    Checks CUDA availability and device information, with placeholders for additional health checks
    like Redis, PostgreSQL, and MinIO connectivity.
    """
    health = {'status': 'not good'}
    try:
        cuda_available = torch.cuda.is_available()
        health['CUDA available'] = cuda_available

        if cuda_available:
            device_name = torch.cuda.get_device_name(0)
            health['CUDA device'] = device_name

        system_health = await system_health_check()

        health.update(system_health)

        health['status'] = 'good'

    except Exception as ex:
        logger.warning('status check failed', exc_info=ex)

    return health
