#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IG Markets (IG Italia) broker client.

This client focuses on:
- Session login (CST + X-SECURITY-TOKEN)
- Basic read endpoints (accounts, positions)

IG keys expected in config/private.txt:
- IG_API_KEY
- IG_USERNAME
- IG_PASSWORD
- IG_ENV=demo|live (optional)
- IG_BASE_URL (optional override)
- IG_ACCOUNT_ID (optional)

IMPORTANT:
- Never print or log credentials or session tokens.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging
from decimal import Decimal, ROUND_DOWN

import requests

from config.private_config import get_private_value

log = logging.getLogger(__name__)


class IGClient:
    name = "ig"

    def __init__(self):
        self.api_key = (get_private_value("IG_API_KEY", "") or "").strip()
        self.username = (get_private_value("IG_USERNAME", "") or "").strip()
        self.password = (get_private_value("IG_PASSWORD", "") or "").strip()
        self.account_id = (get_private_value("IG_ACCOUNT_ID", "") or "").strip()

        env_raw = (get_private_value("IG_ENV", "demo") or "demo").strip().lower()
        # Extra guard: if someone wrote inline comments without our parser.
        env_raw = env_raw.split("#", 1)[0].strip()
        self.env = (env_raw.split() or ["demo"])[0]

        # Safety gates for order placement
        self.enable_trading = (get_private_value("IG_ENABLE_TRADING", "false") or "false").strip().lower() in {"1", "true", "yes"}
        self.allow_live = (get_private_value("IG_ALLOW_LIVE", "false") or "false").strip().lower() in {"1", "true", "yes"}

        if self.enable_trading and self.env in {"live", "prod", "production"} and not self.allow_live:
            raise RuntimeError(
                "Refusing to trade on IG LIVE. Set IG_ENV=demo for demo trading, "
                "or explicitly set IG_ALLOW_LIVE=true to allow live trading."
            )

        base_url = (get_private_value("IG_BASE_URL", "") or "").strip()
        if base_url:
            self.base_url = base_url.rstrip("/")
        else:
            # Default IG endpoints
            if self.env in {"live", "prod", "production"}:
                self.base_url = "https://api.ig.com/gateway/deal"
            else:
                self.base_url = "https://demo-api.ig.com/gateway/deal"

        # Session tokens (acquired on login)
        self.cst: Optional[str] = None
        self.security_token: Optional[str] = None

        # Local HTTP tuning
        timeout_s = get_private_value("IG_TIMEOUT_SECONDS", "10")
        try:
            self.timeout_seconds = float(timeout_s or 10)
        except Exception:
            self.timeout_seconds = 10.0

    def is_configured(self) -> bool:
        if not self.api_key or not self.username or not self.password:
            return False
        if "YOUR_" in self.api_key or "YOUR_" in self.username or "YOUR_" in self.password:
            return False
        return True

    def _headers(self, *, version: str, auth: bool) -> Dict[str, str]:
        headers = {
            "X-IG-API-KEY": self.api_key,
            "Accept": "application/json; charset=UTF-8",
            "Content-Type": "application/json; charset=UTF-8",
            "VERSION": str(version),
        }
        if auth:
            if not self.cst or not self.security_token:
                raise RuntimeError("IG session not established. Call login() first.")
            headers["CST"] = self.cst
            headers["X-SECURITY-TOKEN"] = self.security_token
        return headers

    def login(self) -> Dict[str, Any]:
        """Create an authenticated IG session.

        Stores CST and X-SECURITY-TOKEN in-memory.
        """
        if not self.is_configured():
            raise RuntimeError("IG credentials missing. Set IG_API_KEY/IG_USERNAME/IG_PASSWORD in config/private.txt")

        url = f"{self.base_url}/session"
        payload = {"identifier": self.username, "password": self.password}

        resp = requests.post(
            url,
            headers=self._headers(version="2", auth=False),
            json=payload,
            timeout=self.timeout_seconds,
        )
        resp.raise_for_status()

        # Session tokens are provided in response headers
        self.cst = resp.headers.get("CST")
        self.security_token = resp.headers.get("X-SECURITY-TOKEN")
        if not self.cst or not self.security_token:
            raise RuntimeError("IG login succeeded but session tokens missing in response headers")

        data = resp.json() if resp.content else {}

        # Backfill account id from session payload if missing
        if not self.account_id and isinstance(data, dict):
            self.account_id = str(data.get("currentAccountId") or "").strip()

        return {
            "ok": True,
            "env": self.env,
            "base_url": self.base_url,
            "currentAccountId": (data.get("currentAccountId") if isinstance(data, dict) else None),
        }

    def _ensure_session(self) -> None:
        if not self.cst or not self.security_token:
            self.login()

    def get_accounts(self) -> Dict[str, Any]:
        """Fetch accounts list."""
        self._ensure_session()
        url = f"{self.base_url}/accounts"
        resp = requests.get(
            url,
            headers=self._headers(version="1", auth=True),
            timeout=self.timeout_seconds,
        )
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def get_account_summary(self) -> Dict[str, Any]:
        """Return a compact account summary.

        This is a best-effort wrapper around /accounts.
        """
        data = self.get_accounts()
        if not isinstance(data, dict):
            return {"accounts": data}

        accounts = data.get("accounts")
        if isinstance(accounts, list):
            preferred = next((a for a in accounts if a.get("preferred")), None)
        else:
            preferred = None

        return {
            "accounts_count": len(accounts) if isinstance(accounts, list) else None,
            "preferred_account": preferred,
            "current_account_id": self.account_id or None,
        }

    def get_positions(self) -> List[Dict[str, Any]]:
        """Fetch open positions."""
        self._ensure_session()
        url = f"{self.base_url}/positions"
        resp = requests.get(
            url,
            headers=self._headers(version="2", auth=True),
            timeout=self.timeout_seconds,
        )
        resp.raise_for_status()
        data = resp.json() if resp.content else {}
        if isinstance(data, dict) and isinstance(data.get("positions"), list):
            return data.get("positions")
        if isinstance(data, list):
            return data
        return []

    # --- Market data helpers (read-only) ---
    def search_markets(self, search_term: str) -> Dict[str, Any]:
        """Search IG markets by term.

        Returns the raw JSON payload (typically includes a 'markets' list).
        """
        self._ensure_session()
        url = f"{self.base_url}/markets"
        resp = requests.get(
            url,
            params={"searchTerm": search_term},
            headers=self._headers(version="1", auth=True),
            timeout=self.timeout_seconds,
        )
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def get_market(self, epic: str) -> Dict[str, Any]:
        """Get details + snapshot for a single market epic."""
        self._ensure_session()
        url = f"{self.base_url}/markets/{epic}"

        # IG uses different VERSION headers across endpoints; try the most
        # feature-complete version first.
        last_exc: Optional[BaseException] = None
        for ver in ("3", "2", "1"):
            try:
                resp = requests.get(
                    url,
                    headers=self._headers(version=ver, auth=True),
                    timeout=self.timeout_seconds,
                )
                resp.raise_for_status()
                return resp.json() if resp.content else {}
            except Exception as e:
                last_exc = e
                continue

        raise last_exc  # type: ignore[misc]

    def _quantize_size(self, *, desired: float, min_size: float, step: float) -> float:
        if desired <= 0:
            return 0.0
        if min_size and desired < min_size:
            desired = min_size
        if step and step > 0:
            q = Decimal(str(desired))
            s = Decimal(str(step))
            return float((q / s).to_integral_value(rounding=ROUND_DOWN) * s)
        return float(desired)

    def _extract_dealing_rules(self, market: Dict[str, Any]) -> Dict[str, float]:
        rules = (market.get('dealingRules') if isinstance(market, dict) else None) or {}
        def _val(path: str) -> float:
            cur: Any = rules
            for part in path.split('.'):
                if not isinstance(cur, dict):
                    return 0.0
                cur = cur.get(part)
            try:
                return float(cur)
            except Exception:
                return 0.0

        # IG typically returns objects like {"value": X}. Handle both.
        def _value_obj(key: str) -> float:
            v = rules.get(key)
            if isinstance(v, dict) and 'value' in v:
                try:
                    return float(v['value'])
                except Exception:
                    return 0.0
            try:
                return float(v)
            except Exception:
                return 0.0

        return {
            'minDealSize': _value_obj('minDealSize') or _val('minDealSize.value'),
            'dealSizeIncrement': _value_obj('dealSizeIncrement') or _val('dealSizeIncrement.value'),
        }

    def _confirm(self, deal_reference: str) -> Dict[str, Any]:
        self._ensure_session()
        url = f"{self.base_url}/confirms/{deal_reference}"
        resp = requests.get(
            url,
            headers=self._headers(version="1", auth=True),
            timeout=self.timeout_seconds,
        )
        resp.raise_for_status()
        return resp.json() if resp.content else {}

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
        """Place a basic IG OTC market order in demo/live.

        `symbol` is treated as an IG EPIC.
        """
        if reduce_only:
            raise NotImplementedError("IG reduce_only orders not implemented")

        if not self.enable_trading:
            raise RuntimeError("IG trading disabled. Set IG_ENABLE_TRADING=true to enable demo orders")

        epic = symbol
        direction = 'BUY' if side.upper() in {'BUY', 'LONG'} else 'SELL'

        # Best-effort quantization using market dealing rules
        try:
            market = self.get_market(epic) or {}
        except Exception:
            market = {}

        rules = self._extract_dealing_rules(market)
        min_size = float(rules.get('minDealSize') or 0)
        step = float(rules.get('dealSizeIncrement') or 0)
        size = self._quantize_size(desired=float(quantity), min_size=min_size, step=step)
        if size <= 0:
            raise RuntimeError(f"Invalid IG deal size computed for epic {epic}")

        # Stop/limit levels (optional)
        stop_level = None
        limit_level = None
        if metadata and isinstance(metadata, dict):
            stop_level = metadata.get('stopLevel') or metadata.get('stop_level')
            limit_level = metadata.get('limitLevel') or metadata.get('limit_level')

        currency_code = (metadata.get('currencyCode') if metadata else None) or (market.get('instrument', {}) or {}).get('currencies', [{}])[0].get('code')
        if not currency_code:
            currency_code = 'USD'

        payload: Dict[str, Any] = {
            'epic': epic,
            'direction': direction,
            'size': size,
            'orderType': 'MARKET',
            'currencyCode': currency_code,
            'forceOpen': True,
            'guaranteedStop': False,
        }

        if stop_level is not None:
            payload['stopLevel'] = float(stop_level)
        if limit_level is not None:
            payload['limitLevel'] = float(limit_level)

        # IG market order endpoint
        self._ensure_session()
        url = f"{self.base_url}/positions/otc"
        resp = requests.post(
            url,
            headers=self._headers(version="2", auth=True),
            json=payload,
            timeout=self.timeout_seconds,
        )
        resp.raise_for_status()
        data = resp.json() if resp.content else {}

        deal_ref = (data.get('dealReference') if isinstance(data, dict) else None) or ''
        confirm = {}
        if deal_ref:
            try:
                confirm = self._confirm(deal_ref)
            except Exception:
                confirm = {}

        return {
            'ok': True,
            'env': self.env,
            'epic': epic,
            'direction': direction,
            'size': size,
            'dealReference': deal_ref or None,
            'confirm': confirm,
            'raw': data,
        }
