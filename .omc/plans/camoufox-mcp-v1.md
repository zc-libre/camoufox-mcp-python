# Camoufox MCP Server v1 - Development Plan (Revised)

## Metadata
- Plan ID: camoufox-mcp-v1
- Created: 2026-03-14
- Revised: 2026-03-14
- Source: deep-interview-camoufox-mcp (17 rounds, 4% ambiguity) + Architect/Critic review
- Complexity: HIGH (greenfield, ~20 tools, browser lifecycle management)
- Estimated Files: ~15 source files + pyproject.toml

---

## Context

Build a Python MCP server wrapping camoufox (anti-detect Firefox) as a playwright-mcp-compatible tool interface. The server exposes ~20 browser automation tools over STDIO for AI coding assistants. Key differentiator: camoufox's fingerprint spoofing, proxy/geoip support, and anti-detection capabilities, surfaced through the same ref-based accessibility tree interaction model as playwright-mcp.

**Greenfield project** -- only `.venv` with camoufox dependencies exists. No source code yet.

### Compatibility Level Declaration

**"Playwright-MCP compatible" for v1 means:**
- **Tool names and core interaction model**: 尽量对齐 `playwright-mcp` 的常用工具名、`ref` 驱动交互方式、以及高频参数形状，但不承诺无差别替换。
- **Response format structure**: 对齐 `playwright-mcp` 的 markdown section 模型与关键标题名，但不承诺逐字节一致，也不承诺附件/文件输出行为完全一致。
- **Documented divergences are allowed**: v1 明确保留 Python/Camoufox 特有偏离，例如 `snapshotForAI` 仅按当前 Python 契约处理、`browser_run_code` 暂不提供 1:1 JS runtime 兼容。

---

## RALPLAN-DR Structured Deliberation

### Principles (5)

1. **Playwright-MCP Alignment**: Tool names, core parameter shapes, and response sections should align with playwright-mcp where the Python/Camoufox runtime can honor them faithfully. Avoid claiming drop-in interchangeability when semantics differ.
2. **Anti-Detection First**: Every design decision must preserve camoufox's anti-detection guarantees. Dangerous operations stay behind explicit capability flags. Default behavior should follow verified Camoufox defaults; `humanize` remains opt-in unless later evidence justifies changing the default.
3. **Lazy Initialization**: Browser starts on first tool call, not at server startup. This avoids resource waste when the MCP server is registered but not used.
4. **Single Responsibility Layers**: Clear separation between CLI config parsing, browser lifecycle management, page/tab state, snapshot/ref resolution, and tool handlers.
5. **Minimal Viable Surface**: Ship ~20 core tools that cover 95% of AI-driven browser automation needs. Resist adding optional capability groups (vision/pdf/testing/storage) until v2.

### Decision Drivers (Top 3)

1. **Ref System Viability**: The entire interaction model depends on `page._impl_obj._channel.send("snapshotForAI")` + `page.locator("aria-ref=...")`. This is a private Playwright API. In the current verified Python environment (`camoufox 0.4.11`, `playwright 1.58.0`), `_channel.send("snapshotForAI", ...)` returns a YAML `str`, while Python `Page` does not expose `page._snapshotForAI()`. v1 must treat the return value as an opaque snapshot string and should not assume structured incremental snapshots.
2. **FastMCP Lifespan Pattern**: Browser state must be shared across all tool calls within a session. FastMCP's `lifespan` context manager + `ctx.request_context.lifespan_context` is the sanctioned pattern for this.
3. **CLI-to-Camoufox Mapping**: camoufox's `launch_options()` accepts ~25 parameters. The CLI must expose the most important subset and map them cleanly to camoufox kwargs without leaking implementation details.

### Viable Options

#### Option A: Flat Module Architecture (Recommended)

Single package `camoufox_mcp/` with modules for config, context, tab, snapshot, response, and a `tools/` sub-package. Each tool module registers tools via `@mcp.tool()` decorators. A `@tab_tool` decorator eliminates per-tool boilerplate.

**Pros:**
- Simple, easy to navigate, matches team mental model
- FastMCP decorator pattern is idiomatic for this scale (~20 tools)
- Minimal abstraction layers between tool handler and Playwright API
- `@tab_tool` decorator keeps tools DRY without over-abstraction

**Cons:**
- Tool registration order depends on import order (manageable with explicit `register()` functions)
- If tool count grows beyond ~40, a single `tools/` package could become crowded

#### Option B: Plugin-Based Tool Registry

