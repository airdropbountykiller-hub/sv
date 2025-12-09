#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BRAIN: Regime detection helpers.

Centralises logic that enriches a prediction_eval dict with regime information
using DailyRegimeManager.
"""

from typing import Dict, Any

from modules.regime_manager import get_daily_regime_manager


def enrich_with_regime(prediction_eval: Dict[str, Any], sentiment_payload: Any) -> Dict[str, Any]:
    """Enrich prediction_eval with regime info via DailyRegimeManager.

    sentiment_payload can be either the full sentiment_tracking dict or a
    simple sentiment string; it is passed through update_from_sentiment_tracking.
    """
    manager = get_daily_regime_manager()
    try:
        manager.update_from_sentiment_tracking(sentiment_payload)
        total_tracked = int(prediction_eval.get('total_tracked') or 0)
        accuracy_pct = float(prediction_eval.get('accuracy_pct') or 0.0)
        if total_tracked > 0:
            manager.update_from_accuracy(accuracy_pct, total_tracked)
        regime = manager.infer_regime()
        tomorrow_bias = manager.get_tomorrow_strategy_bias()
        prediction_eval['regime'] = {
            'state': regime.value if hasattr(regime, 'value') else str(regime),
            'sentiment': manager.sentiment.value if manager.sentiment else None,
            'accuracy_grade': manager.accuracy_grade.value if manager.accuracy_grade else None,
            'accuracy_pct': manager.accuracy_pct,
            'tomorrow_bias': tomorrow_bias,
        }
    except Exception:
        # keep heartbeat non-blocking; just leave regime untouched on error
        pass
    return prediction_eval


def get_regime_summary(prediction_eval: Dict[str, Any], sentiment_payload: Any) -> Dict[str, Any]:
    """Return a high-level regime summary for narrative blocks.

    This helper relies on enrich_with_regime to update a copy of the
    prediction_eval structure, then derives a compact summary that can
    be used by Noon/Evening/Summary text blocks without duplicating
    regime logic.

    Returns a dict with at least:
        {
            'regime_state': 'risk_on'|'risk_off'|'neutral'|'transitioning',
            'regime_label': 'RISK_ON'|'RISK_OFF'|'NEUTRAL'|'TRANSITIONING',
            'confidence_pct': int,
            'tone': str,
            'position_sizing': str,
            'risk_management': str,
            'accuracy_pct': float,
            'total_tracked': int,
        }
    """
    # Default neutral summary, used on any error
    summary: Dict[str, Any] = {
        'regime_state': 'neutral',
        'regime_label': 'NEUTRAL',
        'confidence_pct': 60,
        'tone': 'limited live history',
        'position_sizing': 'Standard allocation approach',
        'risk_management': 'Balanced tactical allocation',
        'accuracy_pct': 0.0,
        'total_tracked': 0,
    }

    try:
        # Work on a shallow copy to avoid mutating the caller structure
        try:
            peval = dict(prediction_eval or {})
        except Exception:
            peval = prediction_eval or {}

        total_tracked = int(peval.get('total_tracked') or 0)
        accuracy_pct = float(peval.get('accuracy_pct') or 0.0)

        # Update with regime info (this will also update manager accuracy
        # when total_tracked > 0).
        peval = enrich_with_regime(peval, sentiment_payload) or peval
        regime_info = peval.get('regime') or {}

        regime_state = str(regime_info.get('state') or 'neutral')
        acc_live = float(regime_info.get('accuracy_pct') or accuracy_pct or 0.0)
        tracked_live = int(total_tracked or 0)

        # Map internal regime state to display label
        state_lower = regime_state.lower()
        if 'risk_on' in state_lower:
            regime_label = 'RISK_ON'
            regime_state_norm = 'risk_on'
        elif 'risk_off' in state_lower:
            regime_label = 'RISK_OFF'
            regime_state_norm = 'risk_off'
        elif 'transition' in state_lower:
            regime_label = 'TRANSITIONING'
            regime_state_norm = 'transitioning'
        else:
            regime_label = 'NEUTRAL'
            regime_state_norm = 'neutral'

        # Confidence & tone heuristics based on accuracy and history depth
        if tracked_live >= 5 and acc_live > 0:
            if acc_live >= 70:
                confidence_pct = 70
                tone = 'supported by solid recent accuracy'
            elif acc_live >= 50:
                confidence_pct = 62
                tone = 'with mixed prediction results'
            else:
                confidence_pct = 58
                tone = 'after weak recent accuracy'
        else:
            confidence_pct = 60
            tone = 'limited live history'

        # Position sizing & risk management derived from regime state
        if regime_state_norm == 'risk_on':
            position_sizing = 'Aggressive - growth bias maintained within risk limits'
            risk_management = 'Growth over value, quality focus'
        elif regime_state_norm == 'risk_off':
            position_sizing = 'Defensive - reduced risk and tighter stops'
            risk_management = 'Defensive tilt, capital preservation focus'
        elif regime_state_norm == 'transitioning':
            position_sizing = 'Standard allocation with tactical adjustments'
            risk_management = 'Transition phase  tactical rebalancing in progress'
        else:
            position_sizing = 'Standard allocation approach'
            risk_management = 'Balanced tactical allocation'

        summary.update({
            'regime_state': regime_state_norm,
            'regime_label': regime_label,
            'confidence_pct': confidence_pct,
            'tone': tone,
            'position_sizing': position_sizing,
            'risk_management': risk_management,
            'accuracy_pct': acc_live,
            'total_tracked': tracked_live,
        })
    except Exception:
        # Fall back to default summary on any error
        pass

    return summary
