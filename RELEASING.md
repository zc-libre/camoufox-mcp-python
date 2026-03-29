# Releasing camoufox-mcp-python

This project is intended to be distributed as a Python package and launched remotely via `uvx`.

## Release Model

Published package:

- PyPI package: `camoufox-mcp-python`
- CLI entry point: `camoufox-mcp-python`

Recommended MCP client configuration after publish:

```json
{
  "mcpServers": {
    "camoufox": {
      "command": "uvx",
      "args": ["camoufox-mcp-python@0.2.1", "--headless"]
    }
  }
}
```

Strict package pin form:

```json
{
  "mcpServers": {
    "camoufox": {
      "command": "uvx",
      "args": ["--from", "camoufox-mcp-python==0.2.1", "camoufox-mcp-python", "--headless"]
    }
  }
}
```

## Pre-release Checklist

1. Update the version in `pyproject.toml`.
2. Update the version in `camoufox_mcp/__init__.py`.
3. Review `README.md` for the versioned `uvx` examples.
4. Run the release check script:

```bash
./scripts/release_check.sh
```

5. Build the distribution locally:

```bash
uv build
```

6. Verify the generated files in `dist/`.
7. Publish to PyPI:

```bash
uv publish
```

8. Post-publish verify the released package:

```bash
uvx camoufox-mcp-python@<version> --help
```

## Notes

- `browser_evaluate` remains gated behind `--caps dangerous`.
- First launch on a machine may trigger Camoufox binary/addon setup.
- The server currently targets `stdio` transport only.
