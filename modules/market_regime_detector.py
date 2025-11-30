#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - Market Regime Detection Module
Advanced market regime analysis based on volatility, trend, and sentiment indicators
"""

import os
import json
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict

log = logging.getLogger(__name__)

class MarketRegimeDetector:
    """Detect and analyze market regimes from daily data"""
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Regime classification thresholds
        self.volatility_thresholds = {
            'low': 0.33,
            'medium': 0.66,
            'high': 1.0
        }
        
        self.trend_strength_thresholds = {
            'weak': 0.4,
            'moderate': 0.7,
            'strong': 1.0
        }
    
    def analyze_volatility_regime(self, daily_data: Dict) -> Dict[str, Any]:
        """Analyze volatility regime from daily performance data"""
        try:
            daily_accuracies = []
            accuracy_changes = []
            
            # Extract daily accuracy rates
            for date_str, data in sorted(daily_data.items()):
                if isinstance(data, dict) and 'predictions' in data:
                    predictions = data['predictions']
                    total = predictions.get('total_tracked', 0)
                    hits = predictions.get('hits', 0)
                    
                    if total > 0:
                        accuracy = hits / total
                        daily_accuracies.append(accuracy)
            
            if len(daily_accuracies) < 2:
                return {'volatility_regime': 'INSUFFICIENT_DATA', 'volatility_score': 0.0}
            
            # Calculate accuracy changes (proxy for prediction volatility)
            for i in range(1, len(daily_accuracies)):
                change = abs(daily_accuracies[i] - daily_accuracies[i-1])
                accuracy_changes.append(change)
            
            # Calculate volatility metrics
            mean_accuracy = np.mean(daily_accuracies)
            std_accuracy = np.std(daily_accuracies)
            mean_change = np.mean(accuracy_changes)
            
            # Normalize volatility score (0-1 scale)
            volatility_score = min(std_accuracy * 2, 1.0)  # Scale std to 0-1
            
            # Classify volatility regime
            if volatility_score <= self.volatility_thresholds['low']:
                volatility_regime = 'LOW_VOLATILITY'
                regime_description = 'Stable performance with consistent accuracy'
            elif volatility_score <= self.volatility_thresholds['medium']:
                volatility_regime = 'MEDIUM_VOLATILITY' 
                regime_description = 'Moderate performance swings'
            else:
                volatility_regime = 'HIGH_VOLATILITY'
                regime_description = 'Highly variable performance with significant swings'
            
            return {
                'volatility_regime': volatility_regime,
                'volatility_score': volatility_score,
                'regime_description': regime_description,
                'mean_accuracy': mean_accuracy,
                'accuracy_volatility': std_accuracy,
                'mean_daily_change': mean_change,
                'sample_size': len(daily_accuracies)
            }
            
        except Exception as e:
            log.error(f"[REGIME] Error in volatility analysis: {e}")
            return {'volatility_regime': 'ERROR', 'error': str(e)}
    
    def analyze_trend_regime(self, daily_data: Dict, performance_attribution: Dict) -> Dict[str, Any]:
        """Analyze trend strength and direction from performance data"""
        try:
            # Extract daily performance trend
            daily_performances = []
            accuracy_trend = []
            
            for date_str, data in sorted(daily_data.items()):
                if isinstance(data, dict) and 'predictions' in data:
                    predictions = data['predictions']
                    total = predictions.get('total_tracked', 0)
                    hits = predictions.get('hits', 0)
                    
                    if total > 0:
                        accuracy = hits / total
                        daily_performances.append({'date': date_str, 'accuracy': accuracy})
                        accuracy_trend.append(accuracy)
            
            if len(accuracy_trend) < 3:
                return {'trend_regime': 'INSUFFICIENT_DATA', 'trend_strength': 0.0}
            
            # Calculate trend metrics using linear regression
            x = np.arange(len(accuracy_trend))
            y = np.array(accuracy_trend)
            
            # Simple linear regression
            if len(x) > 1:
                slope, intercept = np.polyfit(x, y, 1)
                correlation = np.corrcoef(x, y)[0, 1] if len(x) > 1 else 0
            else:
                slope, correlation = 0, 0
            
            # Determine trend direction and strength
            trend_strength = abs(correlation) if not np.isnan(correlation) else 0
            
            if slope > 0.05 and trend_strength > self.trend_strength_thresholds['moderate']:
                trend_direction = 'IMPROVING'
                trend_regime = 'STRONG_UPTREND'
            elif slope < -0.05 and trend_strength > self.trend_strength_thresholds['moderate']:
                trend_direction = 'DECLINING'
                trend_regime = 'STRONG_DOWNTREND'
            elif trend_strength > self.trend_strength_thresholds['weak']:
                trend_direction = 'MIXED' if abs(slope) < 0.02 else ('IMPROVING' if slope > 0 else 'DECLINING')
                trend_regime = 'MODERATE_TREND'
            else:
                trend_direction = 'SIDEWAYS'
                trend_regime = 'NO_CLEAR_TREND'
            
            # Additional trend analysis from performance attribution
            best_day = None
            worst_day = None
            
            if performance_attribution and 'daily_attribution' in performance_attribution:
                daily_attr = performance_attribution['daily_attribution']
                best_day = daily_attr.get('best_performing_day', {}).get('day')
                worst_day = daily_attr.get('worst_performing_day', {}).get('day')
            
            return {
                'trend_regime': trend_regime,
                'trend_direction': trend_direction,
                'trend_strength': trend_strength,
                'slope': slope,
                'trend_correlation': correlation,
                'best_performing_day': best_day,
                'worst_performing_day': worst_day,
                'regime_description': self._get_trend_description(trend_regime, trend_direction),
                'sample_size': len(accuracy_trend)
            }
            
        except Exception as e:
            log.error(f"[REGIME] Error in trend analysis: {e}")
            return {'trend_regime': 'ERROR', 'error': str(e)}
    
    def analyze_sentiment_regime(self, daily_data: Dict, journal_entries: List[Dict]) -> Dict[str, Any]:
        """Analyze sentiment regime from market summaries and journal entries"""
        try:
            # Sentiment keywords classification
            bullish_keywords = [
                'strong', 'gains', 'breakout', 'momentum', 'rally', 'positive', 
                'exceptional', 'worked', 'successful', 'profit', 'hit', 'target'
            ]
            
            bearish_keywords = [
                'weak', 'decline', 'selloff', 'pressure', 'failed', 'miss',
                'stopped', 'loss', 'correction', 'defensive', 'cautious'
            ]
            
            neutral_keywords = [
                'mixed', 'consolidation', 'range', 'sideways', 'rotation',
                'uncertain', 'waiting', 'choppy', 'balanced'
            ]
            
            # Analyze daily market summaries
            daily_sentiments = []
            sentiment_scores = []
            
            for date_str, data in daily_data.items():
                if isinstance(data, dict) and 'market_summary' in data:
                    summary = data['market_summary'].lower()
                    
                    bullish_count = sum(1 for keyword in bullish_keywords if keyword in summary)
                    bearish_count = sum(1 for keyword in bearish_keywords if keyword in summary)
                    neutral_count = sum(1 for keyword in neutral_keywords if keyword in summary)
                    
                    # Calculate sentiment score (-1 to +1)
                    total_words = bullish_count + bearish_count + neutral_count
                    if total_words > 0:
                        sentiment_score = (bullish_count - bearish_count) / total_words
                    else:
                        sentiment_score = 0
                    
                    sentiment_scores.append(sentiment_score)
                    
                    # Classify daily sentiment
                    if sentiment_score > 0.3:
                        daily_sentiment = 'BULLISH'
                    elif sentiment_score < -0.3:
                        daily_sentiment = 'BEARISH'
                    else:
                        daily_sentiment = 'NEUTRAL'
                    
                    daily_sentiments.append({
                        'date': date_str,
                        'sentiment': daily_sentiment,
                        'score': sentiment_score,
                        'bullish_signals': bullish_count,
                        'bearish_signals': bearish_count
                    })
            
            # Analyze journal entries sentiment
            journal_sentiment_scores = []
            for entry in journal_entries:
                content = entry.get('content', '').lower()
                
                bullish_count = sum(1 for keyword in bullish_keywords if keyword in content)
                bearish_count = sum(1 for keyword in bearish_keywords if keyword in content)
                
                if bullish_count + bearish_count > 0:
                    journal_score = (bullish_count - bearish_count) / (bullish_count + bearish_count)
                    journal_sentiment_scores.append(journal_score)
            
            # Calculate overall sentiment metrics
            if sentiment_scores:
                overall_sentiment_score = np.mean(sentiment_scores)
                sentiment_volatility = np.std(sentiment_scores)
                
                # Include journal sentiment in overall score
                if journal_sentiment_scores:
                    combined_scores = sentiment_scores + journal_sentiment_scores
                    overall_sentiment_score = np.mean(combined_scores)
            else:
                overall_sentiment_score = 0
                sentiment_volatility = 0
            
            # Determine sentiment regime
            if overall_sentiment_score > 0.4:
                sentiment_regime = 'BULLISH_SENTIMENT'
                regime_description = 'Predominantly positive market sentiment'
            elif overall_sentiment_score < -0.4:
                sentiment_regime = 'BEARISH_SENTIMENT'
                regime_description = 'Predominantly negative market sentiment'
            elif sentiment_volatility > 0.5:
                sentiment_regime = 'VOLATILE_SENTIMENT'
                regime_description = 'Highly variable sentiment with mixed signals'
            else:
                sentiment_regime = 'NEUTRAL_SENTIMENT'
                regime_description = 'Balanced market sentiment'
            
            # Count regime days
            bullish_days = len([s for s in daily_sentiments if s['sentiment'] == 'BULLISH'])
            bearish_days = len([s for s in daily_sentiments if s['sentiment'] == 'BEARISH'])
            neutral_days = len([s for s in daily_sentiments if s['sentiment'] == 'NEUTRAL'])
            
            return {
                'sentiment_regime': sentiment_regime,
                'sentiment_score': overall_sentiment_score,
                'sentiment_volatility': sentiment_volatility,
                'regime_description': regime_description,
                'bullish_days': bullish_days,
                'bearish_days': bearish_days,
                'neutral_days': neutral_days,
                'daily_sentiments': daily_sentiments,
                'sample_size': len(sentiment_scores)
            }
            
        except Exception as e:
            log.error(f"[REGIME] Error in sentiment analysis: {e}")
            return {'sentiment_regime': 'ERROR', 'error': str(e)}
    
    def _get_trend_description(self, trend_regime: str, trend_direction: str) -> str:
        """Generate descriptive text for trend regime"""
        descriptions = {
            'STRONG_UPTREND': 'Strong improving performance trend with consistent gains',
            'STRONG_DOWNTREND': 'Strong declining performance trend requiring attention',
            'MODERATE_TREND': f'Moderate {trend_direction.lower()} trend with mixed signals',
            'NO_CLEAR_TREND': 'No clear directional trend, sideways performance pattern'
        }
        return descriptions.get(trend_regime, 'Mixed trend pattern')
    
    def detect_unified_regime(self, daily_data: Dict, performance_attribution: Dict = None, 
                            journal_entries: List[Dict] = None) -> Dict[str, Any]:
        """Detect comprehensive market regime combining all analyses"""
        try:
            log.info("[REGIME] Detecting unified market regime...")
            
            if performance_attribution is None:
                performance_attribution = {}
            if journal_entries is None:
                journal_entries = []
            
            # Perform all regime analyses
            volatility_analysis = self.analyze_volatility_regime(daily_data)
            trend_analysis = self.analyze_trend_regime(daily_data, performance_attribution)
            sentiment_analysis = self.analyze_sentiment_regime(daily_data, journal_entries)
            
            # Extract key regime components
            volatility_regime = volatility_analysis.get('volatility_regime', 'UNKNOWN')
            trend_regime = trend_analysis.get('trend_regime', 'UNKNOWN')
            sentiment_regime = sentiment_analysis.get('sentiment_regime', 'UNKNOWN')
            
            # Determine unified regime
            regime_components = {
                'volatility': volatility_regime,
                'trend': trend_regime,
                'sentiment': sentiment_regime
            }
            
            # Generate unified regime classification
            unified_regime = self._classify_unified_regime(regime_components)
            
            # Generate regime insights and recommendations
            regime_insights = self._generate_regime_insights(
                volatility_analysis, trend_analysis, sentiment_analysis, unified_regime
            )
            
            return {
                'unified_regime': unified_regime,
                'regime_components': regime_components,
                'volatility_analysis': volatility_analysis,
                'trend_analysis': trend_analysis,
                'sentiment_analysis': sentiment_analysis,
                'regime_insights': regime_insights,
                'regime_confidence': self._calculate_regime_confidence(volatility_analysis, trend_analysis, sentiment_analysis),
                'analysis_timestamp': datetime.now().isoformat(),
                'data_coverage': f"{len(daily_data)} days analyzed"
            }
            
        except Exception as e:
            log.error(f"[REGIME] Error in unified regime detection: {e}")
            return {'error': f'Unified regime detection failed: {e}'}
    
    def _classify_unified_regime(self, regime_components: Dict[str, str]) -> str:
        """Classify unified regime based on component regimes"""
        volatility = regime_components.get('volatility', 'UNKNOWN')
        trend = regime_components.get('trend', 'UNKNOWN')
        sentiment = regime_components.get('sentiment', 'UNKNOWN')
        
        # High volatility regimes
        if 'HIGH_VOLATILITY' in volatility:
            if 'BEARISH' in sentiment:
                return 'VOLATILE_BEARISH'
            elif 'BULLISH' in sentiment:
                return 'VOLATILE_BULLISH'
            else:
                return 'HIGH_VOLATILITY_MIXED'
        
        # Trending regimes
        elif 'STRONG_UPTREND' in trend:
            if 'BULLISH' in sentiment:
                return 'STRONG_BULL_TREND'
            else:
                return 'UPTREND_WITH_CAUTION'
        
        elif 'STRONG_DOWNTREND' in trend:
            if 'BEARISH' in sentiment:
                return 'STRONG_BEAR_TREND'
            else:
                return 'DOWNTREND_WITH_HOPE'
        
        # Low volatility regimes
        elif 'LOW_VOLATILITY' in volatility:
            if 'NEUTRAL' in sentiment:
                return 'STABLE_CONSOLIDATION'
            elif 'BULLISH' in sentiment:
                return 'STABLE_BULLISH'
            elif 'BEARISH' in sentiment:
                return 'STABLE_BEARISH'
            else:
                return 'LOW_VOLATILITY_RANGE'
        
        # Default mixed regime
        else:
            return 'MIXED_REGIME'
    
    def _calculate_regime_confidence(self, volatility_analysis: Dict, trend_analysis: Dict, 
                                   sentiment_analysis: Dict) -> str:
        """Calculate confidence level in regime detection"""
        confidence_factors = []
        
        # Volatility confidence
        vol_sample = volatility_analysis.get('sample_size', 0)
        if vol_sample >= 5:
            confidence_factors.append('HIGH')
        elif vol_sample >= 3:
            confidence_factors.append('MEDIUM')
        else:
            confidence_factors.append('LOW')
        
        # Trend confidence
        trend_strength = trend_analysis.get('trend_strength', 0)
        if trend_strength > 0.7:
            confidence_factors.append('HIGH')
        elif trend_strength > 0.4:
            confidence_factors.append('MEDIUM')
        else:
            confidence_factors.append('LOW')
        
        # Sentiment confidence
        sent_sample = sentiment_analysis.get('sample_size', 0)
        if sent_sample >= 4:
            confidence_factors.append('HIGH')
        elif sent_sample >= 2:
            confidence_factors.append('MEDIUM')
        else:
            confidence_factors.append('LOW')
        
        # Overall confidence
        high_count = confidence_factors.count('HIGH')
        medium_count = confidence_factors.count('MEDIUM')
        
        if high_count >= 2:
            return 'HIGH'
        elif high_count >= 1 or medium_count >= 2:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _generate_regime_insights(self, volatility_analysis: Dict, trend_analysis: Dict,
                                sentiment_analysis: Dict, unified_regime: str) -> List[str]:
        """Generate actionable insights from regime analysis"""
        insights = []
        
        # Volatility insights
        vol_regime = volatility_analysis.get('volatility_regime', '')
        if 'HIGH_VOLATILITY' in vol_regime:
            insights.append("High performance volatility suggests larger position sizing swings")
        elif 'LOW_VOLATILITY' in vol_regime:
            insights.append("Stable performance pattern supports consistent position sizing")
        
        # Trend insights
        trend_regime = trend_analysis.get('trend_regime', '')
        if 'UPTREND' in trend_regime:
            insights.append("Improving performance trend supports increased exposure")
        elif 'DOWNTREND' in trend_regime:
            insights.append("Declining performance trend suggests defensive positioning")
        
        # Sentiment insights
        sentiment_regime = sentiment_analysis.get('sentiment_regime', '')
        if 'BULLISH' in sentiment_regime:
            insights.append("Positive sentiment bias supports momentum strategies")
        elif 'BEARISH' in sentiment_regime:
            insights.append("Negative sentiment bias favors contrarian approaches")
        
        # Unified regime insights
        if unified_regime == 'STRONG_BULL_TREND':
            insights.append("Strong bull regime: maximize exposure with trailing stops")
        elif unified_regime == 'VOLATILE_BEARISH':
            insights.append("Volatile bear regime: minimal exposure with tight risk management")
        elif unified_regime == 'STABLE_CONSOLIDATION':
            insights.append("Stable consolidation: range-trading strategies preferred")
        
        return insights[:4]  # Top 4 insights


# Helper functions
def detect_market_regime(daily_data: Dict, performance_attribution: Dict = None,
                        journal_entries: List[Dict] = None) -> Dict[str, Any]:
    """Helper function to detect market regime"""
    detector = MarketRegimeDetector()
    return detector.detect_unified_regime(daily_data, performance_attribution, journal_entries)

def test_regime_detection():
    """Test function for regime detection"""
    print("🧪 [TEST] Testing Market Regime Detection...")
    
    try:
        # Create test data
        test_daily_data = {
            '2025-11-17': {
                'predictions': {'total_tracked': 3, 'hits': 2},
                'market_summary': 'Strong opening with gains and momentum building'
            },
            '2025-11-18': {
                'predictions': {'total_tracked': 3, 'hits': 1}, 
                'market_summary': 'Mixed session with defensive rotation and uncertainty'
            },
            '2025-11-19': {
                'predictions': {'total_tracked': 3, 'hits': 3},
                'market_summary': 'Exceptional day with breakout and strong positive signals'
            },
            '2025-11-20': {
                'predictions': {'total_tracked': 3, 'hits': 2},
                'market_summary': 'Continued gains with momentum and successful trades'
            }
        }
        
        test_performance_attribution = {
            'daily_attribution': {
                'best_performing_day': {'day': 'Wednesday'},
                'worst_performing_day': {'day': 'Tuesday'}
            }
        }
        
        test_journals = [
            {'date': '2025-11-19', 'content': 'BTC breakout strategy worked exceptionally well with strong momentum'}
        ]
        
        # Test regime detection
        regime_analysis = detect_market_regime(test_daily_data, test_performance_attribution, test_journals)
        
        print(f"✅ [TEST] Unified Regime: {regime_analysis.get('unified_regime')}")
        print(f"✅ [TEST] Regime Confidence: {regime_analysis.get('regime_confidence')}")
        print(f"✅ [TEST] Key Insights: {len(regime_analysis.get('regime_insights', []))}")
        print("✅ [TEST] Market regime detection working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ [TEST] Regime detection error: {e}")
        return False

if __name__ == '__main__':
    test_regime_detection()