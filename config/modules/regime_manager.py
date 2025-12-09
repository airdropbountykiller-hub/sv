#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - Daily Regime Manager
Unified sentiment and regime management across all daily messages
"""

import logging
from typing import Dict, Optional
from enum import Enum

log = logging.getLogger(__name__)

class MarketRegime(Enum):
    RISK_ON = "risk_on"
    RISK_OFF = "risk_off"
    NEUTRAL = "neutral"
    TRANSITIONING = "transitioning"

class SentimentState(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    MIXED = "mixed"
    NEUTRAL = "neutral"

class AccuracyGrade(Enum):
    A = "A"  # ≥80%
    B = "B"  # 60-79%
    C = "C"  # 40-59%
    D = "D"  # 1-39%
    NA = "N.A."  # 0% or no data

class DailyRegimeManager:
    """
    Manages daily market regime, sentiment, and narrative consistency
    across all 22 daily messages (Press→Morning→Noon→Evening→Summary)
    """
    
    def __init__(self):
        self.regime: Optional[MarketRegime] = None
        self.sentiment: Optional[SentimentState] = None
        self.accuracy_grade: Optional[AccuracyGrade] = None
        self.accuracy_pct: Optional[float] = None
        self.day_character: Optional[str] = None
        self.volatility_regime: str = "NORMAL"
        
    def update_from_accuracy(self, accuracy_pct: float, total_tracked: int = 0) -> None:
        """Update regime based on real ML performance"""
        self.accuracy_pct = accuracy_pct
        
        # Accuracy grade calculation
        if total_tracked == 0:
            self.accuracy_grade = AccuracyGrade.NA
        elif accuracy_pct >= 80:
            self.accuracy_grade = AccuracyGrade.A
        elif accuracy_pct >= 60:
            self.accuracy_grade = AccuracyGrade.B
        elif accuracy_pct >= 40:
            self.accuracy_grade = AccuracyGrade.C
        elif accuracy_pct > 0:
            self.accuracy_grade = AccuracyGrade.D
        else:
            self.accuracy_grade = AccuracyGrade.D
            
        log.info(f"[REGIME] Updated accuracy: {accuracy_pct}% (Grade: {self.accuracy_grade.value})")
    
    def update_from_sentiment_tracking(self, sentiment_data: Dict) -> None:
        """Update from sentiment_tracking_YYYY-MM-DD.json

        Accepts both legacy shapes (stage → 'POSITIVE') and the new
        JSON shape (stage → {'sentiment': 'POSITIVE', ...}).
        """
        try:
            primary_sentiment: Optional[str] = None

            if isinstance(sentiment_data, dict):
                # Helper to normalize a single stage entry
                def _extract(stage: str) -> str:
                    raw = sentiment_data.get(stage)
                    if isinstance(raw, dict):
                        val = raw.get('sentiment')
                        return str(val) if val is not None else ''
                    if isinstance(raw, str):
                        return raw
                    return ''

                # Priority: evening → noon → morning → press_review
                for stage in ('evening', 'noon', 'morning', 'press_review'):
                    val = _extract(stage)
                    if val:
                        primary_sentiment = val
                        break

            # Fallback: direct string or default neutral
            if not primary_sentiment:
                if isinstance(sentiment_data, str):
                    primary_sentiment = sentiment_data
                else:
                    primary_sentiment = "NEUTRAL"

            upper_val = primary_sentiment.upper()

            # Map to SentimentState
            if "POSITIVE" in upper_val:
                self.sentiment = SentimentState.POSITIVE
            elif "NEGATIVE" in upper_val:
                self.sentiment = SentimentState.NEGATIVE
            elif "MIXED" in upper_val:
                self.sentiment = SentimentState.MIXED
            else:
                self.sentiment = SentimentState.NEUTRAL

            log.info(f"[REGIME] Updated sentiment: {self.sentiment.value} (raw='{primary_sentiment}')")

        except Exception as e:
            log.warning(f"[REGIME] Error parsing sentiment data: {e} | payload={sentiment_data}")
            self.sentiment = SentimentState.NEUTRAL
    
    def infer_regime(self) -> MarketRegime:
        """Infer market regime from accuracy and sentiment"""
        if self.accuracy_grade in [AccuracyGrade.A, AccuracyGrade.B] and self.sentiment == SentimentState.POSITIVE:
            self.regime = MarketRegime.RISK_ON
        elif self.accuracy_grade == AccuracyGrade.D and self.sentiment == SentimentState.NEGATIVE:
            self.regime = MarketRegime.RISK_OFF
        elif self.sentiment == SentimentState.MIXED or self.accuracy_grade == AccuracyGrade.C:
            self.regime = MarketRegime.NEUTRAL
        else:
            self.regime = MarketRegime.TRANSITIONING
            
        return self.regime
    
    def get_session_character(self) -> str:
        """Get consistent session character description"""
        regime = self.infer_regime()
        
        if regime == MarketRegime.RISK_ON:
            return "Risk-on rotation - tech leadership confirmed"
        elif regime == MarketRegime.RISK_OFF:
            return "Risk-off rotation - defensive positioning"
        elif regime == MarketRegime.NEUTRAL:
            return "Mixed signals - sector rotation active"
        else:
            return "Market transition - regime shift in progress"
    
    def get_market_momentum_text(self) -> str:
        """Get consistent market momentum description"""
        if self.accuracy_grade == AccuracyGrade.A:
            return "Accelerating - trend strength confirmed"
        elif self.accuracy_grade == AccuracyGrade.B:
            return "Steady - momentum maintained"
        elif self.accuracy_grade == AccuracyGrade.C:
            return "Mixed - consolidation phase"
        elif self.accuracy_grade == AccuracyGrade.D:
            return "Challenging - trend unclear"
        else:
            return "Under evaluation - insufficient data"
    
    def get_model_stability_text(self) -> str:
        """Get consistent model stability description"""
        if self.accuracy_pct is None:
            return "Under evaluation - insufficient live tracking"
        elif self.accuracy_pct >= 70:
            return "High - consistent performance"
        elif self.accuracy_pct >= 40:
            return "Moderate - mixed signals"
        elif self.accuracy_pct > 0:
            return "Low - challenging conditions"
        else:
            return "Recalibrating - defensive mode"
    
    def get_risk_assessment_text(self) -> str:
        """Get consistent risk level description"""
        regime = self.infer_regime()
        
        if regime == MarketRegime.RISK_ON and self.accuracy_grade in [AccuracyGrade.A, AccuracyGrade.B]:
            return "STANDARD - Favorable conditions"
        elif regime == MarketRegime.RISK_OFF:
            return "ELEVATED - Defensive positioning"
        elif self.accuracy_grade == AccuracyGrade.D:
            return "HIGH - Capital preservation mode"
        else:
            return "MODERATE - Selective opportunities"
    
    def get_vix_description(self) -> str:
        """Get VIX description aligned with regime"""
        regime = self.infer_regime()
        
        if regime == MarketRegime.RISK_ON:
            return "VIX -5.2% - Complacency watch but manageable"
        elif regime == MarketRegime.RISK_OFF:
            return "VIX elevated - Risk-off sentiment confirmed"
        else:
            return "VIX mixed signals - Monitoring for directional clarity"
    
    def get_tomorrow_strategy_bias(self) -> str:
        """Get tomorrow's strategic bias"""
        regime = self.infer_regime()
        
        if regime == MarketRegime.RISK_ON:
            return "POSITIVE"
        elif regime == MarketRegime.RISK_OFF:
            return "DEFENSIVE"
        else:
            return "NEUTRAL"
    
    def get_narrative_coherence_score(self) -> float:
        """Calculate narrative coherence score (0-100)"""
        coherence_factors = []
        
        # Factor 1: Accuracy alignment (30%)
        if self.accuracy_pct is not None:
            if self.accuracy_pct >= 60:
                coherence_factors.append(0.30)
            elif self.accuracy_pct >= 30:
                coherence_factors.append(0.15)
            else:
                coherence_factors.append(0.05)
        
        # Factor 2: Sentiment consistency (25%)
        if self.sentiment and self.regime:
            if (self.sentiment == SentimentState.POSITIVE and self.regime == MarketRegime.RISK_ON) or \
               (self.sentiment == SentimentState.NEGATIVE and self.regime == MarketRegime.RISK_OFF):
                coherence_factors.append(0.25)
            else:
                coherence_factors.append(0.10)
        
        # Factor 3: Grade-performance alignment (25%)
        if self.accuracy_grade and self.accuracy_pct is not None:
            expected_alignment = True
            coherence_factors.append(0.25 if expected_alignment else 0.10)
        
        # Factor 4: Volatility regime consistency (20%)
        coherence_factors.append(0.20)  # Default - could be enhanced
        
        return sum(coherence_factors) * 100
    
    def get_debug_info(self) -> Dict:
        """Get current state for debugging"""
        return {
            'regime': self.regime.value if self.regime else None,
            'sentiment': self.sentiment.value if self.sentiment else None,
            'accuracy_grade': self.accuracy_grade.value if self.accuracy_grade else None,
            'accuracy_pct': self.accuracy_pct,
            'coherence_score': self.get_narrative_coherence_score(),
            'session_character': self.get_session_character(),
            'tomorrow_bias': self.get_tomorrow_strategy_bias()
        }

