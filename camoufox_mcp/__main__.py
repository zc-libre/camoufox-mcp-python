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
        help="Cursor humanization (default: on). Pass a number for max duration in seconds, or 'false' to disable.",
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
    parser.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run the browser headlessly (default: on).",
    )
    parser.add_argument(
        "--block-webrtc",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Disable WebRTC to reduce leaks (default: on).",
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
        help="Optional persistent profile directory. If omitted, each server process creates an isolated temporary profile and deletes it on exit.",
    )
    parser.add_argument(
        "--caps",
        action="append",
        help="Optional comma-separated capability groups to enable. Currently: dangerous.",
    )
    parser.add_argument(
        "--webgl-config",
        help="WebGL vendor/renderer pair, e.g. 'Intel Inc.,Intel(R) UHD Graphics 620'.",
    )
    parser.add_argument(
        "--addons",
        action="append",
        help="Paths to extracted Firefox addons. Repeat or comma-separate for multiple.",
    )
    parser.add_argument(
        "--exclude-addons",
        action="append",
        help="Default addons to exclude, e.g. UBO. Repeat or comma-separate for multiple.",
    )
    parser.add_argument(
        "--config",
        help="Camoufox fingerprint properties as a JSON string.",
    )
    parser.add_argument(
        "--enable-cache",
        action="store_true",
        help="Cache previous pages and requests (uses more memory).",
    )
    parser.add_argument(
        "--firefox-user-prefs",
        help="Firefox user preferences as a JSON string.",
    )
    parser.add_argument(
        "--i-know-what-im-doing",
        action="store_true",
        help="Silence Camoufox warnings for advanced configurations.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print the config being sent to Camoufox.",
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
