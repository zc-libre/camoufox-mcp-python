# camoufox-mcp-python

[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![PyPI](https://img.shields.io/pypi/v/camoufox-mcp-python)](https://pypi.org/project/camoufox-mcp-python/)

基于 [Camoufox](https://camoufox.com/) 反检测浏览器的 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 服务器。通过无障碍快照和 ref 引用机制提供与 Playwright-MCP 兼容的浏览器自动化工具接口。

> **可以理解为带有反检测和指纹伪装能力的 [playwright-mcp](https://github.com/anthropics/playwright-mcp)。**

## 特性

- **浏览器指纹反检测** — Camoufox 自动伪装浏览器指纹，绕过机器人检测
- **基于 ref 的无障碍快照** — 通过无障碍引用与页面元素交互，无需 CSS 选择器
- **类人光标移动** — 可选的光标拟人化，模拟真实用户操作
- **持久化浏览器配置** — 跨会话保持登录状态、Cookie 和浏览数据
- **GeoIP 自动匹配** — 自动根据代理 IP 匹配浏览器语言/时区
- **代理支持** — 完整的代理支持，包括用户名密码认证
- **隐私保护** — 可屏蔽 WebRTC、WebGL 和图片加载，减少信息泄露和带宽消耗
- **多标签页管理** — 创建、关闭、切换和列出浏览器标签页
- **弹窗与对话框处理** — 处理 JavaScript 对话框和文件选择器
- **控制台与网络监控** — 查看控制台消息和网络请求

## 快速开始

### 在 Claude Desktop 中使用

添加到 Claude Desktop 配置文件（`claude_desktop_config.json`）：

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

### 在 Claude Code 中使用

```bash
claude mcp add camoufox -- uvx camoufox-mcp-python --headless
```

### 在 VS Code / Cursor 中使用

添加到 `.vscode/mcp.json`：

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

### 固定版本号

```json
{
  "mcpServers": {
    "camoufox": {
      "command": "uvx",
      "args": ["--from", "camoufox-mcp-python==0.1.0", "camoufox-mcp-python", "--headless"]
    }
  }
}
```

## 命令行参数

| 参数 | 说明 |
|---|---|
| `--headless` | 以无头模式运行浏览器 |
| `--proxy <url>` | 代理服务器 URL（支持 `user:pass@host:port` 格式） |
| `--os <os>` | 目标操作系统指纹：`windows`、`macos`、`linux`（可重复指定） |
| `--humanize [seconds]` | 启用类人光标移动（可选设置最大持续时间） |
| `--geoip [ip]` | 自动匹配代理 IP 对应的语言/时区，或指定目标 IP |
| `--locale <locale>` | 浏览器语言环境，如 `zh-CN`（可重复指定，逗号分隔） |
| `--window <WxH>` | 外部窗口大小，如 `1280x720` |
| `--block-webrtc` | 禁用 WebRTC 防止 IP 泄露 |
| `--block-webgl` | 禁用 WebGL |
| `--block-images` | 屏蔽图片请求以节省带宽 |
| `--disable-coop` | 禁用 COOP 以允许跨域 iframe 交互 |
| `--user-data-dir <path>` | 持久化配置目录（默认：`~/.camoufox-mcp-python/profile`） |
| `--caps <groups>` | 启用功能组，如 `dangerous`（启用 `browser_evaluate`） |

### 示例

```bash
# 无头模式 + 代理 + GeoIP 自动匹配
camoufox-mcp-python --headless --proxy http://user:pass@proxy.example.com:8080 --geoip

# 可视化浏览器 + 光标拟人化 + 自定义窗口大小
camoufox-mcp-python --humanize --window 1920x1080

# 隐私加固模式
camoufox-mcp-python --headless --block-webrtc --block-webgl --block-images

# 启用 JavaScript 执行
camoufox-mcp-python --headless --caps dangerous
```

## 可用工具

### 导航

| 工具 | 说明 |
|---|---|
| `browser_navigate` | 导航到指定 URL |
| `browser_navigate_back` | 返回上一页 |

### 快照与交互

| 工具 | 说明 |
|---|---|
| `browser_snapshot` | 捕获当前页面的无障碍快照 |
| `browser_click` | 通过 ref 点击元素（支持双击、右键、修饰键） |
| `browser_hover` | 悬停在元素上 |
| `browser_drag` | 从一个元素拖拽到另一个元素 |
| `browser_select_option` | 选择下拉菜单中的选项 |

### 输入

| 工具 | 说明 |
|---|---|
| `browser_type` | 在可编辑元素中输入文本（支持逐字输入和提交） |
| `browser_press_key` | 按下键盘按键或组合键 |
| `browser_fill_form` | 一次性填写多个表单字段 |

### 页面

| 工具 | 说明 |
|---|---|
| `browser_take_screenshot` | 截图（视口、整页或指定元素） |
| `browser_console_messages` | 获取控制台消息 |
| `browser_network_requests` | 列出页面的网络请求 |
| `browser_resize` | 调整视口大小 |
| `browser_wait_for` | 等待文本出现/消失或固定时长 |
| `browser_close` | 关闭浏览器会话 |

### 标签页

| 工具 | 说明 |
|---|---|
| `browser_tabs` | 列出、创建、关闭或选择浏览器标签页 |

### 弹窗与文件

| 工具 | 说明 |
|---|---|
| `browser_handle_dialog` | 接受或关闭 JavaScript 对话框 |
| `browser_file_upload` | 处理文件选择器并上传文件 |

### 危险操作（需要 `--caps dangerous`）

| 工具 | 说明 |
|---|---|
| `browser_evaluate` | 在页面或元素上执行任意 JavaScript |

## 工作原理

服务器通过 Playwright 异步 API 驱动 Camoufox（基于 Firefox 的反检测浏览器）。页面以 YAML 格式的无障碍快照呈现，每个可交互元素分配一个 **ref** 标识符。AI 模型读取快照，识别目标 ref，调用相应工具 — 无需脆弱的 CSS/XPath 选择器。

```
AI 模型  ←→  MCP 服务器  ←→  Camoufox 浏览器
                  │
                  ├── 无障碍快照（YAML 格式）
                  ├── 基于 ref 的元素定位
                  └── 反检测指纹伪装
```

## 本地开发

```bash
# 克隆并安装
git clone https://github.com/user/camoufox-mcp.git
cd camoufox-mcp
uv pip install --python .venv/bin/python -e .

# 运行服务器
./.venv/bin/camoufox-mcp-python --headless

# 或以模块方式运行
./.venv/bin/python -m camoufox_mcp --headless

# 冒烟测试
./.venv/bin/python -m compileall camoufox_mcp
./.venv/bin/camoufox-mcp-python --help
```

## 环境要求

- Python >= 3.10
- [camoufox](https://camoufox.com/) >= 0.4.11
- [mcp\[cli\]](https://github.com/modelcontextprotocol/python-sdk) >= 1.25
- [playwright](https://playwright.dev/python/) >= 1.58

> **注意：** 首次在新机器上启动时可能会自动下载 Camoufox 浏览器二进制文件和插件。

## 许可证

[MIT](https://opensource.org/licenses/MIT)
