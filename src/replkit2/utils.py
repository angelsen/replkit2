"""Utility functions for ReplKit2.

This module provides helper functions for context injection and other
common operations.
"""

from __future__ import annotations

import inspect
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from replkit2.types.context import ExecutionContext


@lru_cache(maxsize=256)
def accepts_context(func: Callable) -> bool:
    """Check if a function accepts an ExecutionContext parameter.

    Inspects the function signature for a parameter named '_ctx'.
    Results are cached (LRU, max 256 entries) for performance.

    Args:
        func: Function to inspect

    Returns:
        True if function has _ctx parameter, False otherwise

    Example:
        >>> def my_func(state, param: str, _ctx: ExecutionContext = None):
        ...     pass
        >>> accepts_context(my_func)
        True
        >>> def other_func(state, param: str):
        ...     pass
        >>> accepts_context(other_func)
        False
    """
    try:
        sig = inspect.signature(func)
        return "_ctx" in sig.parameters
    except (ValueError, TypeError):
        # If signature inspection fails, assume no context
        return False


def inject_context(kwargs: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
    """Inject ExecutionContext into kwargs if not already present.

    Creates a new dictionary with the context added. If _ctx is already
    in kwargs, returns kwargs unchanged (respects explicit overrides).

    Args:
        kwargs: Keyword arguments dictionary
        context: ExecutionContext to inject

    Returns:
        New dictionary with _ctx added if not present, otherwise original dict

    Example:
        >>> ctx = ExecutionContext.for_repl()
        >>> kwargs = {"param1": "value1"}
        >>> inject_context(kwargs, ctx)
        {'param1': 'value1', '_ctx': ExecutionContext(...)}
    """
    if "_ctx" in kwargs:
        # Context already present, don't override
        return kwargs

    # Create new dict with context injected
    return {**kwargs, "_ctx": context}
