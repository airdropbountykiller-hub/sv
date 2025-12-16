#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bybit broker client (v5 REST).

This module is **testnet-first** and includes safety gates so we don't place
orders unless explicitly enabled.

Private config keys (config/private.txt):
- BYBIT_API_KEY
- BYBIT_API_SECRET
- BYBIT_TESTNET=true|false (default false)
- BYBIT_RECV_WINDOW_MS=5000 (optional)
- BYBIT_ENABLE_TRADING=false (default false)

Notes:
- Never print or log secrets.
- Public endpoints (market/time, instruments-info) do not require auth.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import requests

from config.private_config import get_private_value


class BybitClient:
    name = "bybit"

    def __init__(self):
        self.api_key = (get_private_value("BYBIT_API_KEY", "") or "").strip()
        self.api_secret = (get_private_value("BYBIT_API_SECRET", "") or "").strip()

        self.testnet = (get_private_value("BYBIT_TESTNET", "false") or "false").lower() in {"1", "true", "yes"}
        self.enable_trading = (get_private_value("BYBIT_ENABLE_TRADING", "false") or "false").lower() in {"1", "true", "yes"}
        self.allow_live = (get_private_value("BYBIT_ALLOW_LIVE", "false") or "false").lower() in {"1", "true", "yes"}

        if self.enable_trading and (not self.testnet) and (not self.allow_live):
            raise RuntimeError(
                "Refusing to trade on Bybit LIVE. Set BYBIT_TESTNET=true for testnet, "
                "or explicitly set BYBIT_ALLOW_LIVE=true to allow live trading."
            )

        # Optional tuning
        recv_window = get_private_value("BYBIT_RECV_WINDOW_MS", "5000")
        try:
            self.recv_window_ms = int(recv_window or 5000)
        except Exception:
            self.recv_window_ms = 5000

        timeout_s = get_private_value("BYBIT_TIMEOUT_SECONDS", "10")
        try:
            self.timeout_seconds = float(timeout_s or 10)
        except Exception:
            self.timeout_seconds = 10.0

        # Base URL
        self.base_url = "https://api-testnet.bybit.com" if self.testnet else "https://api.bybit.com"

    def is_configured(self) -> bool:
        if not self.api_key or not self.api_secret:
            return False
        if "YOUR_" in self.api_key or "YOUR_" in self.api_secret:
            return False
        return True

    # --- Core helpers ---
    def _now_ms(self) -> str:
        return str(int(time.time() * 1000))

    def _sign(self, *, timestamp_ms: str, payload: str) -> str:
        """Compute Bybit v5 signature: HMAC_SHA256(secret, ts + api_key + recv_window + payload)."""
        prehash = f"{timestamp_ms}{self.api_key}{self.recv_window_ms}{payload}".encode("utf-8")
        return hmac.new(self.api_secret.encode("utf-8"), prehash, hashlib.sha256).hexdigest()

    def _headers(self, *, timestamp_ms: str, signature: str) -> Dict[str, str]:
        return {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-TIMESTAMP": timestamp_ms,
            "X-BAPI-RECV-WINDOW": str(self.recv_window_ms),
            "X-BAPI-SIGN": signature,
            "Content-Type": "application/json",
        }

    def _public_get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        resp = requests.get(url, params=params or {}, timeout=self.timeout_seconds)
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def _private_request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.is_configured():
            raise RuntimeError("Bybit not configured. Set BYBIT_API_KEY/BYBIT_API_SECRET in config/private.txt")

        method_u = method.upper()
        timestamp_ms = self._now_ms()

        if method_u == "GET":
            payload = urlencode(params or {}, doseq=True)
            sig = self._sign(timestamp_ms=timestamp_ms, payload=payload)
            url = f"{self.base_url}{path}"
            resp = requests.get(
                url,
                params=params or {},
                headers=self._headers(timestamp_ms=timestamp_ms, signature=sig),
                timeout=self.timeout_seconds,
            )
        else:
            payload = json.dumps(json_body or {}, separators=(",", ":"), ensure_ascii=False)
            sig = self._sign(timestamp_ms=timestamp_ms, payload=payload)
            url = f"{self.base_url}{path}"
            resp = requests.request(
                method_u,
                url,
                data=payload,
                headers=self._headers(timestamp_ms=timestamp_ms, signature=sig),
                timeout=self.timeout_seconds,
            )

        resp.raise_for_status()
        return resp.json() if resp.content else {}

    # --- Read-only / diagnostics (safe) ---
    def get_server_time(self) -> Dict[str, Any]:
        """Public endpoint. Useful to validate connectivity."""
        return self._public_get("/v5/market/time")

    def get_instruments_info(self, *, category: str = "linear", symbol: Optional[str] = None) -> Dict[str, Any]:
        """Public endpoint. Use to fetch qtyStep/minOrderQty for order quantization."""
        params: Dict[str, Any] = {"category": category}
        if symbol:
            params["symbol"] = symbol
        return self._public_get("/v5/market/instruments-info", params=params)

    # --- Trading endpoints (guarded; implemented next step) ---
    def set_leverage(self, *, category: str, symbol: str, leverage: int) -> Dict[str, Any]:
        if not self.enable_trading:
            raise RuntimeError("Bybit trading disabled. Set BYBIT_ENABLE_TRADING=true to enable testnet orders")
        body = {
            "category": category,
            "symbol": symbol,
            "buyLeverage": str(leverage),
            "sellLeverage": str(leverage),
        }
        return self._private_request("POST", "/v5/position/set-leverage", json_body=body)

    def place_order(
        self,
        *,
        category: str,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "Market",
        price: Optional[float] = None,
        reduce_only: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.enable_trading:
            raise RuntimeError("Bybit trading disabled. Set BYBIT_ENABLE_TRADING=true to enable testnet orders")

        body: Dict[str, Any] = {
            "category": category,
            "symbol": symbol,
            "side": side,
            "orderType": order_type,
            "qty": str(quantity),
            "reduceOnly": bool(reduce_only),
        }
        if price is not None and order_type.lower() != "market":
            body["price"] = str(price)

        if metadata:
            # Best-effort: allow a client-supplied tag for traceability.
            # Bybit supports orderLinkId; keep it small.
            order_link_id = metadata.get("orderLinkId") or metadata.get("order_link_id")
            if order_link_id:
                body["orderLinkId"] = str(order_link_id)[:36]

            # Optional TP/SL (supported for linear/inverse)
            tp = metadata.get('takeProfit') or metadata.get('take_profit')
            sl = metadata.get('stopLoss') or metadata.get('stop_loss')
            if tp is not None:
                body['takeProfit'] = str(tp)
                body['tpTriggerBy'] = str(metadata.get('tpTriggerBy') or metadata.get('tp_trigger_by') or 'LastPrice')
            if sl is not None:
                body['stopLoss'] = str(sl)
                body['slTriggerBy'] = str(metadata.get('slTriggerBy') or metadata.get('sl_trigger_by') or 'LastPrice')

        return self._private_request("POST", "/v5/order/create", json_body=body)

    def get_positions(self, *, category: str = "linear", symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.is_configured():
            raise RuntimeError("Bybit not configured. Set BYBIT_API_KEY/BYBIT_API_SECRET in config/private.txt")
        params: Dict[str, Any] = {"category": category}
        if symbol:
            params["symbol"] = symbol
        data = self._private_request("GET", "/v5/position/list", params=params)
        if isinstance(data, dict) and isinstance(data.get("result"), dict):
            lst = data["result"].get("list")
            if isinstance(lst, list):
                return lst
        return []

    def get_account_summary(self) -> Dict[str, Any]:
        # Placeholder for future; v5 has multiple wallet endpoints depending on account type.
        return {"ok": True, "note": "Not implemented yet"}
