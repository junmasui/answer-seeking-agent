"""
This module implements application-specific signalling.

Each component should be responsible for knowing it is should
do processing upon start-up or reset-all-data event. This knowledge should not
be centralized since it depends on each component's internals.
Decentralization then requires broadcasting those important events.

This module also acts to insulate our application-specific signals
from already existing framework-specific signals. Both FastAPI and Celery
also have signals, but those frameworks are not in every node.
"""

import logging
from functools import cache

from blinker import signal
from pydantic import BaseModel

logger = logging.getLogger(__name__)

_START_UP = signal('start-up')
_DB_READY_FOR_PREDEFINED_DATA = signal('db-predefined-data')
_RESET_DATA = signal('reset-data')


def start_up_handler(receiver):
    """Registers the reciever as a start-up handler.

    This can be used as a decorater, for better readability.
    """
    return _START_UP.connect(receiver=receiver)


def db_predefined_data_handler(receiver):
    """Registers the reciever as a db-ready-for-predefined-data handler.

    This can be used as a decorater, for better readability.
    """
    return _DB_READY_FOR_PREDEFINED_DATA.connect(receiver=receiver)


def reset_data_handler(receiver):
    """Registers the reciever as a reset-data handler.

    This can be used as a decorater, for better readability.
    """
    return _RESET_DATA.connect(receiver=receiver)


class Sender(BaseModel):
    is_worker: bool = False


@cache
def _get_sender():
    sender = Sender()
    return sender


def configure_sender(*, is_worker: bool):
    sender = _get_sender()
    sender.is_worker = is_worker


def send_start_up():
    """Send the start-up signal"""
    logger.info('Sending start-up signal')

    sender = _get_sender()
    _START_UP.send(sender)


def send_db_predefined_data():
    """Send the db-predefined-data signal.

    This signal is sent after the database schema is updated or created
    and the database is ready to accept predefined data.
    """
    logger.info('Sending db-predefined-data signal')

    sender = _get_sender()
    logger.info('Sender %s', sender.is_worker)

    results = _DB_READY_FOR_PREDEFINED_DATA.send(sender)

    results = [(getattr(f, '__name__', f), x) for f, x in results]

    logger.info('Sent db-predefined-data signal: %s', results)


def send_reset_data():
    """Send the reset-data signal"""
    logger.info('Sending reset-data signal')

    sender = _get_sender()
    _RESET_DATA.send(sender)
