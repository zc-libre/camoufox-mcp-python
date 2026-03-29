from __future__ import annotations

import asyncio
import json
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any

from camoufox.async_api import AsyncNewBrowser
from camoufox.pkgman import INSTALL_DIR
from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from .config import CamoufoxConfig
from .snapshot import snapshot_for_ai
from .tab import Tab, TabHeader


class AppContext:
    def __init__(self, config: CamoufoxConfig):
        self.config = config
        self.operation_lock = asyncio.Lock()
        self._playwright: Any | None = None
        self._browser: Browser | None = None
        self._browser_context: BrowserContext | None = None
        self._ephemeral_user_data_dir: tempfile.TemporaryDirectory[str] | None = None
        self._tabs: list[Tab] = []
        self._current_tab_index: int | None = None

    async def ensure_browser(self) -> BrowserContext:
        if self._browser_context is not None:
            self._sync_existing_pages()
            return self._browser_context

        self._cleanup_ephemeral_user_data_dir()
        _repair_camoufox_install_layout()
        self._playwright = await async_playwright().start()
        launch_kwargs = self.config.to_launch_kwargs(
            user_data_dir=self._resolve_user_data_dir()
        )
        try:
            launched = await AsyncNewBrowser(self._playwright, **launch_kwargs)
        except Exception as exc:
            if _should_reset_profile(exc, launch_kwargs):
                _reset_incompatible_profile(Path(str(launch_kwargs["user_data_dir"])))
                launched = await AsyncNewBrowser(self._playwright, **launch_kwargs)
            else:
                raise
        if isinstance(launched, BrowserContext):
            self._browser_context = launched
            self._browser_context.on("close", lambda: self._on_browser_disconnect())
        else:
            self._browser = launched
            self._browser.on("disconnected", lambda: self._on_browser_disconnect())
            self._browser_context = await self._browser.new_context()
            self._browser_context.on("close", lambda: self._on_browser_disconnect())

        self._browser_context.set_default_timeout(self.config.default_timeout_ms)
        self._browser_context.set_default_navigation_timeout(self.config.navigation_timeout_ms)
        self._browser_context.on("page", self._handle_new_page)
        self._sync_existing_pages()
        await self._validate_snapshot_support()
        return self._browser_context

    def _handle_new_page(self, page: Page) -> None:
        self._wrap_page(page)

    async def _validate_snapshot_support(self) -> None:
        context = self._browser_context
        if context is None:
            return
        pages = context.pages
        page = pages[0] if pages else await context.new_page()
        created_page = not pages
        try:
            await snapshot_for_ai(page)
        finally:
            if created_page:
                await page.close()

    def _sync_existing_pages(self) -> None:
        if self._browser_context is None:
            return
        for page in self._browser_context.pages:
            self._wrap_page(page)

    def _wrap_page(self, page: Page) -> Tab:
        for tab in self._tabs:
            if tab.page is page:
                return tab
        tab = Tab(self, page, self._on_page_close)
        self._tabs.append(tab)
        if self._current_tab_index is None:
            self._current_tab_index = len(self._tabs) - 1
        return tab

    def _on_page_close(self, tab: Tab) -> None:
        if tab not in self._tabs:
            return
        index = self._tabs.index(tab)
        self._tabs.pop(index)
        if not self._tabs:
            self._current_tab_index = None
            return
        if self._current_tab_index is None:
            self._current_tab_index = 0
            return
        if self._current_tab_index >= len(self._tabs):
            self._current_tab_index = len(self._tabs) - 1
        elif self._current_tab_index > index:
            self._current_tab_index -= 1

    def _on_browser_disconnect(self) -> None:
        self._browser = None
        self._browser_context = None
        self._playwright = None
        self._tabs.clear()
        self._current_tab_index = None

    def _resolve_user_data_dir(self) -> Path | None:
        if not self.config.persistent_context:
            return None
        if self.config.user_data_dir_explicit:
            if self.config.user_data_dir is None:
                raise RuntimeError("Explicit user_data_dir must not be None.")
            explicit_dir = self.config.user_data_dir.expanduser()
            explicit_dir.mkdir(parents=True, exist_ok=True)
            return explicit_dir
        if self._ephemeral_user_data_dir is None:
            self._ephemeral_user_data_dir = tempfile.TemporaryDirectory(
                prefix="camoufox-mcp-python-profile-"
            )
        ephemeral_dir = Path(self._ephemeral_user_data_dir.name)
        ephemeral_dir.mkdir(parents=True, exist_ok=True)
        return ephemeral_dir

    def _cleanup_ephemeral_user_data_dir(self) -> None:
        if self._ephemeral_user_data_dir is None:
            return
        self._ephemeral_user_data_dir.cleanup()
        self._ephemeral_user_data_dir = None

    def tabs(self) -> list[Tab]:
        return list(self._tabs)

    def current_tab(self) -> Tab | None:
        if self._current_tab_index is None:
            return None
        if self._current_tab_index >= len(self._tabs):
            return None
        return self._tabs[self._current_tab_index]

    def current_tab_or_raise(self) -> Tab:
        tab = self.current_tab()
        if tab is None:
            raise RuntimeError("No open pages available.")
        return tab

    async def ensure_tab(self) -> Tab:
        context = await self.ensure_browser()
        self._sync_existing_pages()
        tab = self.current_tab()
        if tab is not None:
            return tab
        if context.pages:
            tab = self._wrap_page(context.pages[0])
            self._current_tab_index = self._tabs.index(tab)
            return tab
        page = await context.new_page()
        tab = self._wrap_page(page)
        self._current_tab_index = self._tabs.index(tab)
        return tab

    async def new_tab(self) -> Tab:
        context = await self.ensure_browser()
        page = await context.new_page()
        tab = self._wrap_page(page)
        self._current_tab_index = self._tabs.index(tab)
        try:
            await page.bring_to_front()
        except Exception:
            pass
        return tab

    async def select_tab(self, index: int) -> Tab:
        try:
            tab = self._tabs[index]
        except IndexError as exc:
            raise RuntimeError(f"Tab {index} not found.") from exc
        self._current_tab_index = index
        try:
            await tab.page.bring_to_front()
        except Exception:
            pass
        return tab

    async def close_tab(self, index: int | None = None) -> None:
        if index is None:
            tab = self.current_tab_or_raise()
        else:
            try:
                tab = self._tabs[index]
            except IndexError as exc:
                raise RuntimeError(f"Tab {index} not found.") from exc
        await tab.page.close()

    async def tab_headers(self) -> list[TabHeader]:
        headers: list[TabHeader] = []
        for index, tab in enumerate(self._tabs):
            headers.append(await tab.header_snapshot(index == self._current_tab_index))
        return headers

    async def close_browser(self) -> None:
        browser_context = self._browser_context
        browser = self._browser
        playwright = self._playwright
        self._on_browser_disconnect()

        if browser_context is not None:
            try:
                await browser_context.close()
            except Exception:
                pass
        if browser is not None:
            try:
                await browser.close()
            except Exception:
                pass
        if playwright is not None:
            try:
                await playwright.stop()
            except Exception:
                pass
        self._cleanup_ephemeral_user_data_dir()

    async def close(self) -> None:
        await self.close_browser()


