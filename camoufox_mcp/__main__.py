from __future__ import annotations

import argparse
from collections.abc import Sequence

from .config import CamoufoxConfig
from .server import create_server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="camoufox-mcp-python",
        description="Camoufox-backed MCP server over STDIO.",
    )
    parser.add_argument("--proxy", help="Proxy server URL, optionally including credentials.")
    parser.add_argument(
        "--os",
        action="append",
        help="Target browser OS: windows, macos, linux. Repeat or comma-separate for multiple values.",
    )
    parser.add_argument(
        "--humanize",
        nargs="?",
        const="true",
        help="Enable cursor humanization, or pass a max duration in seconds.",
    )
    parser.add_argument(
        "--geoip",
        nargs="?",
        const="true",
        help="Enable GeoIP auto-matching or provide a target IP address.",
    )
    parser.add_argument(
        "--locale",
        action="append",
        help="Locale or comma-separated locales to pass into Camoufox.",
    )
    parser.add_argument(
        "--window",
        help="Outer window size, for example 1280x720.",
    )
    parser.add_argument("--headless", action="store_true", help="Run the browser headlessly.")
    parser.add_argument(
        "--block-webrtc", action="store_true", help="Disable WebRTC to reduce leaks."
    )
    parser.add_argument(
        "--block-webgl", action="store_true", help="Disable WebGL for special cases."
    )
    parser.add_argument(
        "--block-images", action="store_true", help="Block image requests to reduce bandwidth."
    )
    parser.add_argument(
        "--disable-coop",
        action="store_true",
        help="Disable COOP to allow interactions inside cross-origin iframes.",
    )
    parser.add_argument(
        "--user-data-dir",
        default="~/.camoufox-mcp-python/profile",
        help="Persistent profile directory. Defaults to ~/.camoufox-mcp-python/profile.",
    )
    parser.add_argument(
        "--caps",
        action="append",
        help="Optional comma-separated capability groups to enable. Currently: dangerous.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = CamoufoxConfig.from_cli_args(args)
    server = create_server(config)
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
