"""
This module provides decorators
"""

import logging
import pprint
from typing import Any, Callable, Awaitable, Optional
import inspect

from langchain_core.documents import Document
from langchain_core.runnables import Runnable, RunnableLambda

from .agent_state import GraphState


logger = logging.getLogger(__name__)

class ReusableRunnable(Runnable):

    name = 'custom-runnable'

    def __init__(
        self,
        type_name: str,
        func: Optional[Callable[[GraphState], dict[str, Any]]] = None,
        afunc: Optional[Callable[[GraphState], Awaitable[dict[str, Any]]]] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.name = type_name
        self._type = type_name
        self.func = func
        self.afunc = afunc


    def invoke(self, input: GraphState, config: Optional[dict] = None, **kwargs) -> dict[str, Any]:
        logger.info('RUNNABLE INVOKE %s\nconfig: %r', self._type, config)
        if self.func is None:
            raise TypeError("No synchronous function (func) provided for invoke().")
        return self.func(input)


    async def ainvoke(self, input: GraphState, config: Optional[dict] = None, **kwargs) -> dict[str, Any]:
        logger.info('RUNNABLE AINVOKE %s\nconfig: %r', self._type, config)
        if self.afunc is None:
            raise TypeError("No asynchronous function (afunc) provided for ainvoke().")
        return await self.afunc(input)



def runnable(func):
    """
    Decorator or factory to create a ReusableRunnable from a sync or async function.
    Uses the function's name as type_name.
    """
    if func is not None:
        logger.info('DECORATE RUNNABLE\n%r', func)
        type_name = inspect.getattr_static(func, '__name__', 'anonymous')
        type_name = func.__name__
    else:
        raise ValueError("func must be provided.")
    return ReusableRunnable(type_name=type_name, func=func, afunc=None)

def arunnable(afunc):
    """
    Decorator or factory to create a ReusableRunnable from a sync or async function.
    Uses the function's name as type_name.
    """
    if afunc is not None:
        logger.info('DECORATE ARUNNABLE\n%r', afunc)
        type_name = inspect.getattr_static(afunc, '__name__', 'anonymous')
        type_name = afunc.__name__
    else:
        raise ValueError("afunc must be provided.")
    return ReusableRunnable(type_name=type_name, func=None, afunc=afunc)
