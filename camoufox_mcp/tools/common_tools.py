import asyncio

from mcp.server.fastmcp import Context, FastMCP
from mcp.types import TextContent

from ..response import Response, render_tabs_markdown
from .decorators import browser_tool, current_app, current_tab, tab_tool


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="browser_close",
        description="Close the current browser session.",
        structured_output=False,
    )
    @browser_tool
    async def browser_close(ctx: Context | None = None) -> list[TextContent]:
        app = current_app()
        response = Response()
        await app.close_browser()
        response.add_result("\n".join(render_tabs_markdown([])))
        return await response.serialize(app, None)

    @mcp.tool(
        name="browser_resize",
        description="Resize the current page viewport.",
        structured_output=False,
    )
    @tab_tool()
    async def browser_resize(
        width: int, height: int, ctx: Context | None = None
    ) -> list[TextContent]:
        app = current_app()
        tab = current_tab()
        response = Response()
        response.set_include_snapshot()
        await tab.page.set_viewport_size({"width": width, "height": height})
        response.add_result(f"Resized viewport to {width}x{height}.")
        return await response.serialize(app, tab)

    @mcp.tool(
        name="browser_wait_for",
        description="Wait for text to appear or disappear, or for a fixed duration.",
        structured_output=False,
    )
    @tab_tool(block_on_modal=False)
    async def browser_wait_for(
        time: float | None = None,
        text: str | None = None,
        textGone: str | None = None,
        ctx: Context | None = None,
    ) -> list[TextContent]:
        app = current_app()
        tab = current_tab()
        if time is None and text is None and textGone is None:
            raise RuntimeError("Provide at least one of time, text, or text_gone.")

        if time is not None:
            await asyncio.sleep(min(time, 30.0))
        if textGone:
            await tab.page.get_by_text(textGone).first.wait_for(state="hidden")
        if text:
            await tab.page.get_by_text(text).first.wait_for(state="visible")

        response = Response()
        response.set_include_snapshot()
        response.add_result(
            f"Waited for {text or textGone or f'{time} second(s)'}."
        )
        return await response.serialize(app, tab)
