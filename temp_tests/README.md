# temp_tests

This folder is the staging area for exploratory checks, integration spikes, and **everything non-runtime**. Use it when you need to:

- prototype new generators or PDF flows without touching production runners
- create mock data or quick previews for weekly/monthly reports
- run ad-hoc validation scripts that should not be packaged with the main runtime
- park obsolete/retired files that should stay out of `modules/`

## Structure
- `temp_tests/scripts/`: operational entry points (e.g., Telegram senders, manual runners) executed directly with `python temp_tests/scripts/...`.
- `temp_tests/tools/`: development or refactor utilities that manipulate the codebase but are kept outside the runtime package.
- `temp_tests/` root: throwaway tests, previews, fixtures, and any legacy helpers kept for reference.
