#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI helper to discover IG market epics.

Example:
  python modules/api/tools/ig_discover.py "S&P" EURUSD Gold

It logs in using IG_* keys from config/private.txt and prints a short list
of (instrumentName, epic) candidates per search term.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Ensure project root is on sys.path when executing as a script
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from modules.api.brokers.ig import IGClient


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover IG epics by search term")
    parser.add_argument("terms", nargs="*", help="Search terms (default: S&P, EURUSD, Gold)")
    parser.add_argument("--limit", type=int, default=8, help="Max results per term")
    args = parser.parse_args()

    terms = args.terms or ["S&P", "EURUSD", "Gold"]
    limit = max(1, min(25, int(args.limit or 8)))

    client = IGClient()
    if not client.is_configured():
        raise SystemExit("IG not configured. Set IG_API_KEY/IG_USERNAME/IG_PASSWORD in config/private.txt")

    client.login()

    for term in terms:
        print("\n===", term, "===")
        data = client.search_markets(term) or {}
        markets = data.get("markets") if isinstance(data, dict) else None
        if not isinstance(markets, list) or not markets:
            print("(no results)")
            continue

        for m in markets[:limit]:
            try:
                name = (m.get("instrumentName") or m.get("marketName") or "").strip()
                epic = (m.get("epic") or "").strip()
                typ = (m.get("instrumentType") or m.get("type") or "").strip()
                if not epic:
                    continue
                print(f"- {name} | {typ} | epic={epic}")
            except Exception:
                continue

    print("\nAdd your chosen epics to config/private.txt (example):")
    print("IG_EPIC_SPX=...")
    print("IG_EPIC_EURUSD=...")
    print("IG_EPIC_GOLD=...")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
