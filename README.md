# camoufox-mcp-python

Camoufox-powered MCP browser server with ref-based accessibility tools.

## Status

Current package entry points:

- `python -m camoufox_mcp`
- `camoufox-mcp-python`

Current transport:

- `stdio`

## Local Development

Install into the project virtualenv:

```bash
uv pip install --python .venv/bin/python -e .
```

Run the server:

```bash
./.venv/bin/camoufox-mcp-python --headless
```

## Scheme A: Remote Install With `uvx`

This project is a Python package, so the direct equivalent of `npx @playwright/mcp@latest`
is `uvx camoufox-mcp-python`.

After publishing to PyPI, clients can use:

```json
{
  "mcpServers": {
    "camoufox": {
      "command": "uvx",
      "args": ["camoufox-mcp-python@0.1.0", "--headless"]
    }
  }
}
```

If you want a stricter package source declaration:

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

For local verification before publishing, the same shape already works with a local source tree:

```json
{
  "mcpServers": {
    "camoufox": {
      "command": "uvx",
      "args": ["--from", "/Users/libre/code/python/camoufox-mcp", "camoufox-mcp-python", "--headless"]
    }
  }
}
```

## Publish To PyPI

Build and publish:

```bash
uv build
uv publish
```

Recommended release flow:

1. Bump version in `pyproject.toml` and `camoufox_mcp/__init__.py`.
2. Run local smoke validation.
3. Run `uv build`.
4. Run `uv publish`.
5. Verify `uvx camoufox-mcp-python@<version> --help`.

## Smoke Test

Basic CLI checks:

```bash
./.venv/bin/python -m compileall camoufox_mcp
./.venv/bin/camoufox-mcp-python --help
uvx --from /Users/libre/code/python/camoufox-mcp camoufox-mcp-python --help
```
