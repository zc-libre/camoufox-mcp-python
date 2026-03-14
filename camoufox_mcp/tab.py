from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Any, Literal

from playwright.async_api import ConsoleMessage, Dialog, FileChooser, Locator, Page, Request

from .snapshot import snapshot_for_ai

ConsoleLevel = Literal["error", "warning", "info", "debug"]


class RefNotFoundError(RuntimeError):
    def __init__(self, ref: str):
        super().__init__(
            f"Ref {ref} not found. Page may have changed. Use browser_snapshot to get fresh refs."
        )


@dataclass(slots=True)
class ConsoleEntry:
    type: str
    text: str
    timestamp_ms: int
    location: dict[str, Any] | None = None

    def render(self) -> str:
        if not self.location or not self.location.get("url"):
            return f"[{self.type.upper()}] {self.text}"
        url = self.location.get("url", "")
        line = self.location.get("lineNumber", 0)
        return f"[{self.type.upper()}] {self.text} @ {url}:{line}"


@dataclass(slots=True)
class ModalState:
    type: Literal["dialog", "fileChooser"]
    description: str
    dialog: Dialog | None = None
    file_chooser: FileChooser | None = None
    opened_at_ms: int = field(default_factory=lambda: int(time.time() * 1000))

    def render(self) -> str:
        tool_name = (
            "browser_handle_dialog" if self.type == "dialog" else "browser_file_upload"
        )
        return f"- [{self.description}]: can be handled by {tool_name}"


@dataclass(slots=True)
class TabHeader:
    title: str
    url: str
    current: bool
    console_total: int
    console_warnings: int
    console_errors: int


@dataclass(slots=True)
class SnapshotResult:
    yaml: str
    modal_states: list[ModalState]
    events: list[str]


