#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SV Market Data API.

Centralizes fetching live data so we can:
- reuse results within a single run (reduce duplicate calls)
- add fallback providers (AlphaVantage, Finnhub, IG, Bybit) later
- handle retries/backoff consistently

Current providers:
- CryptoCompare (crypto prices)
- Yahoo Finance quote endpoint (indices/FX/commodities)
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from config.private_config import get_private_value
from modules.api.http import request_json

log = logging.getLogger(__name__)

GOLD_GRAMS_PER_TROY_OUNCE = 31.1035

# Simple in-memory TTL cache (per-process)
_CACHE: Dict[str, tuple[float, Any]] = {}

# Optional IG client singleton (reuses session tokens within the process)
_IG_CLIENT: Any = None


def _cache_get(key: str) -> Optional[Any]:
    now = time.time()
    item = _CACHE.get(key)
    if not item:
        return None
    exp, value = item
    if exp < now:
        _CACHE.pop(key, None)
        return None
    return value


def _cache_set(key: str, value: Any, ttl_seconds: float) -> None:
    _CACHE[key] = (time.time() + ttl_seconds, value)


def get_live_crypto_prices(symbols: str = "BTC,ETH,BNB,SOL,ADA,XRP,DOT,LINK") -> Dict[str, Dict[str, float]]:
    """Retrieve live crypto prices (USD) from CryptoCompare.

    Returns a mapping per symbol with: price, change_pct, high_24h, low_24h, volume_24h, market_cap.
    Adds TOTAL_MARKET_CAP as an aggregate field.

    Offline-safe: returns {} on failure.
    """

    cache_key = f"cryptocompare:{symbols}"
    cached = _cache_get(cache_key)
    if isinstance(cached, dict):
        return cached

    try:
        url = "https://min-api.cryptocompare.com/data/pricemultifull"
        params = {"fsyms": symbols, "tsyms": "USD"}
        data = request_json(url, params=params, timeout=10, retries=2)

        if not isinstance(data, dict) or "RAW" not in data:
            return {}

        prices: Dict[str, Dict[str, float]] = {}
        for sym in symbols.split(","):
            sym = sym.strip()
            raw = (data.get("RAW", {}) or {}).get(sym, {})
            usd = (raw or {}).get("USD", {})
            if usd:
                prices[sym] = {
                    "price": float(usd.get("PRICE") or 0),
                    "change_pct": float(usd.get("CHANGEPCT24HOUR") or 0),
                    "high_24h": float(usd.get("HIGH24HOUR") or 0),
                    "low_24h": float(usd.get("LOW24HOUR") or 0),
                    "volume_24h": float(usd.get("VOLUME24HOUR") or 0),
                    "market_cap": float(usd.get("MKTCAP") or 0),
                }
            else:
                prices[sym] = {
                    "price": 0.0,
                    "change_pct": 0.0,
                    "high_24h": 0.0,
                    "low_24h": 0.0,
                    "volume_24h": 0.0,
                    "market_cap": 0.0,
                }

        total_market_cap = sum(v.get("market_cap", 0.0) for v in prices.values())
        prices["TOTAL_MARKET_CAP"] = float(total_market_cap)

        _cache_set(cache_key, prices, ttl_seconds=15)
        return prices

    except Exception as e:
        log.warning(f"[MARKET-DATA] CryptoCompare error: {e}")
        return {}


def _get_ig_client():
    """Return a singleton IGClient instance (or None if not configured)."""
    global _IG_CLIENT
    if _IG_CLIENT is None:
        try:
            from modules.api.brokers.ig import IGClient

            _IG_CLIENT = IGClient()
        except Exception:
            _IG_CLIENT = None
            return None

    try:
        if not _IG_CLIENT or not getattr(_IG_CLIENT, "is_configured", lambda: False)():
            return None
        # Establish a session lazily
        if not getattr(_IG_CLIENT, "cst", None) or not getattr(_IG_CLIENT, "security_token", None):
            _IG_CLIENT.login()
        return _IG_CLIENT
    except Exception as e:
        log.warning(f"[MARKET-DATA] IG client unavailable: {e}")
        return None


def _ig_epic_for_symbol(symbol: str) -> str:
    """Map Yahoo-style symbols to IG epic values configured in private.txt."""
    mapping = {
        '^GSPC': 'IG_EPIC_SPX',
        'EURUSD=X': 'IG_EPIC_EURUSD',
        'XAUUSD=X': 'IG_EPIC_GOLD',
    }
    key = mapping.get(symbol)
    if not key:
        return ''
    return (get_private_value(key, '') or '').strip()


