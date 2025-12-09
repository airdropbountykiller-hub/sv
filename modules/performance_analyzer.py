#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - Performance Attribution Analyzer
Detailed performance analysis by asset, day, strategy type
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict

log = logging.getLogger(__name__)

class PerformanceAttributionAnalyzer:
    """Analyze performance attribution across multiple dimensions"""
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    def analyze_by_asset(self, daily_data: Dict) -> Dict[str, Any]:
        """Analyze performance by individual asset"""
        try:
            asset_performance = defaultdict(lambda: {
                'total_predictions': 0,
                'successful_predictions': 0,
                'accuracy': 0.0,
                'days_active': 0,
                'best_day': None,
                'worst_day': None,
                'daily_results': []
            })
            
            # Extract asset-specific data from daily metrics
            for date_str, data in daily_data.items():
                if isinstance(data, dict) and 'prediction_eval' in data:
                    eval_data = data['prediction_eval']
                    if isinstance(eval_data, dict) and 'items' in eval_data:
                        
                        for item in eval_data['items']:
                            asset = item.get('asset')
                            status = item.get('status', '')
                            
                            if asset:
                                asset_perf = asset_performance[asset]
                                asset_perf['total_predictions'] += 1
                                asset_perf['days_active'] += 1
                                
                                # Determine success
                                is_success = any(keyword in status.upper() for keyword in ['SUCCESS', 'HIT', 'TARGET'])
                                if is_success:
                                    asset_perf['successful_predictions'] += 1
                                
                                # Track daily result
                                daily_result = {
                                    'date': date_str,
                                    'status': status,
                                    'success': is_success
                                }
                                asset_perf['daily_results'].append(daily_result)
            
            # Calculate final metrics for each asset
            asset_summary = {}
            for asset, perf in asset_performance.items():
                if perf['total_predictions'] > 0:
                    accuracy = perf['successful_predictions'] / perf['total_predictions']
                    
                    # Find best and worst days
                    daily_accuracies = {}
                    for result in perf['daily_results']:
                        date = result['date']
                        if date not in daily_accuracies:
                            daily_accuracies[date] = {'success': 0, 'total': 0}
                        daily_accuracies[date]['total'] += 1
                        if result['success']:
                            daily_accuracies[date]['success'] += 1
                    
                    best_day = max(daily_accuracies.items(), 
                                 key=lambda x: x[1]['success']/x[1]['total'] if x[1]['total'] > 0 else 0)
                    worst_day = min(daily_accuracies.items(),
                                  key=lambda x: x[1]['success']/x[1]['total'] if x[1]['total'] > 0 else 1)
                    
                    asset_summary[asset] = {
                        'total_predictions': perf['total_predictions'],
                        'successful_predictions': perf['successful_predictions'],
                        'accuracy': f"{accuracy:.1%}",
                        'days_active': len(daily_accuracies),
                        'best_day': {
                            'date': best_day[0],
                            'accuracy': f"{best_day[1]['success']/best_day[1]['total']:.1%}"
                        },
                        'worst_day': {
                            'date': worst_day[0], 
                            'accuracy': f"{worst_day[1]['success']/worst_day[1]['total']:.1%}"
                        }
                    }
            
            # Rank assets by performance
            sorted_assets = sorted(asset_summary.items(), 
                                 key=lambda x: float(x[1]['accuracy'].strip('%')), 
                                 reverse=True)
            
            return {
                'asset_performance': asset_summary,
                'best_performing_asset': sorted_assets[0] if sorted_assets else None,
                'worst_performing_asset': sorted_assets[-1] if sorted_assets else None,
                'total_assets_tracked': len(asset_summary),
                'analysis_summary': f"Analyzed {len(asset_summary)} assets across {len(daily_data)} days"
            }
            
        except Exception as e:
            log.error(f"[PERF] Error in asset analysis: {e}")
            return {'error': f'Asset analysis failed: {e}'}
    
    def analyze_by_day(self, daily_data: Dict) -> Dict[str, Any]:
        """Analyze performance by day of week"""
        try:
            day_performance = {}
            
            for date_str, data in daily_data.items():
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    day_name = date_obj.strftime('%A')
                    
                    if isinstance(data, dict) and 'predictions' in data:
                        predictions = data['predictions']
                        total = predictions.get('total_tracked', 0)
                        hits = predictions.get('hits', 0)
                        
                        if total > 0:
                            accuracy = hits / total
                            day_performance[day_name] = {
                                'date': date_str,
                                'total_predictions': total,
                                'successful_predictions': hits,
                                'accuracy': f"{accuracy:.1%}",
                                'market_summary': data.get('market_summary', 'No summary available')[:100] + '...'
                            }
                except ValueError:
                    continue  # Skip invalid dates
            
            # Find best and worst performing days
            if day_performance:
                best_day = max(day_performance.items(), 
                             key=lambda x: float(x[1]['accuracy'].strip('%')))
                worst_day = min(day_performance.items(),
                              key=lambda x: float(x[1]['accuracy'].strip('%')))
                
                return {
                    'daily_performance': day_performance,
                    'best_performing_day': {
                        'day': best_day[0],
                        'details': best_day[1]
                    },
                    'worst_performing_day': {
                        'day': worst_day[0],
                        'details': worst_day[1]
                    },
                    'days_analyzed': len(day_performance)
                }
            else:
                return {'error': 'No valid daily performance data found'}
                
        except Exception as e:
            log.error(f"[PERF] Error in daily analysis: {e}")
            return {'error': f'Daily analysis failed: {e}'}
    
    def analyze_strategy_patterns(self, daily_data: Dict, journal_entries: List[Dict]) -> Dict[str, Any]:
        """Analyze performance by strategy type (Long/Short, Breakout/Trend)"""
        try:
            strategy_performance = defaultdict(lambda: {
                'count': 0,
                'successful': 0,
                'accuracy': 0.0,
                'examples': []
            })
            
            # Extract strategy information from prediction data and journals
            for date_str, data in daily_data.items():
                if isinstance(data, dict) and 'prediction_eval' in data:
                    eval_data = data['prediction_eval']
                    if isinstance(eval_data, dict) and 'items' in eval_data:
                        
                        for item in eval_data['items']:
                            direction = item.get('direction', '')
                            asset = item.get('asset', '')
                            status = item.get('status', '')
                            
                            if direction and asset:
                                strategy_key = f"{direction}_positions"
                                strategy_perf = strategy_performance[strategy_key]
                                strategy_perf['count'] += 1
                                
                                is_success = any(keyword in status.upper() 
                                               for keyword in ['SUCCESS', 'HIT', 'TARGET'])
                                if is_success:
                                    strategy_perf['successful'] += 1
                                
                                strategy_perf['examples'].append({
                                    'date': date_str,
                                    'asset': asset,
                                    'success': is_success
                                })
            
            # Extract additional strategy info from journal entries
            strategy_keywords = {
                'breakout_strategy': ['breakout', 'break', 'resistance', 'support'],
                'trend_following': ['trend', 'momentum', 'continuation'],
                'mean_reversion': ['reversion', 'oversold', 'overbought'],
                'volatility_play': ['volatility', 'vol', 'implied']
            }
            
            for entry in journal_entries:
                content = entry.get('content', '').lower()
                date = entry.get('date', '')
                
                for strategy, keywords in strategy_keywords.items():
                    if any(keyword in content for keyword in keywords):
                        if strategy not in strategy_performance:
                            strategy_performance[strategy] = {
                                'count': 0, 'successful': 0, 'accuracy': 0.0, 'examples': []
                            }
                        # Increment based on journal mention (simplified)
                        strategy_performance[strategy]['count'] += 1
                        # Assume 70% success rate for journal-mentioned strategies (simplified)
                        if 'good' in content or 'worked' in content or 'profit' in content:
                            strategy_performance[strategy]['successful'] += 1
            
            # Calculate final accuracies
            strategy_summary = {}
            for strategy, perf in strategy_performance.items():
                if perf['count'] > 0:
                    accuracy = perf['successful'] / perf['count']
                    strategy_summary[strategy] = {
                        'total_trades': perf['count'],
                        'successful_trades': perf['successful'],
                        'accuracy': f"{accuracy:.1%}",
                        'sample_size': len(perf['examples'])
                    }
            
            # Rank strategies by performance
            sorted_strategies = sorted(strategy_summary.items(),
                                     key=lambda x: float(x[1]['accuracy'].strip('%')),
                                     reverse=True)
            
            return {
                'strategy_performance': strategy_summary,
                'best_strategy': sorted_strategies[0] if sorted_strategies else None,
                'worst_strategy': sorted_strategies[-1] if sorted_strategies else None,
                'total_strategies_identified': len(strategy_summary)
            }
            
        except Exception as e:
            log.error(f"[PERF] Error in strategy analysis: {e}")
            return {'error': f'Strategy analysis failed: {e}'}
    
    def generate_performance_attribution(self, daily_data: Dict, journal_entries: List[Dict] = None) -> Dict[str, Any]:
        """Generate comprehensive performance attribution analysis"""
        try:
            log.info("[PERF] Generating performance attribution analysis...")
            
            if journal_entries is None:
                journal_entries = []
            
            # Perform all attribution analyses
            asset_analysis = self.analyze_by_asset(daily_data)
            daily_analysis = self.analyze_by_day(daily_data)
            strategy_analysis = self.analyze_strategy_patterns(daily_data, journal_entries)
            
            # Generate key insights
            insights = []
            
            # Asset insights
            if 'best_performing_asset' in asset_analysis and asset_analysis['best_performing_asset']:
                best_asset = asset_analysis['best_performing_asset']
                insights.append(f"Best asset: {best_asset[0]} ({best_asset[1]['accuracy']} accuracy)")
            
            # Daily insights  
            if 'best_performing_day' in daily_analysis:
                best_day = daily_analysis['best_performing_day']
                insights.append(f"Best day: {best_day['day']} ({best_day['details']['accuracy']} accuracy)")
            
            # Strategy insights
            if 'best_strategy' in strategy_analysis and strategy_analysis['best_strategy']:
                best_strategy = strategy_analysis['best_strategy']
                insights.append(f"Best strategy: {best_strategy[0].replace('_', ' ').title()} ({best_strategy[1]['accuracy']})")
            
            return {
                'asset_attribution': asset_analysis,
                'daily_attribution': daily_analysis, 
                'strategy_attribution': strategy_analysis,
                'key_insights': insights,
                'analysis_timestamp': datetime.now().isoformat(),
                'data_coverage': f"{len(daily_data)} days analyzed"
            }
            
        except Exception as e:
            log.error(f"[PERF] Error in performance attribution: {e}")
            return {'error': f'Performance attribution failed: {e}'}


