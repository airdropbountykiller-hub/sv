#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - Enhanced Scheduler with Market intelligence
Sistema di scheduling intelligente con calendar integration
"""

from pathlib import Path
import datetime
import pytz
import json
import os
import sys
import logging
from typing import Dict, Optional, List

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from config import sv_paths

# Import SV Calendar for market intelligence
from modules.sv_calendar import SVCalendarSystem

log = logging.getLogger(__name__)

ITALY_TZ = pytz.timezone("Europe/Rome")

def _now_it():
    """Get current time in Italian timezone"""
    return datetime.datetime.now(ITALY_TZ)

def _today_key(dt=None):
    """Get today key for date tracking"""
    return (dt or _now_it()).strftime("%Y%m%d")

class SVScheduler:
    """
    Enhanced scheduler with market intelligence for SV content generation
    """
    
    def __init__(self):
        """Initialize SV Enhanced Scheduler"""
        # Initialize calendar system for market intelligence
        self.calendar = SVCalendarSystem()

        # Base schedule (Italy timezone) - every 3 hours as per integrated spec
        # 00:00 Night
        # 03:00 Late Night
        # 06:00 Press Review
        # 09:00 Morning
        # 12:00 Noon
        # 15:00 Afternoon
        # 18:00 Evening
        # 21:00 Summary
        self.schedule = {
            "night": "00:00",             # Night – after-hours/crypto + global handoff
            "late_night": "03:00",        # Late Night – Asia session check
            "press_review": "06:00",      # Press Review – early macro + news analysis
            "morning": "09:00",          # Morning Report – setup + predictions
            "noon": "12:00",             # Noon Update – progress + verification
            "afternoon": "15:00",        # Afternoon Update – mid-session tracking
            "evening": "18:00",          # Evening Analysis – session wrap + review
            "summary": "21:00",          # Daily Summary – complete analysis
            "weekly": "09:05",           # Weekly analysis (Monday) – after morning
            "monthly": "09:10",          # Monthly report (1st/last day of month as configured below)
            "quarterly": "09:15",        # Quarterly report
            "semestral": "09:20",        # Semestral report
        }

        # Market-aware scheduling adjustments
        self.market_adjustments = {
            "PRE_MARKET": {"priority": "high", "frequency_modifier": 1.2},
            "MARKET_OPEN": {"priority": "critical", "frequency_modifier": 1.5},
            "MARKET_HOURS": {"priority": "high", "frequency_modifier": 1.0},
            "AFTER_MARKET": {"priority": "medium", "frequency_modifier": 0.8},
            "CLOSED": {"priority": "low", "frequency_modifier": 0.6}
        }

        # Flags are stored as per-content "last_sent_period" keys.
        # This avoids midnight reset races (00:00 content) and removes the need
        # for a global daily reset.
        self.flags_file = sv_paths.FLAGS_FILE
        self.flags: Dict[str, object] = {
            "schema_version": 2,
            # kept for backward compatibility / legacy inspection only
            "last_reset_date": _today_key(),
        }
        for ct in self.schedule.keys():
            self.flags[f"{ct}_last_sent_period"] = ""
            # derived/status convenience (also kept for backward-compat consumers)
            self.flags[f"{ct}_sent"] = False

        self.ensure_directories()
        self.load_flags()
        
    def ensure_directories(self):
        """Create necessary directories"""
        try:
            sv_paths.setup_all_directories()
        except Exception as e:
            log.error(f"Error preparing config directories: {e}")

        report_dirs = [
            os.path.join(project_root, 'reports', '1_daily'),
            os.path.join(project_root, 'reports', '2_weekly'),
            os.path.join(project_root, 'reports', '3_monthly'),
            os.path.join(project_root, 'reports', '4_quarterly'),
            os.path.join(project_root, 'reports', '5_semestral')
        ]

        for directory in report_dirs:
            try:
                os.makedirs(directory, exist_ok=True)
            except Exception as e:
                log.error(f"Error creating directory {directory}: {e}")
    
    def _period_key(self, content_type: str, now: Optional[datetime.datetime] = None) -> str:
        """Return the dedupe key for a content type.

        Daily contents dedupe by date (YYYYMMDD). Periodic contents dedupe by:
        - weekly: ISO year+week (YYYY-Www)
        - monthly: YYYY-MM
        - quarterly: YYYY-Qq
        - semestral: YYYY-H1/H2
        """
        if now is None:
            now = _now_it()

        if content_type in ("weekly",):
            iso_year, iso_week, _ = now.isocalendar()
            return f"{iso_year}-W{iso_week:02d}"
        if content_type in ("monthly",):
            return now.strftime("%Y-%m")
        if content_type in ("quarterly",):
            q = ((now.month - 1) // 3) + 1
            return f"{now.year}-Q{q}"
        if content_type in ("semestral",):
            half = "H1" if now.month <= 6 else "H2"
            return f"{now.year}-{half}"

        # Default: daily
        return _today_key(now)

    def _sync_derived_sent_flags(self, now: Optional[datetime.datetime] = None) -> None:
        """Update *_sent booleans based on *_last_sent_period for current time."""
        if now is None:
            now = _now_it()
        for ct in self.schedule.keys():
            period_now = self._period_key(ct, now)
            last_key = f"{ct}_last_sent_period"
            self.flags[f"{ct}_sent"] = (self.flags.get(last_key, "") == period_now)

    def load_flags(self):
        """Load flags from file (migration-safe, no resets)."""
        try:
            now = _now_it()
            saved_flags: Dict[str, object] = {}
            if os.path.exists(self.flags_file):
                with open(self.flags_file, 'r', encoding='utf-8') as f:
                    saved_flags = json.load(f) or {}
                    if isinstance(saved_flags, dict):
                        self.flags.update(saved_flags)
                        log.info("ðŸ“„ Flags loaded from file")

            # Migration from legacy schema:
            # - old files stored boolean *_sent plus last_reset_date for daily reset
            # - new schema uses *_last_sent_period and never resets globally
            legacy_reset = str(saved_flags.get("last_reset_date") or "") if isinstance(saved_flags, dict) else ""
            today_key = _today_key(now)

            for ct in self.schedule.keys():
                last_key = f"{ct}_last_sent_period"
                bool_key = f"{ct}_sent"

                # Ensure keys exist
                if last_key not in self.flags:
                    self.flags[last_key] = ""

                # Convert legacy booleans if last_sent_period is missing/empty
                try:
                    has_last = bool(self.flags.get(last_key))
                except Exception:
                    has_last = False

                if not has_last and isinstance(saved_flags, dict) and bool(saved_flags.get(bool_key, False)):
                    # For daily content types, only trust the legacy bool if it's for today.
                    if ct not in ("weekly", "monthly", "quarterly", "semestral"):
                        if legacy_reset == today_key:
                            self.flags[last_key] = self._period_key(ct, now)
                    else:
                        # Periodic content: legacy bool implies "sent for current period"
                        self.flags[last_key] = self._period_key(ct, now)

            # Keep last_reset_date up to date as informational field
            self.flags["last_reset_date"] = today_key

            # Refresh derived booleans
            self._sync_derived_sent_flags(now)

        except Exception as e:
            log.error(f"âŒ Error loading flags: {e}")

    def save_flags(self):
        """Save flags to file (atomic write to avoid partial/corrupt JSON)."""
        try:
            now = _now_it()
            self._sync_derived_sent_flags(now)

            flags_path = Path(self.flags_file)
            flags_path.parent.mkdir(parents=True, exist_ok=True)

            tmp_path = flags_path.with_suffix(flags_path.suffix + ".tmp")
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(self.flags, f, indent=2, ensure_ascii=False)

            # Atomic replace on Windows when source/dest are on same filesystem
            os.replace(str(tmp_path), str(flags_path))
            log.debug("ðŸ’¾ Flags saved to file")
        except Exception as e:
            log.error(f"âŒ Error saving flags: {e}")

    def reset_daily_flags(self):
        """Legacy reset hook (kept for compatibility).

        In schema v2 we do not reset flags globally; we dedupe by period keys.
        This method now clears only the stored last_sent_period keys for daily content.
        """
        for ct in ("night", "late_night", "press_review", "morning", "noon", "afternoon", "evening", "summary"):
            self.flags[f"{ct}_last_sent_period"] = ""
        self._sync_derived_sent_flags(_now_it())

    def is_weekend(self) -> bool:
        """Check if today is weekend"""
        return _now_it().weekday() >= 5

    def is_last_day_of_month(self) -> bool:
        """Check if today is last day of month"""
        today = _now_it().date()
        tomorrow = today + datetime.timedelta(days=1)
        return tomorrow.day == 1
    
    def is_last_week_of_month(self) -> bool:
        """Check if today is in the last week of the month.

        Currently not used by the automatic scheduler loop; kept for potential
        future refinements (e.g. special handling on month-end).
        """
        today = _now_it().date()
        # Get last day of current month
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        last_day_of_month = next_month - datetime.timedelta(days=1)
        
        # Check if today is within 7 days of month end
        days_until_end = (last_day_of_month - today).days
        return days_until_end <= 6  # Last 7 days of month
    
    def get_market_intelligence(self) -> dict:
        """Get current market intelligence from calendar system"""
        try:
            # Get day context
            day_context = self.calendar.get_day_context()
            
            # Get market status
            market_status_data = self.calendar.get_market_status()
            market_status = market_status_data[0] if isinstance(market_status_data, (list, tuple)) and len(market_status_data) > 0 else "UNKNOWN"
            
            # Combine both intelligence sources
            intelligence = {
                "market_status": market_status,
                **day_context
            }
            
            return intelligence
            
        except Exception as e:
            log.error(f"Error getting market intelligence: {e}")
            return {
                "market_status": "UNKNOWN",
                "day_context": "Unknown",
                "week_position": "Unknown",
                "intelligence": ["Market intelligence unavailable"]
            }
    
    def is_high_priority_time(self) -> bool:
        """Check if current time requires high priority content generation"""
        market_intel = self.get_market_intelligence()
        market_status = market_intel.get("market_status", "UNKNOWN")
        
        # High priority during market open and pre-market
        return market_status in ["MARKET_OPEN", "PRE_MARKET"]
    
    def get_content_priority(self, content_type: str) -> str:
        """Get priority level for content type based on market conditions"""
        market_intel = self.get_market_intelligence()
        market_status = market_intel.get("market_status", "UNKNOWN")
        
        base_priority = self.market_adjustments.get(market_status, {}).get("priority", "medium")
        
        # Adjust priority based on content type
        if content_type in ["morning", "noon"] and market_status in ["MARKET_OPEN", "PRE_MARKET"]:
            return "critical"
        elif content_type == "evening" and market_status == "AFTER_MARKET":
            return "high"
        
        return base_priority
    
    def should_adjust_timing(self, content_type: str) -> bool:
        """Check if timing should be adjusted based on market conditions.

        Currently not invoked by ``is_time_for_content``; available as an
        experimental hook if we introduce dynamic rescheduling.
        """
        market_intel = self.get_market_intelligence()
        market_status = market_intel.get("market_status", "UNKNOWN")
        
        # During market hours, be more flexible with timing
        if market_status in ["MARKET_OPEN", "PRE_MARKET"]:
            return True
        
        # Weekend or closed market - stick to schedule
        return False

    def is_time_for_content(self, content_type: str) -> bool:
        """Check if it's time for specific content type with market intelligence"""
        now = _now_it()
        scheduled_time = self.schedule.get(content_type)
        
        if not scheduled_time:
            return False
            
        # Parse scheduled time
        hour, minute = map(int, scheduled_time.split(':'))
        
        # Create scheduled datetime for today
        scheduled_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # Check if current time has passed the scheduled time (catch-up logic)
        # Allow content if we're past scheduled time but haven't sent yet
        time_match = now >= scheduled_dt
        
        # Get market intelligence for context-aware scheduling
        market_intel = self.get_market_intelligence()
        market_status = market_intel.get("market_status", "UNKNOWN")
        
        # Additional checks for special content
        if content_type == "weekly":
            return time_match and now.weekday() == 0  # Monday only
        elif content_type == "monthly":
            return time_match and self.is_last_day_of_month()
        elif content_type == "quarterly":
            # 1st day of quarter: Jan/Apr/Jul/Oct
            return time_match and now.day == 1 and now.month in [1, 4, 7, 10]
        elif content_type == "semestral":
            # 1st day of semester: Jan/Jul
            return time_match and now.day == 1 and now.month in [1, 7]
        else:
            # Market-aware daily content scheduling
            if market_status == "CLOSED" and not self.is_weekend():
                # During market closed hours, still generate content on weekdays
                return time_match
            elif self.is_weekend():
                # Weekend - all daily content allowed (night, late_night, press_review, morning, noon, afternoon, evening, summary)
                return time_match
            else:
                # Regular market days - all content allowed
                return time_match

    def should_generate_content(self, content_type: str) -> bool:
        """Check if content should be generated (time + not already sent for this period)."""
        # Reload flags to avoid stale in-memory state in long-running/multi-process setups
        try:
            self.load_flags()
        except Exception:
            pass

        now = _now_it()
        period_now = self._period_key(content_type, now)
        last_key = f"{content_type}_last_sent_period"
        already_sent = (self.flags.get(last_key, "") == period_now)

        return self.is_time_for_content(content_type) and (not already_sent)

    def mark_content_sent(self, content_type: str):
        """Mark content as sent for the current period and save flags."""
        # Reload first to incorporate other writers, then update
        try:
            self.load_flags()
        except Exception:
            pass

        now = _now_it()
        self.flags[f"{content_type}_last_sent_period"] = self._period_key(content_type, now)
        self._sync_derived_sent_flags(now)
        self.save_flags()
        log.info(f"âœ… {content_type} marked as sent")

    def _maybe_rollover_daily_flags(self) -> None:
        """Legacy rollover hook.

        In schema v2 we never reset flags globally; we only keep last_reset_date
        as an informational field.
        """
        try:
            now = _now_it()
            self.flags["last_reset_date"] = _today_key(now)
            self._sync_derived_sent_flags(now)
        except Exception as e:
            log.warning(f"[SCHEDULER] Rollover check failed: {e}")

    def get_pending_content(self) -> list:
        """Get list of content types that need to be generated"""
        self._maybe_rollover_daily_flags()
        pending = []
        
        for content_type in self.schedule.keys():
            if self.should_generate_content(content_type):
                pending.append(content_type)
        
        return pending

    def get_status(self) -> dict:
        """Get enhanced scheduler status with market intelligence"""
        self._maybe_rollover_daily_flags()
        now = _now_it()
        market_intel = self.get_market_intelligence()
        pending_content = self.get_pending_content()
        
        status = {
            "current_time": now.strftime("%H:%M:%S"),
            "current_date": now.strftime("%Y-%m-%d"),
            "day_of_week": now.strftime("%A"),
            "is_weekend": self.is_weekend(),
            "is_last_day_of_month": self.is_last_day_of_month(),
            "is_high_priority_time": self.is_high_priority_time(),
            "pending_content": pending_content,
            "flags": self.flags.copy(),
            "schedule": self.schedule.copy(),
            "market_intelligence": market_intel,
            "content_priorities": {content: self.get_content_priority(content) for content in self.schedule.keys()}
        }
        
        return status

    def force_reset_flag(self, content_type: str):
        """Force reset a specific flag for testing."""
        last_key = f"{content_type}_last_sent_period"
        if last_key in self.flags:
            self.flags[last_key] = ""
            self._sync_derived_sent_flags(_now_it())
            self.save_flags()
            log.info(f"ðŸ”„ Force reset flag: {content_type}")
            return True
        return False

    def force_reset_all_flags(self):
        """Force reset all flags for testing."""
        for ct in self.schedule.keys():
            self.flags[f"{ct}_last_sent_period"] = ""
            self.flags[f"{ct}_sent"] = False
        self.flags["last_reset_date"] = _today_key(_now_it())
        self.save_flags()
        log.info("ðŸ”„ Force reset all content flags")

