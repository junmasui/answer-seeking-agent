import logging

from core_db.db_models.model_ops import create_tables_if_not_exists, drop_all_tables

from .signals import reset_data_handler, send_db_predefined_data, start_up_handler

logger = logging.getLogger(__name__)


@start_up_handler
async def documents_startup(sender):
    """Initialize document-related database tables and predefined data on application startup."""
    if sender.is_worker:
        return

    await create_tables_if_not_exists()

    await send_db_predefined_data()


@reset_data_handler
async def documents_reset(sender):
    """
    Drop and recreate document-related database tables on reset.

    This handler, triggered by a reset event, drops and recreates all document-related database
    tables and their predefined data.
    """
    if sender.is_worker:
        return

    await drop_all_tables()

    await create_tables_if_not_exists()

    await send_db_predefined_data()
