from __future__ import annotations

import json
from argparse import Namespace
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal
from urllib.parse import unquote, urlparse

BrowserOs = Literal["windows", "macos", "linux"]

DEFAULT_USER_DATA_DIR = Path("~/.camoufox-mcp-python/profile")
SUPPORTED_CAPABILITIES = frozenset({"dangerous"})


def _split_repeated_csv(values: list[str] | None) -> list[str]:
    if not values:
        return []
    result: list[str] = []
    for value in values:
        for part in value.split(","):
            item = part.strip()
            if item:
                result.append(item)
    return result


def _normalize_scalar_or_list(values: list[str] | None) -> str | list[str] | None:
    normalized = _split_repeated_csv(values)
    if not normalized:
        return None
    if len(normalized) == 1:
        return normalized[0]
    return normalized


def _parse_humanize(raw: str | None, *, default: bool | float = True) -> bool | float:
    if raw is None:
        return default
    lowered = raw.strip().lower()
    if lowered in {"", "true", "yes", "on"}:
        return True
    if lowered in {"false", "no", "off"}:
        return False
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"Invalid --humanize value: {raw}") from exc
    if value < 0:
        raise ValueError("--humanize must be a positive number")
    return value


def _parse_geoip(raw: str | None) -> bool | str | None:
    if raw is None:
        return None
    lowered = raw.strip().lower()
    if lowered in {"", "true", "yes", "on"}:
        return True
    if lowered in {"false", "no", "off"}:
        return None
    return raw


def _parse_proxy(raw: str | None) -> dict[str, str] | None:
    if not raw:
        return None
    parsed = urlparse(raw)
    if not parsed.scheme or not parsed.hostname:
        return {"server": raw}
    server = f"{parsed.scheme}://{parsed.hostname}"
    if parsed.port:
        server = f"{server}:{parsed.port}"
    proxy: dict[str, str] = {"server": server}
    if parsed.username:
        proxy["username"] = unquote(parsed.username)
    if parsed.password:
        proxy["password"] = unquote(parsed.password)
    return proxy


def _parse_webgl_config(raw: str | None) -> tuple[str, str] | None:
    if not raw:
        return None
    parts = [part.strip() for part in raw.split(",", 1)]
    if len(parts) != 2 or not all(parts):
        raise ValueError("--webgl-config must be 'vendor,renderer'")
    return (parts[0], parts[1])


def _parse_json_dict(raw: str | None, name: str) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"--{name} must be valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"--{name} must be a JSON object")
    return value


def _parse_window(raw: str | None) -> tuple[int, int] | None:
    if not raw:
        return None
    normalized = raw.lower().replace("x", ",")
    parts = [part.strip() for part in normalized.split(",") if part.strip()]
    if len(parts) != 2:
        raise ValueError("--window must look like 1280x720 or 1280,720")
    width, height = (int(part) for part in parts)
    if width <= 0 or height <= 0:
        raise ValueError("--window values must be positive integers")
    return width, height


