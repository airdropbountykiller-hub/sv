#!/usr/bin/env python3
"""Test all SV modules functionality"""
import sys
from pathlib import Path


# Ensure the repository root is on sys.path so modules can be imported in any
# environment (not just the original Windows path used when the script was
# created).
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

print("\n" + "="*50)
print("SV MODULES - COMPLETE TEST SUITE")
print("="*50)

# Test 1: Core imports
print("\n[TEST 1] Core module imports...")
try:
    from modules import sv_emoji, sv_news, sv_calendar, sv_scheduler
    from modules import telegram_handler, daily_generator
    print("✅ All core imports successful")
except Exception as e:
    print(f"❌ Import failed: {e}")

# Test 2: Narrative continuity
print("\n[TEST 2] Narrative continuity...")
try:
    from modules.narrative_continuity import NarrativeContinuity
    nc = NarrativeContinuity()
    ctx = nc.get_morning_press_review_connection()
    print(f"✅ Narrative continuity working")
    print(f"   Methods available: {len([m for m in dir(nc) if not m.startswith('_')])}")
except Exception as e:
    print(f"❌ Narrative continuity failed: {e}")

# Test 3: Scheduler
print("\n[TEST 3] Scheduler functionality...")
try:
    from modules.sv_scheduler import get_status
    status = get_status()
    print(f"✅ Scheduler operational")
    print(f"   Current time: {status['current_time']}")
    print(f"   Summary sent: {status['flags']['summary_sent']}")
except Exception as e:
    print(f"❌ Scheduler failed: {e}")

# Test 4: Daily generator
print("\n[TEST 4] Daily generator...")
try:
    from modules.daily_generator import get_daily_generator
    gen = get_daily_generator()
    print(f"✅ Daily generator initialized")
    print(f"   Narrative enabled: {gen.narrative is not None}")
except Exception as e:
    print(f"❌ Daily generator failed: {e}")

# Test 5: Telegram handler
print("\n[TEST 5] Telegram handler...")
try:
    from modules.telegram_handler import TelegramHandler
    tg = TelegramHandler()
    print(f"✅ Telegram handler initialized")
except Exception as e:
    print(f"❌ Telegram handler failed: {e}")

# Test 6: News system
print("\n[TEST 6] News system...")
try:
    from modules.sv_news import SVNewsSystem
    news = SVNewsSystem()
    print(f"✅ News system initialized")
    print(f"   RSS feeds: {len(news.RSS_FEEDS)} categories")
except Exception as e:
    print(f"❌ News system failed: {e}")

# Test 7: Calendar system
print("\n[TEST 7] Calendar system...")
try:
    from modules.sv_calendar import SVCalendarSystem
    cal = SVCalendarSystem()
    print(f"✅ Calendar system initialized")
except Exception as e:
    print(f"❌ Calendar system failed: {e}")

print("\n" + "="*50)
print("TEST SUITE COMPLETE")
print("="*50 + "\n")
