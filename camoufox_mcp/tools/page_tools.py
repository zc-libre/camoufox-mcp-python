from typing import Literal

from mcp.server.fastmcp import Context, FastMCP
from mcp.types import ImageContent, TextContent

from ..response import Response
from ..tab import ConsoleLevel
from .decorators import current_app, current_tab, tab_tool


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="browser_take_screenshot",
        description="Take a screenshot of the viewport, full page, or a referenced element.",
        structured_output=False,
    )
    @tab_tool(block_on_modal=False)
    async def browser_take_screenshot(
        type: Literal["png", "jpeg"] = "png",
        filename: str | None = None,
        element: str | None = None,
        ref: str | None = None,
        fullPage: bool | None = None,
        ctx: Context | None = None,
    ) -> list[TextContent | ImageContent]:
        app = current_app()
        tab = current_tab()
        if fullPage and ref:
            raise RuntimeError("full_page cannot be combined with element screenshots.")

        options: dict[str, object] = {"type": type}
        if type == "jpeg":
            options["quality"] = 90
        if fullPage is not None:
            options["full_page"] = fullPage

        if ref:
            locator = await tab.ref_locator(ref, element)
            data = await locator.screenshot(**options)
            target = element or ref
        else:
            data = await tab.page.screenshot(**options)
            target = "full page" if fullPage else "viewport"

        response = Response()
        response.add_result(f"Captured screenshot of {target}.")
        if filename:
            response.add_event(f"- Ignored screenshot filename request: {filename}")
        response.add_image(data, f"image/{type}")
        return await response.serialize(app, tab)

    @mcp.tool(
        name="browser_console_messages",
        description="Return collected console messages.",
        structured_output=False,
    )
    @tab_tool(block_on_modal=False)
    async def browser_console_messages(
        level: ConsoleLevel = "info",
        filename: str | None = None,
        ctx: Context | None = None,
    ) -> list[TextContent]:
        app = current_app()
        tab = current_tab()
        response = Response()
        counts = tab.console_message_count()
        messages = tab.console_messages(level)
        body = [
            f"Total messages: {counts['total']} (Errors: {counts['errors']}, Warnings: {counts['warnings']})"
        ]
        if messages:
            body.append("")
            body.extend(message.render() for message in messages)
        if filename:
            body.append("")
            body.append(f"Ignored filename request: {filename}")
        response.add_result("\n".join(body))
        return await response.serialize(app, tab)

    @mcp.tool(
        name="browser_network_requests",
        description="List network requests seen by the page.",
        structured_output=False,
    )
    @tab_tool(block_on_modal=False)
    async def browser_network_requests(
        includeStatic: bool = False,
        filename: str | None = None,
        ctx: Context | None = None,
    ) -> list[TextContent]:
        app = current_app()
        tab = current_tab()
        response = Response()
        requests = await tab.render_network_requests(include_static=includeStatic)
        if filename:
            requests.append(f"Ignored filename request: {filename}")
        response.add_result("\n".join(requests) if requests else "No recorded network requests.")
        return await response.serialize(app, tab)
