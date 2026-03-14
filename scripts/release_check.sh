#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-./.venv/bin/python}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python interpreter not found: $PYTHON_BIN" >&2
  exit 1
fi

version_init="$("$PYTHON_BIN" - <<'PY'
from pathlib import Path
namespace = {}
exec(Path("camoufox_mcp/__init__.py").read_text(), namespace)
print(namespace["__version__"])
PY
)"

version_project="$("$PYTHON_BIN" - <<'PY'
from pathlib import Path
import tomllib
data = tomllib.loads(Path("pyproject.toml").read_text())
print(data["project"]["version"])
PY
)"

if [[ "$version_init" != "$version_project" ]]; then
  echo "Version mismatch: camoufox_mcp/__init__.py=$version_init pyproject.toml=$version_project" >&2
  exit 1
fi

echo "Version sync OK: $version_project"

uv pip install --python "$PYTHON_BIN" -e .
"$PYTHON_BIN" -m compileall camoufox_mcp
./.venv/bin/camoufox-mcp-python --help >/dev/null
uvx --from "$ROOT" camoufox-mcp-python --help >/dev/null

BUILD_DIR="$(mktemp -d)"
trap 'rm -rf "$BUILD_DIR"' EXIT
uv build --out-dir "$BUILD_DIR"
ls -1 "$BUILD_DIR"

echo "Release checks passed."
