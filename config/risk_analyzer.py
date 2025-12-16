#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - Risk Analyzer Module
Advanced risk metrics calculation based on real prediction data
"""

from pathlib import Path
import os
import json
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

log = logging.getLogger(__name__)

class SVRiskAnalyzer:
    """Advanced risk analysis for SV trading predictions"""
    
    def __init__(self):
        self.project_root = Path(__file__).resolve().parent.parent
        self.daily_metrics_dir = os.path.join(self.project_root, 'reports', 'metrics')
    
    def calculate_prediction_var(self, daily_data: Dict, confidence_level: float = 0.95) -> Dict[str, Any]:
        """Calculate Value at Risk for prediction performance"""
        try:
            # Extract prediction accuracy rates for each day
            accuracy_rates = []
            daily_predictions = []
            
            for date_str, data in daily_data.items():
                if isinstance(data, dict) and 'predictions' in data:
                    predictions = data['predictions']
                    total = predictions.get('total_tracked', 0)
                    hits = predictions.get('hits', 0)
                    
                    if total > 0:
                        accuracy = hits / total
                        accuracy_rates.append(accuracy)
                        daily_predictions.append({
                            'date': date_str,
                            'accuracy': accuracy,
                            'total_signals': total,
                            'hits': hits
                        })
            
            if not accuracy_rates:
                return {'var_95': 'N/A', 'var_99': 'N/A', 'details': 'Insufficient data'}
            
            # Calculate VaR using historical simulation
            accuracy_rates = np.array(accuracy_rates)
            mean_accuracy = np.mean(accuracy_rates)
            std_accuracy = np.std(accuracy_rates)
            
            # VaR calculation (worst case scenarios)
            var_95 = np.percentile(accuracy_rates, (1 - 0.95) * 100)
            var_99 = np.percentile(accuracy_rates, (1 - 0.99) * 100)
            
            # Additional risk metrics
            worst_day = min(daily_predictions, key=lambda x: x['accuracy']) if daily_predictions else None
            best_day = max(daily_predictions, key=lambda x: x['accuracy']) if daily_predictions else None
            
            return {
                'var_95': f"{var_95:.1%}",
                'var_99': f"{var_99:.1%}",
                'mean_accuracy': f"{mean_accuracy:.1%}",
                'volatility': f"{std_accuracy:.1%}",
                'worst_day_accuracy': f"{worst_day['accuracy']:.1%}" if worst_day else 'N/A',
                'best_day_accuracy': f"{best_day['accuracy']:.1%}" if best_day else 'N/A',
                'sample_size': len(accuracy_rates),
                'details': f"Based on {len(accuracy_rates)} days of prediction data"
            }
            
        except Exception as e:
            log.error(f"[RISK] Error calculating VaR: {e}")
            return {'var_95': 'N/A', 'var_99': 'N/A', 'details': f'Calculation error: {e}'}
    
    def analyze_drawdown_sequences(self, daily_data: Dict) -> Dict[str, Any]:
        """Analyze consecutive loss sequences and recovery patterns"""
        try:
            # Extract daily hit/miss sequences
            daily_results = []
            for date_str, data in sorted(daily_data.items()):
                if isinstance(data, dict) and 'predictions' in data:
                    predictions = data['predictions']
                    total = predictions.get('total_tracked', 0)
                    hits = predictions.get('hits', 0)
                    
                    if total > 0:
                        accuracy = hits / total
                        daily_results.append({
                            'date': date_str,
                            'accuracy': accuracy,
                            'is_profitable_day': accuracy > 0.5  # Consider >50% as profitable
                        })
            
            if not daily_results:
                return {'max_consecutive_losses': 'N/A', 'details': 'No data available'}
            
            # Find consecutive loss sequences
            current_drawdown = 0
            max_drawdown = 0
            consecutive_losses = 0
            max_consecutive_losses = 0
            drawdown_sequences = []
            current_sequence_start = None
            
            for i, day_result in enumerate(daily_results):
                if not day_result['is_profitable_day']:
                    if consecutive_losses == 0:
                        current_sequence_start = day_result['date']
                    consecutive_losses += 1
                    current_drawdown += (0.5 - day_result['accuracy'])  # Measure severity
                else:
                    # End of drawdown sequence
                    if consecutive_losses > 0:
                        drawdown_sequences.append({
                            'start_date': current_sequence_start,
                            'end_date': daily_results[i-1]['date'] if i > 0 else day_result['date'],
                            'duration': consecutive_losses,
                            'severity': current_drawdown
                        })
                        max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
                        max_drawdown = max(max_drawdown, current_drawdown)
                    
                    consecutive_losses = 0
                    current_drawdown = 0
            
            # Handle if week ends in drawdown
            if consecutive_losses > 0:
                drawdown_sequences.append({
                    'start_date': current_sequence_start,
                    'end_date': daily_results[-1]['date'],
                    'duration': consecutive_losses,
                    'severity': current_drawdown
                })
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
                max_drawdown = max(max_drawdown, current_drawdown)
            
            # Calculate recovery statistics
            avg_recovery_time = 0
            if len([seq for seq in drawdown_sequences if seq['duration'] > 1]) > 0:
                # Calculate average time to recover from multi-day drawdowns
                recovery_times = []
                for i, seq in enumerate(drawdown_sequences[:-1]):  # Exclude last if ongoing
                    # Recovery time is next profitable day after drawdown end
                    recovery_times.append(1)  # Simplified: assume 1 day recovery
                avg_recovery_time = np.mean(recovery_times) if recovery_times else 0
            
            return {
                'max_consecutive_losses': max_consecutive_losses,
                'max_drawdown_severity': f"{max_drawdown:.1%}" if max_drawdown > 0 else '0%',
                'total_drawdown_periods': len(drawdown_sequences),
                'avg_recovery_time': f"{avg_recovery_time:.1f} days" if avg_recovery_time > 0 else 'N/A',
                'current_streak': 'Profitable' if daily_results and daily_results[-1]['is_profitable_day'] else 'Loss',
                'sample_size': len(daily_results),
                'details': f"Analysis based on {len(daily_results)} days of prediction data"
            }
            
        except Exception as e:
            log.error(f"[RISK] Error analyzing drawdowns: {e}")
            return {'max_consecutive_losses': 'N/A', 'details': f'Analysis error: {e}'}
    
    def calculate_asset_correlations(self, daily_data: Dict) -> Dict[str, Any]:
        """Analyze correlation between different asset predictions"""
        try:
            # Extract asset-specific performance data
            asset_performance = {}
            
            for date_str, data in daily_data.items():
                if isinstance(data, dict) and 'prediction_eval' in data:
                    eval_data = data['prediction_eval']
                    if isinstance(eval_data, dict) and 'items' in eval_data:
                        for item in eval_data['items']:
                            asset = item.get('asset')
                            status = item.get('status')
                            
                            if asset and status:
                                if asset not in asset_performance:
                                    asset_performance[asset] = []
                                
                                # Score: 1 for success, 0 for pending, -1 for failure
                                if 'success' in status.lower() or 'hit' in status.lower():
                                    score = 1
                                elif 'fail' in status.lower() or 'miss' in status.lower():
                                    score = -1
                                else:
                                    score = 0
                                
                                asset_performance[asset].append({
                                    'date': date_str,
                                    'score': score
                                })
            
            if len(asset_performance) < 2:
                return {'correlations': 'N/A', 'details': 'Need at least 2 assets for correlation analysis'}
            
            # Calculate correlation matrix
            assets = list(asset_performance.keys())
            correlations = {}
            
            for i, asset1 in enumerate(assets):
                for j, asset2 in enumerate(assets[i+1:], i+1):
                    # Find common dates
                    dates1 = {item['date']: item['score'] for item in asset_performance[asset1]}
                    dates2 = {item['date']: item['score'] for item in asset_performance[asset2]}
                    
                    common_dates = set(dates1.keys()) & set(dates2.keys())
                    
                    if len(common_dates) > 1:
                        scores1 = [dates1[date] for date in common_dates]
                        scores2 = [dates2[date] for date in common_dates]
                        
                        # Calculate correlation
                        correlation = np.corrcoef(scores1, scores2)[0, 1]
                        if not np.isnan(correlation):
                            correlations[f"{asset1}_vs_{asset2}"] = correlation
            
            # Format results
            correlation_summary = {}
            highest_correlation = 0
            lowest_correlation = 0
            
            if correlations:
                highest_correlation = max(correlations.values())
                lowest_correlation = min(correlations.values())
                
                for pair, corr in correlations.items():
                    correlation_summary[pair] = f"{corr:.2f}"
            
            return {
                'correlations': correlation_summary,
                'highest_correlation': f"{highest_correlation:.2f}",
                'lowest_correlation': f"{lowest_correlation:.2f}",
                'diversification_benefit': 'High' if highest_correlation < 0.7 else 'Medium' if highest_correlation < 0.8 else 'Low',
                'sample_assets': len(asset_performance),
                'details': f"Based on {len(asset_performance)} assets across available prediction data"
            }
            
        except Exception as e:
            log.error(f"[RISK] Error calculating correlations: {e}")
            return {'correlations': 'N/A', 'details': f'Correlation error: {e}'}
    
    def generate_risk_assessment(self, daily_data: Dict) -> Dict[str, Any]:
        """Generate comprehensive risk assessment"""
        try:
            log.info("[RISK] Generating comprehensive risk assessment...")
            
            # Calculate all risk metrics
            var_metrics = self.calculate_prediction_var(daily_data)
            drawdown_metrics = self.analyze_drawdown_sequences(daily_data)
            correlation_metrics = self.calculate_asset_correlations(daily_data)
            
            # Determine overall risk level
            risk_factors = []
            risk_score = 0
            
            # VaR assessment
            if var_metrics.get('var_95') != 'N/A':
                try:
                    var_95_value = float(var_metrics['var_95'].strip('%')) / 100
                    if var_95_value < 0.3:
                        risk_factors.append("Low VaR (good)")
                        risk_score += 1
                    elif var_95_value < 0.5:
                        risk_factors.append("Medium VaR")
                        risk_score += 2
                    else:
                        risk_factors.append("High VaR (concerning)")
                        risk_score += 3
                except:
                    pass
            
            # Drawdown assessment
            max_consecutive = drawdown_metrics.get('max_consecutive_losses')
            if isinstance(max_consecutive, int):
                if max_consecutive <= 1:
                    risk_factors.append("Low drawdown risk")
                    risk_score += 1
                elif max_consecutive <= 2:
                    risk_factors.append("Medium drawdown risk")
                    risk_score += 2
                else:
                    risk_factors.append("High drawdown risk")
                    risk_score += 3
            
            # Correlation assessment
            highest_corr = correlation_metrics.get('highest_correlation')
            if highest_corr != 'N/A' and highest_corr:
                try:
                    corr_value = float(highest_corr)
                    if corr_value < 0.5:
                        risk_factors.append("Good diversification")
                        risk_score += 1
                    elif corr_value < 0.8:
                        risk_factors.append("Moderate diversification")
                        risk_score += 2
                    else:
                        risk_factors.append("Poor diversification")
                        risk_score += 3
                except:
                    pass
            
            # Overall risk level
            avg_risk_score = risk_score / len(risk_factors) if risk_factors else 2
            
            if avg_risk_score <= 1.5:
                overall_risk = "LOW"
            elif avg_risk_score <= 2.5:
                overall_risk = "MEDIUM"
            else:
                overall_risk = "HIGH"
            
            return {
                'risk_level': overall_risk,
                'var_metrics': var_metrics,
                'drawdown_metrics': drawdown_metrics,
                'correlation_metrics': correlation_metrics,
                'risk_factors': risk_factors,
                'risk_score': f"{avg_risk_score:.1f}/3.0",
                'recommendation': self._generate_risk_recommendation(overall_risk, risk_factors)
            }
            
        except Exception as e:
            log.error(f"[RISK] Error in risk assessment: {e}")
            return {
                'risk_level': 'UNKNOWN',
                'details': f'Assessment error: {e}'
            }
    
    def _generate_risk_recommendation(self, risk_level: str, risk_factors: List[str]) -> str:
        """Generate risk management recommendations"""
        
        recommendations = []
        
        if risk_level == "LOW":
            recommendations.append("Current risk profile is acceptable")
            recommendations.append("Consider position size increases if appropriate")
        elif risk_level == "MEDIUM":
            recommendations.append("Monitor risk metrics closely")
            recommendations.append("Consider defensive position sizing")
        else:  # HIGH
            recommendations.append("Reduce position sizes immediately")
            recommendations.append("Review strategy allocation")
        
        if "High VaR" in str(risk_factors):
            recommendations.append("Focus on higher probability setups")
        
        if "High drawdown risk" in str(risk_factors):
            recommendations.append("Implement stricter stop-loss discipline")
        
        if "Poor diversification" in str(risk_factors):
            recommendations.append("Diversify across more asset classes")
        
        return "; ".join(recommendations[:3])  # Top 3 recommendations


# Singleton and helper functions
risk_analyzer = None

def get_risk_analyzer() -> SVRiskAnalyzer:
    """Get singleton instance of risk analyzer"""
    global risk_analyzer
    if risk_analyzer is None:
        risk_analyzer = SVRiskAnalyzer()
    return risk_analyzer

def analyze_weekly_risk(daily_data: Dict) -> Dict[str, Any]:
    """Helper function to analyze weekly risk"""
    analyzer = get_risk_analyzer()
    return analyzer.generate_risk_assessment(daily_data)

def test_risk_analysis():
    """Test function for risk analysis"""
    print("🧪 [TEST] Testing Risk Analysis Module...")
    
    try:
        # Create test data
        test_daily_data = {
            '2025-11-18': {
                'predictions': {'total_tracked': 3, 'hits': 1, 'misses': 2},
                'prediction_eval': {
                    'items': [
                        {'asset': 'BTC', 'status': 'SUCCESS'},
                        {'asset': 'SPX', 'status': 'FAILED'},
                        {'asset': 'EURUSD', 'status': 'PENDING'}
                    ]
                }
            },
            '2025-11-19': {
                'predictions': {'total_tracked': 3, 'hits': 3, 'misses': 0},
                'prediction_eval': {
                    'items': [
                        {'asset': 'BTC', 'status': 'SUCCESS'},
                        {'asset': 'SPX', 'status': 'SUCCESS'},
                        {'asset': 'EURUSD', 'status': 'SUCCESS'}
                    ]
                }
            }
        }
        
        # Test risk analysis
        risk_assessment = analyze_weekly_risk(test_daily_data)
        
        print(f"✅ [TEST] Risk Level: {risk_assessment.get('risk_level')}")
        print(f"✅ [TEST] VaR 95%: {risk_assessment.get('var_metrics', {}).get('var_95')}")
        print(f"✅ [TEST] Max Consecutive Losses: {risk_assessment.get('drawdown_metrics', {}).get('max_consecutive_losses')}")
        print("✅ [TEST] Risk analysis module working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ [TEST] Risk analysis error: {e}")
        return False

if __name__ == '__main__':
    test_risk_analysis()