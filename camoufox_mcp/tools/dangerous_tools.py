from mcp.server.fastmcp import Context, FastMCP
from mcp.types import TextContent

from ..config import CamoufoxConfig
from ..response import Response
from ..tab import Tab
from .decorators import current_app, current_tab, tab_tool


def register(mcp: FastMCP, config: CamoufoxConfig) -> None:
    if not config.has_capability("dangerous"):
        return

    @mcp.tool(
        name="browser_evaluate",
        description="Evaluate JavaScript on the page or a referenced element.",
        structured_output=False,
    )
    @tab_tool()
    async def browser_evaluate(
        function: str,
        element: str | None = None,
        ref: str | None = None,
        ctx: Context | None = None,
    ) -> list[TextContent]:
        app = current_app()
        tab = current_tab()
        response = Response()
        response.set_include_snapshot()
        source = function if "=>" in function else f"() => ({function})"
        holder: dict[str, object] = {}

        async def action() -> None:
            receiver: Tab | object
            if ref is not None:
                locator = await tab.ref_locator(ref, element)
                holder["result"] = await locator.evaluate(source)
            else:
                holder["result"] = await tab.page.evaluate(source)

        await tab.wait_for_completion(action)
        response.add_result(Tab.serialize_value(holder.get("result")))
        return await response.serialize(app, tab)
