from typing import Literal

from mcp.server.fastmcp import Context, FastMCP
from mcp.types import TextContent
from pydantic import BaseModel, Field

from ..response import Response
from .decorators import current_app, current_tab, tab_tool


class FormField(BaseModel):
    name: str = Field(description="Human-readable field name")
    type: Literal["textbox", "checkbox", "radio", "combobox", "slider"] = Field(
        description="Type of the field"
    )
    ref: str = Field(description="Exact target field reference from the page snapshot")
    value: str = Field(description="Value to write or select")


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="browser_type",
        description="Type text into an editable element.",
        structured_output=False,
    )
    @tab_tool()
    async def browser_type(
        ref: str,
        text: str,
        element: str | None = None,
        submit: bool | None = None,
        slowly: bool | None = None,
        ctx: Context | None = None,
    ) -> list[TextContent]:
        app = current_app()
        tab = current_tab()
        locator = await tab.ref_locator(ref, element)
        response = Response()
        response.set_include_snapshot()

        async def action() -> None:
            if slowly:
                await locator.press_sequentially(text)
            else:
                await locator.fill(text)
            if submit:
                await locator.press("Enter")

        await tab.wait_for_completion(action)
        response.add_result(f"Typed into {element or ref}.")
        return await response.serialize(app, tab)

    @mcp.tool(
        name="browser_press_key",
        description="Press a key on the keyboard.",
        structured_output=False,
    )
    @tab_tool()
    async def browser_press_key(
        key: str, ctx: Context | None = None
    ) -> list[TextContent]:
        app = current_app()
        tab = current_tab()
        response = Response()
        response.set_include_snapshot()
        await tab.wait_for_completion(lambda: tab.page.keyboard.press(key))
        response.add_result(f"Pressed key {key}.")
        return await response.serialize(app, tab)

    @mcp.tool(
        name="browser_fill_form",
        description="Fill multiple form fields in one call.",
        structured_output=False,
    )
    @tab_tool()
    async def browser_fill_form(
        fields: list[FormField], ctx: Context | None = None
    ) -> list[TextContent]:
        app = current_app()
        tab = current_tab()
        response = Response()
        response.set_include_snapshot()

        async def action() -> None:
            for field in fields:
                locator = await tab.ref_locator(field.ref, field.name)
                if field.type in {"textbox", "slider"}:
                    await locator.fill(field.value)
                elif field.type in {"checkbox", "radio"}:
                    await locator.set_checked(field.value.lower() == "true")
                elif field.type == "combobox":
                    await locator.select_option(label=field.value)

        await tab.wait_for_completion(action)
        response.add_result(f"Filled {len(fields)} field(s).")
        return await response.serialize(app, tab)
