#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bybit broker client (stub).

Planned:
- v5 REST endpoints
- HMAC-SHA256 signing
- testnet/live switch

Keys expected in config/private.txt:
- BYBIT_API_KEY
- BYBIT_API_SECRET
- BYBIT_TESTNET=true|false (optional)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import os

from config.private_config import get_private_value


class BybitClient:
    name = "bybit"

    def __init__(self):
        self.api_key = get_private_value("BYBIT_API_KEY", "") or ""
        self.api_secret = get_private_value("BYBIT_API_SECRET", "") or ""
        self.testnet = (get_private_value("BYBIT_TESTNET", "false") or "false").lower() in {"1", "true", "yes"}

        # Optional tuning
        recv_window = get_private_value("BYBIT_RECV_WINDOW_MS", "5000")
        try:
            self.recv_window_ms = int(recv_window or 5000)
        except Exception:
            self.recv_window_ms = 5000

    def is_configured(self) -> bool:
        if not self.api_key or not self.api_secret:
            return False
        if "YOUR_" in self.api_key or "YOUR_" in self.api_secret:
            return False
        return True

    # --- Stubs (to be implemented) ---
    def get_account_summary(self) -> Dict[str, Any]:
        raise NotImplementedError("BybitClient.get_account_summary not implemented yet")

    def get_positions(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("BybitClient.get_positions not implemented yet")

    def place_order(
        self,
        *,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        price: Optional[float] = None,
        reduce_only: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError("BybitClient.place_order not implemented yet")
