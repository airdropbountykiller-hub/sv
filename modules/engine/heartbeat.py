#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ENGINE: Heartbeat entry point

Single public entry point for the intraday ENGINE+BRAIN heartbeat.

This thin wrapper delegates to the implementation hosted on the main
_DailyGenerator class, which in turn uses engine/brain helper modules
for market snapshot, prediction evaluation, regime and risk.

Keeping the public API here allows schedulers, CLI tools and dashboards
to depend on ENGINE instead of importing DailyGenerator directly.
"""

from typing import Optional
import datetime
import logging

from modules.daily_generator import get_daily_generator

log = logging.getLogger(__name__)


def run_heartbeat(now: Optional[datetime.datetime] = None) -> None:
    """Run the ENGINE+BRAIN heartbeat once.

    This is a non-blocking call: any internal error is logged as a
    warning by DailyContentGenerator.run_engine_brain_heartbeat.
    """
    try:
        dg = get_daily_generator()
        dg.run_engine_brain_heartbeat(now)
    except Exception as e:
        # Extra protection: never let heartbeat kill the caller.
        log.warning(f"[ENGINE-HEARTBEAT] Error invoking DailyGenerator heartbeat: {e}")
