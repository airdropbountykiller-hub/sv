#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Send one or more saved report JSONs to Telegram using the project's TelegramHandler
(which reads credentials from config/private.txt).

Usage:
  python config/scripts/send_telegram_reports.py <report1.json> [<report2.json> ...]
"""
import os
import sys
import json
import time

# Ensure project root modules are importable
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'modules'))

from telegram_handler import TelegramHandler  # type: ignore

if len(sys.argv) < 2:
    print("Usage: python config/scripts/send_telegram_reports.py <report1.json> [<report2.json> ...]")
    sys.exit(2)

telegram = TelegramHandler()


def load_messages(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    msgs = data.get("messages") or data.get("pages") or []
    # Normalize list of strings
    if isinstance(msgs, list) and all(isinstance(m, str) for m in msgs):
        return msgs
    # Some summaries may be under key 'messages' only
    return data.get("messages", [])


def main(paths):
    total = 0
    for p in paths:
        if not os.path.exists(p):
            print(f"[SKIP] File not found: {p}")
            continue
        msgs = load_messages(p)
        if not msgs:
            print(f"[SKIP] No messages in: {p}")
            continue
        print(f"[SEND] {p} -> {len(msgs)} messages")
        for i, msg in enumerate(msgs, 1):
            result = telegram.send_message(msg, content_type='document')
            total += 1
            print(f"  [{i}/{len(msgs)}] {'OK' if result.get('success') else 'FAIL'}")
            time.sleep(0.7)
    print(f"[DONE] Attempted to send {total} messages.")


if __name__ == "__main__":
    main(sys.argv[1:])
