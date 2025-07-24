"""
This module provides decorators and utility classes for wrapping synchronous and asynchronous
functions as LangChain Runnables. Use these wrappers to integrate custom logic with LangChain's
execution framework. Both synchronous and asynchronous workflows are supported.
"""

import logging
from typing import Any, Awaitable, Callable, Optional

from langchain_core.runnables import Runnable

from .agent_state import GraphState

logger = logging.getLogger(__name__)


class ReusableRunnable(Runnable):
    """Runnable wrapper for synchronous functions operating on GraphState."""

    name = 'custom-runnable'

    def __init__(self, type_name: str, func: Optional[Callable[[GraphState], dict[str, Any]]] = None, **kwargs):
        """
        Initialize a ReusableRunnable.

        Args:
            type_name (str): Name/type for the runnable.
            func (Callable): Synchronous function to wrap.
            **kwargs: Additional keyword arguments for Runnable.

        """
        super().__init__(**kwargs)
        self.name = type_name
        self._type = type_name
        self.func = func

    def invoke(self, input: GraphState, config: Optional[dict] = None, **kwargs) -> dict[str, Any]:
        """
        Invoke the wrapped synchronous function.

        Args:
            input (GraphState): Input state.
            config (dict, optional): Optional config.
            **kwargs: Additional arguments.

        Returns:
            dict[str, Any]: Output from the wrapped function.

        """
        if self.func is None:
            raise TypeError('No synchronous function (func) provided for invoke().')
        return self.func(input)


class AsyncReusableRunnable(Runnable):
    """Runnable wrapper for asynchronous functions operating on GraphState."""

    name = 'custom-async-runnable'

    def __init__(
        self, type_name: str, afunc: Optional[Callable[[GraphState], Awaitable[dict[str, Any]]]] = None, **kwargs
    ):
        """
        Initialize an AsyncReusableRunnable.

        Args:
            type_name (str): Name/type for the runnable.
            afunc (Callable): Asynchronous function to wrap.
            **kwargs: Additional keyword arguments for Runnable.

        """
        super().__init__(**kwargs)
        self.name = type_name
        self._type = type_name
        self.afunc = afunc

    def invoke(self, input: GraphState, config: Optional[dict] = None, **kwargs) -> dict[str, Any]:
        """Synchronous invoke is not implemented for AsyncReusableRunnable."""
        raise NotImplementedError('No synchronous function (func) implemented for invoke().')

    async def ainvoke(self, input: GraphState, config: Optional[dict] = None, **kwargs) -> dict[str, Any]:
        """
        Invoke the wrapped asynchronous function.

        Args:
            input (GraphState): Input state.
            config (dict, optional): Optional config.
            **kwargs: Additional arguments.

        Returns:
            dict[str, Any]: Output from the wrapped async function.

        """
        if self.afunc is None:
            raise TypeError('No asynchronous function (afunc) provided for ainvoke().')
        return await self.afunc(input)


def runnable(func):
    """
    Decorator or factory to create a ReusableRunnable from a synchronous function.

    Args:
        func (Callable): Synchronous function to wrap.

    Returns:
        ReusableRunnable: Runnable wrapper for the function.

    """
    if func is not None:
        type_name = func.__name__
    else:
        raise ValueError('func must be provided.')
    return ReusableRunnable(type_name=type_name, func=func)


def arunnable(afunc):
    """
    Decorator or factory to create an AsyncReusableRunnable from an asynchronous function.

    Args:
        afunc (Callable): Asynchronous function to wrap.

    Returns:
        AsyncReusableRunnable: Runnable wrapper for the async function.

    """
    if afunc is not None:
        type_name = afunc.__name__
    else:
        raise ValueError('afunc must be provided.')
    return AsyncReusableRunnable(type_name=type_name, afunc=afunc)
