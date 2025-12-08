#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, re
# Ensure project root on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    sys.path.insert(0, os.path.join(PROJECT_ROOT, 'modules'))
from modules.daily_generator import DailyContentGenerator
from modules.telegram_handler import TelegramHandler

def no_pua(s: str) -> bool:
    return not any(0xE000 <= ord(ch) <= 0xF8FF for ch in s)

def main():
    g = DailyContentGenerator()

    # Generate all contents (no send)
    pr = g.generate_press_review()
    am = g.generate_morning_report()
    nn = g.generate_noon_update()
    ev = g.generate_evening_analysis()
    sm = g.generate_daily_summary()

    assert isinstance(pr, list) and len(pr) >= 5, "Press Review should have >=5 sections"
    assert isinstance(am, list) and len(am) == 3, "Morning should have 3 messages"
    assert isinstance(nn, list) and len(nn) == 3, "Noon should have 3 messages"
    assert isinstance(ev, list) and len(ev) == 3, "Evening should have 3 messages"
    assert isinstance(sm, list) and len(sm) >= 5, "Summary should have >=5 pages"

    # Summary numbering and page 6 presence
    assert any("Page 1/6" in p for p in sm), "Summary should show Page 1/6"
    assert any("Page 6/6" in p or "DAILY JOURNAL & NOTES" in p for p in sm), "Summary page 6 present"

    # Morning/Noon references to 6 pages
    assert any("20:00 Daily Summary*: Complete day analysis (6 pages)" in m for m in am), "Morning should reference 6 pages"
    assert any("20:00 Daily Summary*: Complete day analysis (6 pages)" in m for m in nn), "Noon should reference 6 pages"

    # Evening detailed predictions present
    assert any("PREDICTION PERFORMANCE (DETAILED)" in e for e in ev), "Evening detailed prediction block present"

    # Telegram sanitization (no PUA)
    th = TelegramHandler()
    sample = "Hello\uE000World"  # includes PUA
    cleaned = th._sanitize_text(sample)
    assert no_pua(cleaned), "Sanitizer should remove Private Use Area glyphs"

    print("ALL IMPROVEMENT TESTS PASSED")

if __name__ == '__main__':
    main()
