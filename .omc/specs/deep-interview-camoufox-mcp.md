# Deep Interview Spec: Camoufox MCP Server

## Metadata
- Interview ID: di-camoufox-mcp-001
- Rounds: 17
- Final Ambiguity Score: 4%
- Type: greenfield
- Generated: 2026-03-14
- Threshold: 20%
- Status: PASSED

## Clarity Breakdown
| Dimension | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| Goal Clarity | 0.98 | 0.40 | 0.392 |
| Constraint Clarity | 0.98 | 0.30 | 0.294 |
| Success Criteria | 0.90 | 0.30 | 0.270 |
| **Total Clarity** | | | **0.956** |
| **Ambiguity** | | | **0.044** |

## Goal

构建一个 Python MCP 服务器 (camoufox-mcp)，将 camoufox 反检测浏览器封装为类似 playwright-mcp 的工具接口，供 AI 编程助手（Claude Code、Cursor 等）通过 STDIO 协议调用。服务器提供 ~20 个核心浏览器自动化工具（基于可访问性树 + ref 元素定位）和 camoufox 反检测能力（指纹伪装、代理、地理位置欺骗等），通过 CLI 参数在启动时配置反检测参数，并采用能力分级门控保护危险操作。

## Constraints

- **语言**: Python 3.10+，使用 `mcp` Python SDK 构建 MCP 服务器
- **浏览器引擎**: 直接调用 camoufox Python 库（`Camoufox`/`AsyncCamoufox`），底层基于 Playwright Firefox
- **传输协议**: v1 仅支持 STDIO（Claude Code/Cursor 集成场景）；SSE/HTTP 留待后续迭代
- **元素定位**: 可访问性树 (accessibility tree) + ref ID，与 playwright-mcp 一致
- **反检测配置**: 启动时通过 CLI 参数传入，运行时不可变（符合 camoufox 的指纹注入设计）
- **安全模型**: 能力分级门控（capability gating）
  - 默认启用：安全的核心浏览器操作工具
  - 需显式 `--caps` 启用：`browser_evaluate` 等高风险工具
  - `browser_run_code` 不纳入 v1，原因是 Python 方案无法诚实复刻 upstream 基于 Node `vm` 的 JS 运行时语义
- **MVP 范围**: playwright-mcp 核心 ~20 工具 + camoufox 反检测配置，可选能力组后续迭代
- **浏览器生命周期**: 懒加载（首次工具调用时启动），服务器关闭时自动清理
- **会话模式**: 默认使用 `persistent_context`（持久化浏览器配置文件，保留 Cookie/登录状态），通过 `--user-data-dir` 指定路径
- **显示模式**: 默认 headed（有界面），通过 `--headless` 切换到无界面模式
- **打包工具**: uv + pyproject.toml，可发布到 PyPI
- **Ref 系统策略**: 已验证 ref roundtrip 可用 — 通过 `page._impl_obj._channel.send("snapshotForAI")` 获取带 ref ID 的 YAML 快照字符串，并通过 `page.locator("aria-ref=<ref>")` 定位元素
- **响应格式**: 参考 playwright-mcp 的结构化 markdown section 模型；v1 对齐关键 section 名称与交互节奏，但不承诺逐字节一致或完整附件/文件输出特性
- **快照模式**: v1 先支持全量 YAML 快照；Python 侧增量快照能力待后续验证，不作为当前验收项
- **异常处理**: 过期 ref 返回友好错误 + 建议重新调用 browser_snapshot；浏览器崩溃时自动重启
- **状态共享**: 通过 FastMCP lifespan 注入 Context，工具通过 `ctx.request_context.lifespan_context` 获取

## Non-Goals

- 不实现 TypeScript 版本或跨语言桥接
- v1 不实现 playwright-mcp 的所有可选能力组（vision/pdf/testing/storage/network 等后续迭代）
- 不实现运行时动态修改指纹/代理（camoufox 设计上不支持）
- 不实现 Chrome/Edge CDP 桥接模式（camoufox 仅基于 Firefox）
- 不实现浏览器扩展桥接模式（playwright-mcp 的 extension bridge）
- 不实现多浏览器实例并发管理（v1 单实例）
- 不实现 `browser_run_code` 的 1:1 JavaScript runtime 兼容
- 不实现 SSE/HTTP transport

## Acceptance Criteria