def _repair_camoufox_install_layout() -> None:
    install_dir = Path(INSTALL_DIR)
    has_root_browser = any(
        (install_dir / name).exists() for name in ("Camoufox.app", "camoufox-bin", "camoufox.exe")
    )
    if _has_compatible_root_version(install_dir) and has_root_browser:
        return

    browser_roots = [
        path
        for path in (install_dir / "browsers").glob("*/*")
        if (path / "version.json").exists()
    ]
    if not browser_roots:
        return

    candidate = max(browser_roots, key=lambda path: path.stat().st_mtime)
    _write_compatible_version_file(install_dir, candidate / "version.json")
    for child in candidate.iterdir():
        if child.name == "version.json":
            continue
        target = install_dir / child.name
        if target.exists():
            continue
        try:
            target.symlink_to(child, target_is_directory=child.is_dir())
        except OSError:
            if child.is_dir():
                shutil.copytree(child, target)
            else:
                shutil.copy2(child, target)


def _write_compatible_version_file(install_dir: Path, source: Path) -> None:
    try:
        payload = json.loads(source.read_text())
    except (OSError, json.JSONDecodeError):
        return

    normalized = {
        "version": payload.get("version"),
        "release": payload.get("release") or payload.get("build"),
    }
    if not normalized["version"] or not normalized["release"]:
        return

    target = install_dir / "version.json"
    if target.exists() or target.is_symlink():
        target.unlink()
    target.write_text(json.dumps(normalized))


def _has_compatible_root_version(install_dir: Path) -> bool:
    version_file = install_dir / "version.json"
    if not version_file.exists():
        return False
    try:
        payload = json.loads(version_file.read_text())
    except (OSError, json.JSONDecodeError):
        return False
    return bool(payload.get("version") and payload.get("release"))


def _should_reset_profile(exc: Exception, launch_kwargs: dict[str, Any]) -> bool:
    if "user_data_dir" not in launch_kwargs:
        return False
    message = str(exc)
    return "newer version of this application" in message


def _reset_incompatible_profile(profile_dir: Path) -> None:
    if not profile_dir.exists():
        return
    backup = profile_dir.with_name(f"{profile_dir.name}.bak-{int(time.time())}")
    if backup.exists():
        return
    profile_dir.rename(backup)
    profile_dir.mkdir(parents=True, exist_ok=True)
