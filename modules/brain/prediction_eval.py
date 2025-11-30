#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BRAIN: Prediction evaluation helpers.

Thin wrapper around the main system's evaluation logic so other modules
(heartbeat, dashboard, generators) can reuse a single entry point.
"""

import datetime
from typing import Dict, Any, Optional

from modules.daily_generator import _DailyGenerator


def evaluate_predictions(now: Optional[datetime.datetime] = None) -> Dict[str, Any]:
    """Evaluate today's predictions using the main DailyGenerator logic.

    This is a thin wrapper around DailyGenerator._evaluate_predictions_with_live_data
    so ENGINE/BRAIN heartbeat and other components can share a single API.
    """
    dg = _DailyGenerator()
    return dg._evaluate_predictions_with_live_data(now) or {}
