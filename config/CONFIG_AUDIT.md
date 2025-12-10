# Config audit (duplicates, obsolete, unused)

## Legacy backups left in `config/`
- `config/daily_generator_20251122.py` and `config/daily_generator_20251123_before_modularization.py` are still present as historical snapshots; the only references come from documentation notes, not runtime code, so they appear to be safe-to-remove backups.【f7b6e3†L27-L28】【df9951†L1-L4】【3399e7†L1-L4】

## Misplaced runtime data (currently ignored)
- Daily contexts and ML coherence outputs now align with their on-disk paths (`config/daily_contexts/` and `config/ml_analysis/`), removing the stale `config/backups/...` indirection that previously left them unused.【f7b6e3†L4-L55】【F:modules/coherence_manager.py†L12-L17】【F:modules/daily_generator.py†L392-L415】【25aee7†L1-L2】

## Templates wired to the dashboard
- The Flask dashboard now reads templates from `config/templates`, matching the directory created alongside the config folder so the packaged HTML files are picked up without falling back to inline placeholders.【F:modules/sv_dashboard.py†L54-L59】【39573e†L1-L2】【f7b6e3†L67-L70】

## Other unused or obsolete configs
- `config/performance_config.py` defines performance tuning settings but is not imported anywhere aside from a README mention, suggesting it is stale configuration.【F:config/performance_config.py†L1-L87】【f3f51c†L1-L3】
- `config/daily_session.json` is only referenced in docs; there is no runtime reader (imports still point to a missing `daily_session_tracker` module), so this state file is unused.【f7b6e3†L29-L29】【28ab5f†L1-L9】
- Text previews for Morning/Noon/Evening/Press/Summary are centralized under `config/previews/`, replacing the unused `config/debug_previews/` path and matching the temp preview generator output.【f7b6e3†L30-L63】【a079d9†L1-L3】【298a5f†L1-L3】【42c903†L1-L3】【0e4864†L1-L3】

## Notes on active configs
- `config/private.txt`, `config/sv_flags.json`, and `config/portfolio_state.json` match the paths loaded by the Telegram handler, scheduler, and portfolio manager; these appear actively used despite the broader cleanup needs.【f7b6e3†L58-L65】【F:modules/telegram_handler.py†L37-L86】【F:modules/sv_scheduler.py†L20-L89】【F:modules/portfolio_manager.py†L13-L22】
