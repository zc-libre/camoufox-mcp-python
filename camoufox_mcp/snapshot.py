from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from playwright.async_api import Page


def _runtime_versions() -> str:
    packages = []
    for package in ("camoufox", "playwright"):
        try:
            packages.append(f"{package}={version(package)}")
        except PackageNotFoundError:
            packages.append(f"{package}=unknown")
    return ", ".join(packages)


def _timeout_calc(timeout: float | None = None) -> float:
    return timeout if timeout is not None else 30_000.0


async def snapshot_for_ai(page: Page) -> str:
    try:
        impl_page = page._impl_obj
        channel = impl_page._channel
    except AttributeError as exc:
        raise RuntimeError(
            f"snapshotForAI is unavailable in the current Python Playwright binding ({_runtime_versions()})."
        ) from exc

    try:
        result = await channel.send("snapshotForAI", _timeout_calc, {})
    except Exception as exc:  # pragma: no cover - depends on upstream private API
        raise RuntimeError(f"snapshotForAI call failed ({_runtime_versions()}).") from exc

    if isinstance(result, dict) and isinstance(result.get("full"), str):
        result = result["full"]

    if not isinstance(result, str):
        raise RuntimeError(
            "snapshotForAI returned an unexpected format for the current Python Playwright binding."
        )
    return result