Abstract tool definition behind a `ToolDefinition` dataclass (like playwright-mcp's `defineTool`/`defineTabTool`). Tools are registered via a discovery mechanism scanning `tools/` modules.

**Pros:**
- More extensible for future capability groups
- Cleaner capability gating through tool metadata
- Matches playwright-mcp's architecture more closely

**Cons:**
- Over-engineering for ~20 tools in v1
- Adds an abstraction layer between FastMCP decorators and actual tool handlers
- More boilerplate per tool definition

**Why Option B is not chosen for v1:** YAGNI. The plugin registry adds complexity without benefit at the current scale. The flat architecture can be refactored to Option B when capability groups are added in v2. Option A's `register(mcp, config)` pattern already supports capability gating via a simple `if config.caps_dangerous:` guard.

---

## ADR: Architecture Decision Record

**Decision:** Flat module architecture with FastMCP decorators, explicit `register()` functions per tool module, and a `@tab_tool` decorator for boilerplate reduction.

**Drivers:**
1. KISS/YAGNI -- 20 tools don't need a plugin system
2. FastMCP's `@mcp.tool()` decorator is the idiomatic Python MCP pattern
3. Capability gating is achievable with simple conditional registration
4. `@tab_tool` eliminates ~5 lines of repeated boilerplate per tool while staying flat

**Alternatives Considered:**
- Plugin-based tool registry (Option B) -- rejected as over-engineering for v1
- Single monolithic `server.py` with all tools inline -- rejected as unmaintainable

**Why Chosen:** Balances simplicity with enough structure for ~20 tools. Each tool module is a self-contained file with a `register(mcp, config)` function. The `config` parameter enables capability gating. The `@tab_tool` decorator centralizes AppContext retrieval, `ensure_tab()`, modal state checking, and stale-ref error handling. Migration path to plugin architecture exists if v2 needs it.

**Consequences:**
- Tool registration happens eagerly at startup (not lazily discovered)
- Adding a new tool requires adding a `register()` call in `server.py`
- Capability gating is per-module (dangerous_tools.py only registered when `--caps dangerous`)
- All tab-based tools share consistent error handling via the decorator

**Follow-ups:**
- If v2 adds 3+ capability groups, revisit plugin-based registry
- Monitor Playwright's `snapshotForAI` API stability across versions

---

## Work Objectives

Build a fully functional camoufox-mcp server that:
1. Starts via `python -m camoufox_mcp` or `camoufox-mcp` CLI
2. Exposes ~20 browser automation tools over STDIO
3. Uses camoufox for anti-detection browser automation
4. Supports ref-based element interaction via accessibility tree snapshots
5. Gates dangerous operations behind `--caps dangerous`

## Guardrails

### Must Have
- All ~20 core tools functional and returning structured markdown responses
- Lazy browser initialization (first tool call triggers launch)
- CLI args for: `--proxy`, `--os`, `--headless`, `--humanize`, `--block-webrtc`, `--block-webgl`, `--geoip`, `--user-data-dir`, `--caps`
- Ref system working: raw `snapshotForAI` YAML string -> `aria-ref` locator roundtrip
- Full snapshot support using the Python-visible YAML string returned by `snapshotForAI`
- Friendly error messages for stale refs (suggest re-snapshot)
- persistent_context as default mode with `user_data_dir` defaulting to `~/.camoufox-mcp/profile`
- Clean shutdown (browser close on server exit)
- `@tab_tool` decorator for consistent tool boilerplate
- `wait_for_completion()` implementing the 3-phase algorithm (not simplified network idle)
- `_race_against_modal_states()` for dialog/filechooser handling
- `asyncio.Lock` protecting browser operations for serial execution
- Browser disconnect detection via `browser_context.on("close")`
- Runtime validation that `snapshotForAI` is callable and returns a non-empty YAML string

### Must NOT Have
- No runtime fingerprint/proxy modification (camoufox design constraint)
- No multi-browser-instance management (v1 is single instance)
- No SSE/HTTP transport implementation (STDIO only for v1)
- No optional capability groups beyond `dangerous` (no vision/pdf/testing/storage)
- No Chrome/CDP support
- No file output mode, secret redaction, or codegen (v2 candidates)
- No fake `browser_run_code` shim that silently changes upstream JS semantics into a different language runtime

---

## Task Flow (6 Phases)

```
Phase 1: Project Scaffold + Config + Dependencies
         |
         v
Phase 2: Browser Lifecycle (Context + Tab + Snapshot + waitForCompletion)
         |
         v
Phase 3: Core Navigation + Snapshot Tools
         |
         v
Phase 4: Interaction + Input Tools
         |
         v
Phase 5: Utility + Dangerous Tools
         |
         v
Phase 6: Integration Testing + Polish
```

---

## Phase 1: Project Scaffold + Config + Dependencies

**Goal:** Establish project structure, install dependencies, CLI entry point, config parsing, and a minimal FastMCP server that starts and responds to `tools/list`.

### Files to Create
- `pyproject.toml` -- project metadata, dependencies, entry points
- `camoufox_mcp/__init__.py` -- package init, version
- `camoufox_mcp/__main__.py` -- CLI entry point (argparse + mcp.run())
- `camoufox_mcp/config.py` -- CamoufoxConfig dataclass, CLI arg -> camoufox kwargs mapping
- `camoufox_mcp/server.py` -- FastMCP instance creation, lifespan skeleton, tool registration

### Detailed TODOs

1. **Install MCP SDK and verify dependencies**
   - Run `uv pip install "mcp[cli]>=1.25,<2"` in the existing `.venv`
   - Verify `camoufox` is already installed: `python -c "from camoufox.async_api import AsyncNewBrowser; print('ok')"`
   - Verify `playwright` is available: `python -c "from playwright.async_api import async_playwright; print('ok')"`
   - **AC:** All three imports succeed without error. `uv pip list` shows `mcp`, `camoufox`, `playwright`.

2. **Create `pyproject.toml`**
   - name: `camoufox-mcp`
   - Python >= 3.10
   - Dependencies: `mcp[cli]>=1.25,<2`, `camoufox`
   - Pin playwright version range compatible with camoufox's bundled version
   - Entry point: `[project.scripts] camoufox-mcp = "camoufox_mcp.__main__:main"`
   - Build system: hatchling or setuptools
   - **AC:** `uv pip install -e .` succeeds; `camoufox-mcp --help` prints usage

3. **Create `CamoufoxConfig` dataclass in `config.py`**
   - Fields for all CLI-configurable params: proxy (dict), os (str/list), headless (bool), humanize (bool/float, **default=False**), block_webrtc (bool), block_webgl (bool), geoip (str/bool), user_data_dir (str, **default="~/.camoufox-mcp/profile"**), caps (set of capability names), locale (str/list), block_images (bool), disable_coop (bool), window (tuple), persistent_context (bool, default=True)
   - Method `to_launch_kwargs() -> dict` that returns a **flat dict of kwargs for `AsyncNewBrowser()`** (NOT for `launch_options()` directly). Keys like `persistent_context` and `user_data_dir` are consumed by `AsyncNewBrowser` itself; other keys (os, proxy, humanize, etc.) pass through to `launch_options()` via `**kwargs`. **When persistent_context=True, must include `user_data_dir` in the returned dict** (expanding `~` to absolute path, creating directory if needed).
   - Method `from_cli_args(args) -> CamoufoxConfig` class method
   - **AC:** `CamoufoxConfig.from_cli_args(...)` produces valid kwargs. When `persistent_context=True`, `to_launch_kwargs()` always contains `user_data_dir`. Default humanize follows current Camoufox default (`False`).

4. **Create CLI entry in `__main__.py`**
   - argparse with all anti-detection flags
   - `--humanize` is opt-in and defaults to False (matching current Camoufox behavior)
   - `--user-data-dir` defaults to `~/.camoufox-mcp/profile`
   - Parse args -> CamoufoxConfig
   - Import and run FastMCP server
   - **AC:** `python -m camoufox_mcp --help` shows all flags; `python -m camoufox_mcp` starts server on STDIO

5. **Create minimal `server.py`**
   - `create_server(config: CamoufoxConfig) -> FastMCP`
   - Lifespan that yields an `AppContext` (browser=None, tabs=[], config=config)
   - Import and call `register()` from each tool module (empty stubs for now)
   - **AC:** Server starts, MCP client can call `tools/list` and get empty or stub tool list

### Acceptance Criteria
- All dependencies installed and importable
- `uv pip install -e .` succeeds
- `camoufox-mcp --help` prints all CLI flags with correct defaults (humanize=False, user_data_dir=~/.camoufox-mcp/profile)
- `python -m camoufox_mcp` starts an MCP server on STDIO
- MCP client `tools/list` returns successfully

---

## Phase 2: Browser Lifecycle (Context + Tab + Snapshot)

**Goal:** Implement the core runtime: browser lazy-loading (without AsyncCamoufox context manager), tab management, accessibility tree snapshot capture as raw YAML, ref-based element resolution, 3-phase `wait_for_completion`, modal state racing, and the `@tab_tool` decorator.

### Files to Create
- `camoufox_mcp/context.py` -- AppContext: browser lazy-load, tab array, ensure_tab(), asyncio.Lock
- `camoufox_mcp/tab.py` -- Tab: wraps Page, console/network log collection, modal state, wait_for_completion, _race_against_modal_states
- `camoufox_mcp/snapshot.py` -- snapshotForAI wrapper, timeout calc, string-return validation
- `camoufox_mcp/response.py` -- Response builder (markdown sections: Result/Error/Snapshot/Events)
- `camoufox_mcp/tools/decorators.py` -- @tab_tool decorator

### Detailed TODOs

1. **Implement `AppContext` in `context.py`**
   - Fields: `config: CamoufoxConfig`, `_playwright: Optional[Playwright]`, `_browser: Optional[BrowserContext]`, `_tabs: list[Tab]`, `_current_tab_index: int`, `_lock: asyncio.Lock`
   - **`async ensure_browser()`** -- Lazy-loads browser **without** using `AsyncCamoufox` context manager. Instead:
     1. `from playwright.async_api import async_playwright`
     2. `self._playwright = await async_playwright().start()`
     3. `from camoufox.async_api import AsyncNewBrowser`
     4. `self._browser = await AsyncNewBrowser(self._playwright, **self.config.to_launch_kwargs())`
        - `to_launch_kwargs()` includes `persistent_context=True` and `user_data_dir` when applicable
     5. Attach disconnect listener: `self._browser.on("close", self._on_browser_disconnect)`
   - **`_on_browser_disconnect()`** -- Sets `self._browser = None`, `self._playwright = None`, `self._tabs = []`. Next `ensure_browser()` call will re-launch.
   - **`async ensure_tab() -> Tab`** -- If no tabs, first check `self._browser.pages` for pre-existing pages from persistent context (wrap them as Tabs). Only if no existing pages, create new page via `_browser.new_page()`. Returns current tab. Protected by `self._lock`.
   - `async new_tab() -> Tab` -- create new page, wrap in Tab, set as current
   - `async close_tab(index)` -- close page, remove Tab from array
   - `async select_tab(index)` -- set current tab index
   - `tabs() -> list[Tab]`, `current_tab() -> Optional[Tab]`
   - **`async close()`** -- `await self._browser.close()` + `await self._playwright.stop()`, cleanup
   - **AC:** `ensure_browser()` launches camoufox on first call without using context manager; subsequent calls reuse instance. Browser disconnect sets state to None for re-launch. `ensure_tab()` creates a page. `close()` terminates both browser and playwright.

2. **Implement `Tab` in `tab.py`**
   - Fields: `page: Page`, `_console_messages: list`, `_network_requests: list`, `_modal_states: list[dict]` (pending dialogs/filechoosers)
   - Constructor: attach page event listeners (console, request, response, pageerror, dialog, filechooser). Dialog/filechooser events append to `_modal_states`.
   - `async capture_snapshot() -> str` -- calls `snapshot_for_ai()`, returns the latest YAML snapshot string
   - `async ref_locator(ref: str, element: str?) -> Locator` -- `page.locator(f"aria-ref={ref}")`, raises friendly error if not found
   - **`async wait_for_completion(callback)`** -- Implements the **3-phase algorithm** from playwright-mcp:
     1. **Phase 1 (Collect + Settle):** Execute `callback`. During execution, collect all initiated requests. After callback completes, wait 500ms for additional requests to settle.
     2. **Phase 2 (Navigation check):** If any collected request caused a navigation (frame navigated), wait for `page.wait_for_load_state("load")` with a 10-second timeout.
     3. **Phase 3 (Resource completion):** Otherwise, for collected requests of type `document`, `stylesheet`, `script`, `xhr`, `fetch` -- race their response completion against a 5-second timeout. If any requests completed, do an additional 500ms settle wait.
   - **`async _race_against_modal_states(callback)`** -- Before executing an action:
     1. Check `_modal_states` for existing pending modals. If found, return modal info immediately (don't execute action).
     2. If no pending modal, execute `callback` while racing against new `dialog`/`filechooser` events.
     3. If a modal event wins the race, return modal info. If action completes first, return action result.
   - `console_messages() -> list`, `network_requests() -> list`
   - `clear_modal_state(type)` -- remove handled modal from `_modal_states`
   - **AC:** Tab captures console/network events. `ref_locator("e6")` returns a working Playwright locator. `wait_for_completion()` implements all 3 phases. `_race_against_modal_states()` detects pre-existing and new modals.

3. **Implement `snapshot.py`**
   - **`async snapshot_for_ai(page) -> str`**:
     1. Call `result = await page._impl_obj._channel.send("snapshotForAI", _timeout_calc, {})` where `_timeout_calc = lambda t=None: t if t is not None else 30000.0`
     2. **Runtime validation:** `assert isinstance(result, str) and result.strip()`, with clear error message on failure: "snapshotForAI returned unexpected format for the current Python Playwright binding."
     3. Return the YAML snapshot string as-is
   - `_timeout_calc` helper function
   - Handle the case where API is unavailable (raise clear error with version info)
   - **Startup-time API availability check:** In `ensure_browser()`, after browser launch, verify `snapshotForAI` is callable on a blank page and yields a string snapshot.
   - **Note:** `track: "response"` and structured `{full, incremental}` snapshots are not part of the v1 contract unless a later Python-side verification proves them.
   - **AC:** Returns a YAML string containing `[ref=eN]` markers. Runtime assertion catches missing/non-string return values.

4. **Implement `Response` builder in `response.py`**
   - `class Response` with methods such as `add_result(text)`, `add_error(text)`, `add_snapshot(snapshot_yaml: str)`, `add_events(entries)`
   - `serialize() -> list[TextContent]` -- builds markdown with upstream-inspired sections such as `### Result`, `### Error`, `### Page`, `### Snapshot`, `### Events`, plus optional `### Open tabs` / `### Modal state` when relevant
   - Keep section names stable for AI clients, but do not promise exact byte-for-byte parity with upstream Node output
   - **AC:** `response.add_result("Navigated"); response.add_snapshot(snapshot_yaml); response.serialize()` produces correctly formatted markdown with stable section headers.

5. **Implement `@tab_tool` decorator in `tools/decorators.py`**
   - A 10-20 line decorator/helper that wraps tool handler functions to:
     1. Extract `app = ctx.request_context.lifespan_context` (AppContext)
     2. `tab = await app.ensure_tab()`
     3. Check modal state via `tab._race_against_modal_states()` (for action tools)
     4. Catch stale ref errors and convert to friendly message: "Ref {ref} not found. Page may have changed. Use browser_snapshot to get fresh refs."
     5. Pass `app` and `tab` as arguments to the wrapped function
   - Two variants: `@tab_tool` (standard) and `@tab_tool(modal_check=True)` (with modal racing)
   - **AC:** Tool handlers using `@tab_tool` are ~5 lines shorter. Stale ref errors produce friendly messages. Modal states are checked before action tools.

### Acceptance Criteria
- Browser launches lazily on first tool call, managed manually (not via AsyncCamoufox context manager)
- Browser disconnect sets state to None for automatic re-launch
- asyncio.Lock protects browser operations
- Tab wraps Page with event listeners and modal state tracking
- `snapshot_for_ai()` returns a YAML string that can be rendered directly
- Runtime validation catches missing or non-string `snapshotForAI` results
- `ref_locator()` returns working Playwright locator from ref ID
- `wait_for_completion()` implements full 3-phase algorithm
- `_race_against_modal_states()` handles pre-existing and racing modals
- Response builder produces playwright-mcp-compatible markdown output
- `@tab_tool` decorator eliminates per-tool boilerplate

---

## Phase 3: Core Navigation + Snapshot Tools

**Goal:** Implement the first batch of tools -- the ones needed for basic browsing: snapshot, navigate, navigate_back, navigate_forward, tabs. All tab-bound tools use `@tab_tool`; context-level tools keep direct registration.

### Files to Create/Modify
- `camoufox_mcp/tools/__init__.py` -- aggregates register functions
- `camoufox_mcp/tools/snapshot_tools.py` -- browser_snapshot, browser_click, browser_hover, browser_drag, browser_select_option
- `camoufox_mcp/tools/navigate_tools.py` -- browser_navigate, browser_navigate_back, browser_navigate_forward
- `camoufox_mcp/tools/tab_tools.py` -- browser_tabs (list/new/select/close)

### Detailed TODOs

1. **Implement snapshot tools (`snapshot_tools.py`)**
   - All tools use `@tab_tool` decorator (or `@tab_tool(modal_check=True)` for action tools)
   - `browser_snapshot(tab, app)` -- capture the latest full YAML snapshot string and return it as Response
   - `browser_click(element: str, ref: str, tab, app)` -- ref_locator -> `tab.wait_for_completion(lambda: locator.click())` -> capture snapshot -> return Response. Uses `@tab_tool(modal_check=True)`.
   - `browser_hover(element: str, ref: str, tab, app)` -- ref_locator -> hover -> capture snapshot
   - `browser_drag(startElement, startRef, endElement, endRef, tab, app)` -- two ref_locators -> dragTo -> snapshot
   - `browser_select_option(element, ref, values: list[str], tab, app)` -- ref_locator -> selectOption -> snapshot
   - **AC:** `browser_snapshot` returns the YAML tree string with ref markers. `browser_click` with valid ref clicks element and returns an updated snapshot. Modal states are checked before click/hover/drag.

2. **Implement navigation tools (`navigate_tools.py`)**
   - `browser_navigate(url: str, tab, app)` -- `tab.wait_for_completion(lambda: page.goto(url, wait_until="domcontentloaded"))`, capture snapshot
   - `browser_navigate_back(tab, app)` -- `tab.wait_for_completion(lambda: page.go_back())`, capture snapshot
   - `browser_navigate_forward(tab, app)` -- `tab.wait_for_completion(lambda: page.go_forward())`, capture snapshot
   - **AC:** `browser_navigate("https://example.com")` loads page using full wait_for_completion algorithm and returns snapshot with page content.

3. **Implement tab management (`tab_tools.py`)**
   - `browser_tabs(action: str, index?: int, ctx)` -- `action` is `"list"|"new"|"select"|"close"` to stay aligned with upstream schema
   - list: return tab list with URLs and titles
   - new: create new tab
   - select: switch current tab by index
   - close: close tab by index (or current)
   - **AC:** Can create, list, switch between, and close tabs.

4. **Wire up tool registration in `server.py` and `tools/__init__.py`**
   - Each tool module exports `register(mcp, config)` that calls `@mcp.tool()` on each function
   - `tools/__init__.py` exports `register_all(mcp, config)` that calls each module's register
   - **AC:** MCP `tools/list` returns all registered tools with correct schemas.

### Acceptance Criteria
- `browser_navigate` + `browser_snapshot` roundtrip works end-to-end
- `browser_click` with ref from snapshot successfully clicks element
- Tab management (new/list/select/close) functional
- All tools return structured markdown responses with correct section headers
- `@tab_tool` decorator used consistently across all tool handlers

---

## Phase 4: Interaction + Input Tools

**Goal:** Implement text input, keyboard, form filling, and checkbox tools.

### Files to Create
- `camoufox_mcp/tools/input_tools.py` -- browser_type, browser_press_key, browser_fill_form, browser_check, browser_uncheck

### Detailed TODOs

1. **Implement `browser_type(element, ref, text, submit?, tab, app)`**
   - Uses `@tab_tool(modal_check=True)`
   - ref_locator -> clear existing text -> type new text
   - If submit=True, press Enter after typing
   - `tab.wait_for_completion(...)` -> capture snapshot
   - **AC:** Types text into input field; submit=True triggers form submission.

2. **Implement `browser_press_key(key: str, tab, app)`**
   - Uses `@tab_tool(modal_check=True)`
   - `page.keyboard.press(key)` -- supports "Enter", "Tab", "Escape", key combos like "Control+A"
   - `tab.wait_for_completion(...)` -> capture snapshot
   - **AC:** `browser_press_key("Enter")` presses Enter on current page.

3. **Implement `browser_fill_form(fields: list[dict], tab, app)`**
   - Uses `@tab_tool`
   - Each field follows the upstream core shape: `{name: str, type: "textbox"|"checkbox"|"radio"|"combobox"|"slider", ref: str, value: str}`
   - Iterate fields and dispatch by `type` (`fill`, `set_checked`, `select_option`, etc.)
   - Single snapshot at the end
   - **AC:** Fills multiple form fields in one call without inventing a custom schema.

4. **Implement `browser_check(element, ref, tab, app)` and `browser_uncheck(element, ref, tab, app)`**
   - Uses `@tab_tool`
   - ref_locator -> check()/uncheck()
   - **AC:** Toggles checkbox state.

### Acceptance Criteria
- Text input works in search boxes, forms
- Keyboard shortcuts work (Enter, Tab, Escape, combos)
- Batch form filling works
- Checkbox toggle works
- All tools use `@tab_tool` decorator

---

## Phase 5: Utility + Dangerous Tools

**Goal:** Implement remaining utility tools and the gated dangerous tools.

### Files to Create
- `camoufox_mcp/tools/page_tools.py` -- browser_take_screenshot, browser_console_messages, browser_network_requests
- `camoufox_mcp/tools/common_tools.py` -- browser_close, browser_resize, browser_wait_for
- `camoufox_mcp/tools/file_tools.py` -- browser_file_upload, browser_handle_dialog
- `camoufox_mcp/tools/dangerous_tools.py` -- browser_evaluate (only registered with --caps dangerous)

### Detailed TODOs

1. **Implement page observation tools (`page_tools.py`)**
   - `browser_take_screenshot(tab, app)` -- call Playwright screenshot APIs and return an MCP image attachment (PNG/JPEG), with optional element/full-page targeting
   - `browser_console_messages(tab, app)` -- return collected console messages from Tab
   - `browser_network_requests(tab, app)` -- return collected network requests from Tab
   - **AC:** Screenshot returns a usable MCP image response, not an ad hoc base64 string stuffed into plain text. Console/network return collected entries.

2. **Implement common tools (`common_tools.py`)**
   - `browser_close(ctx)` -- close the current browser context/session, mirroring upstream `browser_close` semantics; tab-level close remains under `browser_tabs(action="close")`
   - `browser_resize(width: int, height: int, tab, app)` -- page.set_viewport_size()
   - `browser_wait_for(time?: float, text?: str, textGone?: str, ctx)` -- align with upstream wait schema: support waiting by duration, visible text, or disappearing text
   - **AC:** Resize changes viewport. Wait blocks until text appears or timeout.

3. **Implement file/dialog tools (`file_tools.py`)**
   - `browser_file_upload(paths: list[str], tab, app)` -- Uses `_race_against_modal_states()` to handle file chooser modal. Sets input files on the file chooser from `_modal_states`.
   - `browser_handle_dialog(accept: bool, promptText?: str, tab, app)` -- Accept or dismiss dialog from `_modal_states`. Clears modal state after handling.
   - Both tools interact with Tab's `_modal_states` queue
   - **AC:** File upload sets files on file chooser. Dialog handling accepts/dismisses alerts. Modal states are properly consumed.

4. **Implement dangerous tools (`dangerous_tools.py`)**
   - `browser_evaluate(function: str, ref?: str, element?: str, tab, app)` -- align with upstream parameter shape. By default, this still uses Camoufox's isolated-world semantics; DOM mutation in the main world requires explicit runtime support such as `main_world_eval`.
   - `browser_run_code` -- **defer out of v1**. Upstream executes JavaScript Playwright snippets inside a Node `vm`, which the Python server cannot honestly claim to replicate without adding a JS runtime bridge.
   - **GATING:** `register()` is a no-op unless `config.caps` includes `"dangerous"`
   - **AC:** `browser_evaluate` is only available with `--caps dangerous`. `browser_run_code` is explicitly absent from v1 docs and registration.

### Acceptance Criteria
- Screenshots work as MCP image responses
- Console/network request collection works
- Dialog/file handling uses modal state queue pattern
- `browser_evaluate` is ONLY available with `--caps dangerous`
- All tools return structured markdown responses

---

## Phase 6: Integration Testing + Polish

**Goal:** End-to-end validation, error handling hardening, and release readiness.

### Files to Create/Modify
- `tests/` directory with integration tests
- `README.md` (if requested)
- Error handling improvements across all modules

### Detailed TODOs

1. **End-to-end smoke test**
   - Start server -> browser_navigate("https://example.com") -> browser_snapshot -> verify ref IDs in output -> browser_click(ref) -> verify navigation
   - Multi-step flow: navigate -> type in search -> submit -> verify results
   - Verify repeated snapshots continue to return valid YAML with stable ref usage semantics after each action
   - Verify `wait_for_completion` 3-phase behavior (navigation vs. resource-only)
   - **AC:** Full automation flow works without detection on a test site.

2. **Error handling hardening**
   - Stale ref: `@tab_tool` catches locator errors, returns "Ref {ref} not found. Page may have changed. Use browser_snapshot to get fresh refs."
   - Browser crash/disconnect: `_on_browser_disconnect()` sets state to None, next call triggers re-launch with clear log message
   - snapshotForAI format error: runtime assertion with Playwright version info
   - Navigation timeout: return friendly error with suggestion
   - Invalid CLI args: clear error messages
   - Concurrent tool calls: `asyncio.Lock` prevents race conditions, waiting calls get a "busy" message or queue
   - **AC:** All error paths return actionable messages, not stack traces.

3. **Anti-detection validation**
   - Run against creepjs.com or similar fingerprint checker
   - Verify: no WebRTC leak (with --block-webrtc), geoip spoofing works, and `humanize` works when explicitly enabled
   - **AC:** Bot detection score is low/undetected on test sites.

4. **Claude Code integration test**
   - Add to Claude Code MCP config: `{"command": "camoufox-mcp", "args": ["--proxy", "...", "--geoip", "true"]}`
   - Verify tools appear in Claude Code tool list
   - Verify basic browse-and-interact flow works from Claude Code
   - **AC:** Claude Code can successfully use camoufox-mcp tools to browse websites.

### Acceptance Criteria
- Smoke tests pass
- Error messages are user-friendly
- Anti-detection works on test sites
- Claude Code integration works
- Browser disconnect recovery works

---

## Success Criteria (Overall)

1. `camoufox-mcp` CLI starts MCP server on STDIO
2. All ~20 core tools registered and functional
3. Ref-based interaction works: snapshot -> ref -> click/type roundtrip
4. Anti-detection capabilities work (fingerprint, proxy, geoip, optional humanize)
5. Dangerous tools gated behind `--caps dangerous`
6. Browser lazy-loads on first tool call (without AsyncCamoufox context manager), cleans up on shutdown
7. Structured markdown responses match playwright-mcp format (section headers compatible)
8. Repeated full YAML snapshots remain reliable and preserve the ref-based interaction loop
9. `wait_for_completion()` implements full 3-phase algorithm
10. Browser disconnect triggers automatic state reset for re-launch
11. `@tab_tool` decorator used consistently, eliminating per-tool boilerplate

---

## Target Architecture (Final)

```
camoufox_mcp/
  __init__.py              # Package init, __version__
  __main__.py              # CLI entry: argparse -> CamoufoxConfig -> create_server -> mcp.run()
  server.py                # create_server(): FastMCP + lifespan + register_all()
  config.py                # CamoufoxConfig dataclass + to_launch_kwargs() + from_cli_args()
  context.py               # AppContext: browser lazy-load (manual playwright/camoufox), tab mgmt, asyncio.Lock, disconnect detection
  tab.py                   # Tab: Page wrapper, console/network logs, ref_locator, wait_for_completion (3-phase), _race_against_modal_states
  snapshot.py              # snapshot_for_ai(): snapshotForAI wrapper returning YAML string, runtime validation
  response.py              # Response builder: Result/Error/Snapshot/Events markdown sections
  tools/
    __init__.py            # register_all(mcp, config) -> calls each module's register()
    decorators.py          # @tab_tool decorator: AppContext extraction, ensure_tab, modal check, stale-ref error handling
    snapshot_tools.py      # browser_snapshot, browser_click, browser_hover, browser_drag, browser_select_option
    navigate_tools.py      # browser_navigate, browser_navigate_back, browser_navigate_forward
    input_tools.py         # browser_type, browser_press_key, browser_fill_form, browser_check, browser_uncheck
    tab_tools.py           # browser_tabs (list/new/select/close)
    page_tools.py          # browser_take_screenshot, browser_console_messages, browser_network_requests
    common_tools.py        # browser_close, browser_resize, browser_wait_for
    file_tools.py          # browser_file_upload, browser_handle_dialog
    dangerous_tools.py     # browser_evaluate (gated: --caps dangerous), browser_run_code deferred
pyproject.toml             # uv/pip metadata, entry points, dependencies
tests/
  test_smoke.py            # End-to-end smoke tests
```

## Dependency Graph

```
__main__.py -> config.py -> server.py
server.py -> context.py, tools/*
context.py -> tab.py -> snapshot.py
tools/decorators.py -> context.py, tab.py
tools/* -> decorators.py, response.py
```

All tool modules depend on `decorators.py` (for `@tab_tool`), and `response.py` (for Response builder). The decorator depends on `context.py` and `tab.py`. No circular dependencies.

---

## Revision Changelog

### 2026-03-14 (Architect/Critic Review)

**Critical fixes:**
1. **snapshotForAI Python contract**: Corrected the v1 plan to use the currently verified Python behavior: `_channel.send("snapshotForAI", ...)` returns a YAML `str`, not a `{full, incremental}` object. Incremental snapshots were removed from the v1 contract.
2. **Compatibility claim**: Downgraded "interchangeable" wording to "align where practical with documented divergences", so the plan no longer promises more than the Python/Camoufox runtime can deliver.
3. **Dangerous tool scope**: Kept `browser_evaluate` behind `--caps dangerous`, but moved `browser_run_code` out of v1 because upstream relies on a Node `vm` JavaScript runtime.

**Major fixes:**
4. **Tool schema alignment**: Updated `browser_tabs`, `browser_fill_form`, `browser_wait_for`, `browser_take_screenshot`, and `browser_close` descriptions to stop drifting away from upstream shapes/semantics without documentation.
5. **Camoufox default alignment**: Restored `humanize` to the current Camoufox default (`False`) instead of hard-coding an unverified behavioral change.

**Moderate improvements:**
6. **Response model wording**: Clarified that v1 follows the upstream section model but does not promise byte-for-byte parity or identical attachment behavior.
7. **Lazy-load without AsyncCamoufox context manager**: Kept the direct `async_playwright().start()` + `AsyncNewBrowser()` approach, but grounded the rest of the plan in the actual Python API surface.

**Other improvements:**
8. **Runtime snapshot validation**: Validation now checks for a non-empty YAML string rather than a dict structure that does not exist in the current Python binding.
9. **Browser disconnect detection**: `browser_context.on("close")` still resets state for re-launch.
10. **asyncio.Lock**: Still protects browser operations for serial execution.
11. **Playwright version awareness**: Compatibility notes now explicitly reference the verified local environment (`camoufox 0.4.11`, `playwright 1.58.0`).
