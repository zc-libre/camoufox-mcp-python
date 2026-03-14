from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ..config import CamoufoxConfig
from . import common_tools, dangerous_tools, file_tools, input_tools, navigate_tools, page_tools, snapshot_tools, tab_tools


def register_all(mcp: FastMCP, config: CamoufoxConfig) -> None:
    snapshot_tools.register(mcp)
    navigate_tools.register(mcp)
    tab_tools.register(mcp)
    input_tools.register(mcp)
    common_tools.register(mcp)
    page_tools.register(mcp)
    file_tools.register(mcp)
    dangerous_tools.register(mcp, config)
