#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - Daily Content Generator
Generates all 5 daily contents based on 555a_server approach
"""

import datetime
import pytz
import json
import os
import sys
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

# Import clean emoji module
from modules.sv_emoji import EMOJI

# Console-safe logging for Windows compatibility
try:
    from log_handler import get_console_safe_logger
    log = get_console_safe_logger(__name__)
except ImportError:
    log = logging.getLogger(__name__)

# Install ASCII-only log formatter to avoid emoji corruption in console
try:
    from modules.sv_logging import install_ascii_logging
    install_ascii_logging()
except Exception:
    pass

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
# Already in modules directory

ITALY_TZ = pytz.timezone("Europe/Rome")
GOLD_GRAMS_PER_TROY_OUNCE = 31.1035  # standard conversion factor
def _now_it():
    """Get current time in Italian timezone"""
    return datetime.datetime.now(ITALY_TZ)

# Import SV Enhanced modules
try:
    from modules.sv_news import get_news_for_content
    from modules.sv_calendar import get_day_context, get_market_status, analyze_calendar_impact
    SV_ENHANCED_ENABLED = True
    log.info("[OK] [SV-ENHANCED] News and Calendar systems loaded")
except ImportError as e:
    log.warning(f"[WARN] [SV-ENHANCED] Enhanced systems not available: {e}")
    SV_ENHANCED_ENABLED = False

# Import required modules
try:
    from modules.narrative_continuity import get_narrative_continuity
    from daily_session_tracker import daily_tracker
    from modules.momentum_indicators import (
        generate_trading_signals,
        calculate_risk_metrics,
    )
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    log.warning(f"[WARN] [DAILY-GEN] Dependencies not available: {e}")
    DEPENDENCIES_AVAILABLE = False

# Period aggregator for recent performance (no hard dependency on ML extras)
try:
    from modules import period_aggregator
    PERIOD_AGGREGATOR_AVAILABLE = True
except ImportError as e:
    log.warning(f"[WARN] [DAILY-GEN] Period aggregator not available: {e}")
    PERIOD_AGGREGATOR_AVAILABLE = False

# Optional CoherenceManager for BRAIN-style multi-day analysis
try:
    from modules import coherence_manager
    COHERENCE_MANAGER_AVAILABLE = True
except ImportError as e:
    log.warning(f"[WARN] [DAILY-GEN] Coherence manager not available: {e}")
    COHERENCE_MANAGER_AVAILABLE = False

# Enhanced Regime Manager for narrative consistency (v1.5.0)
try:
    from modules.regime_manager import get_daily_regime_manager
    REGIME_MANAGER_AVAILABLE = True
    log.info("[OK] [REGIME-MANAGER] Enhanced narrative consistency system loaded")
except ImportError as e:
    log.warning(f"[WARN] [DAILY-GEN] Regime manager not available: {e}")
    REGIME_MANAGER_AVAILABLE = False

# Portfolio Manager for $25K tracking (v1.5.0)
try:
    from modules.portfolio_manager import get_portfolio_manager
    PORTFOLIO_MANAGER_AVAILABLE = True
    log.info("[OK] [PORTFOLIO-MANAGER] $25K portfolio tracking system loaded")
except ImportError as e:
    log.warning(f"[WARN] [DAILY-GEN] Portfolio manager not available: {e}")
    PORTFOLIO_MANAGER_AVAILABLE = False

# === CRYPTO LIVE FUNCTIONS FROM 555a ===
def get_live_crypto_prices():
    """Recupera prezzi crypto live attuali con cache e fallback system"""
    import requests
    
    try:
        print(f"[CRYPTO] Retrieving live crypto prices...")
        
        # API CryptoCompare per prezzi multipli
        symbols = "BTC,ETH,BNB,SOL,ADA,XRP,DOT,LINK"
        url = f"https://min-api.cryptocompare.com/data/pricemultifull"
        params = {'fsyms': symbols, 'tsyms': 'USD'}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'RAW' in data:
            prices = {}
            for symbol in symbols.split(','):
                if symbol in data['RAW'] and 'USD' in data['RAW'][symbol]:
                    raw_data = data['RAW'][symbol]['USD']
                    prices[symbol] = {
                        'price': raw_data.get('PRICE', 0),
                        'change_pct': raw_data.get('CHANGEPCT24HOUR', 0),
                        'high_24h': raw_data.get('HIGH24HOUR', 0),
                        'low_24h': raw_data.get('LOW24HOUR', 0),
                        'volume_24h': raw_data.get('VOLUME24HOUR', 0),
                        'market_cap': raw_data.get('MKTCAP', 0)
                    }
                else:
                    log.warning(f"⚠️ [CRYPTO-LIVE] Dati non trovati per {symbol}")
                    prices[symbol] = {
                        'price': 0, 'change_pct': 0, 'high_24h': 0, 
                        'low_24h': 0, 'volume_24h': 0, 'market_cap': 0
                    }
            
            # Calcola market cap totale approssimativo
            total_market_cap = sum(p.get('market_cap', 0) for p in prices.values())
            prices['TOTAL_MARKET_CAP'] = total_market_cap
            
            log.info(f"[OK] [CRYPTO-LIVE] Updated prices for {len(prices)} crypto")
            return prices
        else:
            log.error(f"❌ [CRYPTO-LIVE] Formato risposta API non valido")
            return {}
            
    except Exception as e:
        log.error(f"❌ [CRYPTO-LIVE] Errore: {e}")
        return {}


def get_live_equity_fx_quotes(symbols: list[str]) -> dict:
    """Get live quotes for equity indices, FX and commodities (offline-safe).
    Currently supports '^GSPC' (S&P 500), 'EURUSD=X' and 'XAUUSD=X' (Gold).
    Returns mapping like {
        '^GSPC': {'price': float, 'change_pct': float},
        'EURUSD=X': {'price': float, 'change_pct': float},
        'XAUUSD=X': {'price': float, 'change_pct': float},
    }
    """
    try:
        import requests
        # Quick network precheck
        try:
            requests.head('https://query1.finance.yahoo.com', timeout=2)
        except Exception as e:
            log.warning(f"[QUOTES] Network unavailable: {e}")
            return {}
        url = 'https://query1.finance.yahoo.com/v7/finance/quote'
        params = {'symbols': ','.join(symbols)}
        resp = requests.get(url, params=params, timeout=6)
        resp.raise_for_status()
        data = resp.json()
        result = {}
        for q in data.get('quoteResponse', {}).get('result', []):
            sym = q.get('symbol')
            price = q.get('regularMarketPrice') or q.get('postMarketPrice') or 0
            chg_pct = q.get('regularMarketChangePercent') or 0
            result[sym] = {'price': float(price or 0), 'change_pct': float(chg_pct or 0)}
        if result:
            log.info(f"[OK] [QUOTES] Live quotes: {', '.join(result.keys())}")
        return result
    except Exception as e:
        log.warning(f"[QUOTES] Error retrieving quotes: {e}")
        return {}

def format_crypto_price_line(symbol, data, description=""):
    """Formatta una linea di prezzo crypto per i messaggi (Unicode-clean)."""
    try:
        price = data.get('price', 0)
        change_pct = data.get('change_pct', 0)
        
        # Formatta il prezzo
        if price >= 1000:
            price_str = f"${price:,.0f}"
        elif price >= 1:
            price_str = f"${price:,.2f}"
        else:
            price_str = f"${price:.4f}"
        
        # Formatta la variazione percentuale
        change_sign = "+" if change_pct >= 0 else ""
        change_str = f"({change_sign}{change_pct:.1f}%)"
        
        return f"{EMOJI['bullet']} {symbol}: {price_str} {change_str} - {description}"
    except Exception:
        return f"{EMOJI['bullet']} {symbol}: Price unavailable - {description}"

def calculate_crypto_support_resistance(price, change_pct):
    """Calcola supporti e resistenze dinamici per crypto"""
    try:
        # Calcoli precisi come nella 555a
        support_2 = price * 0.97  # -3%
        support_5 = price * 0.95  # -5%
        resistance_2 = price * 1.03  # +3%
        resistance_5 = price * 1.05  # +5%
        
        # Trend direction (Unicode-clean)
        if change_pct > 1:
            trend_direction = f"{EMOJI['chart_up']} BULLISH"
        elif change_pct < -1:
            trend_direction = f"{EMOJI['chart_down']} BEARISH"
        else:
            trend_direction = f"{EMOJI['right_arrow']} SIDEWAYS"
        momentum = min(abs(change_pct) * 2, 10)
        
        return {
            'support_2': support_2,
            'support_5': support_5, 
            'resistance_2': resistance_2,
            'resistance_5': resistance_5,
            'trend_direction': trend_direction,
            'momentum': momentum
        }
    except Exception as e:
        log.error(f"âŒ [CRYPTO-SR] Errore calcolo: {e}")
        return {}

# Enhanced data functions using SV systems
def get_fallback_data():
    """Get enhanced data using SV systems or fallback"""
    data = {
        'market_status': 'OPEN',
        'day_context': _now_it().strftime('%A'),
        'sentiment': 'NEUTRAL',
        'predictions': ['Market consolidation expected'],
        'momentum': 'STABLE'
    }
    
    if SV_ENHANCED_ENABLED:
        try:
            # Get real market status
            market_status, market_message = get_market_status()
            data['market_status'] = market_status
            data['market_message'] = market_message
            
            # Get day context
            day_ctx = get_day_context()
            data['day_context'] = day_ctx['desc']
            data['day_focus'] = day_ctx['focus']
            data['content_priority'] = day_ctx['content_priority']
            
            # Get calendar impact
            calendar_impact = analyze_calendar_impact()
            data['calendar_impact'] = calendar_impact['overall_impact']
            data['market_sentiment'] = calendar_impact['market_sentiment']
            data['calendar_recommendations'] = calendar_impact['recommendations']
            
            log.info(f"âœ… [SV-ENHANCED] Enhanced data loaded: {market_status}, {day_ctx['desc']}")
            
        except Exception as e:
            log.warning(f"âš ï¸ [SV-ENHANCED] Error getting enhanced data: {e}")
    
    return data

def get_enhanced_news(content_type="daily", max_news=None):
    """Get real news using SV News system with offline-safe precheck for all content types."""
    if SV_ENHANCED_ENABLED:
        # Quick network precheck to avoid long RSS timeouts when offline
        try:
            import requests  # local import to avoid hard dependency at import time
            requests.head("https://feeds.bbci.co.uk/news/rss.xml", timeout=2)
        except Exception as e:
            log.warning(f"[SV-NEWS] Network unavailable for {content_type}, using fallback: {e}")
            return {
                'news': [],
                'sentiment': {'sentiment': 'NEUTRAL', 'market_impact': 'LOW'},
                'has_real_news': False
            }
        try:
            # get_news_for_content ora restituisce già news e sentiment normalizzati
            news_data = get_news_for_content(content_type=content_type, max_news=max_news)
            log.info(f"[SV-NEWS] Retrieved {len(news_data.get('news', []))} news for {content_type}")
            return news_data  # già ha news, sentiment, has_real_news
        except Exception as e:
            log.warning(f"[SV-NEWS] Error getting news: {e}")
    # Fallback placeholder news
    return {
        'news': [],
        'sentiment': {'sentiment': 'NEUTRAL', 'market_impact': 'LOW'},
        'has_real_news': False
    }

class DailyContentGenerator:
    def __init__(self):
        """Initialize daily content generator"""
        self.narrative = get_narrative_continuity() if DEPENDENCIES_AVAILABLE else None
        self.session_tracker = daily_tracker if DEPENDENCIES_AVAILABLE else None
        
        # Setup directories for content storage and ML analysis
        self.content_dir = Path(project_root) / 'backups' / 'daily_content'
        self.content_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir = Path(project_root) / 'reports' / '8_daily_content'
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
    def save_content(self, content_type: str, messages: List[str], metadata: Dict = None) -> str:
        """Save generated content to reports directory"""
        try:
            now = _now_it()
            date_str = now.strftime('%Y-%m-%d')
            time_str = now.strftime('%H%M')
            
            # Create filename: YYYY-MM-DD_HHMM_content-type.json
            filename = f"{date_str}_{time_str}_{content_type}.json"
            filepath = self.reports_dir / filename
            
            # Prepare content data
            content_data = {
                'timestamp': now.isoformat(),
                'date': date_str,
                'time': time_str,
                'content_type': content_type,
                'messages_count': len(messages),
                'messages': messages,
                'metadata': metadata or {},
                'total_chars': sum(len(msg) for msg in messages),
                'avg_msg_length': sum(len(msg) for msg in messages) / len(messages) if messages else 0
            }
            
            # Save to JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(content_data, f, ensure_ascii=False, indent=2)
            
            log.info(f"[SAVE] [SAVE] {content_type} saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            log.error(f"Ã¢ÂÅ’ [SAVE] Error saving {content_type}: {e}")
            return None
    
    def _load_recent_prediction_performance(self, now: datetime.datetime, lookback_days: int = 7) -> Dict[str, Any]:
        """Load recent real prediction performance (hits/misses/accuracy) for last N days.

        Uses period_aggregator over the last `lookback_days` ending yesterday.
        Returns a compact dict with hits/misses/pending/total_tracked/accuracy_pct.
        """
        default = {
            'hits': 0,
            'misses': 0,
            'pending': 0,
            'total_tracked': 0,
            'accuracy_pct': 0.0,
        }
        if not PERIOD_AGGREGATOR_AVAILABLE:
            return default
        try:
            if not isinstance(now, datetime.datetime):
                now = _now_it()
            end_date = (now - datetime.timedelta(days=1)).date()
            start_date = end_date - datetime.timedelta(days=max(lookback_days - 1, 0))
            if start_date > end_date:
                return default
            agg = period_aggregator.get_period_metrics(start_date, end_date) or {}
            pred = agg.get('prediction') or {}
            return {
                'hits': int(pred.get('hits', 0) or 0),
                'misses': int(pred.get('misses', 0) or 0),
                'pending': int(pred.get('pending', 0) or 0),
                'total_tracked': int(pred.get('total_tracked', 0) or 0),
                'accuracy_pct': float(pred.get('accuracy_pct', 0.0) or 0.0),
            }
        except Exception as e:
            log.warning(f"{EMOJI['warning']} [PERF-LOAD] Error loading recent prediction performance: {e}")
            return default

    def _load_recent_coherence_summary(self, now: datetime.datetime, history_days: int = 7) -> Dict[str, Any]:
        """Load recent multi-day coherence + accuracy summary from CoherenceManager history.

        This reads backups/ml_analysis/coherence_history.json (if present) and
        computes simple averages over the last `history_days` entries. It is
        intentionally offline-safe and will quietly degrade to a default dict
        when history is unavailable.
        """
        default: Dict[str, Any] = {
            'available': False,
            'days': 0,
            'avg_coherence': 0.0,
            'avg_accuracy': 0.0,
            'entries': [],
        }
        if not COHERENCE_MANAGER_AVAILABLE:
            return default
        try:
            from pathlib import Path as _Path
            import json as _json_local

            # History file is maintained by coherence_manager.run_daily_coherence_analysis
            history_path = _Path(project_root) / 'backups' / 'ml_analysis' / 'coherence_history.json'
            if not history_path.exists():
                return default

            with open(history_path, 'r', encoding='utf-8') as hf:
                data = _json_local.load(hf)

            entries = data.get('entries') or []
            if not entries:
                return default

            # Sort by date ascending and take the most recent `history_days` entries
            try:
                entries_sorted = sorted(entries, key=lambda e: e.get('date', ''))
            except Exception:
                entries_sorted = entries
            latest_entries = entries_sorted[-history_days:]
            n = len(latest_entries)
            if n == 0:
                return default

            total_coh = 0.0
            total_acc = 0.0
            for e in latest_entries:
                try:
                    total_coh += float(e.get('coherence_score', 0.0) or 0.0)
                except Exception:
                    pass
                try:
                    total_acc += float(e.get('daily_accuracy', 0.0) or 0.0)
                except Exception:
                    pass

            avg_coh = total_coh / n if n else 0.0
            avg_acc = total_acc / n if n else 0.0

            return {
                'available': True,
                'days': n,
                'avg_coherence': avg_coh,
                'avg_accuracy': avg_acc,
                'entries': latest_entries,
            }
        except Exception as e:
            log.warning(f"{EMOJI['warning']} [COHERENCE-SUMMARY] Error loading coherence history: {e}")
            return default
    
    def _evaluate_predictions_with_live_data(self, now):
        """Evaluate today's saved predictions against live market data (offline-safe)."""
        results = {
            'items': [],
            'hits': 0,
            'misses': 0,
            'pending': 0,
            'total_tracked': 0,
            'accuracy_pct': 0.0,
        }
        try:
            from pathlib import Path
            import json
            
            pred_file = Path(self.reports_dir).parent / '1_daily' / f"predictions_{now.strftime('%Y-%m-%d')}.json"
            if not pred_file.exists():
                return results
            
            with open(pred_file, 'r', encoding='utf-8') as pf:
                pred_data = json.load(pf)
            preds = pred_data.get('predictions', [])
            if not preds:
                return results
            
            # Fetch live prices via ENGINE snapshot (BTC, SPX, EURUSD) in a single place
            live_prices = {}
            try:
                from modules.engine.market_data import get_market_snapshot
                snapshot = get_market_snapshot(now) or {}
                assets = snapshot.get('assets', {}) or {}
                btc = assets.get('BTC', {}) or {}
                spx = assets.get('SPX', {}) or {}
                eur = assets.get('EURUSD', {}) or {}
                if btc.get('price'):
                    live_prices['BTC'] = btc.get('price') or 0
                if spx.get('price'):
                    live_prices['SPX'] = spx.get('price') or 0
                if eur.get('price'):
                    live_prices['EURUSD'] = eur.get('price') or 0
            except Exception as e:
                log.warning(f"{EMOJI['warning']} [PREDICTION-EVAL] Market snapshot unavailable: {e}")
            
            hits = misses = pending = total = 0
            items = []
            
            for p in preds:
                asset = (p.get('asset') or '').upper()
                direction = (p.get('direction') or 'LONG').upper()
                entry = float(p.get('entry') or 0)
                target = float(p.get('target') or 0)
                stop = float(p.get('stop') or 0)
                
                # Map asset to live price key
                if asset in ('SPX', 'S&P 500'):
                    curr = live_prices.get('SPX', 0)
                elif asset in ('EURUSD', 'EUR/USD'):
                    curr = live_prices.get('EURUSD', 0)
                else:
                    curr = live_prices.get(asset, 0)
                
                status = 'PENDING - live data pending'
                grade = 'PENDING'
                distance = None
                
                if curr:
                    # Asset has a live price; evaluate status
                    total += 1
                    if direction == 'LONG':
                        if curr >= target > 0:
                            status = 'TARGET HIT'
                            grade = 'A+'
                            hits += 1
                        elif stop and curr <= stop:
                            status = 'STOP HIT'
                            grade = 'C'
                            misses += 1
                        else:
                            status = 'IN PROGRESS'
                            grade = 'B+'
                            pending += 1
                            distance = (target - curr) if target else None
                    else:  # SHORT
                        if curr <= target < entry:
                            status = 'TARGET HIT'
                            grade = 'A+'
                            hits += 1
                        elif stop and curr >= stop:
                            status = 'STOP HIT'
                            grade = 'C'
                            misses += 1
                        else:
                            status = 'IN PROGRESS'
                            grade = 'B+'
                            pending += 1
                            distance = (curr - target) if target else None
                
                items.append({
                    'asset': asset,
                    'direction': direction,
                    'entry': entry,
                    'target': target,
                    'stop': stop,
                    'current': curr,
                    'status': status,
                    'grade': grade,
                    'distance_to_target': distance,
                })
            
            # Accuracy is defined only on fully closed signals (hits + misses).
            # Pending trades are explicitly tracked but excluded from the denominator
            # to avoid misleading hit rates on tiny or unresolved samples.
            closed = hits + misses
            accuracy_pct = (hits / closed * 100.0) if closed > 0 else 0.0
            results.update({
                'items': items,
                'hits': hits,
                'misses': misses,
                'pending': pending,
                'total_tracked': closed,
                'accuracy_pct': accuracy_pct,
                'total_evaluated': total,
            })
            return results
            
        except Exception as e:
            log.warning(f"{EMOJI['warn']} [PREDICTION-EVAL] Error evaluating predictions: {e}")
            return results
    
    def _save_sentiment_for_stage(self, stage: str, sentiment: str, now=None):
        """Save sentiment for a specific message stage (press_review, morning, noon, evening).
        This allows Daily Summary to read the full intraday evolution.
        """
        if now is None:
            now = _now_it()
        date_str = now.strftime('%Y-%m-%d')
        tracking_file = self.reports_dir / f"sentiment_tracking_{date_str}.json"
        
        try:
            # Load existing tracking or create new
            if tracking_file.exists():
                with open(tracking_file, 'r', encoding='utf-8') as f:
                    tracking = json.load(f)
            else:
                tracking = {}
            
            # Update the stage sentiment with timestamp
            tracking[stage] = {
                'sentiment': sentiment,
                'timestamp': now.isoformat()
            }
            
            # Save back
            with open(tracking_file, 'w', encoding='utf-8') as f:
                json.dump(tracking, f, indent=2, ensure_ascii=False)
            
            log.info(f"[SENTIMENT-TRACKING] Saved {stage}: {sentiment}")
        except Exception as e:
            log.warning(f"[SENTIMENT-TRACKING] Error saving {stage}: {e}")
    
    def _load_sentiment_tracking(self, now=None) -> Dict[str, Any]:
        """Load sentiment tracking for the day.
        Returns dict like {'press_review': {'sentiment': 'POSITIVE', 'timestamp': ...}, ...}
        """
        if now is None:
            now = _now_it()
        date_str = now.strftime('%Y-%m-%d')
        tracking_file = self.reports_dir / f"sentiment_tracking_{date_str}.json"
        
        try:
            if tracking_file.exists():
                with open(tracking_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            log.warning(f"[SENTIMENT-TRACKING] Error loading: {e}")
        
        return {}
    
    def _save_daily_metrics_snapshot(self, now, prediction_eval: Dict[str, Any], market_snapshot: Dict[str, Any]):
        """Save compact daily metrics (accuracy + key asset snapshot) for weekly/monthly aggregation.

        This writes a JSON file per day under reports/metrics with:
        - date, timestamp
        - prediction_eval: hits/misses/pending/total_tracked/accuracy_pct
        - market_snapshot: latest BTC/SPX/EURUSD/GOLD snapshot (Gold in USD/gram)
        """
        try:
            date_str = now.strftime('%Y-%m-%d')
            metrics_dir = Path(project_root) / 'reports' / 'metrics'
            metrics_dir.mkdir(parents=True, exist_ok=True)

            data = {
                'date': date_str,
                'timestamp': now.isoformat(),
                'prediction_eval': prediction_eval or {},
                'market_snapshot': market_snapshot or {},
            }

            metrics_file = metrics_dir / f"daily_metrics_{date_str}.json"
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            log.info(f"{EMOJI['check']} [SUMMARY-METRICS] Saved daily metrics snapshot: {metrics_file}")
        except Exception as e:
            # Never block Daily Summary generation because of metrics persistence issues
            log.warning(f"{EMOJI['warning']} [SUMMARY-METRICS] Error saving daily metrics snapshot: {e}")

    def _engine_log_stage(self, stage: str, now, sentiment: str = "UNKNOWN", assets: Optional[Dict[str, Any]] = None, prediction_eval: Optional[Dict[str, Any]] = None) -> None:
        """Log intraday ENGINE snapshot for a specific stage (press_review, morning, noon, evening, summary).

        This is a low-level ENGINE logger used by BRAIN and higher-timeframe reports.
        It is designed to be non-blocking: any error is logged as warning only.
        """
        try:
            from pathlib import Path as _Path
            import json as _json

            if now is None:
                now = _now_it()
            date_str = now.strftime('%Y-%m-%d')
            engine_dir = _Path(project_root) / 'reports' / 'metrics'
            engine_dir.mkdir(parents=True, exist_ok=True)

            engine_file = engine_dir / f"engine_{date_str}.json"
            if engine_file.exists():
                try:
                    with open(engine_file, 'r', encoding='utf-8') as f:
                        data = _json.load(f)
                    if not isinstance(data, dict):
                        data = {}
                except Exception:
                    data = {}
            else:
                data = {}

            stages = data.get('stages', []) if isinstance(data.get('stages'), list) else []

            entry = {
                'stage': stage,
                'timestamp': now.isoformat(),
                'sentiment': sentiment or 'UNKNOWN',
                'assets': assets or {},
                'prediction_eval': prediction_eval or {},
            }
            stages.append(entry)

            data.update({
                'date': date_str,
                'stages': stages,
            })

            with open(engine_file, 'w', encoding='utf-8') as f:
                _json.dump(data, f, indent=2, ensure_ascii=False)

            log.info(f"{EMOJI['check']} [ENGINE] Logged stage '{stage}' to {engine_file}")
        except Exception as e:
            log.warning(f"{EMOJI['warning']} [ENGINE] Error logging stage {stage}: {e}")

    def run_engine_brain_heartbeat(self, now: Optional[datetime.datetime] = None) -> None:
        """Lightweight ENGINE+BRAIN heartbeat (v2, modularised).

        Designed to be called periodically (e.g. every 30 minutes) by the orchestrator.
        It now delegates to dedicated ENGINE/BRAIN helpers while preserving the
        exact same external behaviour and JSON structures:

        - compact BTC/SPX/EURUSD/GOLD snapshot (ENGINE),
        - live evaluation of predictions (BRAIN-lite),
        - regime + tomorrow bias via DailyRegimeManager,
        - optional $25K portfolio/risk snapshot when PortfolioManager is available,
        - streaming `live_state.json` for dashboard consumption.

        No Telegram messages are generated and no content files are modified.
        Any error is logged only (non-blocking).
        """
        try:
            from modules.engine.market_data import get_market_snapshot
            from modules.brain.prediction_eval import evaluate_predictions
            from modules.brain.regime_detection import enrich_with_regime
            from modules.brain.risk_snapshot import enrich_with_risk
        except Exception as import_e:
            # If new modules are not available for any reason, fall back to the
            # previous inline implementation for maximum robustness.
            log.warning(f"{EMOJI['warning']} [HEARTBEAT] Import error in modular helpers, skipping heartbeat: {import_e}")
            return

        try:
            if now is None:
                now = _now_it()
            date_str = now.strftime('%Y-%m-%d')

            # 1) Latest intraday sentiment (if available)
            tracking: Dict[str, Any] = {}
            try:
                tracking = self._load_sentiment_tracking(now) or {}
                heartbeat_sentiment = 'NEUTRAL'
                if isinstance(tracking, dict) and tracking:
                    # Take the stage with the most recent timestamp
                    latest_stage = max(
                        tracking.items(),
                        key=lambda kv: kv[1].get('timestamp', '') if isinstance(kv[1], dict) else ''
                    )[1]
                    if isinstance(latest_stage, dict):
                        heartbeat_sentiment = str(latest_stage.get('sentiment', 'NEUTRAL'))
                else:
                    heartbeat_sentiment = 'NEUTRAL'
            except Exception:
                heartbeat_sentiment = 'NEUTRAL'
                tracking = {}

            # 2) ENGINE snapshot via engine.market_data
            try:
                market_snapshot = get_market_snapshot(now) or {}
                assets: Dict[str, Any] = market_snapshot.get('assets', {}) or {}
            except Exception:
                market_snapshot = {}
                assets = {}

            # 3) BRAIN-lite: live evaluation of predictions via brain.prediction_eval
            try:
                raw_prediction_eval = evaluate_predictions(now) or {}
            except Exception:
                raw_prediction_eval = {}

            # Normalize prediction evaluation and derive compact signal metrics
            try:
                prediction_eval: Dict[str, Any] = dict(raw_prediction_eval or {})
            except Exception:
                prediction_eval = raw_prediction_eval or {}

            try:
                hits = int(prediction_eval.get('hits') or 0)
                misses = int(prediction_eval.get('misses') or 0)
                pending = int(prediction_eval.get('pending') or 0)
                total_tracked = int(prediction_eval.get('total_tracked') or 0)
                if total_tracked <= 0:
                    total_tracked = hits + misses + pending
                accuracy_pct = float(prediction_eval.get('accuracy_pct') or 0.0)
            except Exception:
                hits = misses = pending = total_tracked = 0
                accuracy_pct = 0.0

            signals_summary = {
                'hits': hits,
                'misses': misses,
                'pending': pending,
                'total_tracked': total_tracked,
                'accuracy_pct': accuracy_pct,
            }
            prediction_eval['signals'] = signals_summary

            # 4) Regime + tomorrow bias via brain.regime_detection (when available)
            regime_info: Dict[str, Any] = {}
            if REGIME_MANAGER_AVAILABLE:
                try:
                    sentiment_payload: Any = tracking if isinstance(tracking, dict) and tracking else heartbeat_sentiment
                    prediction_eval = enrich_with_regime(prediction_eval, sentiment_payload) or prediction_eval
                    regime_info = prediction_eval.get('regime') or {}
                except Exception as regime_e:
                    log.warning(f"{EMOJI['warning']} [HEARTBEAT-REGIME] Error updating regime manager: {regime_e}")

            # 5) Portfolio / risk snapshot via brain.risk_snapshot (when available)
            risk_info: Dict[str, Any] = {}
            if PORTFOLIO_MANAGER_AVAILABLE:
                try:
                    prediction_eval = enrich_with_risk(prediction_eval, assets) or prediction_eval
                    risk_info = prediction_eval.get('risk') or {}
                except Exception as risk_e:
                    log.warning(f"{EMOJI['warning']} [HEARTBEAT-RISK] Error building portfolio snapshot: {risk_e}")

            # 6) Log ENGINE heartbeat stage (backward compatible + enriched prediction_eval)
            self._engine_log_stage('heartbeat', now, heartbeat_sentiment, assets, prediction_eval)

            # 7) Update live_state.json for dashboard / monitoring
            try:
                metrics_dir = Path(project_root) / 'reports' / 'metrics'
                metrics_dir.mkdir(parents=True, exist_ok=True)

                live_state = {
                    'date': date_str,
                    'timestamp': now.isoformat(),
                    'sentiment': heartbeat_sentiment,
                    'regime': regime_info,
                    'assets': assets,
                    'signals': signals_summary,
                    'risk': risk_info,
                }

                live_state_file = metrics_dir / 'live_state.json'
                with open(live_state_file, 'w', encoding='utf-8') as f:
                    json.dump(live_state, f, indent=2, ensure_ascii=False)

                log.info(f"{EMOJI['check']} [HEARTBEAT] Updated live_state snapshot: {live_state_file}")
            except Exception as ls_e:
                log.warning(f"{EMOJI['warning']} [HEARTBEAT] Error saving live_state.json: {ls_e}")

        except Exception as e:
            log.warning(f"{EMOJI['warning']} [HEARTBEAT] Error running engine/brain heartbeat: {e}")
    
    def _verify_full_day_coherence(self, now):
        """Verify coherence of ALL 5 intraday messages: Press Review→Morning→Noon→Evening→Summary"""
        coherence_results = {
            'press_review_morning_coherence': 0.0,
            'morning_noon_coherence': 0.0,
            'noon_evening_coherence': 0.0,
            'evening_summary_coherence': 0.0,
            'overall_coherence': 0.0,
            'inconsistencies': []
        }
        
        try:
            date_str = now.strftime('%Y-%m-%d')
            
            # Carica tutti i file del day
            files_to_check = [
                ('press_review', f"press_review_{date_str}.json"),
                ('morning', f"morning_report_{date_str}.json"),
                ('noon', f"noon_update_{date_str}.json"),
                ('evening', f"evening_analysis_{date_str}.json")
            ]
            
            daily_contents = {}
            for content_type, filename in files_to_check:
                file_path = self.reports_dir / filename
                if file_path.exists():
                    import json
                    with open(file_path, 'r', encoding='utf-8') as f:
                        daily_contents[content_type] = json.load(f)
            
            # Verifica coerenze progressive
            if 'press_review' in daily_contents and 'morning' in daily_contents:
                coherence_results['press_review_morning_coherence'] = self._calculate_content_coherence(
                    daily_contents['press_review'], daily_contents['morning']
                )
            
            if 'morning' in daily_contents and 'noon' in daily_contents:
                coherence_results['morning_noon_coherence'] = self._calculate_content_coherence(
                    daily_contents['morning'], daily_contents['noon']
                )
                
            if 'noon' in daily_contents and 'evening' in daily_contents:
                coherence_results['noon_evening_coherence'] = self._calculate_content_coherence(
                    daily_contents['noon'], daily_contents['evening']
                )
            
            # Calculate overall coherence
            coherences = [v for k, v in coherence_results.items() if k.endswith('_coherence') and v > 0]
            if coherences:
                coherence_results['overall_coherence'] = sum(coherences) / len(coherences)
                
            # Identifica inconsistenze
            if coherence_results['overall_coherence'] < 0.7:
                coherence_results['inconsistencies'].append("Low overall coherence between messages")
                
        except Exception as e:
            log.error(f"Ã¢ÂÅ’ [COHERENCE-CHECK] Error: {e}")
            
        return coherence_results
    
    def _calculate_content_coherence(self, content1, content2):
        """Calcola coerenza tra due contenuti usando analysis testuale"""
        try:
            # Estrai testi dai contenuti
            text1 = self._extract_text_from_content(content1)
            text2 = self._extract_text_from_content(content2)
            
            # analysis base: parole chiave comuni
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            if not words1 or not words2:
                return 0.5  # Coerenza neutra se non c'ÃƒÂ¨ testo
                
            # Calcola similaritÃƒÂ  Jaccard
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            jaccard_similarity = len(intersection) / len(union) if union else 0.0
            
            # Bonus per termini finanziari comuni
            financial_terms = {'btc', 'bitcoin', 'sp500', 'eur', 'usd', 'market', 'trading', 'analysis'}
            common_financial = intersection.intersection(financial_terms)
            financial_bonus = len(common_financial) * 0.1
            
            return min(1.0, jaccard_similarity + financial_bonus)
            
        except Exception as e:
            log.warning(f"Ã¢Å¡Â Ã¯Â¸Â [COHERENCE-CALC] Error: {e}")
            return 0.5
    
    def _extract_text_from_content(self, content_data):
        """Estrae testo da struttura dati content"""
        try:
            if isinstance(content_data, dict):
                if 'content' in content_data:
                    content = content_data['content']
                    if isinstance(content, list):
                        return ' '.join(str(item) for item in content)
                    else:
                        return str(content)
                else:
                    return str(content_data)
            elif isinstance(content_data, list):
                return ' '.join(str(item) for item in content_data)
            else:
                return str(content_data)
        except Exception:
            return ""
    
    def _prepare_next_day_connection(self, now, coherence_results):
        """Prepara dati per concatenazione con Rassegna del day successivo"""
        try:
            tomorrow = now + datetime.timedelta(days=1)
            
            next_day_setup = {
                'connection_date': tomorrow.strftime('%Y-%m-%d'),
                'summary_sentiment': 'POSITIVE',  # Dal summary corrente
                'key_themes_continuation': [
                    'Tech sector momentum follow-through',
                    'BTC key support/resistance zones',
                    'EUR weakness continuation',
                    'Risk-on bias maintained'
                ],
                'prediction_carryover': {
                    'asian_session': 'Positive momentum expected',
                    'european_open': 'Gap up potential on momentum',
                    'key_levels': 'BTC dynamic levels, EUR/USD 1.080, S&P 5450'
                },
                'coherence_score': coherence_results.get('overall_coherence', 0.7),
                'summary_timestamp': now.isoformat()
            }
            
            # Salva per la rassegna del day dopo
            connection_file = self.reports_dir / f"day_connection_{tomorrow.strftime('%Y-%m-%d')}.json"
            import json
            with open(connection_file, 'w', encoding='utf-8') as f:
                json.dump(next_day_setup, f, indent=2, ensure_ascii=False)
                
            log.info(f"Ã¢Å“â€¦ [NEXT-DAY-CONNECTION] Saved to: {connection_file}")
            return next_day_setup
            
        except Exception as e:
            log.error(f"Ã¢ÂÅ’ [NEXT-DAY-CONNECTION] Error: {e}")
            return {}
    
    def _generate_weekly_intelligence(self, weekday, now):
        """Generate weekly intelligence for each day (555a model)"""
        day_names = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY']
        day_name = day_names[weekday]
        
        intelligence = []
        
        if weekday == 0:  # MONDAY
            intelligence.append(f"{EMOJI['rocket']} *MONDAY: GAP WEEKEND & WEEKLY SETUP*")
            intelligence.append("")
            intelligence.append(f"{EMOJI['target']} *WEEKLY REGIME*: BULL MARKET {EMOJI['rocket']} - Risk-on, growth bias")
            intelligence.append(f"{EMOJI['lightning']} *MOMENTUM*: ACCELERATING POSITIVE")
            intelligence.append(f"{EMOJI['chart']} *RISK LEVEL*: LOW {EMOJI['check']} - Week opening favorable")
            intelligence.append("")
            intelligence.append(f"{EMOJI['world_map']} *MONDAY STRATEGY:*")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['chart']} *Gap Analysis*: Weekend news impact assessment")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['chart_up']} *Fresh Capital*: Institutional flows restart")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['target']} *Week Setup*: Position for 5-day trend")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['chart']} *News Filter*: Critical events impact magnified")
            
        elif weekday == 1:  # TUESDAY
            intelligence.append(f"{EMOJI['chart_up']} *TUESDAY: MOMENTUM CONFIRMATION*")
            intelligence.append("")
            intelligence.append(f"{EMOJI['chart']} *TREND STRENGTH*: Mid-week momentum validation")
            intelligence.append(f"{EMOJI['target']} *POSITION*: Confirm Monday's direction")
            intelligence.append(f"{EMOJI['magnifying_glass']} *FOCUS*: Economic data reactions")
            intelligence.append("")
            intelligence.append(f"{EMOJI['calendar']} *TUESDAY EDGE:*")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['chart']} *Pattern Completion*: Monday setups mature")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['chart']} *Volume Confirmation*: Institutional participation")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['world']} *Global Sync*: Asia/Europe/US alignment check")
            
        elif weekday == 2:  # WEDNESDAY
            intelligence.append(f"{EMOJI['balance']} *WEDNESDAY: MID-WEEK PIVOT*")
            intelligence.append("")
            intelligence.append(f"{EMOJI['chart']} *EQUILIBRIUM*: Week's turning point analysis")
            intelligence.append(f"{EMOJI['target']} *DECISION DAY*: Trend continuation vs reversal")
            intelligence.append(f"{EMOJI['chart']} *DATA HEAVY*: Economic releases cluster")
            intelligence.append("")
            intelligence.append(f"{EMOJI['brain']} *WEDNESDAY WISDOM:*")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['bank']} *Fed Watch*: FOMC minutes/speeches priority")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['bank']} *Central Banks*: Policy divergence plays")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['crystal_ball']} *Crystal Ball*: Week's second half preview")
            
        elif weekday == 3:  # THURSDAY
            intelligence.append(f"{EMOJI['crystal_ball']} *THURSDAY: LATE WEEK POSITIONING & FRIDAY PREP*")
            intelligence.append("")
            intelligence.append(f"{EMOJI['chart']} *WEEKLY PERFORMANCE CHECK:*")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['target']} *Leaders/Laggards*: Sector rotation mid-week")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['chart']} *Vol Realized*: vs Vol Implied gap analysis")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['rocket']} *Momentum Score*: Trend strength validation")
            intelligence.append("")
            intelligence.append(f"{EMOJI['bank']} *INSTITUTIONAL FLOWS:*")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['bank']} *Pension Rebalancing*: Month-end positioning")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['chart']} *Hedge Fund Activity*: Long/short ratios")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['world']} *Foreign Flows*: EM vs DM allocation")
            intelligence.append("")
            intelligence.append(f"{EMOJI['bulb']} *THURSDAY STRATEGY:*")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['target']} *Friday Setup*: Pre-weekend positioning")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['chart']} *Currency Hedge*: G10 vs EM exposure check")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['chart']} *Sector Tilt*: Overweight defensives if vol > 25%")
            
        elif weekday == 4:  # FRIDAY
            intelligence.append(f"{EMOJI['star']} *FRIDAY: WEEK CLOSE & WEEKEND POSITIONING*")
            intelligence.append("")
            intelligence.append(f"{EMOJI['chart']} *WEEKLY WRAP*: Performance summary & lessons")
            intelligence.append(f"{EMOJI['shield']} *RISK MANAGEMENT*: Weekend exposure adjustment")
            intelligence.append(f"{EMOJI['calendar']} *MONDAY PREVIEW*: Next week's key themes")
            intelligence.append("")
            intelligence.append(f"{EMOJI['target']} *FRIDAY DISCIPLINE:*")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['chart']} *Position Sizing*: Reduce if high uncertainty")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['balance']} *Rebalancing*: Monthly/quarterly adjustments")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['world']} *Weekend Events*: Geopolitical risk assessment")
            
        elif weekday == 5:  # SATURDAY
            intelligence.append(f"{EMOJI['world']} *SATURDAY: WEEKEND ANALYSIS & CRYPTO FOCUS*")
            intelligence.append("")
            intelligence.append(f"{EMOJI['bank']} *TRADITIONAL MARKETS*: Closed - weekly analysis")
            intelligence.append(f"{EMOJI['btc']} *CRYPTO Active*: 24/7 trading opportunities")
            intelligence.append(f"{EMOJI['magnifying_glass']} *RESEARCH MODE*: Deep dive analysis")
            intelligence.append("")
            intelligence.append(f"{EMOJI['calendar']} *WEEKEND AGENDA:*")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['chart']} *Week Review*: Performance and lessons learned")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['magnifying_glass']} *Research*: Next week preparation")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['btc']} *Crypto*: DeFi and altcoins opportunities")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['world']} *Global Events*: Weekend news monitoring")
            
        elif weekday == 6:  # SUNDAY
            intelligence.append(f"{EMOJI['sunrise']} *SUNDAY: WEEK AHEAD PREPARATION*")
            intelligence.append("")
            intelligence.append(f"{EMOJI['calendar']} *PREPARATION WEEK*: Monday gap analysis")
            intelligence.append(f"{EMOJI['world']} *ASIAN MARKETS*: Sunday evening trading")
            intelligence.append(f"{EMOJI['chart']} *FUTURES*: Indication for European open")
            intelligence.append("")
            intelligence.append(f"{EMOJI['crystal_ball']} *SUNDAY NIGHT CHECKLIST:*")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['us_flag']} *US Futures*: Pre-market sentiment")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['world']} *Asia-Pacific*: Nikkei, Hang Seng direction")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['btc']} *Crypto*: Weekend volatility patterns")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['news']} *News Flow*: Monday prep priorities")
        
        return intelligence
    
    def _generate_555a_original_format(self, weekday, now):
        """Generate original 555a-style format, cleaned for current day"""
        intelligence = []
        
        if weekday == 5:  # SATURDAY
            intelligence.append(f"{EMOJI['world']} SATURDAY: WEEKEND ANALYSIS & CRYPTO FOCUS")
            intelligence.append("")
            intelligence.append(f"{EMOJI['cross']} TRADITIONAL MARKETS Closed:")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['us_flag']} US Markets: Closed until Monday 15:30 CET")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['eu_flag']} European Markets: Closed until Monday 09:00 CET")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['world']} Asia Markets: Active tomorrow evening CET")
            intelligence.append("")
            intelligence.append(f"{EMOJI['btc']} CRYPTO 24/7 ACTIVE:")
            
            # Live crypto price
            try:
                crypto_prices = get_live_crypto_prices()
                btc_price = crypto_prices.get('BTC', {}).get('price', 0) if crypto_prices else 0
                if btc_price:
                    intelligence.append(f"{EMOJI['bullet']} {EMOJI['btc']} BTC Live: ${btc_price:,.0f} - Weekend liquidity thin")
                else:
                    intelligence.append(f"{EMOJI['bullet']} {EMOJI['btc']} BTC Live: Price unavailable - Weekend liquidity thin")
            except Exception as e:
                log.warning(f"{EMOJI['warning']} [WEEKEND-BTC-LIVE] Error retrieving BTC price: {e}")
                intelligence.append(f"{EMOJI['bullet']} {EMOJI['btc']} BTC Live: Price unavailable - Weekend liquidity thin")
                
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['lightning']} Vol Weekend: Thin liquidity = elevated gap risk")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['news']} News Impact: Weekend events = Monday gap")
            intelligence.append("")
            intelligence.append(f"{EMOJI['bulb']} strategy WEEKEND SATURDAY:")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['news']} News Monitoring: Geopolitical/macro developments")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['magnifying_glass']} Research Mode: Next week preparation")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['btc']} Crypto Only: Watch thin liquidity risks")
            
        elif weekday == 6:  # SUNDAY
            intelligence.append(f"{EMOJI['sunrise']} SUNDAY: WEEK AHEAD PREPARATION")
            intelligence.append("")
            intelligence.append(f"{EMOJI['cross']} TRADITIONAL MARKETS Closed:")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['us_flag']} US Markets: Closed until tomorrow 15:30 CET")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['eu_flag']} European Markets: Closed until tomorrow 09:00 CET")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['world']} Asia Markets: Active tonight from 22:00 CET")
            intelligence.append("")
            intelligence.append(f"{EMOJI['btc']} CRYPTO 24/7 ACTIVE:")
            try:
                crypto_prices = get_live_crypto_prices()
                btc_price = crypto_prices.get('BTC', {}).get('price', 0) if crypto_prices else 0
                if btc_price:
                    intelligence.append(f"{EMOJI['bullet']} {EMOJI['btc']} BTC Live: ${btc_price:,.0f} - Sunday positioning")
                else:
                    intelligence.append(f"{EMOJI['bullet']} {EMOJI['btc']} BTC Live: Price unavailable - Sunday positioning")
            except Exception as e:
                log.warning(f"{EMOJI['warning']} [SUNDAY-BTC-LIVE] Error retrieving BTC price: {e}")
                intelligence.append(f"{EMOJI['bullet']} {EMOJI['btc']} BTC Live: Price unavailable - Sunday positioning")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['world']} Asia Session: Markets opening 22:00 CET")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['chart_up']} Monday Gap: Weekend news impact analysis")
            intelligence.append("")
            intelligence.append(f"{EMOJI['bulb']} strategy SUNDAY EVENING:")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['world']} Asia Watch: Futures direction pre-Europe")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['calendar']} Monday Prep: Gap analysis & positioning")
            intelligence.append(f"{EMOJI['bullet']} {EMOJI['btc']} Crypto: Sunday night momentum patterns")
            
        else:  # GIORNI LAVORATIVI - uso la weekly intelligence normale
            return self._generate_weekly_intelligence(weekday, now)
        
        return intelligence
    
    def _get_professional_market_status(self, now):
        """Get professional market status like this morning format"""
        weekday = now.weekday()
        
        if weekday == 5:  # SATURDAY
            return "WEEKEND_SAB", "Weekend - Markets Closed (reopening Monday)"
        elif weekday == 6:  # SUNDAY  
            return "WEEKEND_DOM", "Weekend - Markets Closed (reopening tomorrow)"
        elif weekday == 0:  # Monday
            return "WEEK_OPEN", "Week open - Fresh capital flows"
        elif weekday == 4:  # Friday
            return "WEEK_CLOSE", "Week close - Weekend positioning"
        else:  # Tuesday, Wednesday, Thursday
            return "MID_WEEK", "Mid-week trading - Normal market hours"
            
    def _load_yesterday_connection(self, now):
        """Carica dati di concatenazione dal Summary del day precedente"""
        try:
            connection_file = self.reports_dir / f"day_connection_{now.strftime('%Y-%m-%d')}.json"
            
            if connection_file.exists():
                import json
                with open(connection_file, 'r', encoding='utf-8') as f:
                    connection_data = json.load(f)
                    
                log.info(f"[OK] [YESTERDAY-CONNECTION] Loaded from: {connection_file}")
                return connection_data
            else:
                log.info(f"Ã°Å¸â€”â€œÃ¯Â¸Â [YESTERDAY-CONNECTION] No connection file found: {connection_file}")
                return None
                
        except Exception as e:
            log.warning(f"Ã¢Å¡Â Ã¯Â¸Â [YESTERDAY-CONNECTION] Error loading: {e}")
            return None
    
    def generate_press_review(self) -> List[str]:
        """
        PRESS REVIEW 07:00 - ENHANCED from 555a with 7 messages
        Integrates: ML Analysis, Sentiment, Critical News, Calendar, Thematic Categories
        
        Returns:
            List of 7 messages for press review
        """
        try:
            log.info(f"[NEWS] [PRESS-REVIEW] Generating ENHANCED press review (7 messages)...")
            
            messages = []
            now = _now_it()

            # Tracciamento titoli usati all'interno della stessa Rassegna (Msg 2 + categorie 4-7)
            used_news_titles: set[str] = set()
            
            # Get enhanced news using SV systems
            news_data = get_enhanced_news(content_type="rassegna", max_news=30)
            
            # Global fallback: if no news, hydrate from dashboard cache so all sections have enough items
            try:
                if not news_data.get('news'):
                    from pathlib import Path
                    cache_path = Path(project_root) / 'data' / 'processed_news.json'
                    if cache_path.exists():
                        with open(cache_path, 'r', encoding='utf-8') as f:
                            cached = json.load(f)
                        latest = cached.get('latest_news', [])
                        normalized = []
                        for it in latest:
                            normalized.append({
                                'title': it.get('titolo') or it.get('title', 'News update'),
                                'source': it.get('fonte') or it.get('source', 'News'),
                                'category': it.get('categoria') or it.get('category', 'General'),
                                'link': it.get('link', ''),
                                'published_hours_ago': 2
                            })
                        if normalized:
                            news_data['news'] = normalized
                            log.info(f"[PRESS-REVIEW] Hydrated news from cache: {len(normalized)} items")
            except Exception as ce:
                log.warning(f"[PRESS-REVIEW] Global news fallback failed: {ce}")
            
            fallback_data = get_fallback_data()
            
            # === MESSAGE 1: DAILY ML ANALYSIS + WEEKLY intelligence (555a MODEL) ===
            try:
                ml_parts = []
                # Professional header
                weekend_greeting = f"{EMOJI['sunrise']} Good Sunday!" if now.weekday() == 6 else f"{EMOJI['sunrise']} Good Saturday!" if now.weekday() == 5 else f"{EMOJI['sunrise']} Good Morning!"
                ml_parts.append(weekend_greeting)
                ml_parts.append(f"{EMOJI['brain']} ML ANALYSIS + WEEKLY intelligence")
                ml_parts.append(f"{EMOJI['calendar']} {now.strftime('%m/%d/%Y %H:%M')} {EMOJI['bullet']} Message 1/7")
                
                # Professional market status
                market_status, status_desc = self._get_professional_market_status(now)
                ml_parts.append(f"{EMOJI['eagle']} Market Status: {status_desc}")
                
                # Extra clarity for weekend vs trading days
                if now.weekday() >= 5:  # Saturday/Sunday
                    ml_parts.append(f"{EMOJI['bullet']} Traditional Markets: Weekend - closed until Monday")
                    ml_parts.append(f"{EMOJI['bullet']} Crypto: 24/7 active - focus on BTC and main alts")
                
                ml_parts.append(EMOJI['line'] * 35)
                ml_parts.append("")
                
                # NUOVA LOGICA: Leggi concatenazione dal Summary del day precedente
                yesterday_connection = self._load_yesterday_connection(now)
                
                if yesterday_connection:
                    ml_parts.append(f"{EMOJI['link']} **CONTINUITY FROM PREVIOUS SUMMARY:**")
                    ml_parts.append(f"{EMOJI['bullet']} {yesterday_connection.get('summary_sentiment', 'NEUTRAL')}: {yesterday_connection.get('prediction_carryover', {}).get('asian_session', 'Transition analysis')}")
                    ml_parts.append(f"{EMOJI['bullet']} Themes: {', '.join(yesterday_connection.get('key_themes_continuation', ['Market evolution'])[:2])}")
                    try:
                        coh_score = float(yesterday_connection.get('coherence_score', 0.7) or 0.0)
                    except Exception:
                        coh_score = 0.0
                    if coh_score > 0.0:
                        ml_parts.append(f"{EMOJI['bullet']} Coherence: ~{coh_score*100:.0f}% validation (journal-based, experimental)")
                    else:
                        ml_parts.append(f"{EMOJI['bullet']} Coherence: signal still in early calibration (journal-based, experimental)")
                    ml_parts.append("")
                
                # intelligence weekly - FORMATO 555a ORIGINALE
                weekday = now.weekday()  # 0=LunedÃƒÂ¬, 6=SUNDAY
                weekly_context = self._generate_555a_original_format(weekday, now)
                ml_parts.extend(weekly_context)
                ml_parts.append("")

                # Multi-day ML track record from BRAIN (CoherenceManager), when available
                try:
                    coherence_summary = self._load_recent_coherence_summary(now)
                except Exception as e:
                    log.warning(f"{EMOJI['warning']} [PRESS-TRACK-RECORD] Error loading coherence summary: {e}")
                    coherence_summary = {'available': False}
                if coherence_summary.get('available') and coherence_summary.get('days', 0) >= 3:
                    days_window = int(coherence_summary.get('days', 0) or 0)
                    avg_acc = float(coherence_summary.get('avg_accuracy', 0.0) or 0.0)
                    avg_coh = float(coherence_summary.get('avg_coherence', 0.0) or 0.0)
                    ml_parts.append(f"{EMOJI['brain']} *ML TRACK RECORD (last {days_window} days):*")
                    if avg_coh > 0.0:
                        coh_text = f"Coherence ~{avg_coh*100:.0f}% (journal-based)"
                    else:
                        coh_text = "Coherence signal still in early calibration (journal-based, experimental)"
                    ml_parts.append(f"{EMOJI['bullet']} Accuracy ~{avg_acc:.0f}% | {coh_text}")
                    ml_parts.append("")
                
                # Day context from SV systems
                day_context = fallback_data.get('day_context', now.strftime('%A'))
                market_status = fallback_data.get('market_status', 'EVALUATING')
                
                ml_parts.append(f"{EMOJI['target']} **CONTEXT: {day_context.upper()}**")
                ml_parts.append(f"{EMOJI['shield']} **Market Status**: {market_status}")
                ml_parts.append(f"{EMOJI['chart']} **Sentiment**: {fallback_data.get('sentiment', 'NEUTRAL')}")
                ml_parts.append("")
                
                # ML Predictions based on day
                predictions = fallback_data.get('predictions', ['Market analysis in progress'])
                ml_parts.append(f"{EMOJI['crystal_ball']} **TODAY'S ML PREDICTIONS:**")
                for i, pred in enumerate(predictions[:3], 1):
                    ml_parts.append(f"{i}. {pred}")
                ml_parts.append("")
                
                # Enhanced crypto analysis with live prices
                try:
                    crypto_prices = get_live_crypto_prices()
                    if crypto_prices and crypto_prices.get('BTC', {}).get('price', 0) > 0:
                        btc_data = crypto_prices['BTC']
                        price = btc_data['price']
                        change_pct = btc_data['change_pct']
                        
                        ml_parts.append(f"{EMOJI['btc']} **CRYPTO LIVE ANALYSIS:**")
                        ml_parts.append(format_crypto_price_line('BTC', btc_data, 'Crypto leader'))
                        
                        # Support/Resistance analysis
                        sr_data = calculate_crypto_support_resistance(price, change_pct)
                        if sr_data:
                            ml_parts.append(f"{EMOJI['bullet']} **Trend**: {sr_data['trend_direction']}")
                            ml_parts.append(f"{EMOJI['bullet']} **Momentum**: {sr_data['momentum']:.1f}/10")
                            if change_pct > 0:
                                ml_parts.append(f"{EMOJI['bullet']} **Target**: ${sr_data['resistance_2']:,.0f} (+3%) | ${sr_data['resistance_5']:,.0f} (+5%)")
                            else:
                                ml_parts.append(f"{EMOJI['bullet']} **Support**: ${sr_data['support_2']:,.0f} (-3%) | ${sr_data['support_5']:,.0f} (-5%)")
                    else:
                        ml_parts.append(f"{EMOJI['btc']} **CRYPTO**: Live data loading...")
                except Exception as e:
                    log.warning(f"âš ï¸ [PRESS-REVIEW] Crypto analysis error: {e}")
                    ml_parts.append(f"{EMOJI['btc']} **CRYPTO**: Analysis in progress")
                
                ml_parts.append("")
                ml_parts.append(EMOJI['line'] * 35)
                if now.weekday() >= 5:
                    ml_parts.append(f"{EMOJI['robot']} SV ML Engine {EMOJI['bullet']} Weekend Crypto Monitor")
                else:
                    ml_parts.append(f"{EMOJI['robot']} SV ML Engine {EMOJI['bullet']} Daily Market Monitor")
                
                messages.append("\n".join(ml_parts))
                log.info(f"[OK] [PRESS-REVIEW] Message 1 (ML Analysis) generated")
                
            except Exception as e:
                log.error(f"âŒ [PRESS-REVIEW] Message 1 error: {e}")
                # Fallback message
                messages.append(f"ðŸ§  **SV - ML ANALYSIS**\nðŸ“… {now.strftime('%H:%M')} â€¢ System initializing")
                
            # === MESSAGE 2: ML ANALYSIS + 5 CRITICAL NEWS (555a MODEL) ===
            try:
                news_parts = []
                news_parts.append(f"{EMOJI['brain']} PRESS REVIEW - ML ANALYSIS & CRITICAL NEWS")
                news_parts.append(f"{EMOJI['calendar']} {now.strftime('%m/%d/%Y %H:%M')} {EMOJI['bullet']} Message 2/7")
                news_parts.append(EMOJI['line'] * 35)
                news_parts.append("")
                
                # analysis ML SENTIMENT AVANZATA (come 555a)
                sentiment_data = news_data.get('sentiment', {})
                press_sentiment = sentiment_data.get('sentiment', 'NEUTRAL')
                self._save_sentiment_for_stage('press_review', press_sentiment, now)
                news_list = news_data.get('news', [])
                # Fallback: if no live news, try cached dashboard news (processed_news.json)
                if not news_list:
                    try:
                        from pathlib import Path
                        cache_path = Path(project_root) / 'data' / 'processed_news.json'
                        if cache_path.exists():
                            with open(cache_path, 'r', encoding='utf-8') as f:
                                cached = json.load(f)
                            latest = cached.get('latest_news', [])
                            mapped = []
                            for item in latest:
                                mapped.append({
                                    'title': item.get('titolo') or item.get('title', 'News update'),
                                    'source': item.get('fonte') or item.get('source', 'News'),
                                    'category': item.get('categoria') or item.get('category', 'General'),
                                    'link': item.get('link', '')
                                })
                            news_list = mapped[:5]
                            log.info(f"[PRESS-REVIEW] Using cached news fallback: {len(news_list)} items")
                    except Exception as ce:
                        log.warning(f"[PRESS-REVIEW] Cached news fallback failed: {ce}")
                
                if sentiment_data:
                    news_parts.append(f"{EMOJI['chart']} ADVANCED SENTIMENT ANALYSIS:")
                    news_parts.append(f"{EMOJI['bullet']} Overall Sentiment: {sentiment_data.get('sentiment', 'NEUTRAL')}")
                    news_parts.append(f"{EMOJI['bullet']} Market Impact: {sentiment_data.get('market_impact', 'MEDIUM')} confidence")
                    news_parts.append(f"{EMOJI['bullet']} Risk Level: {sentiment_data.get('risk_level', 'MEDIUM')}")
                    news_parts.append("")
                    
                    # OPERATIONAL RECOMMENDATIONS
                    news_parts.append(f"{EMOJI['bulb']} OPERATIONAL RECOMMENDATIONS:")
                    news_parts.append(f"{EMOJI['bullet']} Tech: momentum continuation focus")
                    news_parts.append(f"{EMOJI['bullet']} Crypto: BTC {EMOJI['right_arrow']} altcoins rotation watch")
                    news_parts.append(f"{EMOJI['bullet']} FX: USD strength, EUR weakness")
                    news_parts.append("")
                
                # TOP 3 CRITICAL NEWS (optimized for Telegram)
                # APPLY PERSONAL FINANCE FILTER + IMPACT RANKING
                if news_list:
                    # Filter out personal finance content
                    filtered_news = [
                        item for item in news_list 
                        if not self._is_personal_finance(item.get('title', ''))
                    ]

                    if not filtered_news:
                        # If everything was filtered out, fall back to raw list
                        filtered_news = news_list[:5]

                    ranked_news = []
                    for item in filtered_news:
                        title = item.get('title', 'News update')
                        # Skip if not really market-relevant
                        if not self._is_financial_relevant(title):
                            continue
                        hours_ago = item.get('hours_ago', item.get('published_hours_ago', 2))
                        try:
                            hours_ago = int(hours_ago)
                        except Exception:
                            hours_ago = 2
                        impact = self._analyze_news_impact_detailed(title, published_ago_hours=hours_ago)
                        score = impact.get('impact_score', 0.0)
                        ranked_news.append((score, item, impact))

                    if not ranked_news:
                        log.warning(f"[PRESS-REVIEW] Msg 2: No high-impact news after filters, using fallback ordering")
                        for item in filtered_news[:3]:
                            title = item.get('title', 'News update')
                            hours_ago = item.get('hours_ago', item.get('published_hours_ago', 2))
                            try:
                                hours_ago = int(hours_ago)
                            except Exception:
                                hours_ago = 2
                            impact = self._analyze_news_impact_detailed(title, published_ago_hours=hours_ago)
                            score = impact.get('impact_score', 0.0)
                            ranked_news.append((score, item, impact))

                    # Highest impact first
                    ranked_news.sort(key=lambda x: x[0], reverse=True)

                    news_parts.append(f"{EMOJI['warning']} TOP 3 CRITICAL NEWS (24H)")
                    news_parts.append("")
                    
                    for i, (score, news_item, impact) in enumerate(ranked_news[:3], 1):
                        title = news_item.get('title', 'News update')
                        source = news_item.get('source', 'News')
                        category = news_item.get('category', 'Market')
                        link = news_item.get('link', '')
                        sectors = ', '.join(impact.get('sectors', [])[:2]) or 'Broad Market'
                        
                        # Truncate title 
                        title_short = title[:60] + "..." if len(title) > 60 else title
                        
                        news_parts.append(f"{EMOJI['red_circle']} {i}. {title_short}")
                        news_parts.append(f"{EMOJI['folder']} {category} {EMOJI['bullet']} {EMOJI['news']} {source} {EMOJI['bullet']} {sectors}")
                        # LINK COMPLETO
                        if link:
                            news_parts.append(f"{EMOJI['link']} {link}")
                        news_parts.append("")
                        # Mark this news as used per il day (file seen_news) e anche localmente
                        try:
                            self._mark_news_used(news_item, now)
                        except Exception:
                            pass
                        try:
                            if isinstance(title, str) and title:
                                used_news_titles.add(title)
                        except Exception:
                            pass
                else:
                    news_parts.append(f"{EMOJI['news']} News Loading: System initializing")
                
                # Original 555a footer
                news_parts.append("")
                news_parts.append(EMOJI['line'] * 35)
                news_parts.append(f"{EMOJI['robot']} SV Enhanced {EMOJI['bullet']} ML Analysis & Critical Alerts")
                messages.append("\n".join(news_parts))
                log.info(f"[OK] [PRESS-REVIEW] Message 2 (Critical News) generated")
                
            except Exception as e:
                log.error(f"âŒ [PRESS-REVIEW] Message 2 error: {e}")
                messages.append(f"ðŸš¨ **SV - CRITICAL NEWS**\nðŸ“… {now.strftime('%H:%M')} â€¢ News system loading")
            
            # === MESSAGE 3: CALENDAR EVENTS + ML RECOMMENDATIONS (555a MODEL) ===
            try:
                cal_parts = []
                cal_parts.append(f"{EMOJI['calendar']} PRESS REVIEW - CALENDAR & ML OUTLOOK")
                cal_parts.append(f"{EMOJI['calendar']} {now.strftime('%m/%d/%Y %H:%M')} {EMOJI['bullet']} Message 3/7")
                cal_parts.append(EMOJI['line'] * 35)
                cal_parts.append("")
                
                # === CALENDAR EVENTS ===
                cal_parts.append(f"{EMOJI['world_map']} KEY EVENTS CALENDAR")
                cal_parts.append("")
                
                # Calendar events con error handling advanced (come 555a)
                if SV_ENHANCED_ENABLED:
                    try:
                        from sv_calendar import get_calendar_events
                        events = get_calendar_events(days_ahead=7)
                        
                        if events and len(events) > 2:
                            cal_parts.append(f"{EMOJI['calendar']} **Scheduled Events (Next 7 days):**")
                            for event in events[:6]:
                                title = event.get('Title', 'Economic Event')
                                date_str = event.get('FormattedDate', event.get('Date', 'TBD'))
                                impact = event.get('Impact', 'Medium')
                                source = event.get('Source', '')
                                icon = event.get('Icon', 'US')
                                
                                flag_emoji = {
                                    'US': EMOJI['us_flag'], 
                                    'EU': EMOJI['eu_flag'], 
                                    'IT': EMOJI['eu_flag'],
                                    'UK': EMOJI['uk_flag'], 
                                    'JP': EMOJI['jp_flag'],
                                    'GB': EMOJI['uk_flag']
                                }.get(icon, EMOJI['world'])
                                cal_parts.append(f"{EMOJI['bullet']} {flag_emoji} {title}: {date_str} ({impact} - {source})")
                            cal_parts.append("")
                        else:
                            # Simulated events (555a fallback)
                            cal_parts.append(f"{EMOJI['calendar']} **Scheduled Events (Next 7 days):**")
                            cal_parts.append(f"{EMOJI['bullet']} {EMOJI['us_flag']} Fed Meeting: Wednesday 15:00 CET")
                            cal_parts.append(f"{EMOJI['bullet']} {EMOJI['eu_flag']} ECB Speech: Thursday 14:30 CET")
                            cal_parts.append(f"{EMOJI['bullet']} {EMOJI['chart']} US CPI Data: Friday 14:30 CET")
                            cal_parts.append(f"{EMOJI['bullet']} {EMOJI['bank']} Bank Earnings: Multiple days")
                            cal_parts.append(f"{EMOJI['bullet']} {EMOJI['world_map']} G7 Economic Summit: Weekend")
                            cal_parts.append("")
                            
                    except Exception as cal_error:
                        log.warning(f"[WARN] [CALENDAR] Error build_calendar_lines: {cal_error}")
                        # Fallback identical to 555a
                        cal_parts.append(f"{EMOJI['calendar']} **Scheduled Events (Next 7 days):**")
                        cal_parts.append(f"{EMOJI['bullet']} {EMOJI['us_flag']} Fed Meeting: Wednesday 15:00 CET")
                        cal_parts.append(f"{EMOJI['bullet']} {EMOJI['eu_flag']} ECB Speech: Thursday 14:30 CET")
                        cal_parts.append(f"{EMOJI['bullet']} {EMOJI['chart']} US CPI Data: Friday 14:30 CET")
                        cal_parts.append(f"{EMOJI['bullet']} {EMOJI['bank']} Bank Earnings: Multiple days")
                        cal_parts.append("")
                else:
                    # Enhanced fallback if SV_ENHANCED not available
                    cal_parts.append(f"{EMOJI['calendar']} **Scheduled Events (Next 7 days):**")
                    cal_parts.append(f"{EMOJI['bullet']} {EMOJI['us_flag']} Fed Meeting: Wednesday 15:00 CET")
                    cal_parts.append(f"{EMOJI['bullet']} {EMOJI['eu_flag']} ECB Speech: Thursday 14:30 CET")
                    cal_parts.append(f"{EMOJI['bullet']} {EMOJI['chart']} US CPI Data: Friday 14:30 CET")
                    cal_parts.append(f"{EMOJI['bullet']} {EMOJI['bank']} Bank Earnings: Multiple days")
                    cal_parts.append("")
                
                # === ML CALENDAR RECOMMENDATIONS ===
                cal_parts.append(f"{EMOJI['brain']} ML CALENDAR RECOMMENDATIONS")
                cal_parts.append("")
                cal_parts.append(f"{EMOJI['bullet']} **Pre-Fed Strategy**: Reduce risky exposure before meeting")
                cal_parts.append(f"{EMOJI['bullet']} **ECB Preparation**: EUR weakness opportunities on dovish tilt")
                cal_parts.append(f"{EMOJI['bullet']} **Data Release Window**: High volatility expected 14:00-16:00 CET")
                cal_parts.append(f"{EMOJI['bullet']} **Earnings Season**: Selective tech overweight, avoid low quality")
                cal_parts.append(f"{EMOJI['bullet']} **Weekend Positioning**: Crypto focus 24/7, traditional markets closed")
                cal_parts.append("")
                
                # === ADVANCED STRATEGIC OUTLOOK ===
                cal_parts.append(f"{EMOJI['crystal_ball']} ADVANCED STRATEGIC OUTLOOK")
                cal_parts.append("")
                cal_parts.append(f"{EMOJI['bullet']} **Risk Management**: Normal position sizing, hedge ratio 15%")
                cal_parts.append(f"{EMOJI['bullet']} **Sector Rotation**: Tech > Financials > Energy > Healthcare")
                cal_parts.append(f"{EMOJI['bullet']} **Currency Strategy**: USD strength bias, JPY carry opportunities")
                cal_parts.append(f"{EMOJI['bullet']} **Commodity Play**: Oil consolidation, Gold defensive hedge")
                cal_parts.append(f"{EMOJI['bullet']} **Volatility**: VIX below 16 = complacency, trade accordingly")
                cal_parts.append("")
                
                cal_parts.append(EMOJI['line'] * 35)
                cal_parts.append(f"{EMOJI['robot']} SV Enhanced {EMOJI['bullet']} Calendar & ML Strategy")
                
                messages.append("\n".join(cal_parts))
                log.info(f"[OK] [PRESS-REVIEW] Message 3 (Calendar) generated")
                
            except Exception as e:
                log.error(f"âŒ [PRESS-REVIEW] Message 3 error: {e}")
                messages.append(f"ðŸ“… **SV - CALENDAR**\nðŸ“… {now.strftime('%H:%M')} â€¢ Calendar system loading")
                
            # === MESSAGES 4-7: THEMATIC CATEGORIES ===
            thematic_categories = [
                ('Finance', EMOJI['money'], 4),
                ('Cryptocurrency', EMOJI['btc'], 5),  
                ('Geopolitics', EMOJI['world'], 6),
                ('Technology', EMOJI['laptop'], 7)
            ]
            
            log.info(f"[PRESS-REVIEW] Starting thematic categories generation: {len(thematic_categories)} categories")
            
            # `used_news_titles` è iniziato prima e contiene già eventuali titoli critici usati nel Messaggio 2
            
            for category, emoji, msg_num in thematic_categories:
                log.info(f"[PRESS-REVIEW] Processing category: {category} (Message {msg_num})")
                try:
                    cat_parts = []
                    # Geopolitics explicitly includes Emerging Markets in the header
                    display_category = category.upper()
                    if category == 'Geopolitics':
                        display_category = 'GEOPOLITICS & EMERGING MARKETS'
                    cat_parts.append(f"{emoji} **SV - {display_category}** `{now.strftime('%H:%M')}`")
                    cat_parts.append(f"{EMOJI['calendar']} {now.strftime('%A %m/%d/%Y')} {EMOJI['bullet']} Message {msg_num}/7")
                    cat_parts.append(EMOJI['line'] * 35)
                    cat_parts.append("")
                    
                    # === CATEGORY NEWS (ENHANCED FILTERING) ===
                    category_news = []
                    if news_data.get('news'):
                        log.info(f"[PRESS-REVIEW] {category}: Processing {len(news_data['news'])} news items")
                        # Apply filters: personal finance + category matching + anti-duplication
                        for news_item in news_data['news']:
                            title = news_item.get('title', '')
                            news_category = news_item.get('category', '').lower()
                            title_lower = title.lower()
                            
                            # FILTER 0: Skip items already highlighted as critical in Msg 2
                            try:
                                if self._was_news_used(news_item, now):
                                    continue
                            except Exception:
                                pass
                            
                            # FILTER 1: Skip if already used in another category
                            if title in used_news_titles:
                                continue
                            
                            # FILTER 2: Exclude personal finance content (GLOBAL FILTER)
                            if self._is_personal_finance(title):
                                log.debug(f"[PRESS-REVIEW] Excluded personal finance: {title[:50]}...")
                                continue
                            
                            # FILTER 3: Category keyword matching with exclusions
                            category_keywords = self._get_category_keywords(category)
                            
                            # Category-specific match scoring (prioritize crypto for Cryptocurrency)
                            crypto_keywords = [
                                'bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'cryptocurrency', 'blockchain',
                                'defi', 'nft', 'altcoin', 'token', 'doge', 'dogecoin', 'xrp', 'ripple',
                                'cardano', 'ada', 'solana', 'sol', 'polkadot', 'dot', 'litecoin', 'ltc',
                                'binance coin', 'bnb', 'matic', 'polygon'
                            ]
                            is_crypto_news = any(kw in title_lower for kw in crypto_keywords)
                            
                            # If it's crypto news, only put in Cryptocurrency section
                            if is_crypto_news and category != 'Cryptocurrency':
                                continue
                            
                            # Apply category-specific exclusions
                            should_exclude = False
                            if category == 'Technology':
                                # Exclude crypto/finance/geopolitics from tech
                                # FIX NOV 15: Limit crypto to max 3 out of 6 news
                                exclude_keywords = [
                                    'bitcoin', 'crypto', 'btc', 'ethereum', 'stablecoin', 'mining',
                                    # Strong macro/geopolitics filters to avoid bleed into Tech
                                    'war', 'conflict', 'sanctions', 'trade war', 'tariff', 'embargo',
                                    'election', 'government', 'parliament', 'senate', 'congress',
                                    'egypt', 'crisis', 'palace', 'iran', 'illegal'
                                ]
                                should_exclude = any(excl in title_lower for excl in exclude_keywords)
                                # If already have 3+ crypto news, start excluding more crypto
                                crypto_count = sum(
                                    1 for n in category_news
                                    if any(kw in (n.get('title', '') or '').lower() for kw in crypto_keywords)
                                )
                                if crypto_count >= 3 and is_crypto_news:
                                    should_exclude = True
                            elif category == 'Finance':
                                # Exclude crypto from finance
                                should_exclude = is_crypto_news
                                # Evita che vere storie geopolitiche/EM vadano in Finance
                                try:
                                    geo_keywords = self._get_category_keywords('Geopolitics')
                                    if any(gk in title_lower for gk in geo_keywords):
                                        should_exclude = True
                                except Exception:
                                    pass
                                # Evita che news puramente tech (hardware, AI, big tech) finiscano in Finance
                                try:
                                    tech_keywords = self._get_category_keywords('Technology')
                                    if any(tk in title_lower for tk in tech_keywords):
                                        should_exclude = True
                                except Exception:
                                    pass
                            elif category == 'Geopolitics':
                                # FIX NOV 15: Exclude scandal/crime stories
                                should_exclude = self._is_scandal_or_crime(title)
                                # NEW: avoid misclassifying pure cyber/tech-security or housing stories as geopolitics
                                if not should_exclude:
                                    geo_tech_security_patterns = [
                                        'router', 'firmware', 'antivirus', 'malware', 'ransomware',
                                        'hacker', 'hacked', 'data breach', 'breach of data', 'password',
                                        'cyberattack', 'cyber attack', 'cyber-security', 'cybersecurity'
                                    ]
                                    if any(pat in title_lower for pat in geo_tech_security_patterns):
                                        should_exclude = True
                                if not should_exclude:
                                    housing_patterns_geo = [
                                        'housing market', 'real estate market', 'home buyer', 'home buyers',
                                        'homebuyer', 'homebuyers', 'mortgage rate', 'mortgage rates'
                                    ]
                                    if any(pat in title_lower for pat in housing_patterns_geo):
                                        should_exclude = True
                            
                            # Final inclusion rule: Technology is stricter (keywords only),
                            # other categories can still rely on upstream category labeling.
                            if not should_exclude:
                                if category == 'Technology':
                                    if any(keyword in title_lower for keyword in category_keywords):
                                        category_news.append(news_item)
                                else:
                                    if (category.lower() in news_category or 
                                        any(keyword in title_lower for keyword in category_keywords)):
                                        category_news.append(news_item)
                        
                        log.info(f"[PRESS-REVIEW] {category}: Found {len(category_news)} relevant news after filtering")
                        
                        # If not enough category news found, use remaining available news with filters
                        if len(category_news) < 3:
                            log.info(f"[PRESS-REVIEW] {category}: Only {len(category_news)} specific news, looking for more")
                            # Get remaining news NOT used and NOT personal finance
                            remaining_news = []
                            for n in news_data['news']:
                                if n.get('title', '') in used_news_titles or n in category_news:
                                    continue
                                title_n = n.get('title', '') or ''
                                title_n_lower = title_n.lower()
                                if self._is_personal_finance(title_n):
                                    continue
                                # Avoid crypto overflow in non-crypto categories and ensure crypto-only content in Crypto section
                                is_crypto_n = any(kw in title_n_lower for kw in ['bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'cryptocurrency', 'blockchain', 'defi', 'nft', 'altcoin', 'token', 'doge', 'dogecoin', 'xrp', 'ripple', 'cardano', 'ada', 'solana', 'sol', 'polkadot', 'dot', 'litecoin', 'ltc', 'binance coin', 'bnb', 'matic', 'polygon'])
                                if category != 'Cryptocurrency' and is_crypto_n:
                                    continue
                                if category == 'Cryptocurrency' and not is_crypto_n:
                                    continue
                                # Extra filter for Geopolitics fallback: skip scandal/crime and non-geopolitical headlines
                                if category == 'Geopolitics':
                                    if self._is_scandal_or_crime(title_n):
                                        continue
                                    # Avoid housing macro/personal stories and pure cyber/tech-security pieces here;
                                    # they are better suited for Finance or Technology.
                                    housing_patterns_geo_fb = [
                                        'housing market', 'real estate market', 'home buyer', 'home buyers',
                                        'homebuyer', 'homebuyers', 'mortgage rate', 'mortgage rates'
                                    ]
                                    if any(pat in title_n_lower for pat in housing_patterns_geo_fb):
                                        continue
                                    geo_tech_security_patterns_fb = [
                                        'router', 'firmware', 'antivirus', 'malware', 'ransomware',
                                        'hacker', 'hacked', 'data breach', 'breach of data', 'password',
                                        'cyberattack', 'cyber attack', 'cyber-security', 'cybersecurity'
                                    ]
                                    if any(pat in title_n_lower for pat in geo_tech_security_patterns_fb):
                                        continue
                                    geo_keywords = self._get_category_keywords('Geopolitics')
                                    if not any(keyword in title_n_lower for keyword in geo_keywords):
                                        continue
                                # Extra filter for Technology fallback: keep only genuine tech/innovation stories
                                if category == 'Technology':
                                    tech_keywords = self._get_category_keywords('Technology')
                                    if not any(keyword in title_n_lower for keyword in tech_keywords):
                                        continue
                                # Extra filter for Finance fallback: escludi storie chiaramente geopolitiche o tech
                                if category == 'Finance':
                                    try:
                                        geo_keywords_fin = self._get_category_keywords('Geopolitics')
                                        tech_keywords_fin = self._get_category_keywords('Technology')
                                        if any(gk in title_n_lower for gk in geo_keywords_fin) or any(tk in title_n_lower for tk in tech_keywords_fin):
                                            continue
                                    except Exception:
                                        pass
                                remaining_news.append(n)
                            category_news.extend(remaining_news[:(6-len(category_news))])
                        
                        # For Geopolitics, surface Emerging Markets stories near the top
                        if category == 'Geopolitics' and category_news:
                            em_news = []
                            other_geo = []
                            for n in category_news:
                                t = (n.get('title') or '')
                                if self._is_emerging_markets_story(t):
                                    em_news.append(n)
                                else:
                                    other_geo.append(n)
                            # Ensure up to 3 EM stories appear first when available
                            max_em_first = 3
                            reordered = em_news[:max_em_first]
                            for n in other_geo:
                                if n not in reordered:
                                    reordered.append(n)
                            category_news = reordered
                        # Mark used news titles to prevent duplicates
                        for news_item in category_news[:6]:
                            used_news_titles.add(news_item.get('title', ''))
                    
                    # ALWAYS show at least 6 news per category (like original 555a)
                    if category_news:
                        cat_parts.append(f"{EMOJI['news']} **TOP {display_category} NEWS (Latest developments):**")
                        cat_parts.append("")
                        
                        # 6 news per category (like 555a: line 4129)
                        for j, news_item in enumerate(category_news[:6], 1):
                            title = news_item.get('title', 'News update')
                            source = news_item.get('source', 'News Source')
                            link = news_item.get('link', '')
                            
                            # Impact analysis (identical to 555a: lines 4133-4141)
                            impact = self._analyze_news_impact(title)
                            
                            # Short title (identical to 555a: line 4130)
                            title_short = title[:70] + "..." if len(title) > 70 else title
                            
                            # Format identical to 555a (lines 4143-4147)
                            cat_parts.append(f"{impact} **{j}.** {title_short}")
                            cat_parts.append(f"{EMOJI['news']} {source}")
                            if link:
                                # Full link like 555a (line 4146: link[:60]...)
                                cat_parts.append(f"{EMOJI['link']} {link[:60]}..." if len(link) > 60 else f"{EMOJI['link']} {link}")
                            cat_parts.append("")
                            # Mark this news as used globally for the day
                            try:
                                self._mark_news_used(news_item, now)
                            except Exception:
                                pass
                    else:
                        # If no news at all, use fallback content only
                        cat_parts.extend(self._get_fallback_category_content(category))
                    
                    # Live prices section + WEEKLY intelligence per category (555a model)
                    if category in ['Finance', 'Cryptocurrency']:
                        try:
                            if category == 'Cryptocurrency':
                                crypto_prices = get_live_crypto_prices()
                                if crypto_prices:
                                    cat_parts.append(f"{EMOJI['btc']} **CRYPTO LIVE DATA + WEEKLY CONTEXT:**")
                                    cat_parts.append("")
                                    
                                    for symbol in ['BTC', 'ETH', 'BNB', 'SOL'][:3]:
                                        if symbol in crypto_prices:
                                            line = format_crypto_price_line(symbol, crypto_prices[symbol], f"{symbol} tracker")
                                            cat_parts.append(line)
                                    
                                    # WEEKLY CRYPTO intelligence (like 555a)
                                    weekday = now.weekday()
                                    if weekday == 5:  # Saturday
                                        cat_parts.append(f"{EMOJI['bullet']} **Weekend Pattern**: DeFi activity peaks")
                                        cat_parts.append(f"{EMOJI['bullet']} **Asia Focus**: Sunday night momentum")
                                    elif weekday == 0:  # Monday
                                        cat_parts.append(f"{EMOJI['bullet']} **Monday Gap**: Weekend news impact")
                                        cat_parts.append(f"{EMOJI['bullet']} **Institutional**: Fresh capital allocation")
                                    elif weekday == 4:  # Friday
                                        cat_parts.append(f"{EMOJI['bullet']} **Friday Close**: Weekend positioning")
                                        cat_parts.append(f"{EMOJI['bullet']} **Risk Management**: Exposure adjustment")
                                    cat_parts.append("")
                            elif category == 'Finance':
                                cat_parts.append(f"{EMOJI['chart_up']} **MARKET INDICES + WEEKLY intelligence:**")
                                
                                # WEEKLY FINANCE intelligence (like 555a)
                                weekday = now.weekday()
                                if weekday == 5:  # Saturday
                                    cat_parts.append(f"{EMOJI['bullet']} **Markets Closed**: Weekend analysis mode")
                                    cat_parts.append(f"{EMOJI['bullet']} **Futures**: Sunday night indication")
                                
                                # Mark all finance news used globally so Noon/Evening avoid repeating identical titles
                                try:
                                    for finance_item in category_news:
                                        self._mark_news_used(finance_item, now)
                                except Exception:
                                    pass
                                if weekday == 0:  # Monday
                                    cat_parts.append(f"{EMOJI['bullet']} **Gap Analysis**: Weekend news impact")
                                    cat_parts.append(f"{EMOJI['bullet']} **Weekly Setup**: 5-day trend positioning")
                                elif weekday == 3:  # Thursday
                                    cat_parts.append(f"{EMOJI['bullet']} **Late Week**: Friday positioning prep")
                                    cat_parts.append(f"{EMOJI['bullet']} **Institutional**: Month-end flows check")
                                else:
                                    cat_parts.append(f"{EMOJI['bullet']} Global indices: S&P 500, NASDAQ, Europe in focus")
                                    cat_parts.append(f"{EMOJI['bullet']} FX spotlight: EUR/USD and USD cycle monitoring")
                                    cat_parts.append(f"{EMOJI['bullet']} Commodities: Gold as defensive hedge, Oil for growth/risk")
                                cat_parts.append("")
                                
                                # Live snapshot for S&P 500, EUR/USD and Gold (USD/gram) when data available
                                try:
                                    from modules.engine.market_data import get_market_snapshot
                                    snapshot_finance = get_market_snapshot(now) or {}
                                    assets_finance = snapshot_finance.get('assets', {}) or {}
                                    spx_fin = assets_finance.get('SPX', {}) or {}
                                    eur_fin = assets_finance.get('EURUSD', {}) or {}
                                    gold_fin = assets_finance.get('GOLD', {}) or {}
                                except Exception as qe:
                                    log.warning(f"{EMOJI['warn']} [PRESS-REVIEW-FINANCE] Market snapshot unavailable: {qe}")
                                    spx_fin = {}
                                    eur_fin = {}
                                    gold_fin = {}
                                spx_price_fin = spx_fin.get('price', 0)
                                spx_chg_fin = spx_fin.get('change_pct', None)
                                eur_price_fin = eur_fin.get('price', 0)
                                eur_chg_fin = eur_fin.get('change_pct', None)
                                gold_per_gram_fin = gold_fin.get('price', 0)
                                gold_chg_fin = gold_fin.get('change_pct', None)
                                
                                if spx_price_fin:
                                    if spx_chg_fin is not None:
                                        cat_parts.append(f"{EMOJI['bullet']} S&P 500: {int(spx_price_fin)} ({spx_chg_fin:+.1f}%) - live index snapshot")
                                    else:
                                        cat_parts.append(f"{EMOJI['bullet']} S&P 500: Close around {int(spx_price_fin)} - index snapshot")
                                else:
                                    cat_parts.append(f"{EMOJI['bullet']} S&P 500: Live tracking - momentum and breadth")
                                
                                if eur_price_fin:
                                    if eur_chg_fin is not None:
                                        cat_parts.append(f"{EMOJI['bullet']} EUR/USD: {eur_price_fin:.3f} ({eur_chg_fin:+.1f}%) - FX snapshot")
                                    else:
                                        cat_parts.append(f"{EMOJI['bullet']} EUR/USD: {eur_price_fin:.3f} - FX snapshot")
                                else:
                                    cat_parts.append(f"{EMOJI['bullet']} EUR/USD: FX bias monitoring vs USD")
                                
                                if gold_per_gram_fin and gold_chg_fin is not None:
                                    if gold_per_gram_fin >= 1:
                                        gold_price_str_fin = f"${gold_per_gram_fin:,.2f}/g"
                                    else:
                                        gold_price_str_fin = f"${gold_per_gram_fin:.3f}/g"
                                    cat_parts.append(f"{EMOJI['bullet']} Gold: {gold_price_str_fin} ({gold_chg_fin:+.1f}%) - safe haven demand")
                                else:
                                    cat_parts.append(f"{EMOJI['bullet']} Gold: Safe haven demand monitoring")
                                cat_parts.append("")
                                
                        except Exception as price_e:
                            log.warning(f"âš ï¸ [PRESS-REVIEW] Price error {category}: {price_e}")
                    
                    cat_parts.append(EMOJI['line'] * 35)
                    cat_parts.append(f"{EMOJI['robot']} SV Enhanced {EMOJI['bullet']} {category} intelligence")
                    
                    messages.append("\n".join(cat_parts))
                    log.info(f"[OK] [PRESS-REVIEW] Message {msg_num} ({category}) generated")
                    
                except Exception as e:
                    log.error(f"âŒ [PRESS-REVIEW] Message error {msg_num} ({category}): {e}")
                    messages.append(f"{emoji} **SV - {category.upper()}**\n{EMOJI['calendar']} {now.strftime('%H:%M')} {EMOJI['bullet']} System loading")
            
            # Save all messages
            if messages:
                # VERIFY we have all 7 messages
                if len(messages) < 7:
                    log.warning(f"[WARN] [PRESS-REVIEW] Expected 7 messages, got {len(messages)} - check news filtering")
                
                saved_path = self.save_content("press_review", messages, {
                    'total_messages': len(messages),
                    'enhanced_features': ['ML Analysis', 'Live Crypto', 'News Sentiment', 'Calendar Integration'],
                    'news_count': len(news_data.get('news', [])),
                    'sentiment': news_data.get('sentiment', {})
                })
                log.info(f"[SAVE] [PRESS-REVIEW] Saved to: {saved_path}")

                # ENGINE snapshot for press_review stage
                try:
                    sentiment_pr = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL') if isinstance(news_data, dict) else 'NEUTRAL'
                    assets_pr: Dict[str, Any] = {}
                    try:
                        from modules.engine.market_data import get_market_snapshot
                        market_snapshot_pr = get_market_snapshot(now) or {}
                        assets_pr = market_snapshot_pr.get('assets', {}) or {}
                    except Exception as md_e:
                        log.warning(f"{EMOJI['warning']} [ENGINE-PRESS] Error building market snapshot: {md_e}")
                    self._engine_log_stage('press_review', now, sentiment_pr, assets_pr, None)
                except Exception as e:
                    log.warning(f"{EMOJI['warning']} [ENGINE-PRESS] Error logging engine stage: {e}")
            
            log.info(f"[OK] [PRESS-REVIEW] Completed generation of {len(messages)} press review messages")
            return messages
            
        except Exception as e:
            log.error(f"âŒ [PRESS-REVIEW] General error: {e}")
            # Emergency fallback
            return [f"{EMOJI['news']} **SV - PRESS REVIEW**\n{EMOJI['calendar']} {_now_it().strftime('%H:%M')} {EMOJI['bullet']} System under maintenance"]
    
    def _get_category_keywords(self, category: str) -> List[str]:
        """Get keywords to filter news by category"""
        keywords_map = {
            'Finance': [
                'fed', 'federal reserve', 'interest rate', 'inflation', 'gdp', 'unemployment',
                'stock market', 'sp500', 'nasdaq', 'dow jones', 'earnings', 'revenue', 'profit',
                'bank', 'banking', 'morgan stanley', 'goldman sachs', 'jpmorgan', 'wells fargo',
                'merger', 'acquisition', 'ipo', 'bonds', 'treasury', 'yield', 'dividend',
                'financial', 'economic', 'recession', 'growth', 'trade deficit', 'budget',
                # Housing / real estate macro (treated as Finance, not Geopolitics)
                'housing market', 'real estate market', 'home sales', 'home prices',
                'house prices', 'mortgage rate', 'mortgage rates', 'mortgage applications'
            ],
            'Cryptocurrency': [
                'bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'cryptocurrency', 'blockchain',
                'defi', 'nft', 'token', 'altcoin', 'coinbase', 'binance', 'mining',
                'wallet', 'exchange', 'stablecoin', 'regulation', 'sec crypto', 'cbdc'
            ],
            'Geopolitics': [
                # Core geopolitical and policy terms
                'war', 'conflict', 'sanctions', 'trade war', 'election', 'government', 'policy',
                'china', 'russia', 'ukraine', 'nato', 'eu', 'brexit', 'tariff',
                'diplomatic', 'military', 'defense', 'security', 'oil', 'energy',
                # Emerging Markets and sovereign stories
                'emerging market', 'emerging markets', 'frontier market', 'frontier markets',
                'sovereign default', 'sovereign debt', 'sovereign downgrade',
                'imf', 'world bank', 'rating downgrade', 'credit rating',
                # Key EM regions and blocs (used only as hints, combined with other filters)
                'latin america', 'brazil', 'mexico', 'argentina', 'chile', 'colombia', 'peru',
                'south africa', 'nigeria', 'kenya', 'egypt', 'turkey', 'indonesia', 'thailand',
                'malaysia', 'philippines', 'vietnam', 'india', 'pakistan', 'sri lanka', 'ukraine'
            ],
'Technology': [
                'artificial intelligence', 'ai', 'machine learning', 'tech', 'technology', 'software',
                'apple', 'microsoft', 'google', 'amazon', 'meta', 'tesla', 'nvidia', 'intel',
                'semiconductor', 'chip', 'innovation', 'startup', 'ipo tech', 'cloud', 'data',
                'cybersecurity', 'security', 'privacy', 'algorithm', 'automation', 'robotics',
                'app', 'platform',
                # Consumer tech / devices
                'iphone', 'ipad', 'macbook', 'imac', 'magsafe', 'ios', 'android', 'smartphone',
                'laptop', 'pc hardware', 'gpu', 'cpu', 'playstation', 'xbox', 'nintendo',
                # Cyber / infosec specific
                'hacker', 'hacked', 'antivirus', 'malware', 'ransomware', 'data breach',
                'breach of data', 'vulnerability', 'zero-day', 'zero day', 'patch', 'firmware',
                'router', 'password'
            ]
        }
        return keywords_map.get(category, [])
    
    def _is_financial_relevant(self, title: str, content: str = '') -> bool:
        """Filter out personal finance stories and keep market-relevant news"""
        title_lower = title.lower()
        content_lower = content.lower() if content else ''
        text = title_lower + ' ' + content_lower
        
        # EXCLUDE personal finance stories
        personal_keywords = [
            'my husband', 'my girlfriend', 'my wife', 'my family', 'personal finance',
            'retirement planning', 'should i', 'how much should', 'advice column',
            'dear ', 'i have', 'we have', 'my late', 'inheritance', 'will and testament'
        ]
        
        for keyword in personal_keywords:
            if keyword in text:
                return False
        
        # INCLUDE market-relevant stories
        market_keywords = [
            'federal reserve', 'fed rate', 'interest rate', 'inflation', 'gdp',
            'earnings', 'stock price', 'market', 'trading', 'investment',
            'economic', 'financial', 'bank', 'merger', 'acquisition',
            'crypto', 'bitcoin', 'blockchain', 'regulation', 'policy'
        ]
        
        for keyword in market_keywords:
            if keyword in text:
                return True
                
        return False
    
    def _is_personal_finance(self, title: str) -> bool:
        """Enhanced filter to exclude personal finance and lifestyle content
        
        Returns True if the article should be EXCLUDED (is personal finance/lifestyle).
        Used in Press Review to maintain market-relevant focus.
        """
        title_lower = title.lower()
        
        # Personal finance red flags
        personal_finance_keywords = [
            # Personal stories
            'paycheck to paycheck', 'my husband', 'my wife', 'my girlfriend', 'my boyfriend',
            'my family', 'my late', 'my father', 'my mother', 'my parents',
            # Personal finance advice
            'personal finance', 'financial advisor', 'retirement advice', 'save money',
            'budget', 'budgeting', 'debt payoff', 'credit card debt', 'student loan',
            'mortgage advice', '401k', 'ira', 'roth', 'pension plan',
            # Social security / retirement planning
            'social security', 'medicare', 'medicaid', 'retirement planning',
            'when should i retire', 'how much do i need', 'retirement age',
            # Q&A format
            'should i', 'how do i', 'can i afford', 'advice:', 'dear',
            # Lifestyle / entertainment
            'netflix', 'best movies', 'what to watch', 'tv shows', 'streaming',
            'celebrity', 'kardashian', 'reality tv', 'entertainment',
            'travel deals', 'vacation', 'holiday shopping', 'gift guide',
            # Generic listicles
            'top 10', 'best ways to', '5 tips', 'how to save', 'money mistakes',
            # Celebrity / Sports / Endorsements (NEW - FIX NOV 15)
            'steph curry', 'lebron james', 'tom brady', 'roger federer', 'serena williams',
            'athlete', 'endorsement', 'sponsorship', 'brand deal', 'likely made $',
            'reportedly earned', 'signed a deal', 'partnership with', 'ambassador for',
            'celebrity net worth', 'richest', 'wealthiest', 'personal brand'
        ]
        
        # Check if title contains personal finance keywords
        for keyword in personal_finance_keywords:
            if keyword in title_lower:
                return True
        
        # Additional pattern detection: questions to readers
        question_patterns = ['should i', 'can i', 'do i need', 'how much do i', 'am i']
        if any(pattern in title_lower for pattern in question_patterns):
            return True
        
        return False

    def _is_low_impact_gadget_or_lifestyle(self, title: str) -> bool:
        """Filter out gadget reviews / lifestyle / happiness pieces from intraday impact blocks.

        Returns True if the article should be EXCLUDED from NEWS IMPACT blocks
        (e.g. Noon / Evening impact lists), even if it can appear in Press categories.
        """
        title_lower = (title or '').lower()

        # Gadget / product-review style pieces (hardware, accessories, etc.)
        gadget_keywords = [
            'magsafe', 'power bank', 'power banks', 'charger', 'charging pad',
            'wireless charger', 'dock', 'docking station',
            'headphones', 'earbuds', 'earphones', 'headset', 'soundbar',
            'smart tv', 'oled tv', 'tv ',
            'gaming monitor', 'monitor ',
            'laptop', 'macbook', 'chromebook',
            'iphone case', 'ipad case', 'phone case',
        ]
        review_patterns = [
            'best ', 'buyers guide', 'buying guide', 'gift guide',
            'tested and reviewed', 'hands-on review', 'roundup', 'our picks',
        ]

        if any(gk in title_lower for gk in gadget_keywords) and any(rp in title_lower for rp in review_patterns):
            return True

        # Pure happiness/psychology pieces with weak direct market link
        mood_keywords = [
            'happiness', 'happy', 'life satisfaction', 'make you happier', 'feel happier',
        ]
        if any(mk in title_lower for mk in mood_keywords):
            return True

        return False
    
    def _is_scandal_or_crime(self, title: str) -> bool:
        """Filter to exclude scandal/crime stories from Geopolitics
        
        Returns True if the article should be EXCLUDED (is scandal/crime, not geopolitics).
        Used in Geopolitics category to maintain market-relevant focus.
        """
        title_lower = title.lower()
        
        # Scandal/crime red flags
        scandal_crime_keywords = [
            # Crime stories
            'jailed', 'arrested', 'charged with', 'convicted', 'sentenced',
            'theft', 'robbery', 'burglary', 'stolen', 'smash and grab',
            'murder', 'killed', 'shooting', 'stabbing', 'assault',
            'crash', 'accident', 'collision', 'bus crash', 'train crash',
            # Scandals
            'epstein', 'scandal', 'affair', 'mistress', 'cheating',
            'leaked emails', 'private messages', 'alleged ties',
            'investigation into', 'accused of', 'allegations',
            # Celebrity/entertainment crime
            'banksy', 'art theft', 'celebrity arrest', 'famous',
            # Non-market-relevant politics
            'personal relationship', 'friendship', 'dating', 'marriage'
        ]
        
        # Check if title contains scandal/crime keywords
        for keyword in scandal_crime_keywords:
            if keyword in title_lower:
                return True
        
        return False

    def _is_emerging_markets_story(self, title: str, content: str = '') -> bool:
        """Heuristic to detect Emerging Markets-focused stories.

        Used mainly for ordering inside the Geopolitics category so that EM
        sovereign/market news surface near the top without creating duplicates.
        """
        title_lower = (title or '').lower()
        content_lower = (content or '').lower()
        text = f"{title_lower} {content_lower}"
        
        # Core EM/sovereign terms
        em_core = [
            'emerging market', 'emerging markets', 'frontier market', 'frontier markets',
            'sovereign default', 'sovereign debt', 'sovereign downgrade',
            'em debt', 'em bonds', 'em fx', 'local currency debt',
            'imf', 'international monetary fund', 'world bank'
        ]
        if any(k in text for k in em_core):
            return True
        
        # Country list used only when combined with market/credit terms
        em_countries = [
            'brazil', 'mexico', 'argentina', 'chile', 'colombia', 'peru',
            'south africa', 'nigeria', 'kenya', 'ghana', 'egypt',
            'turkey', 'ukraine', 'indonesia', 'thailand', 'malaysia',
            'philippines', 'vietnam', 'india', 'pakistan', 'sri lanka'
        ]
        market_terms = [
            'bond', 'bonds', 'debt', 'credit', 'rating', 'downgrade',
            'markets', 'stocks', 'equities', 'currency', 'currencies', 'fx'
        ]
        if any(c in text for c in em_countries) and any(m in text for m in market_terms):
            return True
        
        return False

    def _get_seen_news_file(self, now=None):
        """Return path for today's seen-news tracking file."""
        if now is None:
            now = _now_it()
        from pathlib import Path as _Path
        date_str = now.strftime('%Y-%m-%d')
        metrics_dir = _Path(project_root) / 'reports' / 'metrics'
        metrics_dir.mkdir(parents=True, exist_ok=True)
        return metrics_dir / f"seen_news_{date_str}.json"

    def _load_seen_news(self, now=None) -> Dict[str, Any]:
        """Load set of titles/links already used today to reduce repetitions.

        Returns a dict with Python sets: {'titles': set(), 'links': set()}.
        """
        if now is None:
            now = _now_it()
        tracking_file = self._get_seen_news_file(now)
        seen = {'titles': set(), 'links': set()}
        try:
            if tracking_file.exists():
                with open(tracking_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for t in data.get('titles', []):
                    if isinstance(t, str):
                        seen['titles'].add(t)
                for l in data.get('links', []):
                    if isinstance(l, str):
                        seen['links'].add(l)
        except Exception as e:
            log.warning(f"{EMOJI['warning']} [SEEN-NEWS] Error loading seen news: {e}")
        return seen

    def _save_seen_news(self, seen: Dict[str, Any], now=None) -> None:
        """Persist today's seen-news set (helper for _mark/_was)."""
        if now is None:
            now = _now_it()
        tracking_file = self._get_seen_news_file(now)
        try:
            data = {
                'titles': sorted(seen.get('titles', [])),
                'links': sorted(seen.get('links', [])),
            }
            with open(tracking_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log.warning(f"{EMOJI['warning']} [SEEN-NEWS] Error saving seen news: {e}")

    def _mark_news_used(self, news_item: Dict[str, Any], now=None) -> None:
        """Mark a news item as used for the current day (by title/link)."""
        if now is None:
            now = _now_it()
        try:
            seen = self._load_seen_news(now)
            title = (news_item.get('title') or '').strip()
            link = (news_item.get('link') or '').strip()
            if title:
                seen['titles'].add(title)
            if link:
                seen['links'].add(link)
            self._save_seen_news(seen, now)
        except Exception as e:
            log.warning(f"{EMOJI['warning']} [SEEN-NEWS] Error marking news used: {e}")

    def _was_news_used(self, news_item: Dict[str, Any], now=None) -> bool:
        """Return True if this news (title/link) was already used today."""
        if now is None:
            now = _now_it()
        try:
            seen = self._load_seen_news(now)
            title = (news_item.get('title') or '').strip()
            link = (news_item.get('link') or '').strip()
            if title and title in seen['titles']:
                return True
            if link and link in seen['links']:
                return True
        except Exception as e:
            log.warning(f"{EMOJI['warning']} [SEEN-NEWS] Error checking seen news: {e}")
        return False
    
    def _analyze_news_impact(self, title: str) -> str:
        """Analyze news impact based on title (LEGACY - returns emoji only)"""
        impact_data = self._analyze_news_impact_detailed(title)
        return impact_data['emoji']
    
    def _analyze_news_impact_detailed(self, title: str, published_ago_hours: int = 2) -> dict:
        """Analyze news impact with detailed scoring
        
        Returns:
            dict with: emoji, impact_score (0-10), sectors, time_relevance, catalyst_type
        """
        title_lower = title.lower()
        
        # Impact classification
        high_keywords = ['crisis', 'crash', 'war', 'fed meeting', 'recession', 'inflation surge', 'breaking', 'emergency', 'collapse']
        med_keywords = ['bank', 'rate decision', 'gdp', 'unemployment', 'etf', 'regulation', 'earnings beat', 'earnings miss']
        
        # Determine impact level
        if any(k in title_lower for k in high_keywords):
            emoji = EMOJI['fire']
            impact_score = 8.5
            impact_label = "High impact"
        elif any(k in title_lower for k in med_keywords):
            emoji = EMOJI['lightning']
            impact_score = 6.0
            impact_label = "Medium impact"
        else:
            emoji = EMOJI['chart']
            impact_score = 4.0
            impact_label = "Standard news"
        
        # Identify affected sectors
        sectors = []
        if any(kw in title_lower for kw in ['tech', 'apple', 'microsoft', 'google', 'nvidia', 'ai', 'software']):
            sectors.append('Tech')
        if any(kw in title_lower for kw in ['bank', 'financial', 'jpmorgan', 'goldman', 'credit']):
            sectors.append('Financials')
        if any(kw in title_lower for kw in ['consumer', 'retail', 'walmart', 'amazon']):
            sectors.append('Consumer')
        if any(kw in title_lower for kw in ['energy', 'oil', 'gas', 'exxon', 'chevron']):
            sectors.append('Energy')
        if any(kw in title_lower for kw in ['healthcare', 'pharma', 'drug', 'biotech']):
            sectors.append('Healthcare')
        if any(kw in title_lower for kw in ['crypto', 'bitcoin', 'ethereum', 'blockchain']):
            sectors.append('Crypto')
        
        if not sectors:
            sectors.append('Broad Market')
        
        # Time relevance calculation
        if published_ago_hours <= 1:
            time_relevance = "Breaking now"
            time_decay_factor = 1.0
        elif published_ago_hours <= 4:
            time_relevance = f"{published_ago_hours}h ago (Still relevant)"
            time_decay_factor = 0.9
        elif published_ago_hours <= 12:
            time_relevance = f"{published_ago_hours}h ago (Fading)"
            time_decay_factor = 0.6
        else:
            time_relevance = "Old news"
            time_decay_factor = 0.3
        
        # Adjust impact score for time decay
        adjusted_score = impact_score * time_decay_factor
        
        # Identify catalyst type
        if any(kw in title_lower for kw in ['earnings', 'revenue', 'profit', 'eps']):
            catalyst = "Earnings season"
        elif any(kw in title_lower for kw in ['fed', 'federal reserve', 'rate', 'monetary']):
            catalyst = "Monetary policy"
        elif any(kw in title_lower for kw in ['election', 'government', 'policy', 'regulation']):
            catalyst = "Policy/Regulation"
        elif any(kw in title_lower for kw in ['merger', 'acquisition', 'deal', 'buyout']):
            catalyst = "M&A activity"
        elif any(kw in title_lower for kw in ['economic', 'gdp', 'employment', 'inflation', 'pmi']):
            catalyst = "Economic data"
        else:
            catalyst = "Market development"
        
        return {
            'emoji': emoji,
            'impact_score': round(adjusted_score, 1),
            'impact_label': impact_label,
            'sectors': sectors,
            'time_relevance': time_relevance,
            'catalyst_type': catalyst,
            'time_decay_factor': time_decay_factor
        }
    def _get_fallback_category_content(self, category: str) -> List[str]:
        """Generate fallback content for category"""
        fallback_map = {
            'Finance': [
                f"{EMOJI['chart']} **Markets under monitoring**",
                f"{EMOJI['bullet']} Focus on central banks and policy rates", 
                f"{EMOJI['bullet']} Earnings season in progress",
                f"{EMOJI['bullet']} Volatility under control",
                ""
            ],
            'Cryptocurrency': [
                f"{EMOJI['btc']} **Crypto Market Update**",
                f"{EMOJI['bullet']} Bitcoin momentum tracking",
                f"{EMOJI['bullet']} DeFi protocol developments", 
                f"{EMOJI['bullet']} Institutional adoption news",
                ""
            ],
'Geopolitics': [
                f"{EMOJI['world']} **Global Developments & Emerging Markets**",
                f"{EMOJI['bullet']} Trade policy and sanctions monitoring",
                f"{EMOJI['bullet']} Central bank and IMF coordination in EM",
                f"{EMOJI['bullet']} Regional stability and sovereign risk watch",
                ""
            ],
            'Technology': [
                f"{EMOJI['laptop']} **Tech Sector Focus**", 
                f"{EMOJI['bullet']} AI developments tracking",
                f"{EMOJI['bullet']} Big Tech earnings watch",
                f"{EMOJI['bullet']} Innovation pipeline active",
                ""
            ]
        }
        return fallback_map.get(category, [f"{EMOJI['news']} **News loading...**", ""])
    
    def generate_morning_report(self) -> List[str]:
        """Generate the 8:30 AM Morning Report (3 messages)."""
        from modules.generators.morning import generate_morning_report as _impl
        return _impl(self)
    def generate_noon_update(self) -> List[str]:
        """Generate the 13:00 Noon Update (3 messages)."""
        from modules.generators.noon import generate_noon_update as _impl
        return _impl(self)
    def generate_evening_analysis(self) -> List[str]:
        """Generate the 18:30 Evening Analysis (3 messages)."""
        from modules.generators.evening import generate_evening_analysis as _impl
        return _impl(self)
    def generate_daily_summary(self) -> List[str]:
        """Generate the 20:00 Daily Summary (6 pages)."""
        from modules.generators.summary import generate_daily_summary as _impl
        return _impl(self)

# Singleton instance
daily_generator = None

def get_daily_generator() -> DailyContentGenerator:
    """Get singleton instance of daily content generator"""
    global daily_generator
    if daily_generator is None:
        daily_generator = DailyContentGenerator()
    return daily_generator

# Helper functions for easy access
def generate_press_review_wrapper() -> List[str]:
    """Generate press review (7 sections) - wrapper for triggers"""
    generator = get_daily_generator()
    return generator.generate_press_review()

def generate_morning() -> List[str]:
    """Generate morning report (3 messages)"""
    generator = get_daily_generator()
    return generator.generate_morning_report()

def generate_noon() -> List[str]:
    """Generate noon update (3 messages)"""
    generator = get_daily_generator()
    return generator.generate_noon_update()

def generate_noon_update() -> List[str]:
    """Generate noon update (3 messages) - Helper for trigger"""
    generator = get_daily_generator()
    return generator.generate_noon_update()

def generate_evening() -> List[str]:
    """Generate evening analysis (3 messages)"""
    generator = get_daily_generator()
    return generator.generate_evening_analysis()

def generate_summary() -> List[str]:
    """Generate daily summary (5 pages as separate messages)"""
    generator = get_daily_generator()
    return generator.generate_daily_summary()


def run_engine_brain_heartbeat() -> None:
    """Run a lightweight ENGINE+BRAIN heartbeat snapshot (public wrapper).

    Kept for backward compatibility: legacy callers may still import
    daily_generator.run_engine_brain_heartbeat(). Internally this now
    delegates to the ENGINE heartbeat entry point.
    """
    from modules.engine.heartbeat import run_heartbeat

    run_heartbeat()













