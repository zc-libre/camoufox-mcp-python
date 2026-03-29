import unittest

from camoufox_mcp.response import (
    MAX_INLINE_EVENT_CHARS,
    MAX_INLINE_EVENT_LINES,
    render_event_markdown,
)


class RenderEventMarkdownTests(unittest.TestCase):
    def test_keeps_short_events_unchanged(self) -> None:
        events = ["- first event", "- second event"]

        self.assertEqual(render_event_markdown(events), events)

    def test_truncates_and_caps_inline_events(self) -> None:
        long_suffix = "x" * (MAX_INLINE_EVENT_CHARS + 40)
        events = [f"- event {index} {long_suffix}" for index in range(MAX_INLINE_EVENT_LINES + 2)]

        rendered = render_event_markdown(events)

        self.assertEqual(len(rendered), MAX_INLINE_EVENT_LINES + 1)
        self.assertTrue(rendered[0].endswith("..."))
        self.assertLessEqual(len(rendered[0]), MAX_INLINE_EVENT_CHARS)
        self.assertEqual(
            rendered[-1],
            "- 2 more events omitted. Use browser_console_messages for full details.",
        )


if __name__ == "__main__":
    unittest.main()