# Singleton instance
scheduler = None

def get_scheduler() -> SVScheduler:
    """Get singleton scheduler instance"""
    global scheduler
    if scheduler is None:
        scheduler = SVScheduler()
    return scheduler

# Helper functions
def is_time_for(content_type: str) -> bool:
    """Quick check if it's time for specific content"""
    return get_scheduler().should_generate_content(content_type)

def mark_sent(content_type: str):
    """Quick mark content as sent"""
    get_scheduler().mark_content_sent(content_type)

def get_pending() -> list:
    """Quick get pending content"""
    return get_scheduler().get_pending_content()

def get_status() -> dict:
    """Quick get scheduler status"""
    return get_scheduler().get_status()

def reset_flag(content_type: str):
    """Quick reset specific flag.

    Not used by the automated pipeline; kept for manual operations/tests.
    """
    return get_scheduler().force_reset_flag(content_type)


def reset_all_flags():
    """Quick reset all flags.

    Not used by the automated pipeline; kept for manual operations/tests.
    """
    get_scheduler().force_reset_all_flags()
# Test function
def test_scheduler():
    """Test enhanced scheduler functionality with market intelligence"""
    print("ðŸ§ª [TEST] Testing Enhanced SV Scheduler...")
    
    try:
        sched = get_scheduler()
        
        # Test status
        status = sched.get_status()
        print(f"âœ… [TEST] Current time: {status['current_time']}")
        print(f"âœ… [TEST] Day: {status['day_of_week']}")
        print(f"âœ… [TEST] Weekend: {status['is_weekend']}")
        print(f"âœ… [TEST] High priority time: {status['is_high_priority_time']}")
        
        # Test market intelligence
        market_intel = status.get('market_intelligence', {})
        print(f"âœ… [TEST] Market status: {market_intel.get('market_status', 'UNKNOWN')}")
        print(f"âœ… [TEST] Day context: {market_intel.get('day_context', 'Unknown')}")
        
        # Test content priorities
        priorities = status.get('content_priorities', {})
        print(f"âœ… [TEST] Content priorities: {priorities}")
        
        # Test pending content
        pending = sched.get_pending_content()
        print(f"âœ… [TEST] Pending content: {pending}")
        
        # Test flag operations
        print(f"âœ… [TEST] Flags: {list(status['flags'].keys())}")
        
        print("âœ… [TEST] Enhanced SV Scheduler working correctly")
        return True
        
    except Exception as e:
        print(f"âŒ [TEST] Enhanced Scheduler error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_scheduler()