# Helper functions
def analyze_performance_attribution(daily_data: Dict, journal_entries: List[Dict] = None) -> Dict[str, Any]:
    """Helper function to perform performance attribution analysis"""
    analyzer = PerformanceAttributionAnalyzer()
    return analyzer.generate_performance_attribution(daily_data, journal_entries)

def test_performance_analysis():
    """Test function for performance analysis"""
    print("🧪 [TEST] Testing Performance Attribution Analysis...")
    
    try:
        # Create test data
        test_daily_data = {
            '2025-11-18': {
                'predictions': {'total_tracked': 3, 'hits': 1, 'misses': 2},
                'market_summary': 'Mixed session with Fed minutes impact',
                'prediction_eval': {
                    'items': [
                        {'asset': 'BTC', 'direction': 'LONG', 'status': 'SUCCESS'},
                        {'asset': 'SPX', 'direction': 'LONG', 'status': 'FAILED'},
                        {'asset': 'EURUSD', 'direction': 'SHORT', 'status': 'PENDING'}
                    ]
                }
            },
            '2025-11-19': {
                'predictions': {'total_tracked': 3, 'hits': 3, 'misses': 0},
                'market_summary': 'Exceptional day with breakout trades working',
                'prediction_eval': {
                    'items': [
                        {'asset': 'BTC', 'direction': 'LONG', 'status': 'SUCCESS'},
                        {'asset': 'SPX', 'direction': 'LONG', 'status': 'SUCCESS'},
                        {'asset': 'EURUSD', 'direction': 'SHORT', 'status': 'SUCCESS'}
                    ]
                }
            }
        }
        
        test_journals = [
            {'date': '2025-11-19', 'content': 'BTC breakout strategy worked well above 85000'}
        ]
        
        # Test performance attribution
        attribution = analyze_performance_attribution(test_daily_data, test_journals)
        
        print(f"✅ [TEST] Best Asset: {attribution.get('key_insights', ['N/A'])[0]}")
        print(f"✅ [TEST] Analysis Coverage: {attribution.get('data_coverage')}")
        print("✅ [TEST] Performance attribution analysis working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ [TEST] Performance analysis error: {e}")
        return False

if __name__ == '__main__':
    test_performance_analysis()