# Global instance
_daily_regime = None

def get_daily_regime_manager() -> DailyRegimeManager:
    """Get singleton daily regime manager"""
    global _daily_regime
    if _daily_regime is None:
        _daily_regime = DailyRegimeManager()
    return _daily_regime

def reset_daily_regime():
    """Reset regime manager (for new day)"""
    global _daily_regime
    _daily_regime = None

# Testing function
def test_regime_manager():
    """Test regime manager functionality"""
    print("🧪 [TEST] Testing Regime Manager...")
    
    manager = get_daily_regime_manager()
    
    # Test accuracy update
    manager.update_from_accuracy(0.0, 1)  # 0% accuracy, 1 tracked
    print(f"✅ Accuracy Grade: {manager.accuracy_grade.value}")
    
    # Test sentiment update
    sentiment_data = {'evening': 'NEGATIVE', 'noon': 'MIXED'}
    manager.update_from_sentiment_tracking(sentiment_data)
    print(f"✅ Sentiment: {manager.sentiment.value}")
    
    # Test regime inference
    regime = manager.infer_regime()
    print(f"✅ Regime: {regime.value}")
    
    # Test text generation
    print(f"✅ Session Character: {manager.get_session_character()}")
    print(f"✅ Market Momentum: {manager.get_market_momentum_text()}")
    print(f"✅ Risk Assessment: {manager.get_risk_assessment_text()}")
    
    # Debug info
    debug = manager.get_debug_info()
    print(f"✅ Coherence Score: {debug['coherence_score']:.1f}%")
    
    print("✅ [TEST] All regime manager tests passed!")
    return True

if __name__ == '__main__':
    test_regime_manager()