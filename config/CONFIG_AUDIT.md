# Config audit (duplicates, obsolete, unused)

## Archival snapshots removed
- The legacy daily generator backups from November 2025 were deleted during the latest cleanup; runtime continues to rely only on `modules/daily_generator.py`. The audit remains to document their prior existence in case they need to be restored from history.【F:DIARY.md†L400-L554】

## Stale or unused configs
- `config/performance_config.py` defines performance tuning settings but is not imported anywhere aside from a README mention, so it is currently dormant.【F:config/performance_config.py†L1-L87】【F:README.md†L538-L559】
- `config/daily_session.json` is only referenced in docs; there is no runtime reader (imports still point to a missing `daily_session_tracker` module), leaving this state file unused.【F:modules/daily_generator.py†L48-L52】【F:README.md†L538-L559】

## Active config locations (verified)
- Daily contexts and ML coherence outputs now load directly from `config/daily_contexts/` and `config/ml_analysis/` instead of the old `backups/` indirection.【F:modules/coherence_manager.py†L12-L22】【F:modules/daily_generator.py†L392-L415】
- Templates remain under `config/templates`, which is the directory consumed by the Flask dashboard views.【F:modules/sv_dashboard.py†L48-L62】
- Telegram credentials, scheduler flags, and portfolio state continue to be read from `config/private.txt`, `config/sv_flags.json`, and `config/portfolio_state.json` respectively.【F:modules/telegram_handler.py†L37-L86】【F:modules/sv_scheduler.py†L20-L93】【F:modules/portfolio_manager.py†L13-L22】
