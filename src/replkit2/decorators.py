from typing import Any, Callable, TypeVar

from .types import CommandMeta

T = TypeVar("T", bound=Callable[..., Any])


def command(
    func: T | None = None,
    *,
    display: str | None = None,
    aliases: list[str] | None = None,
    **display_opts: Any,
) -> T | Callable[[T], T]:
    """Mark method as REPL command with optional display hints.

    Can be used as:
        @command
        def my_command(): ...

        @command(display="table", headers=["Name", "Age"])
        def my_command(): ...
    """

    def decorator(f: T) -> T:
        meta = CommandMeta(display=display, display_opts=display_opts, aliases=aliases or [])
        setattr(f, "__command_meta__", meta)
        setattr(f, "__is_command__", True)
        return f

    # Handle both @command and @command(...) usage
    if func is not None:
        # Direct decoration: @command
        return decorator(func)
    else:
        # Factory pattern: @command(...)
        return decorator


def state(cls: type) -> type:
    """Mark class as stateful command container."""
    setattr(cls, "__is_state__", True)
    return cls