def _ig_quote_for_symbol(symbol: str) -> Optional[Dict[str, float]]:
    epic = _ig_epic_for_symbol(symbol)
    if not epic:
        return None

    cache_key = f"ig_quote:{epic}"
    cached = _cache_get(cache_key)
    if isinstance(cached, dict):
        return cached

    client = _get_ig_client()
    if client is None:
        return None

    try:
        market = client.get_market(epic) or {}
        snapshot = market.get('snapshot', {}) if isinstance(market, dict) else {}
        instrument = market.get('instrument', {}) if isinstance(market, dict) else {}

        bid = snapshot.get('bid')
        offer = snapshot.get('offer')
        last = snapshot.get('lastTraded')

        price = 0.0
        try:
            if bid is not None and offer is not None:
                price = (float(bid) + float(offer)) / 2.0
            elif last is not None:
                price = float(last)
        except Exception:
            price = 0.0

        # IG may return FX prices in "points"; use onePipMeans as a multiplier when present.
        # Example: EUR/USD bid 11765.8 with onePipMeans "0.0001 USD/EUR" -> 1.17658
        try:
            one_pip_means = instrument.get('onePipMeans')
            if isinstance(one_pip_means, str):
                mult_str = one_pip_means.strip().split()[0]
                pip_mult = float(mult_str)
                if price and 0 < pip_mult < 1.0:
                    price = price * pip_mult
        except Exception:
            pass

        try:
            change_pct = float(snapshot.get('percentageChange') or 0.0)
        except Exception:
            change_pct = 0.0

        if price:
            out = {"price": float(price), "change_pct": float(change_pct)}
            _cache_set(cache_key, out, ttl_seconds=10)
            return out

        return None

    except Exception as e:
        log.warning(f"[MARKET-DATA] IG quote error for {symbol}: {e}")
        return None


def get_live_equity_fx_quotes(symbols: list[str]) -> Dict[str, Dict[str, float]]:
    """Get live quotes (Yahoo with IG fallback for core symbols).

    Offline-safe: returns {} on failure.

    IG fallback supports only symbols that have epics configured:
      - ^GSPC -> IG_EPIC_SPX
      - EURUSD=X -> IG_EPIC_EURUSD
      - XAUUSD=X -> IG_EPIC_GOLD
    """

    if not symbols:
        return {}

    # Canonical cache key (stable order)
    symbols_key = ",".join(sorted(set(symbols)))
    cache_key = f"equity_fx_quotes:{symbols_key}"
    cached = _cache_get(cache_key)
    if isinstance(cached, dict):
        return cached

    result: Dict[str, Dict[str, float]] = {}

    provider_pref = (get_private_value('SV_EQUITY_FX_PROVIDER', 'yahoo') or 'yahoo').strip().lower()
    ig_only = provider_pref in {'ig-only', 'ig_only'}
    ig_first = provider_pref in {'ig', 'ig_first'} or ig_only

    def _fill_from_yahoo(symbols_subset: Optional[list[str]] = None) -> None:
        syms = symbols_subset if symbols_subset is not None else symbols
        if not syms:
            return

        try:
            url = "https://query1.finance.yahoo.com/v7/finance/quote"
            params = {"symbols": ",".join(syms)}
            data = request_json(url, params=params, timeout=8, retries=2)

            for q in (data.get("quoteResponse", {}) or {}).get("result", []) if isinstance(data, dict) else []:
                sym = q.get("symbol")
                if not sym:
                    continue
                price = q.get("regularMarketPrice") or q.get("postMarketPrice") or 0
                chg_pct = q.get("regularMarketChangePercent") or 0
                result[sym] = {
                    "price": float(price or 0),
                    "change_pct": float(chg_pct or 0),
                }
        except Exception as e:
            # Many times Yahoo responds 429/401; we treat it as data-unavailable.
            log.warning(f"[MARKET-DATA] Yahoo quote error: {e}")

    def _fill_missing_from_ig() -> None:
        try:
            missing = [
                sym for sym in symbols
                if sym not in result or not float(result.get(sym, {}).get('price') or 0.0)
            ]
            for sym in missing:
                ig_q = _ig_quote_for_symbol(sym)
                if ig_q:
                    result[sym] = ig_q
        except Exception as e:
            log.warning(f"[MARKET-DATA] IG fallback error: {e}")

    # Provider order
    if ig_only:
        _fill_missing_from_ig()
    elif ig_first:
        _fill_missing_from_ig()
        missing_for_yahoo = [
            sym for sym in symbols
            if sym not in result or not float(result.get(sym, {}).get('price') or 0.0)
        ]
        _fill_from_yahoo(missing_for_yahoo)
        _fill_missing_from_ig()
    else:
        _fill_from_yahoo()
        _fill_missing_from_ig()

    _cache_set(cache_key, result, ttl_seconds=20)
    return result