@dataclass(slots=True)
class CamoufoxConfig:
    proxy: dict[str, str] | None = None
    os: str | list[str] | None = None
    humanize: bool | float = True
    block_webrtc: bool = True
    block_webgl: bool = False
    block_images: bool = False
    disable_coop: bool = False
    geoip: bool | str | None = None
    headless: bool = False
    user_data_dir: Path = field(default_factory=lambda: DEFAULT_USER_DATA_DIR.expanduser())
    caps: frozenset[str] = field(default_factory=frozenset)
    locale: str | list[str] | None = None
    window: tuple[int, int] | None = None
    persistent_context: bool = True
    default_timeout_ms: int = 30_000
    navigation_timeout_ms: int = 30_000
    webgl_config: tuple[str, str] | None = None
    addons: list[str] | None = None
    exclude_addons: list[str] | None = None
    config: dict[str, Any] | None = None
    fingerprint: Any | None = None
    enable_cache: bool = False
    firefox_user_prefs: dict[str, Any] | None = None
    i_know_what_im_doing: bool = False
    debug: bool = False

    @classmethod
    def from_cli_args(cls, args: Namespace) -> CamoufoxConfig:
        caps = frozenset(_split_repeated_csv(args.caps))
        unknown_caps = sorted(caps - SUPPORTED_CAPABILITIES)
        if unknown_caps:
            supported = ", ".join(sorted(SUPPORTED_CAPABILITIES))
            raise ValueError(
                f"Unsupported capability values: {', '.join(unknown_caps)}. Supported values: {supported}."
            )

        return cls(
            proxy=_parse_proxy(args.proxy),
            os=_normalize_scalar_or_list(args.os),
            humanize=_parse_humanize(args.humanize),
            block_webrtc=args.block_webrtc,
            block_webgl=args.block_webgl,
            block_images=args.block_images,
            disable_coop=args.disable_coop,
            geoip=_parse_geoip(args.geoip),
            headless=args.headless,
            user_data_dir=Path(args.user_data_dir).expanduser(),
            caps=caps,
            locale=_normalize_scalar_or_list(args.locale),
            window=_parse_window(args.window),
            webgl_config=_parse_webgl_config(args.webgl_config),
            addons=_split_repeated_csv(args.addons) or None,
            exclude_addons=_split_repeated_csv(args.exclude_addons) or None,
            config=_parse_json_dict(args.config, "config"),
            enable_cache=args.enable_cache,
            firefox_user_prefs=_parse_json_dict(args.firefox_user_prefs, "firefox-user-prefs"),
            i_know_what_im_doing=args.i_know_what_im_doing,
            debug=args.debug,
        )

    def to_launch_kwargs(self) -> dict[str, Any]:
        launch_kwargs: dict[str, Any] = {
            "persistent_context": self.persistent_context,
            "headless": self.headless,
            "humanize": self.humanize,
        }
        if self.persistent_context:
            user_data_dir = self.user_data_dir.expanduser()
            user_data_dir.mkdir(parents=True, exist_ok=True)
            launch_kwargs["user_data_dir"] = str(user_data_dir)
        if self.proxy:
            launch_kwargs["proxy"] = dict(self.proxy)
        if self.os is not None:
            launch_kwargs["os"] = self.os
        if self.geoip is not None:
            launch_kwargs["geoip"] = self.geoip
        if self.locale is not None:
            launch_kwargs["locale"] = self.locale
        if self.window is not None:
            launch_kwargs["window"] = self.window
        if self.block_images:
            launch_kwargs["block_images"] = True
        if self.block_webrtc:
            launch_kwargs["block_webrtc"] = True
        if self.block_webgl:
            launch_kwargs["block_webgl"] = True
        if self.disable_coop:
            launch_kwargs["disable_coop"] = True
        if self.webgl_config is not None:
            launch_kwargs["webgl_config"] = self.webgl_config
        if self.addons is not None:
            launch_kwargs["addons"] = list(self.addons)
        if self.exclude_addons is not None:
            from camoufox.addons import DefaultAddons

            launch_kwargs["exclude_addons"] = [
                DefaultAddons[name] for name in self.exclude_addons
            ]
        if self.config is not None:
            launch_kwargs["config"] = dict(self.config)
        if self.fingerprint is not None:
            launch_kwargs["fingerprint"] = self.fingerprint
        if self.enable_cache:
            launch_kwargs["enable_cache"] = True
        if self.firefox_user_prefs is not None:
            launch_kwargs["firefox_user_prefs"] = dict(self.firefox_user_prefs)
        if self.i_know_what_im_doing:
            launch_kwargs["i_know_what_im_doing"] = True
        if self.debug:
            launch_kwargs["debug"] = True
        return launch_kwargs

    def has_capability(self, name: str) -> bool:
        return name in self.caps
