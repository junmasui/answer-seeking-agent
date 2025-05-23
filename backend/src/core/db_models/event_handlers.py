import logging

from .model_ops import create_tables_if_not_exists, drop_all_tables

from ..signals import start_up_handler, reset_data_handler, send_db_predefined_data


logger = logging.getLogger(__name__)


@start_up_handler
def documents_startup(sender):
    if sender.is_worker:
        return

    create_tables_if_not_exists()

    send_db_predefined_data()


@reset_data_handler
def documents_reset(sender):
    if sender.is_worker:
        return

    drop_all_tables()

    create_tables_if_not_exists()

    send_db_predefined_data()