- [ ] MCP 服务器可通过 `python -m camoufox_mcp` 或 `camoufox-mcp` 命令启动
- [ ] 支持 STDIO 传输协议，可在 Claude Code 的 MCP 配置中添加使用
- [ ] CLI 参数支持反检测配置：`--proxy`、`--os`、`--humanize`、`--block-webrtc`、`--block-webgl`、`--geoip`、`--headless` 等
- [ ] 实现 `browser_snapshot` 工具：返回可访问性树，每个可交互元素带 ref ID
- [ ] 实现 `browser_navigate` 工具：导航到指定 URL
- [ ] 实现 `browser_click` 工具：通过 ref ID 点击元素
- [ ] 实现 `browser_type` 工具：在输入框中输入文本
- [ ] 实现 `browser_fill_form` 工具：批量填充表单
- [ ] 实现 `browser_select_option` 工具：选择下拉选项
- [ ] 实现 `browser_hover` 工具：悬停在元素上
- [ ] 实现 `browser_press_key` 工具：发送键盘按键
- [ ] 实现 `browser_navigate_back` 工具：浏览器后退
- [ ] 实现 `browser_wait_for` 工具：等待文本出现或超时
- [ ] 实现 `browser_take_screenshot` 工具：截取页面/元素截图
- [ ] 实现 `browser_console_messages` 工具：获取控制台消息
- [ ] 实现 `browser_network_requests` 工具：列出网络请求
- [ ] 实现 `browser_tabs` 工具：标签页管理（列出/创建/关闭/切换）
- [ ] 实现 `browser_close` 工具：关闭当前浏览器会话/上下文
- [ ] 实现 `browser_resize` 工具：调整视口大小
- [ ] 实现 `browser_drag` 工具：拖拽操作
- [ ] 实现 `browser_file_upload` 工具：文件上传
- [ ] 实现 `browser_handle_dialog` 工具：处理对话框
- [ ] 能力门控：`browser_evaluate` 需要 `--caps dangerous` 启用；`browser_run_code` 不属于 v1 范围
- [ ] 浏览器懒加载：首次工具调用时才启动 camoufox
- [ ] 在公开测试站点或选定目标站点上完成一次基础访问链路，并记录反检测配置是否生效
- [ ] 多步骤自动化流程（打开网站 → 登录 → 导航 → 提取数据）可在选定验证场景中完成，且未出现明显自动化阻断

## Assumptions Exposed & Resolved

| Assumption | Challenge | Resolution |
|------------|-----------|------------|
| 需要复刻 playwright-mcp 全部 ~70 个工具 | Simplifier: 是否所有工具在 v1 都必要？ | MVP 只需核心 ~20 工具，可选能力组后续迭代 |
| 所有 playwright-mcp 工具都适合反检测 | Contrarian: JS 执行和任意运行时代码会破坏反检测或超出 Python 能力边界 | 采用能力分级门控；`browser_evaluate` 走危险能力组，`browser_run_code` 移出 v1 |
| 反检测参数需要运行时动态调整 | camoufox 指纹在启动时注入不可变 | 启动时配置，符合 camoufox 设计 |
| 需要 Poetry 与 camoufox 原项目保持一致 | 现代 Python 工具链选择 | 使用 uv + pyproject.toml，更快更现代 |
| 浏览器默认 headless 节省资源 | AI 操作需要可观察性和调试便利 | 默认 headed，--headless 切换 |
| 临时会话更安全 | 多步骤登录场景需要状态持久化 | 默认 persistent_context，保留 Cookie/登录状态 |
| 可以直接使用 Playwright 内部 API _snapshotForAI | camoufox 的 Playwright 版本可能不支持 | **已验证部分可用** — 当前 Python 环境可通过 `page._impl_obj._channel.send("snapshotForAI")` 取得 YAML 字符串，并用 `aria-ref` 定位元素；不假设 Python 层存在 `page._snapshotForAI()` |
| 每次返回全量快照 | 大页面 token 消耗过高 | v1 先使用全量 YAML 快照；增量快照待 Python 绑定侧再验证 |
| 工具间状态用全局单例共享 | 架构耦合度高 | 用 FastMCP lifespan 注入，更干净的依赖管理 |
| 错误直接抛出让 AI 处理 | AI 无法理解底层错误 | 友好错误消息 + 建议动作（如"请先调用 browser_snapshot"）|

## Technical Context

### Camoufox 项目结构
- 源码位置: `/Users/libre/code/python/camoufox/pythonlib/camoufox/`
- 入口 API: `Camoufox` (sync), `AsyncCamoufox` (async) 上下文管理器
- 核心函数: `launch_options()` 构建 Playwright 启动配置
- 指纹系统: `fingerprints.generate_fingerprint()` 使用 BrowserForge
- 地理位置: `geolocation.get_geolocation()` 基于 MaxMind GeoIP
- 依赖: playwright, browserforge, orjson, requests, numpy 等

