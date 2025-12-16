#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SV Central Trader (backtesting / simulate-only).

This module is the single place where "predictions -> portfolio positions" happens.
Generators (e.g. morning) MUST NOT place trades.

Design goals:
- Safe by default: simulate_only=True
- Idempotent: won't re-open positions repeatedly if orchestrator reruns
- Uses the existing SVPortfolioManager risk/sizing rules

Predictions source:
- reports/1_daily/predictions_YYYY-MM-DD.json

Outputs:
- config/portfolio_signals.json (stores last run date + summary)
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import logging

from config import sv_paths

log = logging.getLogger(__name__)


def _now_it() -> datetime:
    """Reuse the same 'Italy time' concept used by the daily generator, if available."""
    try:
        from modules.daily_generator import _now_it as _impl

        return _impl()
    except Exception:
        return datetime.now()


def _predictions_file_for_date(date_str: str) -> Path:
    return Path(sv_paths.PROJECT_ROOT) / 'reports' / '1_daily' / f'predictions_{date_str}.json'


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        if not path.exists():
            return None
        with open(path, 'r', encoding='utf-8') as f:
            obj = json.load(f)
        return obj if isinstance(obj, dict) else None
    except Exception as e:
        log.warning(f"[TRADER] Failed to load JSON {path}: {e}")
        return None


def _save_json_atomic(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


def _load_trader_state() -> Dict[str, Any]:
    state_path = Path(sv_paths.PORTFOLIO_SIGNALS_FILE)
    return _load_json(state_path) or {}


def _save_trader_state(state: Dict[str, Any]) -> None:
    state_path = Path(sv_paths.PORTFOLIO_SIGNALS_FILE)
    _save_json_atomic(state_path, state)


def _market_price_for_asset(snapshot: Dict[str, Any], asset: str) -> Optional[float]:
    try:
        assets = snapshot.get('assets', {}) if isinstance(snapshot, dict) else {}
        a = (assets or {}).get(asset)
        if isinstance(a, dict) and a.get('price'):
            return float(a.get('price'))
    except Exception:
        pass
    return None


def run_daily_trader(
    *,
    date_str: str | None = None,
    simulate_only: bool = True,
    force: bool = False,
) -> Dict[str, Any]:
    """Run the central trader for a given date.

    Args:
        date_str: YYYY-MM-DD. Defaults to "today" in Italy tz (same as generator).
        simulate_only: if True, NEVER sends broker orders.
        force: if True, ignores idempotency guard.

    Returns:
        { opened_positions: [...], skipped: [...], source_file: str }
    """

    if date_str is None:
        date_str = _now_it().strftime('%Y-%m-%d')

    # Idempotency guard
    state = _load_trader_state()
    if not force:
        last = (state.get('daily_trader') or {}).get('last_run_date')
        if last == date_str:
            return {
                'opened_positions': [],
                'skipped': [{'reason': 'already_ran_today', 'date': date_str}],
                'source_file': str(_predictions_file_for_date(date_str)),
            }

    pred_path = _predictions_file_for_date(date_str)
    payload = _load_json(pred_path)
    preds = (payload or {}).get('predictions') if isinstance(payload, dict) else None
    if not isinstance(preds, list) or not preds:
        state['daily_trader'] = {
            'last_run_date': date_str,
            'last_run_at': datetime.now().isoformat(),
            'simulate_only': bool(simulate_only),
            'opened': 0,
            'note': 'no_predictions',
        }
        _save_trader_state(state)
        return {
            'opened_positions': [],
            'skipped': [{'reason': 'no_predictions', 'date': date_str}],
            'source_file': str(pred_path),
        }

    # Market snapshot (core assets)
    try:
        from modules.engine.market_data import get_market_snapshot

        snapshot = get_market_snapshot()
    except Exception as e:
        snapshot = {'assets': {}}
        log.warning(f"[TRADER] Market snapshot unavailable: {e}")

    # Portfolio manager
    from modules.portfolio_manager import get_portfolio_manager

    pm = get_portfolio_manager(sv_paths.PROJECT_ROOT)

    opened_positions: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []

    for pred in preds:
        if not isinstance(pred, dict):
            skipped.append({'reason': 'invalid_prediction', 'prediction': pred})
            continue

        asset = (pred.get('asset') or '').upper().strip()
        if not asset:
            skipped.append({'reason': 'missing_asset', 'prediction': pred})
            continue

        current_price = _market_price_for_asset(snapshot, asset)
        if current_price is None:
            # Fallback: let portfolio manager use entry as current
            current_price = None

        pos_id = pm.open_position(pred, current_price=current_price, simulate_only=simulate_only)
        if pos_id:
            opened_positions.append({'asset': asset, 'position_id': pos_id})
        else:
            skipped.append({'asset': asset, 'reason': 'rejected_by_risk_or_limits'})

    state['daily_trader'] = {
        'last_run_date': date_str,
        'last_run_at': datetime.now().isoformat(),
        'simulate_only': bool(simulate_only),
        'opened': len(opened_positions),
        'skipped': len(skipped),
        'predictions_file': str(pred_path),
    }
    _save_trader_state(state)

    return {
        'opened_positions': opened_positions,
        'skipped': skipped,
        'source_file': str(pred_path),
    }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    out = run_daily_trader(simulate_only=True)
    print(json.dumps(out, indent=2))
