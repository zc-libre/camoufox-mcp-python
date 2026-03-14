from __future__ import annotations

from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from .config import CamoufoxConfig
from .context import AppContext
from .tools import register_all


def create_server(config: CamoufoxConfig) -> FastMCP[AppContext]:
    @asynccontextmanager
    async def lifespan(_: FastMCP[AppContext]):
        app = AppContext(config)
        try:
            yield app
        finally:
            await app.close()

    mcp = FastMCP(
        "camoufox-mcp-python",
        instructions=(
            "Camoufox anti-detect browser automation over MCP using accessibility snapshots and ref-based actions."
        ),
        lifespan=lifespan,
    )
    register_all(mcp, config)
    return mcp
