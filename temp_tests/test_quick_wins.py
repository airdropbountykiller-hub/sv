#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, json, datetime, sys

# Ensure project root on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

ok = True
errors = []

def check(cond, msg):
    global ok
    if cond:
        print(f"[OK] {msg}")
    else:
        ok = False
        print(f"[FAIL] {msg}")

try:
    from modules.daily_generator import DailyContentGenerator
    g = DailyContentGenerator()
except Exception as e:
    print(f"[ERROR] Import DailyContentGenerator failed: {e}")
    sys.exit(1)

# Run Morning
try:
    morning = g.generate_morning_report()
    check(isinstance(morning, list) and len(morning) >= 3, "Morning generated 3 messages")
    m1 = morning[0] if morning else ""
    check("MACRO CONTEXT SNAPSHOT" in m1, "Morning msg1 contains Macro Context Snapshot")
    check("NEWS IMPACT SNAPSHOT" in m1, "Morning msg1 contains News Impact Snapshot")
except Exception as e:
    ok = False
    errors.append(f"Morning error: {e}")

# Check predictions file saved
try:
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    pred_path = os.path.join('reports','1_daily', f'predictions_{today}.json')
    check(os.path.exists(pred_path), f"Predictions file exists: {pred_path}")
    if os.path.exists(pred_path):
        with open(pred_path, 'r', encoding='utf-8') as f:
            pdata = json.load(f)
        preds = pdata.get('predictions', [])
        check(len(preds) >= 3, "Predictions contain at least 3 entries (BTC, SPX, EURUSD)")
except Exception as e:
    ok = False
    errors.append(f"Predictions file check error: {e}")

# Run Noon
try:
    noon = g.generate_noon_update()
    check(isinstance(noon, list) and len(noon) >= 3, "Noon generated 3 messages")
    n1 = noon[0] if noon else ""
    n3 = noon[2] if len(noon) >= 3 else ""
    check("NEWS IMPACT SINCE MORNING" in n1, "Noon msg1 contains News Impact Since Morning")
    check("MORNING PREDICTIONS VERIFICATION" in n3, "Noon msg3 contains Morning Predictions Verification + Daily Accuracy")
except Exception as e:
    ok = False
    errors.append(f"Noon error: {e}")

# Run Evening
try:
    ev = g.generate_evening_analysis()
    check(isinstance(ev, list) and len(ev) >= 3, "Evening generated 3 messages")
    e1 = ev[0] if ev else ""
    e2 = ev[1] if len(ev) >= 2 else ""
    check("DAY'S IMPACTFUL NEWS" in e1, "Evening msg1 contains Day's Impactful News")
    check("PREDICTION PERFORMANCE (DETAILED)" in e2, "Evening msg2 contains detailed prediction breakdown")
except Exception as e:
    ok = False
    errors.append(f"Evening error: {e}")

# Run Summary
try:
    summ = g.generate_daily_summary()
    check(isinstance(summ, list) and len(summ) >= 5, "Summary generated at least 5 pages")
    contains_journal = any("DAILY JOURNAL & NOTES" in p for p in summ)
    check(contains_journal, "Summary includes Page 6 - Daily Journal & Notes")
except Exception as e:
    ok = False
    errors.append(f"Summary error: {e}")

print("\n=== TEST RESULT ===")
print("SUCCESS" if ok else "FAILED")
if errors:
    print("Errors:")
    for err in errors:
        print(" - ", err)
