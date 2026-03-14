from __future__ import annotations

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


def _parse_humanize(raw: str | None) -> bool | float:
    if raw is None:
        return False
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
    humanize: bool | float = False
    block_webrtc: bool = False
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
        return launch_kwargs

    def has_capability(self, name: str) -> bool:
        return name in self.caps
