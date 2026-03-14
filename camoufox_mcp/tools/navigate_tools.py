from urllib.parse import urlparse

from mcp.server.fastmcp import Context, FastMCP
from mcp.types import TextContent

from ..response import Response
from .decorators import current_app, current_tab, tab_tool


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="browser_navigate",
        description="Navigate to a URL.",
        structured_output=False,
    )
    @tab_tool()
    async def browser_navigate(url: str, ctx: Context | None = None) -> list[TextContent]:
        app = current_app()
        tab = current_tab()
        response = Response()
        response.set_include_snapshot()
        target = _normalize_url(url)
        await tab.wait_for_completion(
            lambda: tab.page.goto(target, wait_until="domcontentloaded")
        )
        response.add_result(f"Navigated to {target}.")
        return await response.serialize(app, tab)

    @mcp.tool(
        name="browser_navigate_back",
        description="Go back to the previous page.",
        structured_output=False,
    )
    @tab_tool()
    async def browser_navigate_back(ctx: Context | None = None) -> list[TextContent]:
        app = current_app()
        tab = current_tab()
        response = Response()
        response.set_include_snapshot()
        await tab.wait_for_completion(tab.page.go_back)
        response.add_result("Navigated back.")
        return await response.serialize(app, tab)


def _normalize_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme:
        return url
    if url.startswith("localhost"):
        return f"http://{url}"
    return f"https://{url}"
