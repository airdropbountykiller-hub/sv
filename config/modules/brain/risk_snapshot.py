#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BRAIN: Risk/portfolio snapshot helpers.

Centralises logic to attach portfolio/risk information to a prediction_eval
structure using the SVPortfolioManager.
"""

from typing import Dict, Any

from modules.portfolio_manager import get_portfolio_manager
from modules.daily_generator import project_root


def enrich_with_risk(prediction_eval: Dict[str, Any], assets: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich prediction_eval with portfolio risk snapshot when available.

    Uses the shared $25K portfolio manager. Any error is swallowed so that
    callers remain non-blocking.
    """
    try:
        portfolio_manager = get_portfolio_manager(project_root)
        if assets:
            try:
                portfolio_manager.update_positions(assets)
            except Exception:
                # non-blocking: ignore update errors and still try to snapshot
                pass
        snapshot = portfolio_manager.get_portfolio_snapshot()
        perf = snapshot.get('performance_metrics', {}) or {}
        prediction_eval['risk'] = {
            'portfolio': {
                'current_balance': snapshot.get('current_balance'),
                'available_cash': snapshot.get('available_cash'),
                'total_invested': snapshot.get('total_invested'),
                'total_pnl': snapshot.get('total_pnl'),
                'total_pnl_pct': snapshot.get('total_pnl_pct'),
                'active_positions': snapshot.get('active_positions'),
                'win_rate': perf.get('win_rate'),
                'max_drawdown': perf.get('max_drawdown'),
                'sharpe_ratio': perf.get('sharpe_ratio'),
            },
            'intraday': {
                'pnl': None,
                'pnl_pct': None,
                'max_drawdown_intraday': None,
                'var_95': None,
            },
        }
    except Exception:
        # keep heartbeat non-blocking
        pass
    return prediction_eval
