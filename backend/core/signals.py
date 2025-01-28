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
from functools import cache
from blinker import signal
from pydantic import BaseModel

_START_UP = signal('start-up')
_RESET_DATA = signal('reset-data')


def start_up_handler(receiver):
    """Registers the reciever as a start-up handler.

    This can be used as a decorater, for better readability.
    """
    return _START_UP.connect(receiver=receiver)


def reset_data_handler(receiver):
    """Registers the reciever as a reset-data handler.

    This can be used as a decorater, for better readability.
    """
    return _RESET_DATA.connect(receiver=receiver)


class Sender(BaseModel):
    is_worker: bool

@cache
def _get_sender(is_worker: bool):
    sender = Sender(is_worker=is_worker)
    return sender


def send_start_up(is_worker: bool):
    """Send the start-up signal
    """
    sender = _get_sender(is_worker)
    _START_UP.send(sender)


def send_reset_data(is_worker: bool):
    """Send the reset-data signal
    """
    sender = _get_sender(is_worker)
    _RESET_DATA.send(sender)
