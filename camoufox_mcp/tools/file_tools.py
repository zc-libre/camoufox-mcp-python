from mcp.server.fastmcp import Context, FastMCP
from mcp.types import TextContent

from ..response import Response
from .decorators import current_app, current_tab, tab_tool


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="browser_file_upload",
        description="Handle an active file chooser.",
        structured_output=False,
    )
    @tab_tool(block_on_modal=False)
    async def browser_file_upload(
        paths: list[str] | None = None, ctx: Context | None = None
    ) -> list[TextContent]:
        app = current_app()
        tab = current_tab()
        modal = next((state for state in tab.modal_states() if state.type == "fileChooser"), None)
        if modal is None or modal.file_chooser is None:
            raise RuntimeError("No file chooser visible.")
        tab.clear_modal_state(modal)
        response = Response()
        response.set_include_snapshot()
        await tab.wait_for_completion(lambda: modal.file_chooser.set_files(paths or []))
        response.add_result(
            f"Updated file chooser with {len(paths or [])} file(s)."
        )
        return await response.serialize(app, tab)

    @mcp.tool(
        name="browser_handle_dialog",
        description="Accept or dismiss an active dialog.",
        structured_output=False,
    )
    @tab_tool(block_on_modal=False)
    async def browser_handle_dialog(
        accept: bool, promptText: str | None = None, ctx: Context | None = None
    ) -> list[TextContent]:
        app = current_app()
        tab = current_tab()
        modal = next((state for state in tab.modal_states() if state.type == "dialog"), None)
        if modal is None or modal.dialog is None:
            raise RuntimeError("No dialog visible.")
        tab.clear_modal_state(modal)
        response = Response()
        response.set_include_snapshot()

        async def action() -> None:
            if accept:
                await modal.dialog.accept(promptText)
            else:
                await modal.dialog.dismiss()

        await tab.wait_for_completion(action)
        response.add_result("Handled dialog.")
        return await response.serialize(app, tab)
