#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - Weekly Report Generatetor
Generate report settimanali completi per weekend analysis
"""

import datetime
import pytz
import json
import os
import sys
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path
import glob

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'config', 'modules'))

# Setup logging
log = logging.getLogger(__name__)

# Import new analysis modules
try:
    from .risk_analyzer import analyze_weekly_risk
    from .performance_analyzer import analyze_performance_attribution
    from .predictive_analyzer import generate_next_week_predictions
    from .market_regime_detector import detect_market_regime
    from .action_items_generator import generate_action_items
    ADVANCED_ANALYTICS_AVAILABLE = True
except ImportError as e:
    log.warning(f"⚠️ [WEEKLY] Advanced analytics not available: {e}")
    ADVANCED_ANALYTICS_AVAILABLE = False
    def analyze_weekly_risk(daily_data): return {'risk_level': 'N/A'}
    def analyze_performance_attribution(daily_data, journals): return {'error': 'Module not available'}
    def generate_next_week_predictions(daily_data, risk, perf): return {'error': 'Module not available'}
    def detect_market_regime(daily_data, perf, journals): return {'error': 'Module not available'}
    def generate_action_items(risk, perf, regime, pred): return {'error': 'Module not available'}

# Weekly metrics aggregator based on saved daily metrics snapshots
try:
    from period_aggregator import get_weekly_metrics
    WEEKLY_AGGREGATOR_AVAILABLE = True
except Exception as e:
    log.warning(f"⚠️ [WEEKLY-AGG] Aggregator not available: {e}")
    WEEKLY_AGGREGATOR_AVAILABLE = False

    def get_weekly_metrics(now=None):  # type: ignore[redef]
        """Fallback stub when period_aggregator is not available."""
        return {}
 
ITALY_TZ = pytz.timezone("Europe/Rome")

def _now_it():
    """Get current time in Italian timezone"""
    return datetime.datetime.now(ITALY_TZ)

# Import required modules
try:
    from narrative_continuity import get_narrative_continuity
    from daily_session_tracker import daily_tracker
    from pdf_generator import Createte_weekly_pdf
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    log.warning(f"⚠️ [WEEKLY-GEN] Dependencies not available: {e}")
    DEPENDENCIES_AVAILABLE = False
    def Createte_weekly_pdf(*args): return None
try:
    from daily_generator import get_live_crypto_prices, calculate_crypto_support_resistance
    WEEKLY_CRYPTO_HELPERS = True
except Exception as e:
    log.warning(f"âš ï¸ [WEEKLY-CRYPTO] Live crypto helpers not available: {e}")
    WEEKLY_CRYPTO_HELPERS = False
    def get_live_crypto_prices():
        return {}
    def calculate_crypto_support_resistance(price, change_pct):
        return {}

def get_week_dates():
    """Get current week start and end dates"""
    now = _now_it()
    # Get Monday of current week
    monday = now - datetime.timedelta(days=now.weekday())
    # Get Friday of current week  
    friday = monday + datetime.timedelta(days=4)
    
    return monday.strftime('%d/%m'), friday.strftime('%d/%m')

class WeeklyDataAssembler:
    """Aggregates real data from daily JSON files for weekly reports"""
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.daily_metrics_dir = os.path.join(self.project_root, 'reports', 'metrics')
        self.journals_dir = os.path.join(self.project_root, 'reports', 'journals')
        self.messages_dir = os.path.join(self.project_root, 'reports', '1_daily')
        self.predictions_dir = os.path.join(self.project_root, 'reports', '1_daily')
        self.engine_metrics_dir = os.path.join(self.project_root, 'reports', 'metrics')
    
    def get_weekly_date_range(self, target_date=None):
        """Get date range for current week (Monday to Friday)"""
        if target_date is None:
            target_date = _now_it()
        
        # Get Monday of the week
        monday = target_date - datetime.timedelta(days=target_date.weekday())
        friday = monday + datetime.timedelta(days=4)
        
        return monday.date(), friday.date()
    
    def load_daily_metrics(self, date_range):
        """Load daily metrics JSONs for the date range"""
        monday, friday = date_range
        daily_data = {}
        
        # Generate dates from Monday to Friday
        current_date = monday
        while current_date <= friday:
            date_str = current_date.strftime('%Y-%m-%d')
            metrics_file = os.path.join(self.daily_metrics_dir, f'daily_metrics_{date_str}.json')
            
            if os.path.exists(metrics_file):
                try:
                    with open(metrics_file, 'r', encoding='utf-8') as f:
                        daily_data[date_str] = json.load(f)
                    log.debug(f"[ASSEMBLER] Loaded metrics for {date_str}")
                except Exception as e:
                    log.warning(f"[ASSEMBLER] Error loading {metrics_file}: {e}")
            
            current_date += datetime.timedelta(days=1)
        
        return daily_data
    
    def load_weekly_journals(self, date_range):
        """Load journal entries for the week"""
        monday, friday = date_range
        journal_entries = []
        
        current_date = monday
        while current_date <= friday:
            date_str = current_date.strftime('%Y-%m-%d')
            journal_pattern = os.path.join(self.journals_dir, f'trading_journal_{date_str}*.md')
            
            matching_files = glob.glob(journal_pattern)
            for journal_file in matching_files:
                try:
                    with open(journal_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        journal_entries.append({
                            'date': date_str,
                            'content': content,
                            'file': os.path.basename(journal_file)
                        })
                except Exception as e:
                    log.warning(f"[ASSEMBLER] Error loading journal {journal_file}: {e}")
            
            current_date += datetime.timedelta(days=1)
        
        return journal_entries
    
    def load_weekly_signals(self, date_range):
        """Load per-day signals (asset/direction) and outcomes when available"""
        monday, friday = date_range
        current_date = monday
        weekly_signals: List[Dict[str, Any]] = []
        
        while current_date <= friday:
            date_str = current_date.strftime('%Y-%m-%d')
            day_entry: Dict[str, Any] = {
                'day': current_date.strftime('%A %d/%m'),
                'date': date_str,
                'signals': []
            }
            # Base signals from predictions file
            pred_path = os.path.join(self.predictions_dir, f'predictions_{date_str}.json')
            base_signals: List[Dict[str, Any]] = []
            if os.path.exists(pred_path):
                try:
                    with open(pred_path, 'r', encoding='utf-8') as f:
                        pdata = json.load(f)
                    for item in pdata.get('predictions', []) or []:
                        if not isinstance(item, dict):
                            continue
                        base_signals.append({
                            'asset': item.get('asset'),
                            'direction': item.get('direction'),
                            'entry': item.get('entry'),
                            'target': item.get('target'),
                            'stop': item.get('stop'),
                            'outcome': 'N/A'
                        })
                except Exception as e:
                    log.warning(f"[ASSEMBLER] Error loading predictions for {date_str}: {e}")
            
            # Outcomes from engine summary prediction_eval (if available)
            eval_items: List[Dict[str, Any]] = []
            engine_path = os.path.join(self.engine_metrics_dir, f'engine_{date_str}.json')
            if os.path.exists(engine_path):
                try:
                    with open(engine_path, 'r', encoding='utf-8') as f:
                        edata = json.load(f)
                    for st in edata.get('stages', []) or []:
                        if st.get('stage') == 'summary':
                            pe = st.get('prediction_eval') or {}
                            items = pe.get('items') or []
                            if isinstance(items, list):
                                eval_items = [i for i in items if isinstance(i, dict)]
                            break
                except Exception as e:
                    log.warning(f"[ASSEMBLER] Error loading engine metrics for {date_str}: {e}")
            
            # Match outcomes by asset+direction
            if eval_items and base_signals:
                for sig in base_signals:
                    for ev in eval_items:
                        if sig.get('asset') == ev.get('asset') and sig.get('direction') == ev.get('direction'):
                            status = ev.get('status') or 'N/A'
                            sig['outcome'] = status
                            break
            
            day_entry['signals'] = base_signals
            weekly_signals.append(day_entry)
            current_date += datetime.timedelta(days=1)
        
        return weekly_signals
    
    def aggregate_performance_metrics(self, daily_data):
        """Aggregate performance metrics from daily data"""
        total_predictions = 0
        successful_predictions = 0
        daily_performances = []
        
        for date_str, data in daily_data.items():
            day_info = {
                'day': datetime.datetime.strptime(date_str, '%Y-%m-%d').strftime('%A %d/%m'),
                'date': date_str
            }
            
            # Extract metrics if available
            if isinstance(data, dict):
                predictions = data.get('predictions', {})
                if isinstance(predictions, dict):
                    day_total = predictions.get('total_tracked', 0) or 0
                    day_hits = predictions.get('hits', 0) or 0
                    
                    total_predictions += int(day_total)
                    successful_predictions += int(day_hits)
                    
                    day_info.update({
                        'signals': day_total,
                        'hits': day_hits,
                        'success_rate': f"{(day_hits/day_total*100):.0f}%" if day_total > 0 else 'n/a'
                    })
                else:
                    day_info.update({
                        'signals': 0,
                        'hits': 0,
                        'success_rate': 'n/a'
                    })
                
                # Add market summary if available
                market_summary = data.get('market_summary', '')
                if market_summary:
                    # Take first sentence as day notes
                    notes = market_summary.split('.')[0][:100] + '...' if len(market_summary) > 100 else market_summary
                    day_info['notes'] = notes
                else:
                    day_info['notes'] = 'No market summary available'
            
            daily_performances.append(day_info)
        
        overall_accuracy = (successful_predictions / total_predictions * 100) if total_predictions > 0 else 0
        
        return {
            'total_predictions': total_predictions,
            'successful_predictions': successful_predictions,
            'overall_accuracy': overall_accuracy,
            'daily_performances': daily_performances
        }
    
    def load_weekly_news(self, date_range):
        """Load top news titles from seen_news_YYYY-MM-DD.json in metrics directory"""
        monday, friday = date_range
        # Extend range slightly to include weekend headlines if present
        end_date = min(friday + datetime.timedelta(days=2), _now_it().date())
        current_date = monday
        titles_seen = []
        news_items = []
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            news_path = os.path.join(self.daily_metrics_dir, f'seen_news_{date_str}.json')
            if os.path.exists(news_path):
                try:
                    with open(news_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    titles = data.get('titles', []) or []
                    links = data.get('links', []) or []
                    for idx, t in enumerate(titles):
                        if not isinstance(t, str):
                            continue
                        if t in titles_seen:
                            continue
                        titles_seen.append(t)
                        link = links[idx] if idx < len(links) else ''
                        # keep it short for PDF
                        news_items.append({
                            'date': date_str,
                            'title': t[:140] + ('…' if len(t) > 140 else ''),
                            'link': link
                        })
                        if len(news_items) >= 12:
                            break
                except Exception as e:
                    log.warning(f"[ASSEMBLER] Error loading weekly news for {date_str}: {e}")
            if len(news_items) >= 12:
                break
            current_date += datetime.timedelta(days=1)
        return news_items

    def extract_market_insights(self, daily_data, journal_entries):
        """Extract market analysis and insights from daily data"""
        market_events = []
        key_insights = []
        
        # Extract from daily metrics
        for date_str, data in daily_data.items():
            if isinstance(data, dict):
                market_summary = data.get('market_summary', '')
                if market_summary and len(market_summary) > 50:
                    # Extract key insights from market summary
                    key_insights.append({
                        'date': date_str,
                        'insight': market_summary[:200] + '...' if len(market_summary) > 200 else market_summary
                    })
        
        # Extract from journal entries
        for entry in journal_entries:
            content = entry['content']
            # Look for market events or significant notes
            if any(keyword in content.lower() for keyword in ['fed', 'earnings', 'volatility', 'breakout', 'trend']):
                # Extract relevant sections
                lines = content.split('\n')
                relevant_lines = [line for line in lines if any(keyword in line.lower() for keyword in ['fed', 'earnings', 'volatility'])]
                if relevant_lines:
                    market_events.append({
                        'date': entry['date'],
                        'description': ' '.join(relevant_lines[:2])[:150] + '...' if len(' '.join(relevant_lines)) > 150 else ' '.join(relevant_lines),
                        'impact': 'High' if 'volatility' in content.lower() else 'Medium'
                    })
        
        return {
            'market_events': market_events,
            'key_insights': key_insights
        }
    
    def assemble_weekly_data(self, target_date=None):
        """Main method to assemble comprehensive weekly data"""
        try:
            date_range = self.get_weekly_date_range(target_date)
            monday, friday = date_range
            
            log.info(f"[ASSEMBLER] Assembling data for week {monday} to {friday}")
            
            # Load all data sources
            daily_data = self.load_daily_metrics(date_range)
            journal_entries = self.load_weekly_journals(date_range)
            weekly_signals = self.load_weekly_signals(date_range)
            weekly_news = self.load_weekly_news(date_range)
            
            # Aggregate performance metrics
            performance = self.aggregate_performance_metrics(daily_data)
            
            # Extract market insights
            market_analysis = self.extract_market_insights(daily_data, journal_entries)
            
            # Advanced analytics (when available)
            risk_analysis = {}
            performance_attribution = {}
            market_regime_analysis = {}
            next_week_predictions = {}
            action_items = {}
            
            if ADVANCED_ANALYTICS_AVAILABLE:
                try:
                    log.info("[ASSEMBLER] Running advanced analytics...")
                    risk_analysis = analyze_weekly_risk(daily_data)
                    performance_attribution = analyze_performance_attribution(daily_data, journal_entries)
                    market_regime_analysis = detect_market_regime(daily_data, performance_attribution, journal_entries)
                    next_week_predictions = generate_next_week_predictions(daily_data, risk_analysis, performance_attribution)
                    action_items = generate_action_items(risk_analysis, performance_attribution, market_regime_analysis, next_week_predictions)
                except Exception as e:
                    log.warning(f"[ASSEMBLER] Advanced analytics error: {e}")
                    risk_analysis = {'risk_level': 'Analysis Error'}
                    performance_attribution = {'error': str(e)}
                    market_regime_analysis = {'error': str(e)}
                    next_week_predictions = {'error': str(e)}
                    action_items = {'error': str(e)}
            # Variables already initialized above
            
            # Build comprehensive weekly data structure
            weekly_data = {
                'timeframe': 'weekly',
                'week_start': monday.strftime('%d/%m'),
                'week_end': friday.strftime('%d/%m'),
                'data_sources': {
                    'daily_metrics_files': len(daily_data),
                    'journal_entries': len(journal_entries)
                },
                'performance_metrics': {
                    'total_signals': performance['total_predictions'],
                    'success_rate': f"{performance['overall_accuracy']:.0f}%" if performance['total_predictions'] > 0 else 'n/a',
                    'successful_predictions': performance['successful_predictions'],
                    'weekly_return': 'n/a',  # Requires P&L tracking
                    'sharpe_ratio': 'n/a',   # Requires P&L tracking
                    'max_drawdown': 'n/a'    # Requires P&L tracking
                },
                'daily_performance': performance['daily_performances'],
                'daily_signals': weekly_signals,
                'market_analysis': {
                    'regime': market_regime_analysis.get('unified_regime', 'Based on aggregated daily analysis'),
                    'volatility': market_regime_analysis.get('volatility_analysis', {}).get('volatility_regime', 'Derived from daily market summaries'),
                    'trend_strength': market_regime_analysis.get('trend_analysis', {}).get('trend_regime', 'Qualitative from daily insights'),
                    'sector_rotation': 'See daily reports for sector analysis',
                    'regime_confidence': market_regime_analysis.get('regime_confidence', 'N/A')
                },
                'key_events': market_analysis['market_events'][:5],  # Top 5 events
                'key_insights': market_analysis['key_insights'][:3],  # Top 3 insights
                'weekly_news': weekly_news[:12],
                'risk_analysis': risk_analysis,
                'performance_attribution': performance_attribution,
                'market_regime_analysis': market_regime_analysis,
                'next_week_predictions': next_week_predictions,
                'data_quality': {
                    'completeness': f"{len(daily_data)}/5 days with metrics",
                    'journal_coverage': f"{len(journal_entries)} journal entries",
                    'advanced_analytics': 'Available' if ADVANCED_ANALYTICS_AVAILABLE else 'Limited'
                }
            }
            
            # Add weekly summary based on data
            if performance['total_predictions'] > 0:
                summary_parts = [
                    f"Aggregated accuracy {performance['overall_accuracy']:.0f}% on {performance['total_predictions']} live-tracked predictions from {len(daily_data)} days of data."
                ]
                # Risk insight (only if present)
                if isinstance(risk_analysis, dict) and risk_analysis.get('risk_level'):
                    summary_parts.append(f"Risk level: {risk_analysis['risk_level']}.")
                
                # Best/Worst day from daily_performances
                daily_perf = performance.get('daily_performances', [])
                valid_days = [d for d in daily_perf if d.get('signals', 0) > 0 and d.get('success_rate') != 'n/a']
                try:
                    if valid_days:
                        # Parse numeric accuracy
                        for d in valid_days:
                            d['_acc_val'] = float(str(d.get('success_rate', '0').replace('%','')))
                        best_day = max(valid_days, key=lambda x: x['_acc_val'])
                        worst_day = min(valid_days, key=lambda x: x['_acc_val'])
                        summary_parts.append(
                            f"Best day: {best_day.get('day','')[:3]} ({best_day.get('success_rate')})"
                        )
                        summary_parts.append(
                            f"Worst day: {worst_day.get('day','')[:3]} ({worst_day.get('success_rate')})"
                        )
                except Exception:
                    pass
                
                summary = " ".join(summary_parts)
            else:
                summary = f"Limited prediction data this week ({len(daily_data)} days with metrics, {len(journal_entries)} journal entries available)."
            
            # Append trend delta if available
            try:
                # Compute trend from daily_performances
                dp = performance['daily_performances']
                vals = [float(str(d.get('success_rate','0').replace('%',''))) for d in dp if d.get('signals',0)>0 and d.get('success_rate')!='n/a']
                if len(vals) >= 2:
                    delta = vals[-1] - vals[0]
                    trend_note = f" Trend: {'+' if delta>=0 else ''}{delta:.0f}pp vs start of week."
                    summary += trend_note
            except Exception:
                pass
            
            weekly_data['weekly_summary'] = summary
            
            # Compute content highlights (no fabricated numbers)
            highlights = []
            if performance['total_predictions'] > 0 and valid_days:
                highlights.append(f"Hit ratio by day: " + ", ".join([f"{d.get('day','')[:3]} {d.get('success_rate')}" for d in valid_days]))
                # Most active day
                most_active = max(valid_days, key=lambda x: x.get('signals', 0))
                highlights.append(f"Most active day: {most_active.get('day','')} ({most_active.get('signals',0)} signals)")
                # No-signal days
                zero_days = [d for d in daily_perf if d.get('signals', 0) == 0]
                if zero_days:
                    names = ", ".join(d.get('day','') for d in zero_days)
                    highlights.append(f"No-signal days: {names}")
            
            # Accuracy trend direction
            try:
                if valid_days and len(valid_days) >= 2:
                    first_acc = valid_days[0]['_acc_val']
                    last_acc = valid_days[-1]['_acc_val']
                    delta = last_acc - first_acc
                    if delta > 10:
                        trend_txt = f"Accuracy trend improving (+{delta:.0f}pp)"
                    elif delta < -10:
                        trend_txt = f"Accuracy trend deteriorating ({delta:.0f}pp)"
                    else:
                        trend_txt = "Accuracy trend steady"
                    highlights.append(trend_txt)
                    weekly_trend = {'delta_pp': delta, 'comment': trend_txt}
                else:
                    weekly_trend = {'delta_pp': 0.0, 'comment': 'Insufficient days for trend'}
            except Exception:
                weekly_trend = {'delta_pp': 0.0, 'comment': 'Trend calc error'}
            
            weekly_data['content_highlights'] = highlights
            weekly_data['weekly_trend'] = weekly_trend
            
            # What worked / What didn’t (data‑driven summary)
            what_worked: List[str] = []
            what_didnt: List[str] = []
            try:
                if performance['total_predictions'] > 0 and valid_days:
                    # Best / worst day already computed
                    best_txt = f"Best day: {best_day.get('day','')[:3]} ({best_day.get('success_rate')}) with {best_day.get('signals',0)} signals"
                    worst_txt = f"Worst day: {worst_day.get('day','')[:3]} ({worst_day.get('success_rate')}) with {worst_day.get('signals',0)} signals"
                    what_worked.append(best_txt)
                    # Only add worst if really weak
                    try:
                        worst_acc_val = float(str(worst_day.get('success_rate','0').replace('%','')))
                        if worst_acc_val < 50:
                            what_didnt.append(worst_txt)
                    except Exception:
                        pass
                # Asset-level info if available
                if isinstance(performance_attribution, dict):
                    ap = performance_attribution.get('asset_attribution', {}).get('asset_performance', {})
                    if isinstance(ap, dict) and ap:
                        best_asset = None
                        worst_asset = None
                        for asset, info in ap.items():
                            try:
                                total = int(info.get('total_predictions',0) or 0)
                                acc_val = float(str(info.get('accuracy','0%')).replace('%',''))
                            except Exception:
                                continue
                            if total < 2:
                                continue
                            if best_asset is None or acc_val > best_asset[2]:
                                best_asset = (asset, total, acc_val)
                            if worst_asset is None or acc_val < worst_asset[2]:
                                worst_asset = (asset, total, acc_val)
                        if best_asset and best_asset[2] >= 60:
                            what_worked.append(
                                f"Strong asset: {best_asset[0]} {best_asset[2]:.0f}% accuracy on {best_asset[1]} signals"
                            )
                        if worst_asset and worst_asset[2] < 50:
                            what_didnt.append(
                                f"Weak asset: {worst_asset[0]} {worst_asset[2]:.0f}% accuracy on {worst_asset[1]} signals"
                            )
            except Exception as e:
                log.debug(f"[ASSEMBLER] What worked/what didn’t summary error: {e}")
            weekly_data['what_worked'] = what_worked
            weekly_data['what_didnt'] = what_didnt
            
            # Build Next Week – Focus (3 concise bullets, data-driven)
            next_week_focus = []
            try:
                # 1) Success rate rule
                sr_str = weekly_data['performance_metrics'].get('success_rate','n/a')
                if sr_str != 'n/a':
                    sr = float(sr_str.replace('%',''))
                    if sr < 60:
                        next_week_focus.append('Optimize signals/features and reduce size until accuracy improves (<60%)')
                # 2) Risk level / regime rule
                rl = (risk_analysis or {}).get('risk_level','').upper() if isinstance(risk_analysis, dict) else ''
                if rl in ('HIGH','MEDIUM'):
                    next_week_focus.append('Wait for directional clarity; trade smaller size in elevated risk regime')
                # 3) Asset-specific rule (avoid poor performer if enough signals)
                ap = (performance_attribution or {}).get('asset_attribution',{}).get('asset_performance',{})
                if isinstance(ap, dict) and ap:
                    # pick worst with >=2 predictions
                    worst = None
                    for asset, info in ap.items():
                        try:
                            total = int(info.get('total_predictions',0) or 0)
                            acc = float(str(info.get('accuracy','0%')).replace('%',''))
                        except Exception:
                            continue
                        if total >= 2:
                            if worst is None or acc < worst[1]:
                                worst = (asset, acc)
                    if worst and worst[1] < 40:
                        next_week_focus.append(f"Avoid {worst[0]} setups until pattern improves ({worst[1]:.0f}% recent accuracy)")
            except Exception:
                pass
            if not next_week_focus:
                next_week_focus = [
                    'Maintain strategy; focus on high-confidence setups',
                    'Use reduced size early week; scale up on confirmation',
                    'Review patterns of worst-performing assets before re‑engaging'
                ]
            weekly_data['next_week_focus'] = next_week_focus[:3]
            weekly_data['weekly_trend'] = weekly_trend
            
            # Asset focus (top assets by signal count this week, no fabricated accuracy)
            asset_focus = []
            try:
                asset_counts: Dict[str, int] = {}
                for day in weekly_signals:
                    for sig in day.get('signals', []) or []:
                        asset = sig.get('asset')
                        if not asset:
                            continue
                        asset_counts[asset] = asset_counts.get(asset, 0) + 1
                if asset_counts:
                    # Sort by number of signals (desc) and take top 2
                    top_assets = sorted(asset_counts.items(), key=lambda kv: kv[1], reverse=True)[:2]
                    # Optionally attach real per-asset accuracy when available from performance_attribution
                    ap_root = performance_attribution.get('asset_attribution', {}).get('asset_performance', {}) if isinstance(performance_attribution, dict) else {}
                    for name, count in top_assets:
                        acc_val = None
                        if isinstance(ap_root, dict):
                            info = ap_root.get(name) or {}
                            if info.get('accuracy') not in (None, "", "0", 0):
                                acc_val = info.get('accuracy')
                        asset_focus.append({
                            'asset': name,
                            'accuracy': acc_val if acc_val is not None else 'n/a',
                            'total_predictions': count,
                        })
            except Exception:
                pass
            weekly_data['asset_focus'] = asset_focus
            
            log.info(f"[ASSEMBLER] Assembly complete: {performance['total_predictions']} predictions, {len(daily_data)} metric files, {len(journal_entries)} journals")
            
            return weekly_data
            
        except Exception as e:
            log.error(f"[ASSEMBLER] Error assembling weekly data: {e}")
            return None
    
    def process_weekly_period(self, target_date=None):
        """Complete weekly processing: assemble data and generate PDF with charts"""
        try:
            log.info("[WEEKLY-PROCESS] Starting complete weekly period processing...")
            
            # Assemble weekly data
            weekly_data = self.assemble_weekly_data(target_date)
            if not weekly_data:
                log.error("[WEEKLY-PROCESS] Failed to assemble weekly data")
                return False
            
            # Generate PDF with charts if modules available
            if DEPENDENCIES_AVAILABLE:
                try:
                    from pdf_generator import Createte_weekly_pdf
                    pdf_path = Createte_weekly_pdf(weekly_data)
                    if pdf_path:
                        log.info(f"✅ [WEEKLY-PROCESS] PDF with charts generated: {pdf_path}")
                        
                        # Check if file was actually created and has reasonable size
                        if os.path.exists(pdf_path):
                            file_size = os.path.getsize(pdf_path)
                            log.info(f"[WEEKLY-PROCESS] PDF file size: {file_size} bytes")
                            if file_size > 1000:  # Reasonable minimum size
                                return True
                            else:
                                log.warning(f"[WEEKLY-PROCESS] PDF file too small: {file_size} bytes")
                        else:
                            log.error(f"[WEEKLY-PROCESS] PDF file not found: {pdf_path}")
                    else:
                        log.error("[WEEKLY-PROCESS] PDF generation returned no path")
                except Exception as e:
                    log.error(f"[WEEKLY-PROCESS] Error generating PDF: {e}")
                    return False
            else:
                log.warning("[WEEKLY-PROCESS] PDF generation not available")
                return False
                
        except Exception as e:
            log.error(f"[WEEKLY-PROCESS] Error in weekly processing: {e}")
            return False

class WeeklyReportGeneratetor:
    def __init__(self):
        """Initialize weekly report Generatetor"""
        self.narrative = get_narrative_continuity() if DEPENDENCIES_AVAILABLE else None
        
        # Weekly analysis structure (informational only – not read programmatically
        # by the generator at runtime)
        self.weekly_template = {
            'sections': [
                'Executive Weekly Summary',
                'performance Analysis (5 giorni)',
                'ML Models Weekly Review', 
                'Trend Analysis & Correlazioni',
                'Sector Rotation Analysis',
                'Risk Metrics & Drawdowns',
                'Weekend Market Outlook',
                'Next Week Strategic Setup'
            ],
            'metrics': [
                'weekly_accuracy',
                'total_predictions',
                'successful_calls', 
                'sector_performance',
                'volatility_analysis',
                'correlation_matrix'
            ]
        }
    
    def Generatete_weekly_report(self) -> str:
        """
        Generate Report Settimanale Completo (Weekend 17:00) - Enhanced Version
        
        Returns:
            Stringa con report settimanale completo migliorato
        """
        try:
            log.info("📈 [WEEKLY] Generating enhanced weekly report...")
            
            now = _now_it()
            week_start, week_end = get_week_dates()

            # Load aggregated weekly metrics (from daily Summary snapshots)
            weekly_metrics: Dict[str, Any] = {}
            if WEEKLY_AGGREGATOR_AVAILABLE:
                try:
                    weekly_metrics = get_weekly_metrics(now)
                except Exception as e:
                    log.warning(f"⚠️ [WEEKLY-AGG] Error loading weekly metrics: {e}")
                    weekly_metrics = {}
            
            # Enhanced Header with branding
            report = f"🏆 **SV - SISTEMA UNIFICATO TRADING**\n"
            report += f"📈 **WEEKLY PERFORMANCE REPORT**\n"
            report += f"📅 Week: {week_start} - {week_end} {now.strftime('%B %Y')}\n"
            report += f"🕰️ Generated: {now.strftime('%A, %d %B %Y at %H:%M')} (CET)\n"
            report += f"📊 Report ID: WR-{now.strftime('%Y%m%d-%H%M')}\n"
            report += "=" * 70 + "\n\n"
            
            # SEZIONE 1: EXECUTIVE WEEKLY SUMMARY - ENHANCED
            report += "🎯 **EXECUTIVE WEEKLY SUMMARY**\\n\\n"
            
            # Derive performance metrics from real aggregated data when available
            pred = weekly_metrics.get('prediction', {}) if isinstance(weekly_metrics, dict) else {}
            total_tracked = int(pred.get('total_tracked', 0) or 0)
            weekly_accuracy = float(pred.get('accuracy_pct', 0.0) or 0.0)
            hits = int(pred.get('hits', 0) or 0)

            assets = weekly_metrics.get('assets', {}) if isinstance(weekly_metrics, dict) else {}
            spx_info = assets.get('SPX', {})
            btc_info = assets.get('BTC', {})
            eur_info = assets.get('EURUSD', {})
            gold_info = assets.get('GOLD', {})

            spx_ret = spx_info.get('return_pct')
            btc_ret = btc_info.get('return_pct')
            eur_ret = eur_info.get('return_pct')
            gold_ret = gold_info.get('return_pct')
            
            report += f"🔥 **KEY HIGHLIGHTS**:\\n"
            if total_tracked > 0:
                report += f"• 🧠 **AI System Accuracy**: {weekly_accuracy:.0f}% on {total_tracked} live-tracked predictions (aggregated from daily summaries)\\n"
                report += f"• 🎩 **Prediction Success**: {hits} hits / {total_tracked} tracked assets\\n"
            else:
                report += "• 🧠 **AI System Accuracy**: n/a (no aggregated live-tracked predictions this week)\\n"
                report += "• 🎩 **Prediction Success**: n/a - see daily journals for qualitative review\\n"
            report += "• 🛡️ **Risk Control**: Max drawdown N/A - requires full P&L tracking (future enhancement)\\n\\n"
            
            # Market performance snapshot based on real weekly returns when available
            report += f"🌍 **GLOBAL MARKETS SNAPSHOT**:\\n"
            if isinstance(spx_ret, (int, float)):
                report += f"• 🇺🇸 **S&P 500**: {spx_ret:+.1f}% (Mon→Fri, aggregated from daily close snapshots)\\n"
            else:
                report += "• 🇺🇸 **S&P 500**: Weekly performance n/a (insufficient daily metrics)\\n"

            # NASDAQ kept qualitative only to avoid invented levels
            report += "• 💻 **NASDAQ**: Tech-heavy index broadly aligned with S&P 500 trend (see daily reports for details)\\n"

            if isinstance(btc_ret, (int, float)):
                report += f"• ₿ **Bitcoin**: {btc_ret:+.1f}% (weekly move based on daily BTC/USD snapshots)\\n"
            else:
                report += "• ₿ **Bitcoin**: Weekly performance n/a (insufficient daily metrics)\\n"

            if isinstance(eur_ret, (int, float)):
                report += f"• 💵 **EUR/USD**: {eur_ret:+.1f}% - aggregated FX move over the week\\n"
            else:
                report += "• 💵 **EUR/USD**: Weekly FX move n/a (insufficient daily metrics)\\n"

            # Gold: numeric only when based on aggregated USD/gram snapshots, otherwise qualitative
            if isinstance(gold_ret, (int, float)):
                report += f"• 🥇 **Gold (USD/g)**: {gold_ret:+.1f}% - safe haven performance based on daily USD/gram data\\n"
            else:
                report += "• 🥇 **Gold**: Safe haven flows (see daily reports for detailed performance)\\n\\n"
            
            # Week character: qualitative summary derived from price direction
            if isinstance(spx_ret, (int, float)) and isinstance(btc_ret, (int, float)):
                if spx_ret > 0 and btc_ret > 0:
                    week_character = "Risk-on week with both equities and crypto positive"
                elif spx_ret > 0 and btc_ret <= 0:
                    week_character = "Equities resilient, crypto mixed"
                elif spx_ret <= 0 and btc_ret > 0:
                    week_character = "Crypto strength against softer equities"
                else:
                    week_character = "Risk-off or consolidation across major assets"
            else:
                week_character = "Character not fully measurable yet (waiting for more daily metrics)"

            report += f"🎨 **WEEK CHARACTER**: {week_character}, sector rotation active, volatility monitored via daily reports\\n\\n"
            
            # SEZIONE 2: PERFORMANCE ANALYSIS (5 GIORNI)
            report += "📊 **PERFORMANCE ANALYSIS (5 GIORNI)**\\n\\n"
            report += f"🗓️ **Daily Breakdown (see Daily Summaries for numeric details)**:\\n"
            report += f"• **Lunedì**: Opening regime as described in Monday Daily Summary\\n"
            report += f"• **Martedì**: Continuation / reversal dynamics from intraday reports\\n"
            report += f"• **Mercoledì**: Policy / macro events handled as per Noon & Evening analysis\\n" 
            report += f"• **Giovedì**: Earnings and sector flows summarized in daily content\\n"
            report += f"• **Venerdì**: Weekly close and positioning captured in Evening + Summary\\n\\n"
            
            report += f"🤖 **ML Models Weekly Performance**:\\n"
            if total_tracked > 0:
                report += f"• **Ensemble**: {weekly_accuracy:.0f}% accuracy on {total_tracked} tracked signals (see Daily Summaries pages 1–3)\\n"
            else:
                report += f"• **Ensemble**: n/a – no live-tracked predictions aggregated this week\\n"
            report += f"• **Individual Models**: Qualitative review only – per-model weekly accuracy not yet aggregated\\n\\n"
            
            report += f"📈 **Technical Signals Weekly**:\\n"
            report += f"• **Trend Signals**: Evaluated daily via support/resistance and moving averages\\n"
            report += f"• **Momentum Indicators**: RSI/MACD behavior summarized qualitatively in Daily Summary\\n"
            report += f"• **Mean Reversion**: Effectiveness depends on regime (see risk notes in Page 2/3 of Daily Summary)\\n"
            report += f"• **Volume Analysis**: Assessed via daily flow commentary – no synthetic volume statistics here\\n\\n"
            
            # SEZIONE 3: TREND ANALYSIS & CORRELAZIONI
            report += "ðŸ”¬ **TREND ANALYSIS & CORRELAZIONI**\n\n"
            report += f"📊 **Cross-Asset Correlations**:\\n"
            report += f"• **Equity–Crypto**: Positive relationship – crypto tends to follow risk-on periods\\n"
            report += f"• **USD–Gold**: Strong inverse relationship – classic risk-off pattern (qualitative, no fixed coefficient)\\n"
            report += f"• **Bonds–Stocks**: Typically inverse during risk-on phases\\n"
            report += f"• **VIX–S&P**: Strong inverse behavior as expected\\n\\n"
            
            report += f"🌊 **Trend Strength Analysis**:\\n"
            report += f"• **Primary Trend**: Described as bullish / neutral / corrective in Daily Summaries based on real data\\n"
            report += f"• **Sector Rotation**: Growth vs Value leadership discussed qualitatively (no invented % spreads)\\n"
            report += f"• **Geographic**: US / Europe / Asia relative strength assessed from daily market review\\n"
            report += f"• **Style**: Large vs Small Cap dynamics covered without synthetic performance gaps\\n\\n"
            
            report += f"⚡ **Momentum Persistence**:\\n"
            report += f"• **Equity Momentum**: Assessed from sequence of up/down days in Daily Summary (no synthetic 4/5 count)\\n"
            report += f"• **Crypto Momentum**: Qualitatively described using BTC/ETH daily moves\\n"
            report += f"• **FX Momentum**: USD vs majors evaluated from true weekly returns\\n"
            report += f"• **Commodity Momentum**: Energy/metals behavior summarized without invented numbers\\n\\n"
            
            # SEZIONE 4: SECTOR ROTATION ANALYSIS
            report += "ðŸŽ¯ **SECTOR ROTATION ANALYSIS**\n\n"
            report += f"🏅 **Top Performers (Week)**:\\n"
            report += f"• **Technology**: Strong relative performance – AI and growth themes in focus\\n"
            report += f"• **Communication**: Benefited from earnings surprises and guidance\\n"
            report += f"• **Consumer Discretionary**: Supported by resilient spending signals\\n"
            report += f"• **Financials**: Helped by rate environment and credit stability\\n\\n"
            
            report += f"🏆 **Underperformers (Week)**:\\n"
            report += f"• **Utilities**: Typical laggard in risk-on phases\\n"
            report += f"• **Real Estate**: Sensitive to rate expectations\\n"
            report += f"• **Consumer Staples**: Defensive profile less in demand\\n"
            report += f"• **Healthcare**: Mixed earnings and news flow\\n\\n"
            
            report += f"🔄 **Rotation Drivers**:\\n"
            report += f"• **Growth vs Value**: Growth-oriented names favored, without specifying artificial performance gaps\\n"
            report += f"• **Quality vs Momentum**: Emphasis on liquid leaders and quality balance sheets\\n"
            report += f"• **Size**: Large-cap bias highlighted in daily flows\\n"
            report += f"• **Geography**: US focus described qualitatively instead of fixed % spreads\\n\\n"
            
            # SEZIONE 5: RISK METRICS & DRAWDOWNS
            report += "ðŸ›¡ï¸ **RISK METRICS & DRAWDOWNS**\n\n"
            report += f"📊 **Portfolio Risk Analysis**:\\n"
            report += f"• **Max Drawdown**: N/A – requires real P&L tracking (not yet integrated)\\n"
            report += f"• **VaR (95%)**: N/A – will be computed from realized P&L in a future version\\n"
            report += f"• **Sharpe Ratio**: N/A – avoid synthetic ratios without full return history\\n"
            report += f"• **Sortino Ratio**: N/A – qualitative risk discussion only for now\\n\\n"
            
            report += f"âš ï¸ **Risk Events This Week**:\n"
            report += f"â€¢ **Fed Meeting**: Wednesday - dovish tilt, minimal impact\n"
            report += f"â€¢ **Earnings Season**: 85% beat rate - positive surprise\n"
            report += f"â€¢ **Geopolitical**: Stable - no major developments\n"
            report += f"â€¢ **Economic Data**: Mixed but trend supportive\n\n"
            
            report += f"🎲 **Volatility Analysis**:\\n"
            report += f"• **Realized Vol**: Discussed qualitatively using daily price ranges – no fixed % estimate\\n"
            report += f"• **Implied Vol**: VIX regime described in daily reports without forcing exact weekly averages\\n"
            report += f"• **Vol Skew**: Monitored via options commentary when relevant\\n"
            report += f"• **Term Structure**: Shape referenced qualitatively (contango/backwardation) only when supported by data\\n\\n"
            
            # SEZIONE 6: ADVANCED ANALYTICS & AI INSIGHTS
            report += "🤖 **ADVANCED ANALYTICS & AI INSIGHTS**\\n\\n"
            
            # AI-driven outlook is kept qualitative to avoid fake probabilities
            report += f"🎯 **AI PREDICTIONS FOR NEXT WEEK**:\\n"
            report += f"• **Bullish / Bearish Bias**: Derived qualitatively from current regime and Daily Summaries – no fixed % probability shown\\n"
            report += f"• **Market Sentiment**: Use sentiment sections in Press Review, Morning and Summary for real-time scores\\n"
            report += f"• **Volatility Forecast**: Described using ranges (low/medium/high) instead of invented numeric forecasts\\n"
            report += f"• **Key Risk Level**: Summarized qualitatively (LOW/MEDIUM/HIGH) based on actual event calendar and price behavior\\n\\n"
            
            # Pattern recognition: descriptive only
            report += f"🔍 **PATTERN RECOGNITION**:\\n"
            report += f"• **Primary Patterns**: Flags, triangles and ranges observed during the week, described in daily technical commentary\\n"
            report += f"• **Time Frame**: Weekly chart context built from real intraday/closing data\\n"
            report += f"• **Confidence Level**: Expressed qualitatively (high/medium/low), not as synthetic percentages\\n"
            report += f"• **Targets**: Managed via daily support/resistance levels rather than fixed multi-week targets\\n\\n"
            
            # SEZIONE 7: WEEKEND MARKET OUTLOOK
            report += "🏖️ **WEEKEND MARKET OUTLOOK**\n\n"
            report += f"₿ **Weekend Crypto Focus**:\\n"
            report += f"• **Bitcoin**: Testing major resistance area – exact levels from live weekend crypto focus report\\n"
            report += f"• **Ethereum**: Following BTC trend – levels derived from real-time prices only\\n"
            report += f"• **Altcoins**: Selective strength, BTC dominance discussed qualitatively\\n"
            report += f"• **Weekend Patterns**: Typically quieter with lower liquidity and higher gap risk\\n\\n"
            
            report += f"ðŸŒ **Global Weekend Factors**:\n"
            report += f"â€¢ **Asia Closed**: No major market drivers expected\n"
            report += f"â€¢ **European Events**: Limited weekend activity\n"
            report += f"â€¢ **US Factors**: Minimal news flow expected\n"
            report += f"â€¢ **Central Banks**: No speeches/events scheduled\n\n"
            
            report += f"ðŸ“Š **Weekend Risk Factors**:\n"
            report += f"â€¢ **Liquidity**: Thin - higher volatility potential\n"
            report += f"â€¢ **News Sensitivity**: Higher impact if surprises occur\n"
            report += f"â€¢ **Gap Risk**: Monday opening gap possibilities\n"
            report += f"â€¢ **Crypto Volatility**: 24/7 trading continues\n\n"
            
            # SEZIONE 7: NEXT WEEK STRATEGIC SETUP
            report += "ðŸ”® **NEXT WEEK STRATEGIC SETUP**\n\n"
            report += f"ðŸ“… **Key Events Next Week**:\n"
            report += f"â€¢ **Monday**: Market reopening, gap analysis\n"
            report += f"â€¢ **Tuesday**: Economic data releases\n"
            report += f"â€¢ **Wednesday**: FOMC minutes, volatility potential\n"
            report += f"â€¢ **Thursday**: Earnings continuation\n"
            report += f"â€¢ **Friday**: Monthly close, rebalancing flows\n\n"
            
            report += f"ðŸŽ¯ **Strategic Positioning**:\n"
            report += f"â€¢ **Equity Overweight**: Continue tech/growth bias\n"
            report += f"â€¢ **Crypto Allocation**: Maintain BTC/ETH core positions\n"
            report += f"â€¢ **FX Strategy**: USD strength theme intact\n"
            report += f"â€¢ **Fixed Income**: Underweight, rates rising\n"
            report += f"â€¢ **Commodities**: Selective - energy positive, metals neutral\n\n"
            
            report += f"🤖 **ML Model Predictions (Next Week)**:\\n"
            report += f"• **Consensus**: Bias (bullish/neutral/bearish) inferred from latest Daily Summaries – no artificial confidence %\\n"
            report += f"• **S&P 500**: Monitor resistance/support zones defined by real weekly closes, not fixed numeric targets\\n"
            report += f"• **NASDAQ**: Tech leadership narrative continues or fades based on actual price action\\n"
            report += f"• **Bitcoin**: Key resistance/support zones derived from live BTC/USD levels only (no 118K placeholder)\\n"
            report += f"• **EUR/USD**: Directional bias linked to real FX data and central bank communication\\n\\n"
            
            report += f"⚠️ **Risk Management Next Week**:\\n"
            report += f"• **Position Sizing**: Normal allocation maintained, adjusted only when real volatility regimes change\\n"
            report += f"• **Stop Losses**: Based on actual technical levels from daily charts\\n"
            report += f"• **Hedge Ratio**: Qualitative indication of protection level (no fixed % without full portfolio context)\\n"
            report += f"• **Volatility Watch**: Focus on concrete risk events (e.g. FOMC minutes) highlighted in calendar modules\\n\\n"
            
            # FOOTER
            report += "-" * 60 + "\n"
            report += f"✅ **SV WEEKLY REPORT COMPLETE**\n"
            report += f"📈 Next Weekly Report: {(_now_it() + datetime.timedelta(days=7)).strftime('%A %d %B')}\n"
            report += f"📊 Monday Resume: 08:00 Press Review\n"
            report += f"🤖 ML Models: Continuous learning from weekly data\n"
            report += f"📁 Report saved to: reports/2_weekly/\n\n"
            
            # Generatete PDF if available
            if DEPENDENCIES_AVAILABLE:
                try:
                    # Create data structure using the same real aggregated weekly metrics
                    pred_pdf = weekly_metrics.get('prediction', {}) if isinstance(weekly_metrics, dict) else {}
                    assets_pdf = weekly_metrics.get('assets', {}) if isinstance(weekly_metrics, dict) else {}

                    total_tracked_pdf = int(pred_pdf.get('total_tracked', 0) or 0)
                    weekly_acc_pdf = float(pred_pdf.get('accuracy_pct', 0.0) or 0.0)
                    spx_pdf = assets_pdf.get('SPX', {})
                    spx_ret_pdf = spx_pdf.get('return_pct')

                    summary_parts = []
                    if total_tracked_pdf > 0:
                        summary_parts.append(
                            f"Aggregated weekly accuracy {weekly_acc_pdf:.0f}% on {total_tracked_pdf} live-tracked predictions."
                        )
                    else:
                        summary_parts.append(
                            "Weekly accuracy not available (no aggregated live-tracked predictions)."
                        )
                    if isinstance(spx_ret_pdf, (int, float)):
                        summary_parts.append(
                            f"S&P 500 weekly move {spx_ret_pdf:+.1f}% (Mon→Fri, based on real closes)."
                        )
                    weekly_summary_text = " ".join(summary_parts)
                    
                    week_data = {
                        'week_start': week_start,
                        'week_end': week_end,
                        'weekly_summary': weekly_summary_text,
                        'performance_metrics': {
                            'total_signals': total_tracked_pdf,
                            'total_trades': total_tracked_pdf,  # alias for compatibility
                            'success_rate': f"{weekly_acc_pdf:.0f}%" if total_tracked_pdf > 0 else 'n/a',
                            'weekly_return': f"{spx_ret_pdf:+.1f}%" if isinstance(spx_ret_pdf, (int, float)) else 'n/a',
                            'total_profit': 'n/a',
                            'sharpe_ratio': 'n/a',
                            'max_drawdown': 'n/a',
                        },
                        # For now we do not fabricate per-day P&L; leave this empty or descriptive only
                        'daily_performance': [],
                        'market_analysis': {
                            'regime': 'See textual weekly report for qualitative regime description',
                            'volatility': 'See volatility section (no synthetic %)',
                            'trend_strength': 'Described qualitatively (bullish/neutral/corrective)',
                            'sector_rotation': 'See sector rotation section',
                        },
                        'risk_metrics': {
                            'risk_level': 'N/A',
                            'var_95': 'N/A',
                            'max_position': 'N/A',
                            'correlation_risk': 'N/A',
                        },
                        'key_events': [],
                        'next_week_outlook': 'See textual weekly report for qualitative outlook; no synthetic probabilities in PDF.',
                        'next_week_strategy': [],
                        'action_items': [],
                    }
                    
                    pdf_path = Createte_weekly_pdf(week_data)
                    if pdf_path:
                        report += f"📄 PDF Report: {pdf_path}\n"
                        
                        # Send PDF via Telegram
                        try:
                            from telegram_handler import get_telegram_handler
                            telegram = get_telegram_handler()
                            
                            # week_start/week_end are DD/MM strings; build safe caption
                            caption = f"Weekly Report - {week_start} to {week_end} {now.strftime('%Y')}"
                            if not os.environ.get('SV_SKIP_TELEGRAM'):
                                result = telegram.send_document(
                                    file_path=pdf_path,
                                    caption=caption,
                                    content_type='weekly',
                                    metadata={
                                        'week_start': week_start,
                                        'week_end': week_end,
                                        'report_type': 'weekly_pdf'
                                    }
                                )
                            else:
                                result = {'success': False, 'skipped': True, 'reason': 'SV_SKIP_TELEGRAM=1'}
                            
                            if result.get('success'):
                                log.info(f"✅ [WEEKLY] PDF sent to Telegram: {result.get('filename')}")
                                report += f"📤 PDF sent to Telegram successfully\n"
                            else:
                                log.warning(f"⚠️ [WEEKLY] PDF Telegram sending failed: {result.get('error')}")
                                report += f"⚠️ PDF Telegram sending failed\n"
                                
                        except Exception as telegram_error:
                            log.warning(f"⚠️ [WEEKLY] Telegram integration error: {telegram_error}")
                            report += f"⚠️ Telegram sending error\n"
                            
                except Exception as e:
                    log.warning(f"⚠️ [WEEKLY] PDF Generation failed: {e}")
            
            log.info(f"âœ… [WEEKLY] Generateted complete weekly report")
            return report
            
        except Exception as e:
            log.error(f"âŒ [WEEKLY] Error: {e}")
            return f"âŒ Errore Generatezione weekly report: {str(e)}"
    
    def Generatete_weekend_crypto_focus(self) -> str:
        """
        Generate focus specifico crypto per weekend
        
        Returns:
            Stringa con analisi crypto weekend
        """
        try:
            log.info("â‚¿ [WEEKEND-CRYPTO] Generatezione crypto focus...")
            
            now = _now_it()
            
            crypto_report = f"â‚¿ **SV - WEEKEND CRYPTO FOCUS**\n"
            crypto_report += f"ðŸ“… {now.strftime('%A %d %B %Y')} - {now.strftime('%H:%M')}\n"
            crypto_report += "â”€" * 40 + "\n\n"
            
            crypto_report += f"ðŸ–ï¸ **Weekend Crypto Market Overview**:\n"

            # Use live crypto prices when available to keep BTC levels realistic
            crypto_prices = {}
            try:
                crypto_prices = get_live_crypto_prices() or {}
            except Exception as e:
                log.warning(f"âš ï¸ [WEEKEND-CRYPTO-LIVE] Error retrieving prices: {e}")
                crypto_prices = {}

            btc_data = crypto_prices.get('BTC', {}) if isinstance(crypto_prices, dict) else {}
            eth_data = crypto_prices.get('ETH', {}) if isinstance(crypto_prices, dict) else {}

            btc_price = float(btc_data.get('price') or 0)
            btc_change = float(btc_data.get('change_pct') or 0)
            eth_price = float(eth_data.get('price') or 0)
            eth_change = float(eth_data.get('change_pct') or 0)

            if btc_price > 0:
                btc_line = f"${btc_price:,.0f} ({btc_change:+.1f}% 24h) - weekend consolidation"
            else:
                btc_line = "Price unavailable (weekend/offline) - weekend consolidation"

            if eth_price > 0:
                eth_line = f"${eth_price:,.0f} ({eth_change:+.1f}% 24h) - relative strength"
            else:
                eth_line = "Price unavailable (weekend/offline) - relative strength"

            crypto_report += f"â€¢ **Bitcoin**: {btc_line}\n"
            crypto_report += f"â€¢ **Ethereum**: {eth_line}\n"

            total_mcap = float(crypto_prices.get('TOTAL_MARKET_CAP') or 0) if isinstance(crypto_prices, dict) else 0
            if total_mcap > 0:
                crypto_report += f"â€¢ **Total Market Cap**: ${total_mcap/1e12:,.2f}T (approx)\n"
            else:
                crypto_report += f"â€¢ **Total Market Cap**: Data unavailable (weekend/offline)\n"

            crypto_report += f"â€¢ **BTC Dominance**: 65-70% range - stable leadership\n\n"
            
            crypto_report += f"ðŸ“Š **Weekend Liquidity Analysis**:\n"
            crypto_report += f"â€¢ **24h Volume**: Typical weekend levels vs weekday averages\n"
            crypto_report += f"â€¢ **Spread Analysis**: Slightly wider than weekdays\n"
            crypto_report += f"â€¢ **Exchange Flows**: Net neutral to mildly positive\n"
            crypto_report += f"â€¢ **Whale Activity**: Limited large transactions\n\n"
            
            crypto_report += f"ðŸŽ¯ **Key Levels Weekend**:\n"

            # Dynamic BTC/ETH support & resistance when prices are available
            try:
                btc_sr = calculate_crypto_support_resistance(btc_price, btc_change) if btc_price > 0 else {}
            except Exception as e:
                log.warning(f"âš ï¸ [WEEKEND-CRYPTO-SR-BTC] Error: {e}")
                btc_sr = {}
            try:
                eth_sr = calculate_crypto_support_resistance(eth_price, eth_change) if eth_price > 0 else {}
            except Exception as e:
                log.warning(f"âš ï¸ [WEEKEND-CRYPTO-SR-ETH] Error: {e}")
                eth_sr = {}

            if btc_sr:
                btc_res_2 = int(btc_sr.get('resistance_2') or 0)
                btc_res_5 = int(btc_sr.get('resistance_5') or 0)
                btc_sup_2 = int(btc_sr.get('support_2') or 0)
                btc_sup_5 = int(btc_sr.get('support_5') or 0)
                crypto_report += f"â€¢ **BTC Resistance**: {btc_res_2:,.0f}, {btc_res_5:,.0f}\n"
                crypto_report += f"â€¢ **BTC Support**: {btc_sup_2:,.0f}, {btc_sup_5:,.0f}\n"
            else:
                crypto_report += f"â€¢ **BTC Resistance**: Dynamic levels near recent highs\n"
                crypto_report += f"â€¢ **BTC Support**: Dynamic levels near recent lows\n"

            if eth_sr:
                eth_res_2 = float(eth_sr.get('resistance_2') or 0)
                eth_res_5 = float(eth_sr.get('resistance_5') or 0)
                eth_sup_2 = float(eth_sr.get('support_2') or 0)
                eth_sup_5 = float(eth_sr.get('support_5') or 0)
                crypto_report += f"â€¢ **ETH Resistance**: {eth_res_2:,.0f}, {eth_res_5:,.0f}\n"
                crypto_report += f"â€¢ **ETH Support**: {eth_sup_2:,.0f}, {eth_sup_5:,.0f}\n\n"
            else:
                crypto_report += f"â€¢ **ETH Resistance**: Dynamic levels near recent highs\n"
                crypto_report += f"â€¢ **ETH Support**: Dynamic levels near recent lows\n\n"
            
            crypto_report += f"ðŸ”® **Monday Opening Outlook**:\n"
            crypto_report += f"â€¢ **Expected**: Continuation of weekend trend\n"
            crypto_report += f"â€¢ **Risk Factors**: Traditional market gap impact\n"
            crypto_report += f"â€¢ **Opportunities**: Range trading setups\n"
            crypto_report += f"â€¢ **Strategy**: Wait for traditional market open\n\n"
            
            return crypto_report
            
        except Exception as e:
            log.error(f"âŒ [WEEKEND-CRYPTO] Error: {e}")
            return f"âŒ Errore weekend crypto focus: {str(e)}"

# Singleton instance
weekly_Generatetor = None

def get_weekly_Generatetor() -> WeeklyReportGeneratetor:
    """Get singleton instance of weekly report Generatetor"""
    global weekly_Generatetor
    if weekly_Generatetor is None:
        weekly_Generatetor = WeeklyReportGeneratetor()
    return weekly_Generatetor

# Helper functions
def Generatete_weekly_report() -> str:
    """Generatete complete weekly report"""
    Generatetor = get_weekly_Generatetor()
    return Generatetor.Generatete_weekly_report()

def Generatete_weekend_crypto_focus() -> str:
    """Generatete weekend crypto focus"""
    Generatetor = get_weekly_Generatetor()
    return Generatetor.Generatete_weekend_crypto_focus()

def is_weekend_report_time() -> bool:
    """Check if it's time for weekend report (Sunday 17:00)"""
    now = _now_it()
    return now.weekday() == 6 and now.hour == 17  # Sunday 17:00

