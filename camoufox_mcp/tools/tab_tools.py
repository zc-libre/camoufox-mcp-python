from typing import Literal

from mcp.server.fastmcp import Context, FastMCP
from mcp.types import TextContent

from ..response import Response, render_tabs_markdown
from .decorators import browser_tool, current_app


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="browser_tabs",
        description="List, create, close, or select a browser tab.",
        structured_output=False,
    )
    @browser_tool
    async def browser_tabs(
        action: Literal["list", "new", "close", "select"],
        index: int | None = None,
        ctx: Context | None = None,
    ) -> list[TextContent]:
        app = current_app()
        response = Response()
        if action == "list":
            if not app.tabs():
                await app.ensure_tab()
        elif action == "new":
            await app.new_tab()
        elif action == "close":
            await app.close_tab(index)
        elif action == "select":
            if index is None:
                raise RuntimeError("Tab index is required for select.")
            await app.select_tab(index)

        response.add_result("\n".join(render_tabs_markdown(await app.tab_headers())))
        return await response.serialize(app, app.current_tab())
