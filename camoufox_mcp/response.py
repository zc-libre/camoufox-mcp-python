from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import TYPE_CHECKING

from mcp.types import ImageContent, TextContent

from .tab import ModalState, SnapshotResult, TabHeader

if TYPE_CHECKING:
    from .context import AppContext
    from .tab import Tab

MAX_INLINE_EVENT_LINES = 10
MAX_INLINE_EVENT_CHARS = 280


@dataclass(slots=True)
class ImageAttachment:
    data: bytes
    mime_type: str


class Response:
    def __init__(self) -> None:
        self._results: list[str] = []
        self._errors: list[str] = []
        self._events: list[str] = []
        self._images: list[ImageAttachment] = []
        self._include_snapshot = False

    def add_result(self, text: str) -> None:
        self._results.append(text)

    def add_error(self, text: str) -> None:
        self._errors.append(text)

    def add_event(self, text: str) -> None:
        self._events.append(text)

    def add_image(self, data: bytes, mime_type: str) -> None:
        self._images.append(ImageAttachment(data=data, mime_type=mime_type))

    def set_include_snapshot(self, include: bool = True) -> None:
        self._include_snapshot = include

    async def serialize(
        self, app: AppContext, tab: Tab | None = None
    ) -> list[TextContent | ImageContent]:
        sections: list[tuple[str, list[str]]] = []

        if self._errors:
            sections.append(("Error", list(self._errors)))
        if self._results:
            sections.append(("Result", list(self._results)))

        headers = await app.tab_headers()
        if headers:
            if len(headers) != 1:
                sections.append(("Open tabs", render_tabs_markdown(headers)))
            current_header = next((item for item in headers if item.current), headers[0])
            sections.append(("Page", render_tab_markdown(current_header)))

        snapshot_result: SnapshotResult | None = None
        if tab is not None and self._include_snapshot:
            snapshot_result = await tab.capture_snapshot()
            if snapshot_result.modal_states:
                sections.append(
                    ("Modal state", render_modal_states(snapshot_result.modal_states))
                )
            if snapshot_result.yaml:
                sections.append(("Snapshot", [f"```yaml\n{snapshot_result.yaml.rstrip()}\n```"]))
            if snapshot_result.events:
                sections.append(("Events", render_event_markdown(snapshot_result.events)))

        if self._events:
            sections.append(("Events", render_event_markdown(self._events)))

        if not sections:
            sections.append(("Result", ["OK"]))

        lines: list[str] = []
        for title, content in sections:
            if not content:
                continue
            lines.append(f"### {title}")
            lines.extend(content)

        content_blocks: list[TextContent | ImageContent] = [
            TextContent(type="text", text="\n".join(lines).strip())
        ]
        for image in self._images:
            content_blocks.append(
                ImageContent(
                    type="image",
                    data=base64.b64encode(image.data).decode("ascii"),
                    mimeType=image.mime_type,
                )
            )
        return content_blocks


def render_tab_markdown(tab: TabHeader) -> list[str]:
    lines = [f"- Page URL: {tab.url}"]
    if tab.title:
        lines.append(f"- Page Title: {tab.title}")
    if tab.console_errors or tab.console_warnings:
        lines.append(
            f"- Console: {tab.console_errors} errors, {tab.console_warnings} warnings"
        )
    return lines


def render_tabs_markdown(tabs: list[TabHeader]) -> list[str]:
    if not tabs:
        return ["No open tabs. Navigate to a URL to create one."]
    lines: list[str] = []
    for index, tab in enumerate(tabs):
        current = " (current)" if tab.current else ""
        lines.append(f"- {index}:{current} [{tab.title}]({tab.url})")
    return lines


def render_modal_states(modal_states: list[ModalState]) -> list[str]:
    if not modal_states:
        return ["- There is no modal state present"]
    return [state.render() for state in modal_states]


def render_event_markdown(events: list[str]) -> list[str]:
    rendered = [_truncate_line(event) for event in events[:MAX_INLINE_EVENT_LINES]]
    remaining = len(events) - len(rendered)
    if remaining > 0:
        rendered.append(
            f"- {remaining} more events omitted. Use browser_console_messages for full details."
        )
    return rendered


def _truncate_line(line: str) -> str:
    normalized = line.strip()
    if len(normalized) <= MAX_INLINE_EVENT_CHARS:
        return normalized
    return f"{normalized[: MAX_INLINE_EVENT_CHARS - 3].rstrip()}..."
