# camoufox-mcp-python

[中文文档](README_zh.md)

[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![PyPI](https://img.shields.io/pypi/v/camoufox-mcp-python)](https://pypi.org/project/camoufox-mcp-python/)

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that provides browser automation tools powered by [Camoufox](https://camoufox.com/) — a stealthy, anti-detect browser built on Firefox. It exposes a Playwright-MCP compatible tool interface using accessibility snapshots and ref-based element targeting.

> **Think of it as [playwright-mcp](https://github.com/anthropics/playwright-mcp), but with built-in anti-detection and fingerprint spoofing.**

## Features

- **Anti-detect browser fingerprinting** — Camoufox automatically spoofs browser fingerprints to bypass bot detection
- **Ref-based accessibility snapshots** — Interact with page elements via accessibility refs, no CSS selectors needed
- **Human-like cursor movement** — Cursor humanization enabled by default for realistic interactions
- **WebRTC leak protection** — WebRTC blocked by default to prevent IP leaks
- **Persistent browser profile** — Maintain session state, cookies, and login across runs
- **GeoIP auto-matching** — Automatically match browser locale/timezone to proxy location
- **Proxy support** — Full proxy support including authentication
- **WebGL fingerprint control** — Specify WebGL vendor/renderer pair or block entirely
- **Custom addons** — Load custom Firefox addons or exclude defaults like uBlock Origin
- **Advanced fingerprint config** — Override any BrowserForge fingerprint property or use a custom fingerprint
- **Firefox preferences** — Set custom Firefox user preferences
- **Browser caching** — Optional page/request caching for performance
- **Privacy controls** — Block WebGL and image loading to reduce leaks and bandwidth
- **Multi-tab management** — Create, close, select, and list browser tabs
- **Modal & dialog handling** — Handle JavaScript dialogs and file choosers
- **Console & network monitoring** — Inspect console messages and network requests

## Quick Start

### Use with Claude Desktop

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "camoufox": {
      "command": "uvx",
      "args": ["camoufox-mcp-python", "--headless"]
    }
  }
}
```

### Use with Claude Code

```bash
claude mcp add camoufox -- uvx camoufox-mcp-python --headless
```

### Use with VS Code / Cursor

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "camoufox": {
      "command": "uvx",
      "args": ["camoufox-mcp-python", "--headless"]
    }
  }
}
```

### Use with Codex CLI

Add to `codex.json` or pass via CLI:

```bash
codex --mcp-server "npx @anthropic-ai/mcp-proxy -- uvx camoufox-mcp-python --headless"
```

### Pin a specific version

```json
{
  "mcpServers": {
    "camoufox": {
      "command": "uvx",
      "args": ["--from", "camoufox-mcp-python==0.2.0", "camoufox-mcp-python", "--headless"]
    }
  }
}
```

## CLI Options

| Option | Description |
|---|---|
| `--headless` | Run the browser in headless mode |
| `--proxy <url>` | Proxy server URL (supports `user:pass@host:port`) |
| `--os <os>` | Target OS fingerprint: `windows`, `macos`, `linux` (repeatable) |
| `--humanize [seconds]` | Cursor humanization (default: on). Pass a number for max duration, or `false` to disable |
| `--geoip [ip]` | Auto-match locale/timezone to proxy IP, or specify a target IP |
| `--locale <locale>` | Browser locale(s), e.g. `en-US` (repeatable, comma-separated) |
| `--window <WxH>` | Outer window size, e.g. `1280x720` |
| `--block-webrtc / --no-block-webrtc` | Block WebRTC to prevent IP leaks (default: on) |
| `--block-webgl` | Disable WebGL |
| `--block-images` | Block image requests to reduce bandwidth |
| `--disable-coop` | Disable COOP for cross-origin iframe interactions |
| `--user-data-dir <path>` | Persistent profile directory (default: `~/.camoufox-mcp-python/profile`) |
| `--caps <groups>` | Enable capability groups, e.g. `dangerous` (enables `browser_evaluate`) |
| `--webgl-config <v,r>` | WebGL vendor/renderer pair, e.g. `"Intel Inc.,Intel(R) UHD Graphics 620"` |
| `--addons <paths>` | Paths to extracted Firefox addons (repeatable, comma-separated) |
| `--exclude-addons <names>` | Default addons to exclude, e.g. `UBO` (repeatable, comma-separated) |
| `--config <json>` | Camoufox fingerprint properties as a JSON string |
| `--enable-cache` | Cache previous pages and requests (uses more memory) |
| `--firefox-user-prefs <json>` | Firefox user preferences as a JSON string |
| `--i-know-what-im-doing` | Silence Camoufox warnings for advanced configurations |
| `--debug` | Print the config being sent to Camoufox |

### Examples

```bash
# Zero-config anti-detection (humanize + block-webrtc on by default)
camoufox-mcp-python --headless

# With proxy and GeoIP matching
camoufox-mcp-python --headless --proxy http://user:pass@proxy.example.com:8080 --geoip

# Custom WebGL fingerprint
camoufox-mcp-python --headless --webgl-config "Intel Inc.,Intel(R) UHD Graphics 620" --os windows

# Custom fingerprint properties
camoufox-mcp-python --headless --config '{"navigator.hardwareConcurrency": 8}'

# With caching and custom Firefox prefs
camoufox-mcp-python --headless --enable-cache --firefox-user-prefs '{"dom.webnotifications.enabled": false}'

# Privacy-hardened mode
camoufox-mcp-python --headless --block-webgl --block-images

# Disable default anti-detection for debugging
camoufox-mcp-python --humanize false --no-block-webrtc --debug

# Enable JavaScript evaluation
camoufox-mcp-python --headless --caps dangerous
```

## Available Tools

### Navigation

| Tool | Description |
|---|---|
| `browser_navigate` | Navigate to a URL |
| `browser_navigate_back` | Go back to the previous page |

### Snapshot & Interaction

| Tool | Description |
|---|---|
| `browser_snapshot` | Capture an accessibility snapshot of the current page |
| `browser_click` | Click an element by ref (supports double-click, right-click, modifiers) |
| `browser_hover` | Hover over an element |
| `browser_drag` | Drag from one element to another |
| `browser_select_option` | Select option(s) in a dropdown |

### Input

| Tool | Description |
|---|---|
| `browser_type` | Type text into an editable element (supports slow typing and submit) |
| `browser_press_key` | Press a keyboard key or key combination |
| `browser_fill_form` | Fill multiple form fields in a single call |

### Page

| Tool | Description |
|---|---|
| `browser_take_screenshot` | Take a screenshot (viewport, full page, or element) |
| `browser_console_messages` | Retrieve collected console messages |
| `browser_network_requests` | List network requests seen by the page |
| `browser_resize` | Resize the viewport |
| `browser_wait_for` | Wait for text to appear/disappear, or a fixed duration |
| `browser_close` | Close the browser session |

### Tabs

| Tool | Description |
|---|---|
| `browser_tabs` | List, create, close, or select browser tabs |

### Modals & Files

| Tool | Description |
|---|---|
| `browser_handle_dialog` | Accept or dismiss a JavaScript dialog |
| `browser_file_upload` | Handle a file chooser and upload files |

### Dangerous (requires `--caps dangerous`)

| Tool | Description |
|---|---|
| `browser_evaluate` | Execute arbitrary JavaScript on the page or an element |

## How It Works

The server uses Camoufox (a Firefox-based anti-detect browser) through Playwright's async API. Pages are represented as accessibility snapshots in YAML format, where each interactive element is assigned a **ref** identifier. The AI model reads the snapshot, identifies the target ref, and calls the appropriate tool — no fragile CSS/XPath selectors required.

```
AI Model  ←→  MCP Server  ←→  Camoufox Browser
                  │
                  ├── Accessibility Snapshot (YAML)
                  ├── Ref-based element targeting
                  └── Anti-detect fingerprinting
```

## Local Development

```bash
# Clone and install
git clone https://github.com/user/camoufox-mcp.git
cd camoufox-mcp
uv pip install --python .venv/bin/python -e .

# Run the server
./.venv/bin/camoufox-mcp-python --headless

# Or run as a module
./.venv/bin/python -m camoufox_mcp --headless

# Smoke test
./.venv/bin/python -m compileall camoufox_mcp
./.venv/bin/camoufox-mcp-python --help
```

## Requirements

- Python >= 3.10
- [camoufox](https://camoufox.com/) >= 0.4.11
- [mcp\[cli\]](https://github.com/modelcontextprotocol/python-sdk) >= 1.25
- [playwright](https://playwright.dev/python/) >= 1.58

> **Note:** The first launch on a new machine may trigger automatic Camoufox binary and addon downloads.

## License

[MIT](https://opensource.org/licenses/MIT)
