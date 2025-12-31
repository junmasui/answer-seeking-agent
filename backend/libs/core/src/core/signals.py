"""
This module implements application-specific signalling.

Each component should be responsible for knowing it is should do processing upon start-up or reset-
all-data event. This knowledge should not be centralized since it depends on each component's
internals. Decentralization then requires broadcasting those important events.

This module also acts to insulate our application-specific signals from already existing framework-
specific signals. Both FastAPI and Celery also have signals, but those frameworks are not in every
node.
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
    """
    Register a receiver function as a start-up signal handler.

    This decorator registers the receiver to be called when the application sends a start-up signal.
    Can be used as a decorator for better readability.
    """
    return _START_UP.connect(receiver=receiver)


def db_predefined_data_handler(receiver):
    """
    Register a receiver function as a database predefined data handler.

    This decorator registers the receiver to be called when the database is ready to accept
    predefined data after schema initialization.
    """
    return _DB_READY_FOR_PREDEFINED_DATA.connect(receiver=receiver)


def reset_data_handler(receiver):
    """
    Register a receiver function as a reset data signal handler.

    This decorator registers the receiver to be called when the application sends a reset-data
    signal to clean up and reinitialize data stores.
    """
    return _RESET_DATA.connect(receiver=receiver)


class Sender(BaseModel):
    """
    Represents the sender of application signals.

    Attributes:
        is_worker: A boolean indicating whether the signal originates from a worker process.
                   Defaults to False.

    """

    is_worker: bool = False

import inspect


@cache
def _get_sender():
    """Get the cached sender instance for application signals."""
    sender = Sender()
    return sender


def configure_sender(*, is_worker: bool):
    """Configure the signal sender to indicate whether it's from a worker process."""
    sender = _get_sender()
    sender.is_worker = is_worker


async def send_start_up():
    """Send the start-up signal."""
    logger.info('Sending start-up signal')

    sender = _get_sender()
    results = _START_UP.send(sender)

    for _, response in results:
        await response


async def send_db_predefined_data():
    """
    Send the db-predefined-data signal.

    This signal is sent after the database schema is updated or created and the database is ready to
    accept predefined data like initial prompts.
    """
    logger.info('Sending db-predefined-data signal')

    sender = _get_sender()
    logger.info('Sender %s', sender.is_worker)

    results = _DB_READY_FOR_PREDEFINED_DATA.send(sender)

    for _, response in results:
        await response

    logger.info('Sent db-predefined-data signal')


async def send_reset_data():
    """Send the reset-data signal."""
    logger.info('Sending reset-data signal')

    sender = _get_sender()
    results = _RESET_DATA.send(sender)

    for _, response in results:
        await response
