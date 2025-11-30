#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BRAIN: Single-prediction status helpers.

Shared logic to evaluate a single prediction against live prices.
Used by dashboard ML endpoints and can be reused by generators/heartbeat.
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def calculate_prediction_accuracy(prediction: Dict[str, Any], current_price: float) -> Dict[str, Any]:
    """Calculate accuracy of a prediction vs current price.

    This is a pure helper (no I/O). It returns:
        {
            'accuracy': float 0-100,
            'status': str,
            'actual_move': float,
            'expected_move': float,
        }
    """
    try:
        entry = float(prediction.get('entry') or 0)
        target = float(prediction.get('target') or 0)
        direction = (prediction.get('direction') or 'LONG').upper()

        if entry == 0 or target == 0:
            return {'accuracy': 0.0, 'status': 'Invalid', 'actual_move': 0.0, 'expected_move': 0.0}

        if direction == 'LONG':
            expected_move = target - entry
            actual_move = current_price - entry
        else:  # SHORT
            expected_move = entry - target
            actual_move = entry - current_price

        if expected_move == 0:
            return {'accuracy': 0.0, 'status': 'No Movement', 'actual_move': 0.0, 'expected_move': 0.0}

        accuracy = min(100.0, max(0.0, (actual_move / expected_move) * 100.0))

        if accuracy >= 90:
            status = '🎯 Excellent'
        elif accuracy >= 70:
            status = '✅ Good'
        elif accuracy >= 50:
            status = '⚠️ Partial'
        else:
            status = '❌ Miss'

        return {
            'accuracy': round(accuracy, 1),
            'status': status,
            'actual_move': actual_move,
            'expected_move': expected_move,
        }
    except Exception:
        logger.warning("calculate_prediction_accuracy error", exc_info=True)
        return {'accuracy': 0.0, 'status': 'Error', 'actual_move': 0.0, 'expected_move': 0.0}


def compute_prediction_status(
    pred: Dict[str, Any],
    live_prices: Dict[str, Any],
    crypto_prices: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Resolve current status (Hit/Stopped/Pending) and progress for a single prediction.

    Arguments:
        pred: prediction dict with at least asset, direction, entry, target, stop.
        live_prices: mapping like get_key_assets_prices() (SPX/EURUSD/GOLD, possibly BTC).
        crypto_prices: optional mapping from get_current_crypto_prices() for per-coin prices.
    """
    try:
        asset = (pred.get('asset') or '').upper()
        direction = (pred.get('direction') or 'LONG').upper()
        entry = float(pred.get('entry') or 0)
        target = float(pred.get('target') or 0)
        stop = float(pred.get('stop') or 0)

        lp = live_prices or {}
        cp = crypto_prices or {}

        # Map asset to current live price
        if asset in lp:
            current = float(lp[asset].get('price') or 0)
        elif asset in ('SP500', 'SPX'):
            current = float(lp.get('SPX', {}).get('price') or 0)
        elif asset in ('EURUSD', 'EUR/USD'):
            current = float(lp.get('EURUSD', {}).get('price') or 0)
        elif asset in ('XAUUSD', 'GOLD', 'GC'):
            current = float(lp.get('GOLD', {}).get('price') or 0)
        elif asset in cp:
            current = float(cp[asset].get('price') or 0)
        else:
            current = float(pred.get('current_price') or 0)

        acc = calculate_prediction_accuracy(pred, current)
        status = 'Pending'
        hit = False
        progress = 0.0

        if entry and target:
            if direction == 'LONG':
                if current >= target > 0:
                    status, hit = 'Hit target', True
                elif stop and current <= stop:
                    status = 'Stopped out'
                else:
                    denom = (target - entry) or 1.0
                    progress = max(0.0, min(1.0, (current - entry) / denom))
            else:  # SHORT
                if current <= target < entry:
                    status, hit = 'Hit target', True
                elif stop and current >= stop:
                    status = 'Stopped out'
                else:
                    denom = (entry - target) or 1.0
                    progress = max(0.0, min(1.0, (entry - current) / denom))

        rr = (abs(target - entry) / abs(entry - stop)) if stop and stop != entry else 1.0

        return {
            'current_price': current,
            'status': status,
            'hit': hit,
            'progress_pct': round(progress * 100.0, 1),
            'accuracy': acc.get('accuracy', 0.0),
            'rr': round(rr, 2),
        }
    except Exception:
        logger.warning("compute_prediction_status error", exc_info=True)
        return {
            'current_price': 0.0,
            'status': 'Error',
            'hit': False,
            'progress_pct': 0.0,
            'accuracy': 0.0,
            'rr': 1.0,
        }
