# temp_tests

This folder is a staging area for exploratory checks, integration spikes, and temporary scripts that accompany the test suite. Use it when you need to:

- prototype new generators or PDF flows without touching production runners
- create mock data or quick previews for weekly/monthly reports
- run ad-hoc validation scripts that should not be packaged with the main runtime

## Why not move `scripts/` or `tools/` here?
The top-level `scripts/` directory contains operational entry points (e.g., Telegram senders, manual runners) that are invoked directly with `python scripts/...`. Keeping them at the project root avoids import path hacks and makes them easy to call in production environments.

The `tools/` folder hosts development/refactor utilities that manipulate the codebase itself. They are intentionally outside the `modules` package and the `temp_tests` sandbox to keep the runtime namespace clean and to avoid shipping maintenance helpers with production artifacts.

If you need a temporary utility for testing purposes, place it here. If it is a production entry point, keep it in `scripts/`. If it is a one-off refactor/maintenance helper, keep it in `tools/`.
