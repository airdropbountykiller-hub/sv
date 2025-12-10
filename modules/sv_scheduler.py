#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - Enhanced Scheduler with Market intelligence
Sistema di scheduling intelligente con calendar integration
"""

import datetime
import pytz
import json
import os
import sys
import logging
from typing import Dict, Optional, List

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

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
        
        # Base schedule with market-aware timing - STRATEGIC HOURS
        self.schedule = {
            "press_review": "07:00",      # Press Review – early macro + news analysis
            "morning": "08:30",          # Morning Report – setup + predictions
            "noon": "13:00",             # Noon Update – progress + verification
            "evening": "18:30",          # Evening Analysis – session wrap + review
            "summary": "20:00",          # Daily Summary – complete 6-page analysis
            "weekly": "08:35",           # Weekly analysis (Monday 08:35) - after press review
            "monthly": "08:40",          # Monthly report (1st day of month)
            "quarterly": "08:45",        # Quarterly report (1st day of quarter: Jan/Apr/Jul/Oct)
            "semestral": "08:50",        # Semestral report (1st day of semester: Jan/Jul)
        }
        
        # Market-aware scheduling adjustments
        self.market_adjustments = {
            "PRE_MARKET": {"priority": "high", "frequency_modifier": 1.2},
            "MARKET_OPEN": {"priority": "critical", "frequency_modifier": 1.5},
            "MARKET_HOURS": {"priority": "high", "frequency_modifier": 1.0},
            "AFTER_MARKET": {"priority": "medium", "frequency_modifier": 0.8},
            "CLOSED": {"priority": "low", "frequency_modifier": 0.6}
        }
        
        self.flags_file = sv_paths.FLAGS_FILE
        self.flags = {
            "press_review_sent": False,
            "morning_sent": False,
            "noon_sent": False,
            "evening_sent": False,
            "summary_sent": False,
            "weekly_sent": False,
            "monthly_sent": False,
            "quarterly_sent": False,
            "semestral_sent": False,
            "last_reset_date": _today_key()
        }
        
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
    
    def load_flags(self):
        """Load flags from file"""
        try:
            if os.path.exists(self.flags_file):
                with open(self.flags_file, 'r') as f:
                    saved_flags = json.load(f)
                    self.flags.update(saved_flags)
                    log.info("ðŸ“„ Flags loaded from file")
            
            # Reset flags if new day
            current_date = _today_key()
            if self.flags.get("last_reset_date") != current_date:
                self.reset_daily_flags()
                self.flags["last_reset_date"] = current_date
                self.save_flags()
                log.info("ðŸ”„ Daily flags reset for new day")
                
        except Exception as e:
            log.error(f"âŒ Error loading flags: {e}")

    def save_flags(self):
        """Save flags to file"""
        try:
            with open(self.flags_file, 'w') as f:
                json.dump(self.flags, f, indent=2)
            log.debug("ðŸ’¾ Flags saved to file")
        except Exception as e:
            log.error(f"âŒ Error saving flags: {e}")

    def reset_daily_flags(self):
        """Reset daily content flags"""
        daily_flags = ["press_review_sent", "morning_sent", "noon_sent", "evening_sent", "summary_sent"]
        for flag in daily_flags:
            self.flags[flag] = False
        
        # Reset weekly on Monday (weekday 0)
        if _now_it().weekday() == 0:  # Monday
            self.flags["weekly_sent"] = False
        
        # Reset monthly on 1st day of month
        if _now_it().day == 1:
            self.flags["monthly_sent"] = False
            
            # Reset quarterly on 1st day of Jan/Apr/Jul/Oct
            if _now_it().month in [1, 4, 7, 10]:
                self.flags["quarterly_sent"] = False
            
            # Reset semestral on 1st day of Jan/Jul
            if _now_it().month in [1, 7]:
                self.flags["semestral_sent"] = False

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
        else:
            # Market-aware daily content scheduling
            if market_status == "CLOSED" and not self.is_weekend():
                # During market closed hours, still generate content on weekdays
                return time_match
            elif self.is_weekend():
                # Weekend - all daily content allowed (press_review, morning, noon, evening, summary)
                return time_match
            else:
                # Regular market days - all content allowed
                return time_match

    def should_generate_content(self, content_type: str) -> bool:
        """Check if content should be generated (time + not already sent)"""
        flag_key = f"{content_type}_sent"
        
        return (
            self.is_time_for_content(content_type) and 
            not self.flags.get(flag_key, False)
        )

    def mark_content_sent(self, content_type: str):
        """Mark content as sent and save flags"""
        flag_key = f"{content_type}_sent"
        self.flags[flag_key] = True
        self.save_flags()
        log.info(f"âœ… {content_type} marked as sent")

    def get_pending_content(self) -> list:
        """Get list of content types that need to be generated"""
        pending = []
        
        for content_type in self.schedule.keys():
            if self.should_generate_content(content_type):
                pending.append(content_type)
        
        return pending

    def get_status(self) -> dict:
        """Get enhanced scheduler status with market intelligence"""
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
        """Force reset a specific flag for testing"""
        flag_key = f"{content_type}_sent"
        if flag_key in self.flags:
            self.flags[flag_key] = False
            self.save_flags()
            log.info(f"ðŸ”„ Force reset flag: {content_type}")
            return True
        return False

    def force_reset_all_flags(self):
        """Force reset all flags for testing"""
        for key in self.flags.keys():
            if key.endswith('_sent'):
                self.flags[key] = False
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