class Tab:
    def __init__(self, app: Any, page: Page, on_page_close: Any):
        self.app = app
        self.page = page
        self._on_page_close = on_page_close
        self._console_messages: list[ConsoleEntry] = []
        self._requests: list[Request] = []
        self._request_ids: set[int] = set()
        self._modal_states: list[ModalState] = []
        self._modal_waiters: list[asyncio.Future[list[ModalState]]] = []
        self._recent_events: list[str] = []

        page.on("console", self._handle_console_message)
        page.on("pageerror", self._handle_page_error)
        page.on("request", self._handle_request)
        page.on("response", self._handle_response)
        page.on("requestfailed", self._handle_request_failed)
        page.on("dialog", self._handle_dialog)
        page.on("filechooser", self._handle_file_chooser)
        page.on("close", self._handle_close)

    def _handle_console_message(self, message: ConsoleMessage) -> None:
        entry = ConsoleEntry(
            type=message.type,
            text=message.text,
            timestamp_ms=int(time.time() * 1000),
            location=message.location,
        )
        self._console_messages.append(entry)
        if entry.type in {"error", "warning"}:
            self._recent_events.append(f"- {entry.render()}")

    def _handle_page_error(self, error: Any) -> None:
        text = error.message if isinstance(error, Exception) else str(error)
        entry = ConsoleEntry(
            type="error",
            text=text,
            timestamp_ms=int(time.time() * 1000),
            location=None,
        )
        self._console_messages.append(entry)
        self._recent_events.append(f"- {entry.render()}")

    def _handle_request(self, request: Request) -> None:
        request_id = id(request)
        if request_id not in self._request_ids:
            self._request_ids.add(request_id)
            self._requests.append(request)

    def _handle_response(self, response: Any) -> None:
        request = response.request
        if response.status >= 400:
            self._recent_events.append(
                f"- [{request.method}] {request.url} -> {response.status} {response.status_text}"
            )

    def _handle_request_failed(self, request: Request) -> None:
        failure = request.failure
        detail = failure or "request failed"
        self._recent_events.append(f"- [{request.method}] {request.url} -> FAILED: {detail}")

    def _push_modal_state(self, state: ModalState) -> None:
        self._modal_states.append(state)
        for waiter in self._modal_waiters:
            if not waiter.done():
                waiter.set_result([state])
        self._modal_waiters = [waiter for waiter in self._modal_waiters if not waiter.done()]

    def _handle_dialog(self, dialog: Dialog) -> None:
        self._push_modal_state(
            ModalState(
                type="dialog",
                description=f'"{dialog.type}" dialog with message "{dialog.message}"',
                dialog=dialog,
            )
        )

    def _handle_file_chooser(self, chooser: FileChooser) -> None:
        self._push_modal_state(
            ModalState(
                type="fileChooser",
                description="File chooser",
                file_chooser=chooser,
            )
        )

    def _handle_close(self) -> None:
        self._on_page_close(self)

    def modal_states(self) -> list[ModalState]:
        return list(self._modal_states)

    def clear_modal_state(self, state: ModalState | str) -> None:
        if isinstance(state, str):
            self._modal_states = [item for item in self._modal_states if item.type != state]
            return
        self._modal_states = [item for item in self._modal_states if item is not state]

    async def _race_against_modal_states(self, action: Any) -> Any:
        if self._modal_states:
            return list(self._modal_states)

        loop = asyncio.get_running_loop()
        waiter: asyncio.Future[list[ModalState]] = loop.create_future()
        self._modal_waiters.append(waiter)
        action_task = asyncio.create_task(action())
        done, _ = await asyncio.wait(
            {action_task, waiter}, return_when=asyncio.FIRST_COMPLETED
        )

        if waiter in done:
            if not action_task.done():
                action_task.add_done_callback(lambda task: task.exception())
            return waiter.result()

        waiter.cancel()
        try:
            return await action_task
        finally:
            self._modal_waiters = [
                pending for pending in self._modal_waiters if pending is not waiter
            ]

    async def wait_for_timeout(self, seconds: float) -> None:
        await asyncio.sleep(seconds)

    async def wait_for_completion(self, callback: Any) -> list[ModalState]:
        async def runner() -> None:
            requests: list[Request] = []

            def request_listener(request: Request) -> None:
                requests.append(request)

            self.page.on("request", request_listener)
            try:
                await callback()
                await self.wait_for_timeout(0.5)
            finally:
                self.page.remove_listener("request", request_listener)

            if any(request.is_navigation_request() for request in requests):
                try:
                    await self.page.wait_for_load_state("load", timeout=10_000)
                except Exception:
                    return
                return

            relevant = [
                request
                for request in requests
                if request.resource_type in {"document", "stylesheet", "script", "xhr", "fetch"}
            ]
            tasks = [asyncio.create_task(self._wait_for_request(request)) for request in relevant]
            if tasks:
                done, pending = await asyncio.wait(tasks, timeout=5.0)
                for task in pending:
                    task.cancel()
                for task in done:
                    try:
                        task.result()
                    except Exception:
                        pass
                await self.wait_for_timeout(0.5)

        raced = await self._race_against_modal_states(runner)
        if isinstance(raced, list):
            return raced
        return []

    async def _wait_for_request(self, request: Request) -> None:
        response = await request.response()
        if response is not None:
            await response.finished()

    async def capture_snapshot(self) -> SnapshotResult:
        raced = await self._race_against_modal_states(lambda: snapshot_for_ai(self.page))
        if isinstance(raced, list):
            return SnapshotResult(yaml="", modal_states=raced, events=[])

        yaml = raced
        events = list(self._recent_events)
        self._recent_events.clear()
        return SnapshotResult(yaml=yaml, modal_states=[], events=events)

    async def ref_locator(self, ref: str, element: str | None = None) -> Locator:
        locator = self.page.locator(f"aria-ref={ref}").first
        try:
            count = await locator.count()
        except Exception as exc:
            raise RefNotFoundError(ref) from exc
        if count < 1:
            raise RefNotFoundError(ref)
        return locator

    async def header_snapshot(self, current: bool) -> TabHeader:
        try:
            title = await self.page.title()
        except Exception:
            title = ""
        counts = self.console_message_count()
        return TabHeader(
            title=title,
            url=self.page.url,
            current=current,
            console_total=counts["total"],
            console_warnings=counts["warnings"],
            console_errors=counts["errors"],
        )

    def console_message_count(self) -> dict[str, int]:
        errors = sum(1 for message in self._console_messages if message.type == "error")
        warnings = sum(1 for message in self._console_messages if message.type == "warning")
        return {
            "total": len(self._console_messages),
            "errors": errors,
            "warnings": warnings,
        }

    def console_messages(self, level: ConsoleLevel = "info") -> list[ConsoleEntry]:
        threshold = _console_level_rank(level)
        return [
            message
            for message in self._console_messages
            if _console_level_rank(_console_message_level(message.type)) <= threshold
        ]

    def clear_console_messages(self) -> None:
        self._console_messages.clear()

    def requests(self) -> list[Request]:
        return list(self._requests)

    def clear_requests(self) -> None:
        self._requests.clear()
        self._request_ids.clear()

    async def render_network_requests(self, include_static: bool = False) -> list[str]:
        lines: list[str] = []
        for request in self._requests:
            line = await self._render_request(request)
            if include_static or request.resource_type in {"document", "xhr", "fetch"}:
                lines.append(line)
                continue
            response = await request.response()
            if response is None or response.status >= 400 or request.failure:
                lines.append(line)
        return lines

    async def _render_request(self, request: Request) -> str:
        response = await request.response()
        if response is not None:
            return f"[{request.method}] {request.url} => [{response.status}] {response.status_text}"
        if request.failure:
            return f"[{request.method}] {request.url} => [FAILED] {request.failure}"
        return f"[{request.method}] {request.url}"

    @staticmethod
    def serialize_value(value: Any) -> str:
        if value is None:
            return "undefined"
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def _console_message_level(message_type: str) -> ConsoleLevel:
    if message_type in {"assert", "error"}:
        return "error"
    if message_type == "warning":
        return "warning"
    if message_type in {"count", "dir", "dirxml", "info", "log", "table", "time", "timeEnd"}:
        return "info"
    return "debug"


def _console_level_rank(level: ConsoleLevel) -> int:
    return {"error": 0, "warning": 1, "info": 2, "debug": 3}[level]
