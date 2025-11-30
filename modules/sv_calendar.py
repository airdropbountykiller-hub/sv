#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - Calendar intelligence System
System calendario intelligente per Content Createtion Engine
Estratto dalle migliori funzionalitÃ  di 555.py e 555a_server.py
"""

import datetime
from datetime import timedelta
import pytz
import logging
import os
import json

# Setup logging  
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

ITALY_TZ = pytz.timezone("Europe/Rome")

def _now_it():
    """Get current time in Italian timezone"""
    return datetime.datetime.now(ITALY_TZ)

class SVCalendarSystem:
    """
    System calendario intelligente per SV Content Createtion Engine
    """
    
    def __init__(self):
        """Initialize SV Calendar System"""
        self.setup_economic_events()
        self.setup_market_schedule()
        
    def setup_economic_events(self):
        """Setup economic calendar events with expanded coverage"""
        today = datetime.date.today()
        
        # Expanded economic events for richer coverage
        self.economic_events = {
            "Finance": [
                self._Createte_event("FED Rate Decision", today + timedelta(days=2), "High", "Federal Reserve", "US"),
                self._Createte_event("US CPI Release", today + timedelta(days=6), "High", "Bureau of Labor Statistics", "US"),
                self._Createte_event("Eurozone Employment", today + timedelta(days=10), "Medium", "Eurostat", "EU"),
                self._Createte_event("ECB Conference", today + timedelta(days=15), "High", "European Central Bank", "EU"),
                self._Createte_event("NFP Report USA", today + timedelta(days=3), "High", "BLS", "US"),
                self._Createte_event("PMI Manufacturing EU", today + timedelta(days=7), "Medium", "Markit", "EU"),
                self._Createte_event("Bank of Japan Decision", today + timedelta(days=12), "High", "Bank of Japan", "JP"),
                self._Createte_event("UK GDP Release", today + timedelta(days=9), "Medium", "ONS", "GB")
            ],
            "Earnings": [
                self._Createte_event("NVIDIA Earnings Q4", today + timedelta(days=4), "High", "NVIDIA Corp", "NVDA"),
                self._Createte_event("Apple Q4 Results", today + timedelta(days=8), "High", "Apple Inc", "AAPL"),
                self._Createte_event("Tesla Deliveries", today + timedelta(days=5), "Medium", "Tesla Motors", "TSLA"),
                self._Createte_event("Microsoft Azure Update", today + timedelta(days=11), "Medium", "Microsoft", "MSFT"),
                self._Createte_event("Meta Q4 Guidance", today + timedelta(days=13), "Medium", "Meta Platforms", "META")
            ],
            "Crypto": [
                self._Createte_event("Ethereum Shanghai Upgrade", today + timedelta(days=3), "High", "Ethereum Foundation", "CRYPTO"),
                self._Createte_event("Bitcoin Halving Event", today + timedelta(days=45), "High", "Bitcoin Network", "CRYPTO"),
                self._Createte_event("Cardano Vasil Hard Fork", today + timedelta(days=7), "Medium", "IOHK", "CRYPTO"),
                self._Createte_event("Solana Network Update", today + timedelta(days=14), "Medium", "Solana Labs", "CRYPTO"),
                self._Createte_event("Polygon zkEVM Launch", today + timedelta(days=21), "Low", "Polygon", "CRYPTO"),
                self._Createte_event("Chainlink CCIP Release", today + timedelta(days=28), "Low", "Chainlink", "CRYPTO")
            ],
            "Geopolitics": [
                self._Createte_event("NATO Summit Brussels", today + timedelta(days=1), "High", "NATO HQ", "GLOBE"),
                self._Createte_event("G7 Finance Ministers", today + timedelta(days=8), "High", "G7 Presidency", "GLOBE"),
                self._Createte_event("OPEC+ Meeting", today + timedelta(days=11), "High", "OPEC Secretariat", "GLOBE"),
                self._Createte_event("WTO Trade Review", today + timedelta(days=18), "Medium", "World Trade Org", "GLOBE"),
                self._Createte_event("UN Climate Summit COP29", today + timedelta(days=25), "Medium", "United Nations", "GLOBE")
            ],
            "Italy": [
                self._Createte_event("EU Council Meeting", today + timedelta(days=2), "High", "EU Council", "IT"),
                self._Createte_event("ISTAT Inflation", today + timedelta(days=5), "Medium", "ISTAT", "IT"),
                self._Createte_event("Italian Stock Exchange Close", today + timedelta(days=1), "Low", "Borsa Italiana", "IT"),
                self._Createte_event("Bank of Italy Conference", today + timedelta(days=16), "Medium", "Bank of Italy", "IT")
            ],
            "Market Holidays": [
                self._Createte_event("US Thanksgiving", today + timedelta(days=30), "Medium", "NYSE", "US"),
                self._Createte_event("Black Friday", today + timedelta(days=31), "Low", "US Markets", "US"),
                self._Createte_event("Year End Close", today + timedelta(days=60), "High", "Global Markets", "GLOBAL"),
                self._Createte_event("New Year Break", today + timedelta(days=65), "Medium", "Global Markets", "GLOBAL")
            ],
            "Seasonal Events": [
                self._Createte_event("Q4 Earnings Season", today + timedelta(days=14), "High", "S&P 500", "SP500"),
                self._Createte_event("Tax Season Prep", today + timedelta(days=90), "Medium", "IRS", "IRS"),
                self._Createte_event("Crypto Tax Reports", today + timedelta(days=120), "Low", "Blockchain", "CRYPTO"),
                self._Createte_event("Summer Trading Lull", today + timedelta(days=200), "Low", "Markets", "MARKETS")
            ]
        }
        
    def setup_market_schedule(self):
        """Setup market schedule and timing logic"""
        # Main market hours (from 555a_server.py)
        self.market_hours = {
            "europe": {"open": 9, "close": 17.5},  # 9:00-17:30 CET
            "us_premarket": {"open": 10, "close": 15.5},  # 10:00-15:30 CET
            "us_regular": {"open": 15.5, "close": 22},  # 15:30-22:00 CET
            "asia": {"open": 2, "close": 9}  # 02:00-09:00 CET
        }
        
    def _Createte_event(self, title, date, impact, source, icon="CAL"):
        """Createte event object with enhanced data"""
        days_from_now = (date - datetime.date.today()).days
        urgency = "TODAY" if days_from_now == 0 else "TOMORROW" if days_from_now == 1 else f"{days_from_now}d"
        
        return {
            "Date": date.strftime("%Y-%m-%d"), 
            "FormattedDate": date.strftime("%d/%m"),
            "Title": title, 
            "Impact": impact, 
            "Source": source,
            "Category": "Economic",
            "Icon": icon,
            "Urgency": urgency,
            "DaysFromNow": days_from_now
        }
    
    def is_weekend(self):
        """Check if today is weekend (Saturday=5, Sunday=6)"""
        return _now_it().weekday() >= 5
    
    def is_last_day_of_month(self):
        """Check if today is last day of month"""
        today = _now_it().date()
        tomorrow = today + timedelta(days=1)
        return tomorrow.day == 1
    
    def get_market_status(self):
        """
        Get current market status with intelligence
        Algoritmo da 555a_server.py e sv-server.py
        """
        if self.is_weekend():
            now = _now_it()
            if now.weekday() == 5:  # Saturday
                return "WEEKEND_SAT", "Weekend - Markets closed (reopening Monday)"
            else:  # Sunday
                return "WEEKEND_SUN", "Weekend - Markets closed (reopening tomorrow)"
        
        # Check market hours (9:00-17:30 CET)
        now = _now_it()
        market_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
        market_close = now.replace(hour=17, minute=30, second=0, microsecond=0)
        
        if market_open <= now <= market_close:
            return "OPEN", "Markets open"
        elif now.hour < 9:
            return "PRE_MARKET", "Pre-market - Markets closed"
        else:
            return "AFTER_MARKET", "After-market - Markets closed"
    
    def get_day_context(self):
        """
        Get intelligent day context
        Algoritmo da sv-server.py
        """
        day = _now_it().strftime("%A").lower()
        
        contexts = {
            "monday": {
                "focus": "week_opening", 
                "tone": "setup_energy", 
                "desc": "Monday - Week Opening",
                "content_priority": "gap_analysis"
            },
            "tuesday": {
                "focus": "momentum_build", 
                "tone": "confirmation", 
                "desc": "Tuesday - Momentum Build",
                "content_priority": "trend_follow"
            },
            "wednesday": {
                "focus": "mid_week", 
                "tone": "fed_potential", 
                "desc": "Wednesday - Mid Week",
                "content_priority": "central_bank_watch"
            },
            "thursday": {
                "focus": "pre_weekend", 
                "tone": "positioning", 
                "desc": "Thursday - Pre Weekend Setup",
                "content_priority": "position_review"
            },
            "friday": {
                "focus": "week_close", 
                "tone": "summary_outlook", 
                "desc": "Friday - Week Close",
                "content_priority": "week_wrap"
            },
            "saturday": {
                "focus": "weekend_analysis", 
                "tone": "relaxed_deep", 
                "desc": "Saturday - Weekend Analysis",
                "content_priority": "crypto_focus"
            },
            "sunday": {
                "focus": "week_prep", 
                "tone": "anticipation", 
                "desc": "Sunday - Week Preparation",
                "content_priority": "week_preview"
            }
        }
        
        return contexts.get(day, contexts["monday"])
    
    def is_content_time(self, content_type, target_time):
        """
        Check if it's time for specific content with intelligent scheduling
        """
        now = _now_it()
        
        # Parse target time (e.g., "08:00", "13:00")
        try:
            target_hour, target_minute = map(int, target_time.split(':'))
        except ValueError:
            return False
        
        # Check if current time matches (within 1 minute window)
        time_match = (now.hour == target_hour and 
                     now.minute >= target_minute and 
                     now.minute < target_minute + 1)
        
        # Additional checks for special content
        if content_type == "weekly":
            return time_match and now.weekday() == 6  # Sunday only
        elif content_type == "monthly":
            return time_match and self.is_last_day_of_month()
        else:
            return time_match and not self.is_weekend()  # Normal daily content
    
    def get_events_next_days(self, days=7):
        """Get economic events for next N days"""
        today = datetime.date.today()
        end_date = today + timedelta(days=days)
        
        upcoming_events = []
        
        for category, events in self.economic_events.items():
            for event in events:
                event_date = datetime.datetime.strptime(event["Date"], "%Y-%m-%d").date()
                if today <= event_date <= end_date:
                    event_copy = event.copy()
                    event_copy["Category"] = category
                    event_copy["days_from_now"] = (event_date - today).days
                    upcoming_events.append(event_copy)
        
        # Sort by date
        upcoming_events.sort(key=lambda x: x["Date"])
        
        return upcoming_events
    
    def analyze_calendar_impact(self, events=None):
        """
        Analyze calendar impact using ML-style logic
        Algoritmo da 555.py Generatete_ml_comment_for_event
        """
        if events is None:
            events = self.get_events_next_days(7)
        
        if not events:
            return {
                "overall_impact": "LOW",
                "market_sentiment": "NEUTRAL", 
                "recommendations": ["Normal market operations"],
                "high_impact_events": 0
            }
        
        impact_scores = []
        high_impact_events = 0
        recommendations = []
        
        for event in events:
            title_lower = event["Title"].lower()
            impact = event["Impact"]
            days_away = event["days_from_now"]
            
            # Calculate impact score
            if impact == "High":
                score = 3
                high_impact_events += 1
            elif impact == "Medium":
                score = 2  
            else:
                score = 1
                
            # Boost score for imminent events
            if days_away <= 1:
                score *= 1.5
            elif days_away <= 3:
                score *= 1.2
            
            impact_scores.append(score)
            
            # Generatete recommendations based on event type
            if "fed" in title_lower or "ecb" in title_lower:
                if impact == "High":
                    recommendations.append("Monitor USD/EUR volatility pre-central bank decision")
            elif "inflation" in title_lower or "cpi" in title_lower:
                recommendations.append("Prepare defensive strategies for inflation data")
            elif "employment" in title_lower:
                recommendations.append("Watch cyclical sectors for employment data")
        
        # Calculate overall impact
        avg_score = sum(impact_scores) / len(impact_scores) if impact_scores else 0
        
        if avg_score >= 2.5:
            overall_impact = "HIGH"
            market_sentiment = "VOLATILE"
        elif avg_score >= 1.8:
            overall_impact = "MEDIUM"
            market_sentiment = "CAUTIOUS"
        else:
            overall_impact = "LOW"
            market_sentiment = "STABLE"
        
        return {
            "overall_impact": overall_impact,
            "market_sentiment": market_sentiment,
            "recommendations": recommendations[:3],  # Max 3
            "high_impact_events": high_impact_events,
            "total_events": len(events),
            "avg_impact_score": round(avg_score, 2)
        }
    
    def get_content_timing_advice(self, content_type):
        """Get timing advice for content Createtion"""
        day_context = self.get_day_context()
        market_status, market_msg = self.get_market_status()
        calendar_impact = self.analyze_calendar_impact()
        
        advice = {
            "optimal_time": True,
            "day_context": day_context,
            "market_status": market_status,
            "calendar_impact": calendar_impact,
            "timing_notes": []
        }
        
        # Add timing notes based on context
        if content_type == "press_review" and day_context["focus"] == "week_opening":
            advice["timing_notes"].append("Focus on weekend gap and weekly setup")
            
        elif content_type == "morning" and calendar_impact["overall_impact"] == "HIGH":
            advice["timing_notes"].append("High volatility expected - highlight key events")
            
        elif content_type == "evening" and day_context["focus"] == "week_close":
            advice["timing_notes"].append("Weekend preparation - focus on crypto and outlook")
            
        if market_status == "WEEKEND_SAT":
            advice["timing_notes"].append("Weekend mode - focus crypto and technical analysis")
        
        return advice

# Singleton instance
sv_calendar_system = None

def get_sv_calendar_system() -> SVCalendarSystem:
    """Get singleton instance of SV Calendar System"""
    global sv_calendar_system
    if sv_calendar_system is None:
        sv_calendar_system = SVCalendarSystem()
    return sv_calendar_system

# Helper functions for easy access
def get_market_status():
    """Get market status - quick access"""
    return get_sv_calendar_system().get_market_status()

def get_day_context():
    """Get day context - quick access"""
    return get_sv_calendar_system().get_day_context()

def is_content_time(content_type, target_time):
    """Check content timing - quick access"""
    return get_sv_calendar_system().is_content_time(content_type, target_time)

def get_events_next_days(days=7):
    """Get upcoming events"""
    return get_sv_calendar_system().get_events_next_days(days=days)

# Backward/compatibility wrapper expected by daily_generator
# Some parts of the code import `get_calendar_events(days_ahead=7)`
# Map it to the canonical get_events_next_days(days)

def get_calendar_events(days_ahead=7):
    """Compatibility wrapper: return events for the next N days.
    Args:
        days_ahead (int): number of days ahead to include (default 7)
    Returns:
        list[dict]: normalized event dictionaries
    """
    try:
        return get_sv_calendar_system().get_events_next_days(days=days_ahead)
    except Exception:
        # Fallback to empty list on any unexpected error to avoid breaking callers
        return []

def analyze_calendar_impact():
    """Analyze calendar impact"""
    return get_sv_calendar_system().analyze_calendar_impact()

def get_content_timing_advice(content_type):
    """Get content timing advice"""
    return get_sv_calendar_system().get_content_timing_advice(content_type)

# Test function
def test_sv_calendar():
    """Test SV Calendar System"""
    print("ðŸ§ª [TEST] Testing SV Calendar System...")
    
    try:
        calendar_system = get_sv_calendar_system()
        
        # Test market status
        status, message = calendar_system.get_market_status()
        print(f"âœ… [TEST] Market Status: {status} - {message}")
        
        # Test day context
        context = calendar_system.get_day_context()
        print(f"âœ… [TEST] Day Context: {context['desc']} (Focus: {context['focus']})")
        
        # Test upcoming events
        events = calendar_system.get_events_next_days(7)
        print(f"âœ… [TEST] Upcoming Events: {len(events)} eventi prossimi 7 giorni")
        
        if events:
            print(f"âœ… [TEST] Next Event: {events[0]['Titolo']} ({events[0]['Impatto']})")
        
        # Test calendar impact
        impact = calendar_system.analyze_calendar_impact()
        print(f"âœ… [TEST] Calendar Impact: {impact['overall_impact']} (Sentiment: {impact['market_sentiment']})")
        
        print("âœ… [TEST] SV Calendar System working correctly")
        return True
        
    except Exception as e:
        print(f"âŒ [TEST] Calendar system error: {e}")
        return False

if __name__ == '__main__':
    test_sv_calendar()



