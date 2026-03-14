# Open Questions

## camoufox-mcp-v1 - 2026-03-14

- [ ] `snapshotForAI` API stability -- This is a private Playwright internal API. If Playwright updates the protocol, the snapshot/ref system breaks. Mitigation: pin playwright version range in pyproject.toml, add startup-time API availability check. Monitor across versions.
- [ ] `browser_run_code` sandboxing -- How thoroughly should the arbitrary Playwright code execution be sandboxed? Options: exec() with limited globals, or full subprocess isolation. This only applies to the `--caps dangerous` gated tool.
- [ ] PyPI package name availability -- Need to verify `camoufox-mcp` is available on PyPI before publish.

## Resolved (2026-03-14, Architect/Critic review)

- [x] `persistent_context` + `user_data_dir` default path -- **Resolved:** Default to `~/.camoufox-mcp/profile`. `to_launch_kwargs()` injects user_data_dir when persistent_context=True.
- [x] `humanize` default value -- **Resolved:** Default to False, matching current Camoufox docs and the accepted v1 spec. `--humanize` is opt-in and may also accept a max duration value.
- [x] `page.consoleMessages()` / `page.pageErrors()` availability -- **Resolved:** Use event-listener-only collection in Tab (already planned). No dependency on newer Playwright convenience APIs.