### playwright-mcp 参考架构（源码分析: /Users/libre/code/ai/playwright-mcp/）

**三层架构:**
```
CLI (cli.js) / Library (index.js)
       |
       v
BrowserServerBackend(config, contextFactory)
  - listTools() -> browserTools.map(toMcpTool)
  - callTool(name, args) -> tool.handle(context, params, response)
       |
       v
Context (浏览器生命周期) -> Tab[] (页面状态/快照/ref)
```

**核心模式详解:**

1. **工具定义模式**: `defineTool(schema, capability, handle)` / `defineTabTool(...)` — 声明式，Tab 版本自动处理模态状态（dialog/fileChooser）
2. **Ref 系统**: upstream JS 使用 `page._snapshotForAI()`；但在当前 Python 方案中，已验证入口是 `page._impl_obj._channel.send("snapshotForAI", ...)`，返回 YAML 字符串，其中包含 `ref` 标记。后续工具用 `aria-ref=<ref>` 选择器定位元素。Ref 是临时的，每次新 snapshot 后旧 ref 失效
3. **Response 构建器**: 结构化 markdown 响应，至少稳定输出 Result / Error / Snapshot / Events 等核心 section，并在需要时补充 Page / Open tabs / Modal state
4. **waitForCompletion**: 操作后等待网络请求稳定（500ms 静默 + 导航等待），再截取快照
5. **能力门控**: `core*` 前缀始终启用，其他（vision/storage/network/testing/devtools/pdf）需 `--caps` 显式启用
6. **浏览器工厂**: PersistentContextFactory (默认) / IsolatedContextFactory / CdpContextFactory 等

**关键文件映射:**
- `sdk/server.js`: MCP Server 创建，注册 ListTools/CallTool handlers
- `browser/browserServerBackend.js`: 核心后端，listTools + callTool 调度
- `browser/context.js`: 浏览器生命周期、Tab 数组管理、懒加载
- `browser/tab.js`: 页面状态、console/network 日志、snapshot 捕获、ref 解析
- `browser/response.js`: 响应构建器
- `browser/tools/*.js`: 各工具实现（snapshot.js, navigate.js, keyboard.js 等）

### Python MCP SDK 方案

**官方包**: `mcp>=1.25,<2` (PyPI)，Python 3.10+

**推荐使用 FastMCP**（已内置在 mcp SDK 中）:
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("camoufox-mcp", instructions="Anti-detect browser automation")

@mcp.tool()
async def browser_navigate(url: str) -> str:
    """Navigate to a URL."""
    ...

if __name__ == "__main__":
    mcp.run()  # STDIO by default
```

**关键模式:**
- 装饰器 `@mcp.tool()` + 类型注解自动生成 JSON Schema
- `lifespan` 上下文管理器管理浏览器实例的生命周期
- 模块化注册: 每个工具模块提供 `register(mcp)` 函数
- `mcp.run()` 默认 STDIO；其他 transport 能力存在于 SDK，但不属于 v1 范围
- `Context` 参数注入支持进度报告

**Lifespan 模式（管理浏览器实例）:**
```python
@asynccontextmanager
async def lifespan(server: FastMCP):
    browser_ctx = await create_camoufox_context(config)
    yield {"browser": browser_ctx}
    await browser_ctx.close()

mcp = FastMCP("camoufox-mcp", lifespan=lifespan)
```

### 技术选型
- Python MCP SDK: `mcp>=1.25,<2` 包（官方 SDK，FastMCP 高层 API）
- 异步框架: asyncio（camoufox 的 AsyncCamoufox 基于 async/await）
- CLI: FastMCP 内置参数 + 自定义 argparse（解析 --proxy、--os 等反检测参数）
- 项目管理: uv + pyproject.toml（可发布 PyPI）
- 参考实现: `rlgrpe/camoufox-mcp-python` (GitHub)

### Ref 系统实现方案（已验证）

**结论：ref roundtrip 方案可行，无需自建 ref 映射；但 Python v1 仅以全量 YAML 快照为已验证契约。**

在 camoufox + Playwright 1.58.0 上的验证结果（2026-03-14）：

| API | 可用性 | 说明 |
|-----|--------|------|
| `page._impl_obj._channel.send("snapshotForAI", timeout_calc, {})` | **可用** | 返回带 `[ref=eN]` 的可访问性树 YAML 字符串 |
| `page.locator("aria-ref=eN")` | **可用** | 通过 ref ID 精确定位元素 |
| `snapshotForAI` + `track: "response"` | **未验证为增量契约** | 当前 Python 环境下仍观测到字符串返回，不能据此宣称支持结构化增量快照 |
| `page._snapshotForAI()` | **当前 Python 环境不可用** | Python `Page` 上未暴露该 helper |
| `locator.aria_snapshot()` | **可用** | 公开 API，但不含 ref ID（备用方案） |

**调用方式（Python）：**
```python
# TimeoutCalculator: Callable[[Optional[float]], float]
def _timeout_calc(t=None):
    return t if t is not None else 30000.0

