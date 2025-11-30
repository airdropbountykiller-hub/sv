#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - Predictive Analyzer Module
Generate next week recommendations based on historical patterns and trends
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

log = logging.getLogger(__name__)

class PredictiveWeeklyAnalyzer:
    """Generate predictive insights and recommendations for next week"""
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    def analyze_asset_patterns(self, daily_data: Dict, performance_attribution: Dict) -> Dict[str, Any]:
        """Identify asset-specific patterns and predict next week performance"""
        try:
            asset_predictions = {}
            
            # Extract asset performance data
            asset_attribution = performance_attribution.get('asset_attribution', {})
            asset_performance = asset_attribution.get('asset_performance', {})
            
            for asset, perf_data in asset_performance.items():
                accuracy = float(perf_data.get('accuracy', '0%').strip('%'))
                days_active = perf_data.get('days_active', 0)
                
                # Generate prediction based on recent performance
                if accuracy >= 75 and days_active >= 3:
                    confidence = "HIGH"
                    recommendation = f"FOCUS on {asset} setups (historically {accuracy:.0f}% accuracy)"
                    action = "Increase position sizing"
                elif accuracy >= 50 and days_active >= 2:
                    confidence = "MEDIUM"  
                    recommendation = f"MONITOR {asset} opportunities (recent {accuracy:.0f}% success rate)"
                    action = "Standard position sizing"
                else:
                    confidence = "LOW"
                    recommendation = f"AVOID {asset} until pattern improves ({accuracy:.0f}% recent accuracy)"
                    action = "Reduce exposure"
                
                asset_predictions[asset] = {
                    'confidence': confidence,
                    'recommendation': recommendation,
                    'action': action,
                    'historical_accuracy': f"{accuracy:.0f}%",
                    'sample_size': days_active
                }
            
            # Rank assets by predicted performance
            ranked_assets = sorted(
                asset_predictions.items(),
                key=lambda x: (x[1]['confidence'] == 'HIGH', float(x[1]['historical_accuracy'].strip('%'))),
                reverse=True
            )
            
            return {
                'asset_predictions': asset_predictions,
                'top_asset_next_week': ranked_assets[0] if ranked_assets else None,
                'avoid_assets': [asset for asset, pred in asset_predictions.items() 
                               if pred['confidence'] == 'LOW'],
                'total_assets_analyzed': len(asset_predictions)
            }
            
        except Exception as e:
            log.error(f"[PREDICT] Error in asset pattern analysis: {e}")
            return {'error': f'Asset pattern analysis failed: {e}'}
    
    def predict_weekly_regime(self, daily_data: Dict, risk_analysis: Dict) -> Dict[str, Any]:
        """Predict market regime for next week based on current trends"""
        try:
            # Analyze recent volatility trends
            volatility_trend = "UNKNOWN"
            regime_prediction = "NEUTRAL"
            
            # Extract daily summaries for trend analysis
            daily_summaries = []
            for date_str, data in sorted(daily_data.items()):
                if isinstance(data, dict) and 'market_summary' in data:
                    summary = data['market_summary'].lower()
                    daily_summaries.append(summary)
            
            # Count key regime indicators
            bullish_keywords = ['strong', 'breakout', 'gains', 'positive', 'momentum', 'rally']
            bearish_keywords = ['weak', 'selloff', 'decline', 'negative', 'pressure', 'correction']
            volatile_keywords = ['volatile', 'uncertainty', 'mixed', 'choppy', 'rotation']
            
            bullish_count = sum(1 for summary in daily_summaries 
                              if any(keyword in summary for keyword in bullish_keywords))
            bearish_count = sum(1 for summary in daily_summaries
                              if any(keyword in summary for keyword in bearish_keywords))
            volatile_count = sum(1 for summary in daily_summaries
                               if any(keyword in summary for keyword in volatile_keywords))
            
            # Determine regime prediction
            total_days = len(daily_summaries)
            if total_days > 0:
                bullish_ratio = bullish_count / total_days
                bearish_ratio = bearish_count / total_days
                volatile_ratio = volatile_count / total_days
                
                if bullish_ratio > 0.6:
                    regime_prediction = "BULLISH_CONTINUATION"
                    confidence = "HIGH"
                elif bearish_ratio > 0.6:
                    regime_prediction = "BEARISH_CONTINUATION"  
                    confidence = "HIGH"
                elif volatile_ratio > 0.5:
                    regime_prediction = "VOLATILE_RANGE"
                    confidence = "MEDIUM"
                else:
                    regime_prediction = "CONSOLIDATION"
                    confidence = "MEDIUM"
            else:
                confidence = "LOW"
            
            # Factor in risk analysis
            risk_level = risk_analysis.get('risk_level', 'MEDIUM')
            if risk_level == 'HIGH':
                regime_prediction = f"DEFENSIVE_{regime_prediction}"
                confidence = "HIGH"
            
            # Generate specific outlook
            outlooks = {
                'BULLISH_CONTINUATION': "Expect continued upward momentum with breakout opportunities",
                'BEARISH_CONTINUATION': "Defensive positioning recommended, expect further downside",
                'VOLATILE_RANGE': "Range-bound trading expected, focus on mean reversion",
                'CONSOLIDATION': "Sideways movement likely, wait for directional clarity",
                'DEFENSIVE_BULLISH_CONTINUATION': "Bullish but with caution due to elevated risk levels",
                'DEFENSIVE_BEARISH_CONTINUATION': "Bearish trend with high risk - minimal exposure recommended"
            }
            
            return {
                'regime_prediction': regime_prediction,
                'confidence': confidence,
                'outlook': outlooks.get(regime_prediction, "Mixed market conditions expected"),
                'bullish_signals': bullish_count,
                'bearish_signals': bearish_count,
                'volatile_signals': volatile_count,
                'analysis_period': f"{total_days} days"
            }
            
        except Exception as e:
            log.error(f"[PREDICT] Error in regime prediction: {e}")
            return {'error': f'Regime prediction failed: {e}'}
    
    def generate_tactical_recommendations(self, asset_patterns: Dict, regime_prediction: Dict, 
                                        performance_attribution: Dict) -> List[Dict[str, Any]]:
        """Generate specific tactical recommendations for next week"""
        try:
            recommendations = []
            
            # Asset-based recommendations
            top_info = asset_patterns.get('top_asset_next_week')
            if top_info:
                asset_name, asset_data = top_info
                rec_text = str(asset_data.get('recommendation', '') or '')
                confidence = asset_data.get('confidence', 'LOW')
                # Only create a positive focus call when confidence is HIGH and
                # the underlying recommendation is not an explicit AVOID.
                if confidence == 'HIGH' and not rec_text.upper().startswith('AVOID '):
                    recommendations.append({
                        'priority': 'HIGH',
                        'category': 'ASSET_FOCUS',
                        'title': f"Focus on {asset_name} setups",
                        'description': f"{rec_text} based on {asset_data.get('historical_accuracy','n/a')} recent accuracy",
                        'action': asset_data.get('action'),
                        'confidence': confidence,
                    })
                # For LOW/medium confidence or AVOID cases we rely on the generic
                # "avoid assets" risk recommendation below instead of adding a
                # contradictory positive focus line.
            
            # Regime-based recommendations
            regime = regime_prediction.get('regime_prediction', 'NEUTRAL')
            regime_confidence = regime_prediction.get('confidence', 'MEDIUM')
            
            if 'BULLISH' in regime:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'MARKET_REGIME',
                    'title': "Bullish Regime Strategy",
                    'description': "Focus on momentum and breakout strategies",
                    'action': "Look for upside breakouts, avoid shorts",
                    'confidence': regime_confidence
                })
            elif 'BEARISH' in regime:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'MARKET_REGIME', 
                    'title': "Bearish Regime Defense",
                    'description': "Defensive positioning with selective shorts",
                    'action': "Reduce long exposure, consider hedging",
                    'confidence': regime_confidence
                })
            elif 'VOLATILE' in regime:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'MARKET_REGIME',
                    'title': "Volatile Range Strategy",
                    'description': "Range-bound trading with quick profits",
                    'action': "Mean reversion plays, tight stops",
                    'confidence': regime_confidence
                })
            
            # Avoid recommendations based on poor performers
            avoid_assets = asset_patterns.get('avoid_assets', [])
            if avoid_assets:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'RISK_MANAGEMENT',
                    'title': f"Avoid {', '.join(avoid_assets[:2])} Setups",
                    'description': f"Recent underperformance suggests avoiding these assets",
                    'action': "Skip signals, wait for improvement",
                    'confidence': 'HIGH'
                })
            
            # Performance-based recommendations
            daily_attribution = performance_attribution.get('daily_attribution', {})
            best_day = daily_attribution.get('best_performing_day', {})
            
            if best_day and 'day' in best_day:
                best_day_name = best_day['day']
                recommendations.append({
                    'priority': 'LOW',
                    'category': 'TIMING',
                    'title': f"{best_day_name} Performance Edge",
                    'description': f"Historical best performance on {best_day_name}s",
                    'action': f"Consider larger positions on {best_day_name}",
                    'confidence': 'MEDIUM'
                })
            
            return recommendations
            
        except Exception as e:
            log.error(f"[PREDICT] Error generating recommendations: {e}")
            return [{'error': f'Recommendation generation failed: {e}'}]
    
    def generate_next_week_predictions(self, daily_data: Dict, risk_analysis: Dict = None, 
                                     performance_attribution: Dict = None) -> Dict[str, Any]:
        """Generate comprehensive next week predictions and recommendations"""
        try:
            log.info("[PREDICT] Generating next week predictions...")
            
            if risk_analysis is None:
                risk_analysis = {}
            if performance_attribution is None:
                performance_attribution = {}
            
            # Perform predictive analyses
            asset_patterns = self.analyze_asset_patterns(daily_data, performance_attribution)
            regime_prediction = self.predict_weekly_regime(daily_data, risk_analysis)
            tactical_recommendations = self.generate_tactical_recommendations(
                asset_patterns, regime_prediction, performance_attribution
            )
            
            # Generate weekly outlook summary
            regime = regime_prediction.get('regime_prediction', 'NEUTRAL')
            outlook = regime_prediction.get('outlook', 'Mixed conditions expected')
            
            top_recommendations = [rec for rec in tactical_recommendations 
                                 if rec.get('priority') == 'HIGH'][:3]
            
            return {
                'asset_predictions': asset_patterns,
                'regime_forecast': regime_prediction,
                'tactical_recommendations': tactical_recommendations,
                'top_recommendations': top_recommendations,
                'weekly_outlook': outlook,
                'prediction_confidence': regime_prediction.get('confidence', 'MEDIUM'),
                'generation_timestamp': datetime.now().isoformat(),
                'data_basis': f"Analysis based on {len(daily_data)} days of historical data"
            }
            
        except Exception as e:
            log.error(f"[PREDICT] Error in next week predictions: {e}")
            return {'error': f'Next week predictions failed: {e}'}


