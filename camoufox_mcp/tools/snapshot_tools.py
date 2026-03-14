from typing import Literal

from mcp.server.fastmcp import Context, FastMCP
from mcp.types import TextContent

from ..response import Response
from .decorators import current_app, current_tab, tab_tool


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="browser_snapshot",
        description="Capture the current accessibility snapshot.",
        structured_output=False,
    )
    @tab_tool(block_on_modal=False)
    async def browser_snapshot(
        filename: str | None = None, ctx: Context | None = None
    ) -> list[TextContent]:
        app = current_app()
        tab = current_tab()
        response = Response()
        response.set_include_snapshot()
        if filename:
            response.add_event(f"- Ignored snapshot filename request: {filename}")
        return await response.serialize(app, tab)

    @mcp.tool(
        name="browser_click",
        description="Perform click on a web page.",
        structured_output=False,
    )
    @tab_tool()
    async def browser_click(
        ref: str,
        element: str | None = None,
        doubleClick: bool | None = None,
        button: Literal["left", "right", "middle"] | None = None,
        modifiers: list[Literal["Alt", "Control", "ControlOrMeta", "Meta", "Shift"]]
        | None = None,
        ctx: Context | None = None,
    ) -> list[TextContent]:
        app = current_app()
        tab = current_tab()
        locator = await tab.ref_locator(ref, element)
        response = Response()
        response.set_include_snapshot()

        async def action() -> None:
            options = {"button": button, "modifiers": modifiers}
            clean_options = {key: value for key, value in options.items() if value is not None}
            if doubleClick:
                await locator.dblclick(**clean_options)
            else:
                await locator.click(**clean_options)

        await tab.wait_for_completion(action)
        response.add_result(f"Clicked {element or ref}.")
        return await response.serialize(app, tab)

    @mcp.tool(
        name="browser_hover",
        description="Hover over a web page element.",
        structured_output=False,
    )
    @tab_tool()
    async def browser_hover(
        ref: str,
        element: str | None = None,
        ctx: Context | None = None,
    ) -> list[TextContent]:
        app = current_app()
        tab = current_tab()
        locator = await tab.ref_locator(ref, element)
        response = Response()
        response.set_include_snapshot()
        await tab.wait_for_completion(locator.hover)
        response.add_result(f"Hovered {element or ref}.")
        return await response.serialize(app, tab)

    @mcp.tool(
        name="browser_drag",
        description="Drag from one ref to another.",
        structured_output=False,
    )
    @tab_tool()
    async def browser_drag(
        startRef: str,
        endRef: str,
        startElement: str,
        endElement: str,
        ctx: Context | None = None,
    ) -> list[TextContent]:
        app = current_app()
        tab = current_tab()
        start = await tab.ref_locator(startRef, startElement)
        end = await tab.ref_locator(endRef, endElement)
        response = Response()
        response.set_include_snapshot()
        await tab.wait_for_completion(lambda: start.drag_to(end))
        response.add_result(f"Dragged {startElement} to {endElement}.")
        return await response.serialize(app, tab)

    @mcp.tool(
        name="browser_select_option",
        description="Select one or more values in a dropdown.",
        structured_output=False,
    )
    @tab_tool()
    async def browser_select_option(
        ref: str,
        values: list[str],
        element: str | None = None,
        ctx: Context | None = None,
    ) -> list[TextContent]:
        app = current_app()
        tab = current_tab()
        locator = await tab.ref_locator(ref, element)
        response = Response()
        response.set_include_snapshot()
        await tab.wait_for_completion(lambda: locator.select_option(values))
        response.add_result(f"Selected {len(values)} option(s) for {element or ref}.")
        return await response.serialize(app, tab)