# 获取快照（带 ref ID）
impl_page = page._impl_obj
result = await impl_page._channel.send("snapshotForAI", _timeout_calc, {})
# result 是 YAML 字符串，如:
# - generic [ref=e2]:
#   - heading "Example Domain" [level=1] [ref=e3]
#   - link "Learn more" [ref=e6] [cursor=pointer]

# 通过 ref 定位元素
locator = page.locator("aria-ref=e6")
await locator.click()

```

**注意事项：**
- `snapshotForAI` 不是公开 API，属于 Playwright 内部协议，未来版本可能变化
- ref ID 是临时的，每次新快照后旧 ref 失效
- 需要通过 `page._impl_obj` 访问内部通道，不是标准用法
- 当前 Python 绑定未暴露 `page._snapshotForAI()`，也未验证出结构化 `{full, incremental}` 返回值

## Ontology (Key Entities)

| Entity | Fields | Relationships |
|--------|--------|---------------|
| FastMCP Server | name, instructions, lifespan, tools[] | 入口，管理 Context |
| Context | browser, browser_context, tabs[], current_tab, config, routes[] | 管理浏览器生命周期和 Tab 数组 |
| Tab | page, console_log[], network_requests[], modal_states[], last_snapshot_yaml | 包装 Playwright Page，并基于 `aria-ref` 直接定位元素 |
| Tool | name, description, input_schema, capability, handle() | 注册到 FastMCP，分 core/dangerous 能力组 |
| Response | sections: result/error/code/snapshot/events | 工具 handle() 填充，序列化为 markdown |
| CamoufoxConfig | proxy, os, humanize, geoip, block_webrtc, headless, user_data_dir, etc. | CLI 解析后传入 Context 启动参数 |

## Architecture (Python 实现蓝图)

```
camoufox_mcp/
├── __init__.py
├── __main__.py              # CLI 入口: argparse 解析反检测参数 + mcp.run()
├── server.py                # FastMCP 实例创建 + lifespan + 工具注册
├── context.py               # Context: 浏览器懒加载、Tab 管理、能力门控
├── tab.py                   # Tab: 页面状态、snapshot 捕获、ref 解析
├── response.py              # Response 构建器 (markdown sections)
├── snapshot.py              # snapshotForAI 封装 + YAML 快照处理
├── config.py                # CamoufoxConfig: CLI 参数 → camoufox launch_options 映射
└── tools/
    ├── __init__.py           # 聚合所有工具模块
    ├── snapshot_tools.py     # browser_snapshot, browser_click, browser_hover, browser_drag
    ├── navigate_tools.py     # browser_navigate, browser_navigate_back
    ├── input_tools.py        # browser_type, browser_press_key, browser_fill_form, browser_select_option
    ├── page_tools.py         # browser_take_screenshot, browser_console_messages, browser_network_requests
    ├── tab_tools.py          # browser_tabs
    ├── common_tools.py       # browser_close, browser_resize, browser_wait_for
    ├── file_tools.py         # browser_file_upload, browser_handle_dialog
    └── dangerous_tools.py    # browser_evaluate (需 --caps dangerous)，browser_run_code 不在 v1
```

**数据流:**
```
Claude Code/Cursor
  → STDIO Transport
    → FastMCP Server (mcp.run())
      → @mcp.tool() handler
        → Context.ensure_tab()  (懒加载浏览器)
          → Tab.ref_locator(ref)  (ref → Playwright locator)
            → Playwright action (click/type/navigate...)
              → Tab.capture_snapshot()  (刷新可访问性树 + ref)
                → Response 序列化 (markdown)
                  → STDIO → Claude Code
