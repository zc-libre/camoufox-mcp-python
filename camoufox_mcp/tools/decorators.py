from __future__ import annotations

import inspect
from contextvars import ContextVar
from functools import wraps
from typing import Any, Callable, TypeVar

from mcp.server.fastmcp import Context

from ..context import AppContext
from ..response import Response
from ..tab import Tab

F = TypeVar("F", bound=Callable[..., Any])

_CURRENT_APP: ContextVar[AppContext | None] = ContextVar("current_app", default=None)
_CURRENT_TAB: ContextVar[Tab | None] = ContextVar("current_tab", default=None)


def current_app() -> AppContext:
    app = _CURRENT_APP.get()
    if app is None:
        raise RuntimeError("App context is unavailable outside of a running tool.")
    return app


def current_tab() -> Tab:
    tab = _CURRENT_TAB.get()
    if tab is None:
        raise RuntimeError("Tab context is unavailable outside of a tab-bound tool.")
    return tab


def browser_tool(fn: F) -> F:
    signature = inspect.signature(fn)

    @wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        bound = signature.bind_partial(*args, **kwargs)
        ctx = _extract_context(bound.arguments)
        app = ctx.request_context.lifespan_context
        token = _CURRENT_APP.set(app)
        try:
            async with app.operation_lock:
                try:
                    return await fn(*args, **kwargs)
                except Exception as exc:
                    response = Response()
                    response.add_error(str(exc))
                    return await response.serialize(app, app.current_tab())
        finally:
            _CURRENT_APP.reset(token)

    wrapper.__signature__ = signature
    return wrapper  # type: ignore[return-value]


def tab_tool(*, block_on_modal: bool = True) -> Callable[[F], F]:
    def decorator(fn: F) -> F:
        signature = inspect.signature(fn)

        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            bound = signature.bind_partial(*args, **kwargs)
            ctx = _extract_context(bound.arguments)
            app = ctx.request_context.lifespan_context
            async with app.operation_lock:
                tab = await app.ensure_tab()
                app_token = _CURRENT_APP.set(app)
                tab_token = _CURRENT_TAB.set(tab)
                try:
                    if block_on_modal and tab.modal_states():
                        response = Response()
                        response.add_error(
                            f'Tool "{fn.__name__}" does not handle the current modal state.'
                        )
                        return await response.serialize(app, tab)
                    try:
                        return await fn(*args, **kwargs)
                    except Exception as exc:
                        response = Response()
                        response.add_error(str(exc))
                        return await response.serialize(app, tab)
                finally:
                    _CURRENT_TAB.reset(tab_token)
                    _CURRENT_APP.reset(app_token)

        wrapper.__signature__ = signature
        return wrapper  # type: ignore[return-value]

    return decorator


def _extract_context(arguments: dict[str, Any]) -> Context:
    for value in arguments.values():
        if isinstance(value, Context):
            return value
    raise RuntimeError("FastMCP context argument is required.")
