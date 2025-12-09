#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - Period Aggregator

Aggregates compact daily metrics snapshots produced by DailyContentGenerator
(daily_metrics_YYYY-MM-DD.json under reports/metrics) into weekly/monthly metrics.

All numbers in this module are derived from saved daily data:
- prediction_eval: hits/misses/pending/total_tracked/accuracy_pct
- market_snapshot: BTC/SPX/EURUSD/GOLD with prices (Gold in USD/gram)

No random or template values are generated here.
"""

import datetime
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import pytz

# Project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
METRICS_DIR = Path(project_root) / "reports" / "metrics"

log = logging.getLogger(__name__)

ITALY_TZ = pytz.timezone("Europe/Rome")


def _now_it() -> datetime.datetime:
    """Current time in Italian timezone (kept consistent with daily_generator)."""
    return datetime.datetime.now(ITALY_TZ)


def _date_range(start: datetime.date, end: datetime.date):
    """Yield all dates from start to end inclusive."""
    current = start
    while current <= end:
        yield current
        current += datetime.timedelta(days=1)


def load_daily_metrics(day: datetime.date) -> Optional[Dict[str, Any]]:
    """Load one day's metrics snapshot if available.

    Returns the JSON dict or None if the file does not exist or cannot be parsed.
    """
    date_str = day.strftime("%Y-%m-%d")
    path = METRICS_DIR / f"daily_metrics_{date_str}.json"
    if not path.exists():
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            log.warning("[AGGREGATOR] Invalid metrics format for %s", date_str)
            return None
        return data
    except Exception as e:
        log.warning("[AGGREGATOR] Error loading metrics for %s: %s", date_str, e)
        return None


def get_period_metrics(start_date: datetime.date, end_date: datetime.date) -> Dict[str, Any]:
    """Aggregate accuracy and key asset performance over a date range.

    The result has the shape:
    {
        'start_date': 'YYYY-MM-DD',
        'end_date': 'YYYY-MM-DD',
        'days_with_data': int,
        'prediction': {
            'hits': int,
            'misses': int,
            'pending': int,
            'total_tracked': int,
            'accuracy_pct': float,
        },
        'assets': {
            'BTC': {
                'start_price': float,
                'end_price': float,
                'return_pct': float | None,
                'unit': 'USD',
                'days_with_price': int,
                'start_date': 'YYYY-MM-DD',
                'end_date': 'YYYY-MM-DD',
            },
            'SPX': { ... },
            'EURUSD': { ... },
            'GOLD': { 'unit': 'USD/g', ... },
        }
    }
    """
    if end_date < start_date:
        start_date, end_date = end_date, start_date

    agg: Dict[str, Any] = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "days_with_data": 0,
        "prediction": {
            "hits": 0,
            "misses": 0,
            "pending": 0,
            "total_tracked": 0,
            "accuracy_pct": 0.0,
        },
        "assets": {},
    }

    # Prediction counters
    total_hits = 0
    total_misses = 0
    total_pending = 0
    total_tracked = 0

    # Asset tracking: first/last non-zero price within the period
    asset_first: Dict[str, Dict[str, Any]] = {}
    asset_last: Dict[str, Dict[str, Any]] = {}
    asset_days: Dict[str, int] = {}

    for day in _date_range(start_date, end_date):
        metrics = load_daily_metrics(day)
        if not metrics:
            continue

        agg["days_with_data"] += 1

        # --- Prediction aggregation ---
        pe = metrics.get("prediction_eval") or {}
        try:
            hits = int(pe.get("hits", 0) or 0)
            misses = int(pe.get("misses", 0) or 0)
            pending = int(pe.get("pending", 0) or 0)
            tracked = int(pe.get("total_tracked", 0) or 0)
        except Exception:
            hits = misses = pending = tracked = 0

        total_hits += hits
        total_misses += misses
        total_pending += pending
        total_tracked += tracked

        # --- Market snapshot aggregation ---
        mkt = metrics.get("market_snapshot") or {}
        if isinstance(mkt, dict):
            for asset, data in mkt.items():
                if not isinstance(data, dict):
                    continue
                try:
                    price = float(data.get("price", 0) or 0.0)
                except Exception:
                    price = 0.0
                if price <= 0:
                    continue
                unit = data.get("unit") or ""

                if asset not in asset_first:
                    asset_first[asset] = {"price": price, "date": day, "unit": unit}
                # Always treat last as the most recent non-zero in range
                asset_last[asset] = {"price": price, "date": day, "unit": unit}
                asset_days[asset] = asset_days.get(asset, 0) + 1

    # Final prediction accuracy
    accuracy_pct = (total_hits / total_tracked * 100.0) if total_tracked > 0 else 0.0
    agg["prediction"] = {
        "hits": total_hits,
        "misses": total_misses,
        "pending": total_pending,
        "total_tracked": total_tracked,
        "accuracy_pct": accuracy_pct,
    }

    # Asset returns
    assets_out: Dict[str, Any] = {}
    for asset, first in asset_first.items():
        last = asset_last.get(asset, first)
        start_price = float(first.get("price", 0.0) or 0.0)
        end_price = float(last.get("price", 0.0) or 0.0)
        unit = last.get("unit", "")
        if start_price > 0 and end_price > 0:
            return_pct: Optional[float] = (end_price - start_price) / start_price * 100.0
        else:
            return_pct = None

        assets_out[asset] = {
            "start_price": start_price,
            "end_price": end_price,
            "return_pct": return_pct,
            "unit": unit,
            "days_with_price": asset_days.get(asset, 0),
            "start_date": first["date"].strftime("%Y-%m-%d"),
            "end_date": last["date"].strftime("%Y-%m-%d"),
        }

    agg["assets"] = assets_out

    log.info(
        "[AGGREGATOR] Aggregated %d days (%s → %s), tracked assets: %s",
        agg["days_with_data"],
        agg["start_date"],
        agg["end_date"],
        ", ".join(sorted(assets_out.keys())) or "none",
    )

    return agg


def get_weekly_metrics(now: Optional[datetime.datetime] = None) -> Dict[str, Any]:
    """Convenience wrapper for current week's Monday→Friday metrics.

    Uses Italian timezone for week boundaries, consistent with other modules.
    """
    if now is None:
        now = _now_it()
    if isinstance(now, datetime.date) and not isinstance(now, datetime.datetime):
        # Allow passing a date directly
        now_date = now
    else:
        now_date = now.date()

    monday = now_date - datetime.timedelta(days=now_date.weekday())
    friday = monday + datetime.timedelta(days=4)
    return get_period_metrics(monday, friday)


def get_monthly_metrics(now: Optional[datetime.datetime] = None) -> Dict[str, Any]:
    """Convenience wrapper for current calendar month's metrics.

    Uses Italian timezone for month boundaries.
    """
    if now is None:
        now = _now_it()
    if isinstance(now, datetime.date) and not isinstance(now, datetime.datetime):
        now_date = now
    else:
        now_date = now.date()

    # First day of the month
    first = now_date.replace(day=1)
    # Compute last day of the month via "first of next month minus one day"
    if first.month == 12:
        first_next_month = first.replace(year=first.year + 1, month=1)
    else:
        first_next_month = first.replace(month=first.month + 1)
    last = first_next_month - datetime.timedelta(days=1)

    return get_period_metrics(first, last)