```

## Interview Transcript

以下问答记录保留了访谈阶段的原始结论；若后续源码/本机验证推翻了其中某个技术假设，以本 spec 当前正文为准。

<details>
<summary>Full Q&A (17 rounds)</summary>

### Round 1
**Q:** 这个 MCP 服务器的核心定位是什么？
**A:** 全量浏览器自动化 + 反检测
**Ambiguity:** 74% (Goal: 0.50, Constraints: 0.10, Criteria: 0.10)

### Round 2
**Q:** Camoufox 是 Python 库，而 playwright-mcp 是 TypeScript 实现。你希望用什么语言实现？
**A:** Python（推荐）
**Ambiguity:** 67% (Goal: 0.50, Constraints: 0.35, Criteria: 0.10)

### Round 3
**Q:** 你计划如何使用这个 MCP 服务器？主要的使用场景是什么？
**A:** 集成到 Claude Code/Cursor
**Ambiguity:** 55% (Goal: 0.60, Constraints: 0.40, Criteria: 0.30)

### Round 4
**Q:** [可访问性树 + ref 引用] 作为元素定位方式？
**A:** 可访问性树 + ref（推荐）
**Ambiguity:** 48% (Goal: 0.75, Constraints: 0.45, Criteria: 0.30)

### Round 5 (Contrarian Mode)
**Q:** 不是所有 playwright-mcp 的工具都适合反检测场景，应该如何处理这种矛盾？
**A:** 能力分级门控
**Ambiguity:** 40% (Goal: 0.82, Constraints: 0.55, Criteria: 0.35)

### Round 6
**Q:** 验收场景是什么？
**A:** 以上都要具备（Claude Code 反爬访问 + 多步骤自动化 + 对标 playwright-mcp 功能）
**Ambiguity:** 33% (Goal: 0.85, Constraints: 0.55, Criteria: 0.55)

### Round 7 (Simplifier Mode)
**Q:** v1 的最简可行范围是什么？
**A:** 核心 20 工具 + 反检测配置
**Ambiguity:** 27% (Goal: 0.90, Constraints: 0.60, Criteria: 0.65)

### Round 8
**Q:** Camoufox 的反检测特性应该在什么时机配置？
**A:** 启动时配置（推荐）
**Ambiguity:** 21% (Goal: 0.93, Constraints: 0.70, Criteria: 0.70)

### Round 9
**Q:** 用户如何配置反检测参数？
**A:** CLI 参数（推荐）
**Ambiguity:** 16% (Goal: 0.95, Constraints: 0.80, Criteria: 0.75)

### Round 10 (Refinement)
**Q:** MCP 服务器是否需要支持持久化会话？
**A:** 支持持久化（推荐） — 默认 persistent_context，通过 --user-data-dir 指定路径
**Ambiguity:** 13% (Goal: 0.95, Constraints: 0.85, Criteria: 0.78)

### Round 11
**Q:** 浏览器默认应该是 headless 还是 headed？
**A:** Headed 默认（推荐） — 通过 --headless 切换
**Ambiguity:** 11% (Goal: 0.96, Constraints: 0.90, Criteria: 0.80)

### Round 12
**Q:** 项目的打包和分发方式？
**A:** uv + pyproject.toml（推荐） — 可发布到 PyPI
**Ambiguity:** 9% (Goal: 0.96, Constraints: 0.93, Criteria: 0.82)

### Round 13 (Refinement)
**Q:** Ref 系统是整个项目的技术核心，如何处理 _snapshotForAI 可能不存在的风险？
**A:** 先验证再决定 — 执行阶段先检查 API 可用性，可用直接复用，不可用回退自建方案
**Ambiguity:** 8% (Goal: 0.96, Constraints: 0.95, Criteria: 0.84)

### Round 14
**Q:** 工具响应格式怎么设计？
**A:** 复用 playwright-mcp 格式 — 结构化 markdown（Result/Error/Code/Snapshot/Events 区段）
**Ambiguity:** 7% (Goal: 0.97, Constraints: 0.96, Criteria: 0.86)

### Round 15
**Q:** 当 AI 使用过期 ref ID 或浏览器崩溃时如何处理？
**A:** 友好错误 + 建议重新快照 — 返回清晰错误消息和建议动作，崩溃时自动重启浏览器
**Ambiguity:** 6% (Goal: 0.97, Constraints: 0.97, Criteria: 0.88)

### Round 16
**Q:** 是否支持增量快照？
**A:** 支持增量 + 全量 — 默认增量快照（只返回变化部分），可通过参数切换全量
**Ambiguity:** 5% (Goal: 0.98, Constraints: 0.97, Criteria: 0.88)

### Round 17
**Q:** 各工具之间如何共享浏览器状态？
**A:** FastMCP lifespan 注入 — 通过 lifespan yield Context，工具通过 ctx.request_context.lifespan_context 获取
**Ambiguity:** 4% (Goal: 0.98, Constraints: 0.98, Criteria: 0.90)

</details>
