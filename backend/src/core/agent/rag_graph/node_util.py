import logging

from .agent_state import GraphState
from .decorator_util import runnable

logger = logging.getLogger(__name__)


def no_op(banner_msg):
    """
    Create a logging only node.

    This is useful for defining a fan-out or a fan-in node.
    """

    @runnable
    def _no_op(_state: GraphState):
        """Does nothing other than log."""
        logger.info('---%s---', banner_msg)
        return {}

    return _no_op
