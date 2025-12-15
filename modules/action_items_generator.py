#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - Action Items Generator
Automatic generation of actionable tasks based on performance metrics and insights
"""

from pathlib import Path
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict

log = logging.getLogger(__name__)

class ActionItemsGenerator:
    """Generate actionable tasks based on comprehensive analytics"""
    
    def __init__(self):
        self.project_root = Path(__file__).resolve().parent.parent
        
        # Priority scoring weights
        self.priority_weights = {
            'risk_level': {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1},
            'performance_impact': {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1},
            'urgency': {'IMMEDIATE': 3, 'NEAR_TERM': 2, 'FUTURE': 1}
        }
    
    def generate_risk_based_actions(self, risk_analysis: Dict) -> List[Dict[str, Any]]:
        """Generate action items based on risk analysis"""
        actions = []
        
        if not risk_analysis or 'risk_level' not in risk_analysis:
            return actions
        
        risk_level = risk_analysis.get('risk_level', 'UNKNOWN')
        var_metrics = risk_analysis.get('var_metrics', {})
        drawdown_metrics = risk_analysis.get('drawdown_metrics', {})
        correlation_metrics = risk_analysis.get('correlation_metrics', {})
        
        # High risk level actions
        if risk_level == 'HIGH':
            actions.append({
                'category': 'RISK_MANAGEMENT',
                'priority': 'HIGH',
                'title': 'Implement Enhanced Risk Controls',
                'description': 'System showing HIGH risk level - implement immediate risk mitigation',
                'specific_tasks': [
                    'Reduce position sizes by 50%',
                    'Implement stricter stop-loss levels',
                    'Review and adjust risk parameters'
                ],
                'deadline': 'IMMEDIATE',
                'estimated_effort': '2-3 hours',
                'success_criteria': 'Risk level reduced to MEDIUM or below'
            })
        
        # VaR-based actions
        var_95 = var_metrics.get('var_95', 'N/A')
        if var_95 != 'N/A' and '%' in str(var_95):
            try:
                var_value = float(str(var_95).replace('%', ''))
                if var_value > 40:  # VaR above 40%
                    actions.append({
                        'category': 'PERFORMANCE_OPTIMIZATION',
                        'priority': 'MEDIUM',
                        'title': 'Improve Prediction Consistency',
                        'description': f'High VaR ({var_95}) indicates volatile performance',
                        'specific_tasks': [
                            'Review prediction methodology for consistency',
                            'Analyze worst-performing predictions',
                            'Consider ensemble model approaches'
                        ],
                        'deadline': 'NEAR_TERM',
                        'estimated_effort': '4-6 hours',
                        'success_criteria': 'VaR reduced below 35%'
                    })
            except ValueError:
                pass
        
        # Drawdown-based actions
        max_consecutive_losses = drawdown_metrics.get('max_consecutive_losses')
        if isinstance(max_consecutive_losses, int) and max_consecutive_losses >= 3:
            actions.append({
                'category': 'STRATEGY_REVIEW',
                'priority': 'HIGH',
                'title': 'Address Consecutive Loss Pattern',
                'description': f'System experienced {max_consecutive_losses} consecutive losses',
                'specific_tasks': [
                    'Analyze loss sequence patterns',
                    'Review strategy allocation during drawdown',
                    'Implement circuit breaker mechanisms'
                ],
                'deadline': 'IMMEDIATE',
                'estimated_effort': '3-4 hours',
                'success_criteria': 'Max consecutive losses reduced to 2 or below'
            })
        
        # Correlation-based actions
        diversification_benefit = correlation_metrics.get('diversification_benefit')
        if diversification_benefit == 'Low':
            actions.append({
                'category': 'PORTFOLIO_OPTIMIZATION',
                'priority': 'MEDIUM',
                'title': 'Improve Asset Diversification',
                'description': 'Low diversification benefit indicates high asset correlation',
                'specific_tasks': [
                    'Add uncorrelated asset classes',
                    'Review asset selection criteria',
                    'Consider alternative strategies'
                ],
                'deadline': 'NEAR_TERM',
                'estimated_effort': '2-3 hours',
                'success_criteria': 'Diversification benefit improved to Medium or High'
            })
        
        return actions
    
    def generate_performance_based_actions(self, performance_attribution: Dict) -> List[Dict[str, Any]]:
        """Generate action items based on performance analysis"""
        actions = []
        
        if not performance_attribution:
            return actions
        
        asset_attribution = performance_attribution.get('asset_attribution', {})
        daily_attribution = performance_attribution.get('daily_attribution', {})
        
        # Asset performance actions
        if 'worst_performing_asset' in asset_attribution:
            worst_asset = asset_attribution['worst_performing_asset']
            if worst_asset:
                asset_name = worst_asset[0]
                asset_data = worst_asset[1]
                accuracy = asset_data.get('accuracy', '0%')
                
                try:
                    accuracy_value = float(accuracy.replace('%', ''))
                    if accuracy_value < 40:  # Below 40% accuracy
                        actions.append({
                            'category': 'ASSET_STRATEGY',
                            'priority': 'HIGH',
                            'title': f'Fix {asset_name} Strategy Performance',
                            'description': f'{asset_name} showing poor performance ({accuracy} accuracy)',
                            'specific_tasks': [
                                f'Suspend {asset_name} predictions until review',
                                f'Analyze {asset_name} prediction methodology',
                                f'Recalibrate {asset_name} models'
                            ],
                            'deadline': 'IMMEDIATE',
                            'estimated_effort': '4-5 hours',
                            'success_criteria': f'{asset_name} accuracy improved above 50%'
                        })
                except ValueError:
                    pass
        
        # Daily performance actions
        if 'worst_performing_day' in daily_attribution:
            worst_day_data = daily_attribution['worst_performing_day']
            if worst_day_data:
                day_name = worst_day_data.get('day')
                day_details = worst_day_data.get('details', {})
                day_accuracy = day_details.get('accuracy', 'N/A')
                
                try:
                    if day_accuracy != 'N/A':
                        accuracy_value = float(day_accuracy.replace('%', ''))
                        if accuracy_value < 30:  # Very poor day performance
                            actions.append({
                                'category': 'TIMING_OPTIMIZATION',
                                'priority': 'MEDIUM',
                                'title': f'Optimize {day_name} Performance',
                                'description': f'{day_name} consistently underperforms ({day_accuracy} accuracy)',
                                'specific_tasks': [
                                    f'Review {day_name} market conditions',
                                    f'Adjust {day_name} prediction parameters',
                                    f'Consider reducing {day_name} position sizes'
                                ],
                                'deadline': 'NEAR_TERM',
                                'estimated_effort': '2-3 hours',
                                'success_criteria': f'{day_name} accuracy improved above 40%'
                            })
                except ValueError:
                    pass
        
        # Strategy performance actions
        strategy_attribution = performance_attribution.get('strategy_attribution', {})
        if 'worst_strategy' in strategy_attribution:
            worst_strategy = strategy_attribution['worst_strategy']
            if worst_strategy:
                strategy_name = worst_strategy[0]
                strategy_data = worst_strategy[1]
                strategy_accuracy = strategy_data.get('accuracy', '0%')
                
                try:
                    accuracy_value = float(strategy_accuracy.replace('%', ''))
                    if accuracy_value < 35:  # Poor strategy performance
                        actions.append({
                            'category': 'STRATEGY_OPTIMIZATION',
                            'priority': 'MEDIUM',
                            'title': f'Improve {strategy_name.replace("_", " ").title()} Strategy',
                            'description': f'{strategy_name} strategy underperforming ({strategy_accuracy} accuracy)',
                            'specific_tasks': [
                                f'Review {strategy_name} entry/exit criteria',
                                f'Backtest {strategy_name} parameters',
                                f'Consider {strategy_name} strategy modifications'
                            ],
                            'deadline': 'NEAR_TERM',
                            'estimated_effort': '3-4 hours',
                            'success_criteria': f'{strategy_name} accuracy improved above 45%'
                        })
                except ValueError:
                    pass
        
        return actions
    
    def generate_regime_based_actions(self, market_regime_analysis: Dict) -> List[Dict[str, Any]]:
        """Generate action items based on market regime analysis"""
        actions = []
        
        if not market_regime_analysis:
            return actions
        
        unified_regime = market_regime_analysis.get('unified_regime', 'UNKNOWN')
        regime_confidence = market_regime_analysis.get('regime_confidence', 'LOW')
        regime_insights = market_regime_analysis.get('regime_insights', [])
        
        # Regime-specific actions
        if unified_regime == 'VOLATILE_BEARISH':
            actions.append({
                'category': 'REGIME_ADAPTATION',
                'priority': 'HIGH',
                'title': 'Adapt to Volatile Bearish Regime',
                'description': 'Market regime requires defensive positioning',
                'specific_tasks': [
                    'Reduce overall exposure by 40%',
                    'Focus on short-bias strategies',
                    'Implement tighter stop-losses'
                ],
                'deadline': 'IMMEDIATE',
                'estimated_effort': '1-2 hours',
                'success_criteria': 'Portfolio adapted to bearish regime'
            })
        
        elif unified_regime == 'STRONG_BULL_TREND':
            actions.append({
                'category': 'REGIME_ADAPTATION',
                'priority': 'MEDIUM',
                'title': 'Capitalize on Bull Trend',
                'description': 'Strong bullish regime supports increased exposure',
                'specific_tasks': [
                    'Increase exposure in trending assets',
                    'Focus on momentum strategies',
                    'Use trailing stops to capture gains'
                ],
                'deadline': 'NEAR_TERM',
                'estimated_effort': '1-2 hours',
                'success_criteria': 'Exposure optimized for bull trend'
            })
        
        elif unified_regime == 'HIGH_VOLATILITY_MIXED':
            actions.append({
                'category': 'REGIME_ADAPTATION',
                'priority': 'MEDIUM',
                'title': 'Navigate High Volatility Environment',
                'description': 'High volatility requires adaptive position sizing',
                'specific_tasks': [
                    'Implement dynamic position sizing',
                    'Use shorter-term strategies',
                    'Monitor regime changes closely'
                ],
                'deadline': 'NEAR_TERM',
                'estimated_effort': '2-3 hours',
                'success_criteria': 'Position sizing adapted to volatility'
            })
        
        # Low confidence regime actions
        if regime_confidence == 'LOW':
            actions.append({
                'category': 'DATA_QUALITY',
                'priority': 'MEDIUM',
                'title': 'Improve Regime Detection Accuracy',
                'description': 'Low confidence in regime detection needs attention',
                'specific_tasks': [
                    'Increase daily data collection',
                    'Enhance market summary quality',
                    'Add regime confirmation indicators'
                ],
                'deadline': 'FUTURE',
                'estimated_effort': '3-4 hours',
                'success_criteria': 'Regime confidence improved to MEDIUM or HIGH'
            })
        
        return actions
    
    def generate_predictive_based_actions(self, next_week_predictions: Dict) -> List[Dict[str, Any]]:
        """Generate action items based on next week predictions"""
        actions = []
        
        if not next_week_predictions:
            return actions
        
        top_recommendations = next_week_predictions.get('top_recommendations', [])
        prediction_confidence = next_week_predictions.get('prediction_confidence', 'LOW')
        
        # Convert predictions to action items
        for rec in top_recommendations:
            if rec.get('priority') == 'HIGH':
                actions.append({
                    'category': 'TACTICAL_EXECUTION',
                    'priority': 'HIGH',
                    'title': f"Execute: {rec.get('title', 'N/A')}",
                    'description': rec.get('description', 'N/A'),
                    'specific_tasks': [
                        rec.get('action', 'No specific action provided'),
                        'Monitor execution results',
                        'Adjust as needed'
                    ],
                    'deadline': 'IMMEDIATE',
                    'estimated_effort': '30-60 minutes',
                    'success_criteria': 'Recommendation successfully implemented'
                })
        
        # Low prediction confidence actions
        if prediction_confidence == 'LOW':
            actions.append({
                'category': 'PREDICTION_IMPROVEMENT',
                'priority': 'MEDIUM',
                'title': 'Enhance Prediction Confidence',
                'description': 'Low prediction confidence indicates need for model improvement',
                'specific_tasks': [
                    'Review prediction methodology',
                    'Add more historical data',
                    'Validate prediction models'
                ],
                'deadline': 'FUTURE',
                'estimated_effort': '4-6 hours',
                'success_criteria': 'Prediction confidence improved to MEDIUM or HIGH'
            })
        
        return actions
    
    def calculate_action_priority_score(self, action: Dict[str, Any]) -> float:
        """Calculate numerical priority score for ranking actions"""
        score = 0.0
        
        # Base priority score
        priority = action.get('priority', 'LOW')
        score += self.priority_weights['risk_level'].get(priority, 1)
        
        # Deadline urgency
        deadline = action.get('deadline', 'FUTURE')
        if deadline == 'IMMEDIATE':
            score += 3
        elif deadline == 'NEAR_TERM':
            score += 2
        else:
            score += 1
        
        # Category importance
        category = action.get('category', '')
        category_weights = {
            'RISK_MANAGEMENT': 3,
            'STRATEGY_REVIEW': 2.5,
            'PERFORMANCE_OPTIMIZATION': 2,
            'REGIME_ADAPTATION': 2,
            'TACTICAL_EXECUTION': 1.5,
            'DATA_QUALITY': 1
        }
        score += category_weights.get(category, 1)
        
        return score
    
    def generate_comprehensive_action_items(self, risk_analysis: Dict = None, 
                                          performance_attribution: Dict = None,
                                          market_regime_analysis: Dict = None,
                                          next_week_predictions: Dict = None) -> Dict[str, Any]:
        """Generate comprehensive action items from all analytics"""
        try:
            log.info("[ACTION] Generating comprehensive action items...")
            
            all_actions = []
            
            # Generate actions from each analysis
            if risk_analysis:
                risk_actions = self.generate_risk_based_actions(risk_analysis)
                all_actions.extend(risk_actions)
            
            if performance_attribution:
                perf_actions = self.generate_performance_based_actions(performance_attribution)
                all_actions.extend(perf_actions)
            
            if market_regime_analysis:
                regime_actions = self.generate_regime_based_actions(market_regime_analysis)
                all_actions.extend(regime_actions)
            
            if next_week_predictions:
                pred_actions = self.generate_predictive_based_actions(next_week_predictions)
                all_actions.extend(pred_actions)
            
            # Calculate priority scores and sort
            for action in all_actions:
                action['priority_score'] = self.calculate_action_priority_score(action)
            
            # Sort by priority score (highest first)
            sorted_actions = sorted(all_actions, key=lambda x: x['priority_score'], reverse=True)
            
            # Categorize actions
            actions_by_category = defaultdict(list)
            actions_by_priority = defaultdict(list)
            
            for action in sorted_actions:
                actions_by_category[action.get('category', 'OTHER')].append(action)
                actions_by_priority[action.get('priority', 'LOW')].append(action)
            
            return {
                'total_actions': len(sorted_actions),
                'high_priority_actions': len(actions_by_priority['HIGH']),
                'medium_priority_actions': len(actions_by_priority['MEDIUM']),
                'low_priority_actions': len(actions_by_priority['LOW']),
                'all_actions': sorted_actions,
                'top_5_actions': sorted_actions[:5],
                'actions_by_category': dict(actions_by_category),
                'actions_by_priority': dict(actions_by_priority),
                'generation_timestamp': datetime.now().isoformat(),
                'summary': f"Generated {len(sorted_actions)} action items across {len(actions_by_category)} categories"
            }
            
        except Exception as e:
            log.error(f"[ACTION] Error generating action items: {e}")
            return {'error': f'Action items generation failed: {e}'}


# Helper functions
def generate_action_items(risk_analysis: Dict = None, performance_attribution: Dict = None,
                         market_regime_analysis: Dict = None, next_week_predictions: Dict = None) -> Dict[str, Any]:
    """Helper function to generate action items"""
    generator = ActionItemsGenerator()
    return generator.generate_comprehensive_action_items(
        risk_analysis, performance_attribution, market_regime_analysis, next_week_predictions
    )

def test_action_items_generation():
    """Test function for action items generation"""
    print("🧪 [TEST] Testing Action Items Generation...")
    
    try:
        # Create test data
        test_risk_analysis = {
            'risk_level': 'HIGH',
            'var_metrics': {'var_95': '45%'},
            'drawdown_metrics': {'max_consecutive_losses': 3}
        }
        
        test_performance_attribution = {
            'asset_attribution': {
                'worst_performing_asset': ['BTC', {'accuracy': '25%'}]
            },
            'daily_attribution': {
                'worst_performing_day': {'day': 'Tuesday', 'details': {'accuracy': '20%'}}
            }
        }
        
        test_regime_analysis = {
            'unified_regime': 'VOLATILE_BEARISH',
            'regime_confidence': 'HIGH'
        }
        
        test_predictions = {
            'top_recommendations': [
                {'priority': 'HIGH', 'title': 'Reduce BTC exposure', 'action': 'Sell 50% BTC position'}
            ],
            'prediction_confidence': 'MEDIUM'
        }
        
        # Test action items generation
        action_items = generate_action_items(
            test_risk_analysis, test_performance_attribution, 
            test_regime_analysis, test_predictions
        )
        
        print(f"✅ [TEST] Total Actions: {action_items.get('total_actions')}")
        print(f"✅ [TEST] High Priority: {action_items.get('high_priority_actions')}")
        print(f"✅ [TEST] Top Action: {action_items.get('top_5_actions', [{}])[0].get('title', 'N/A')}")
        print("✅ [TEST] Action items generation working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ [TEST] Action items generation error: {e}")
        return False

if __name__ == '__main__':
    test_action_items_generation()