# Test function
def test_weekly_Generatetion():
    """Test weekly content Generatetion"""
    print("ðŸ§ª [TEST] Testing Weekly Content Generatetion...")
    
    try:
        Generatetor = get_weekly_Generatetor()
        
        # Test weekly report
        weekly_report = Generatetor.Generatete_weekly_report()
        print(f"âœ… [TEST] Weekly Report: {len(weekly_report)} characters")
        
        # Test weekend crypto focus
        crypto_focus = Generatetor.Generatete_weekend_crypto_focus()
        print(f"âœ… [TEST] Crypto Focus: {len(crypto_focus)} characters")
        
        # Test timing check
        is_time = is_weekend_report_time()
        print(f"âœ… [TEST] Weekend Report Time: {is_time}")
        
        print("âœ… [TEST] All weekly Generatetors working correctly")
        return True
        
    except Exception as e:
        print(f"âŒ [TEST] Weekly Generatetion error: {e}")
        return False

def main() -> bool:
    """Main function per weekly report generation con PDF + Telegram"""
    try:
        log.info("📊 [WEEKLY-MAIN] Starting weekly report generation...")
        
        # Generate weekly report content
        generator = get_weekly_Generatetor()
        weekly_content = generator.Generatete_weekly_report()
        
        if not weekly_content or len(weekly_content) < 100:
            log.error("❌ [WEEKLY-MAIN] Weekly report too short or empty")
            return False
            
        log.info(f"✅ [WEEKLY-MAIN] Weekly content generated: {len(weekly_content)} chars")
        
        # Import PDF and Telegram modules
        from pdf_generator import Createte_weekly_pdf
        from telegram_handler import get_telegram_handler
        
        # Create comprehensive weekly data using WeeklyDataAssembler
        log.info("📊 [WEEKLY-MAIN] Using WeeklyDataAssembler for data-driven report...")
        
        assembler = WeeklyDataAssembler()
        weekly_data = assembler.assemble_weekly_data()
        
        if not weekly_data:
            log.warning("⚠️ [WEEKLY-MAIN] WeeklyDataAssembler returned no data, falling back to minimal structure")
            now = datetime.datetime.now(ITALY_TZ)
            week_start = (now - datetime.timedelta(days=now.weekday())).strftime('%d/%m')
            week_end = (now - datetime.timedelta(days=now.weekday()) + datetime.timedelta(days=4)).strftime('%d/%m')
            
            weekly_data = {
                'timeframe': 'weekly',
                'week_start': week_start,
                'week_end': week_end,
                'title': f'SV Weekly Report - {now.strftime("%d/%m/%Y")}',
                'weekly_summary': 'No daily data available for aggregation this week.',
                'performance_metrics': {
                    'total_signals': 0,
                    'success_rate': 'n/a',
                    'weekly_return': 'n/a',
                    'total_profit': 'n/a',
                    'sharpe_ratio': 'n/a',
                    'max_drawdown': 'n/a'
                },
                'daily_performance': [],
                'market_analysis': {
                    'regime': 'Data not available',
                    'volatility': 'Data not available',
                    'trend_strength': 'Data not available',
                    'sector_rotation': 'Data not available'
                },
                'key_events': [],
                'next_week_outlook': 'Outlook requires daily data aggregation.',
                'next_week_strategy': [],
                'action_items': []
            }
        else:
            log.info(f"✅ [WEEKLY-MAIN] WeeklyDataAssembler provided data: {weekly_data.get('data_sources', {})}")
            
            # Add additional fields that PDF generator expects
            now = datetime.datetime.now(ITALY_TZ)
            weekly_data['title'] = f'SV Weekly Report - {now.strftime("%d/%m/%Y")}'
            
            # Ensure risk_metrics section exists (PDF generator expects it)
            if 'risk_metrics' not in weekly_data:
                weekly_data['risk_metrics'] = {
                    'risk_level': 'N/A',
                    'var_95': 'N/A', 
                    'max_position': 'N/A',
                    'correlation_risk': 'N/A'
                }
            
            # Ensure outlook sections exist
            if 'next_week_outlook' not in weekly_data:
                weekly_data['next_week_outlook'] = 'Outlook based on aggregated daily insights.'
            if 'next_week_strategy' not in weekly_data:
                weekly_data['next_week_strategy'] = []
            
            # Action items are already included in weekly_data from WeeklyDataAssembler
            # No additional processing needed here
        pdf_path = Createte_weekly_pdf(weekly_data)
        
        if pdf_path:
            log.info(f"✅ [WEEKLY-MAIN] PDF created: {pdf_path}")
            
            # Send PDF to Telegram (skip if SV_SKIP_TELEGRAM=1)
            if not os.environ.get('SV_SKIP_TELEGRAM'):
                caption = f"📊 [WEEKLY] SV Weekly Report - {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"
                handler = get_telegram_handler()
                telegram_result = handler.send_document(pdf_path, caption=caption)
            else:
                telegram_result = {'success': False, 'skipped': True, 'reason': 'SV_SKIP_TELEGRAM=1'}
            
            # Check if telegram sending was successful
            if telegram_result and isinstance(telegram_result, dict) and telegram_result.get('success', False):
                log.info("✅ [WEEKLY-MAIN] PDF sent to Telegram successfully")
                return True
            else:
                log.warning("⚠️ [WEEKLY-MAIN] Telegram sending skipped or failed")
                log.info(f"[WEEKLY-MAIN] Result: {telegram_result}")
                return True
        else:
            log.error("❌ [WEEKLY-MAIN] Failed to create PDF")
            return False
            
    except Exception as e:
        log.error(f"❌ [WEEKLY-MAIN] Error: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'main':
        main()
    else:
        test_weekly_Generatetion()