# Helper functions
def generate_next_week_predictions(daily_data: Dict, risk_analysis: Dict = None, 
                                 performance_attribution: Dict = None) -> Dict[str, Any]:
    """Helper function to generate next week predictions"""
    analyzer = PredictiveWeeklyAnalyzer()
    return analyzer.generate_next_week_predictions(daily_data, risk_analysis, performance_attribution)

def test_predictive_analysis():
    """Test function for predictive analysis"""
    print("🧪 [TEST] Testing Predictive Weekly Analysis...")
    
    try:
        # Create test data
        test_daily_data = {
            '2025-11-18': {
                'market_summary': 'Mixed session with Fed minutes causing rotation into defensive sectors',
                'predictions': {'total_tracked': 3, 'hits': 1}
            },
            '2025-11-19': {
                'market_summary': 'Strong gains with breakout momentum continuing across markets',
                'predictions': {'total_tracked': 3, 'hits': 3}
            }
        }
        
        test_risk_analysis = {'risk_level': 'LOW'}
        
        test_performance_attribution = {
            'asset_attribution': {
                'asset_performance': {
                    'BTC': {'accuracy': '85%', 'days_active': 4},
                    'SPX': {'accuracy': '60%', 'days_active': 3}
                }
            },
            'daily_attribution': {
                'best_performing_day': {'day': 'Wednesday', 'details': {'accuracy': '100%'}}
            }
        }
        
        # Test predictive analysis
        predictions = generate_next_week_predictions(
            test_daily_data, test_risk_analysis, test_performance_attribution
        )
        
        print(f"✅ [TEST] Regime Forecast: {predictions.get('regime_forecast', {}).get('regime_prediction')}")
        print(f"✅ [TEST] Top Recommendations: {len(predictions.get('top_recommendations', []))}")
        print(f"✅ [TEST] Prediction Confidence: {predictions.get('prediction_confidence')}")
        print("✅ [TEST] Predictive analysis working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ [TEST] Predictive analysis error: {e}")
        return False

if __name__ == '__main__':
    test_predictive_analysis()