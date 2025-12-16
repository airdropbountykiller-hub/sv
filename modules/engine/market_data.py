#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ENGINE: Market data helpers

Centralised helpers to build live market snapshots for BTC, SPX, EURUSD, GOLD.
Designed to be imported by heartbeat, dashboard and generators.
"""

import datetime
from typing import Dict, Any, Optional

from modules.api.market_data import get_live_crypto_prices, get_live_equity_fx_quotes, GOLD_GRAMS_PER_TROY_OUNCE


def get_market_snapshot(now: Optional[datetime.datetime] = None) -> Dict[str, Any]:
    """Return a compact market snapshot for core assets.

    Structure:
        {
            'timestamp': ISO8601 string,
            'assets': {
                'BTC':    {'price': float, 'change_pct': float, 'unit': 'USD'},
                'SPX':    {'price': float, 'change_pct': float, 'unit': 'index'},
                'EURUSD': {'price': float, 'change_pct': float, 'unit': 'rate'},
                'GOLD':   {'price': float, 'change_pct': float, 'unit': 'USD/g'},
            }
        }
    """
    if now is None:
        now = datetime.datetime.now()

    assets: Dict[str, Any] = {}

    # BTC
    try:
        crypto = get_live_crypto_prices() or {}
        if 'BTC' in crypto:
            btc = crypto['BTC']
            assets['BTC'] = {
                'price': float(btc.get('price') or 0.0),
                'change_pct': float(btc.get('change_pct') or 0.0),
                'unit': 'USD',
            }
    except Exception:
        pass

    # SPX / EURUSD / GOLD
    try:
        quotes = get_live_equity_fx_quotes(['^GSPC', 'EURUSD=X', 'XAUUSD=X']) or {}
    except Exception:
        quotes = {}

    spx_q = quotes.get('^GSPC', {})
    eur_q = quotes.get('EURUSD=X', {})
    gold_q = quotes.get('XAUUSD=X', {})

    if spx_q.get('price'):
        try:
            assets['SPX'] = {
                'price': float(spx_q.get('price') or 0.0),
                'change_pct': float(spx_q.get('change_pct') or 0.0),
                'unit': 'index',
            }
        except Exception:
            pass

    if eur_q.get('price'):
        try:
            assets['EURUSD'] = {
                'price': float(eur_q.get('price') or 0.0),
                'change_pct': float(eur_q.get('change_pct') or 0.0),
                'unit': 'rate',
            }
        except Exception:
            pass

    # Gold in USD/gram
    try:
        gold_price = float(gold_q.get('price') or 0.0)
    except Exception:
        gold_price = 0.0
    try:
        gold_chg = float(gold_q.get('change_pct') or 0.0)
    except Exception:
        gold_chg = 0.0
    if gold_price:
        try:
            gold_per_gram = gold_price / GOLD_GRAMS_PER_TROY_OUNCE
            assets['GOLD'] = {
                'price': gold_per_gram,
                'change_pct': gold_chg,
                'unit': 'USD/g',
            }
        except Exception:
            pass

    return {
        'timestamp': now.isoformat(),
        'assets': assets,
    }
