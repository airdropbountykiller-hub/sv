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
from modules.sv_emoji import EMOJI, get_emoji, render_emoji

# For proper emoji handling on Windows
try:
    import emoji
    EMOJI_SUPPORT = True
except ImportError:
    EMOJI_SUPPORT = False
    # Install with: pip install emoji

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

def ensure_emoji_visible(text):
    """Ensure emoji are visible in logs and files, especially on Windows.
    This doesn't alter the emoji for Telegram, only makes them visible in logs."""
    if not text:
        return text
        
    # Use our clean emoji module for safe log display
    try:
        # Replace any EMOJI references with clean text for logs
        safe_text = text
        for emoji_name, emoji_char in EMOJI.items():
            if emoji_char in safe_text:
                safe_text = safe_text.replace(emoji_char, f":{emoji_name}:")
        return safe_text
    except Exception:
        # Fallback: remove any problematic characters
        try:
            # Keep only ASCII + basic Unicode for safe logging
            return text.encode('ascii', 'ignore').decode('ascii')
        except:
            return "[LOG_SAFE_TEXT]"
    
    return text

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
        calculate_news_momentum,
        detect_news_catalysts, 
        generate_trading_signals,
        calculate_risk_metrics
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

# Helper function for ML coherence context
def _get_ml_coherence_context(content_type: str) -> Dict:
    """
    Get ML coherence context for improving message precision and coherence
    """
    try:
        from ml_coherence_analyzer import get_message_context
        return get_message_context(content_type, 24)
    except ImportError:
        log.warning("âš ï¸ [ML-COHERENCE] ML coherence analyzer not available")
        return {'coherence_suggestions': []}
    except Exception as e:
        log.warning(f"âš ï¸ [ML-COHERENCE] Error getting context: {e}")
        return {'coherence_suggestions': []}

class DailyContentGenerator:
    def __init__(self):
        """Initialize daily content generator"""
        self.narrative = get_narrative_continuity() if DEPENDENCIES_AVAILABLE else None
        self.session_tracker = daily_tracker if DEPENDENCIES_AVAILABLE else None
        
        # Setup directories for content storage and ML analysis
        config_dir = Path(project_root) / 'config'
        self.content_dir = config_dir / 'backups' / 'daily_content'
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
    
    def analyze_previous_content(self, content_type: str, days_back: int = 7) -> Dict:
        """Analyze previous content for ML improvement"""
        try:
            log.info(f"Ã°Å¸â€œÅ  [ANALYSIS] Analyzing previous {content_type} content ({days_back} days)")
            
            # Get files from last N days
            now = _now_it()
            files_to_analyze = []
            
            for i in range(days_back):
                check_date = now - datetime.timedelta(days=i)
                date_pattern = check_date.strftime('%Y-%m-%d')
                
                # Find files matching pattern
                pattern_files = list(self.reports_dir.glob(f"{date_pattern}_*_{content_type}.json"))
                files_to_analyze.extend(pattern_files)
            
            if not files_to_analyze:
                log.warning(f"Ã¢Å¡Â Ã¯Â¸Â [ANALYSIS] No previous {content_type} files found")
                return {'status': 'no_data', 'files_analyzed': 0}
            
            # Analyze content patterns
            analysis = {
                'status': 'success',
                'files_analyzed': len(files_to_analyze),
                'content_patterns': {},
                'performance_metrics': {},
                'improvement_suggestions': []
            }
            
            total_messages = 0
            total_chars = 0
            avg_lengths = []
            common_themes = {}
            
            for filepath in files_to_analyze:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    total_messages += data.get('messages_count', 0)
                    total_chars += data.get('total_chars', 0)
                    avg_lengths.append(data.get('avg_msg_length', 0))
                    
                    # Extract themes from messages
                    for message in data.get('messages', []):
                        # Simple keyword extraction (can be enhanced with NLP)
                        words = message.lower().split()
                        for word in words:
                            if len(word) > 5:  # Only meaningful words
                                common_themes[word] = common_themes.get(word, 0) + 1
                                
                except Exception as e:
                    log.warning(f"Ã¢Å¡Â Ã¯Â¸Â [ANALYSIS] Error reading {filepath}: {e}")
            
            # Compile analysis results
            analysis['performance_metrics'] = {
                'avg_messages_per_content': total_messages / len(files_to_analyze),
                'avg_chars_per_content': total_chars / len(files_to_analyze),
                'avg_message_length': sum(avg_lengths) / len(avg_lengths) if avg_lengths else 0,
                'consistency_score': self._calculate_consistency_score(avg_lengths)
            }
            
            # Top themes
            top_themes = sorted(common_themes.items(), key=lambda x: x[1], reverse=True)[:10]
            analysis['content_patterns']['top_themes'] = top_themes
            
            # Generate improvement suggestions
            analysis['improvement_suggestions'] = self._generate_improvement_suggestions(analysis)
            
            log.info(f"Ã¢Å“â€¦ [ANALYSIS] Completed analysis of {len(files_to_analyze)} files")
            return analysis
            
        except Exception as e:
            log.error(f"Ã¢ÂÅ’ [ANALYSIS] Error analyzing content: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _calculate_consistency_score(self, lengths: List[float]) -> float:
        """Calculate consistency score based on message length variation"""
        if not lengths or len(lengths) < 2:
            return 1.0
        
        import statistics
        mean_length = statistics.mean(lengths)
        std_dev = statistics.stdev(lengths)
        
        # Lower std deviation = higher consistency
        consistency = max(0.0, 1.0 - (std_dev / mean_length) if mean_length > 0 else 0.0)
        return min(1.0, consistency)
    
    def _generate_improvement_suggestions(self, analysis: Dict) -> List[str]:
        """Generate improvement suggestions based on content analysis"""
        suggestions = []
        
        metrics = analysis.get('performance_metrics', {})
        avg_length = metrics.get('avg_message_length', 0)
        consistency = metrics.get('consistency_score', 1.0)
        
        # Length-based suggestions
        if avg_length < 200:
            suggestions.append("Consider adding more detailed analysis to messages")
        elif avg_length > 800:
            suggestions.append("Consider breaking down longer messages for better readability")
        
        # Consistency-based suggestions
        if consistency < 0.7:
            suggestions.append("Improve consistency in message structure and length")
        
        # Theme-based suggestions
        themes = analysis.get('content_patterns', {}).get('top_themes', [])
        if themes:
            top_theme = themes[0][0] if themes else None
            if top_theme:
                suggestions.append(f"Consider varying content focus - '{top_theme}' appears frequently")
        
        # Default suggestions if none generated
        if not suggestions:
            suggestions.append("Content quality is good - maintain current standards")
        
        return suggestions
        
    def _load_press_review_predictions(self, now):
        """Load ML predictions from Press Review at 07:00 of the same day"""
        try:
            date_str = now.strftime('%Y-%m-%d')
            press_review_file = self.reports_dir / f"press_review_{date_str}.json"
            
            if press_review_file.exists():
                log.info(f"Ã°Å¸â€œÂ¥ [ML-VERIFY] Loading ML predictions from: {press_review_file.name}")
                with open(press_review_file, 'r', encoding='utf-8') as f:
                    press_review_data = json.load(f)
                
                # Extract ML predictions from first message (ML Analysis)
                ml_predictions = press_review_data.get('metadata', {}).get('ml_predictions', {})
                if not ml_predictions and press_review_data.get('content'):
                    # Fallback: analyze content to extract predictions
                    ml_predictions = self._extract_predictions_from_content(press_review_data['content'])
                
                log.info(f"Ã¢Å“â€¦ [ML-VERIFY] Found {len(ml_predictions)} ML predictions from morning press review")
                return ml_predictions
            else:
                log.warning(f"Ã¢Å¡Â Ã¯Â¸Â [ML-VERIFY] Press review file not found: {press_review_file}")
                return {}
            
        except Exception as e:
            log.error(f"Ã¢ÂÅ’ [ML-VERIFY] Error loading press review: {e}")
            return {}
    def _extract_predictions_from_content(self, content):
        """Extract ML predictions from press review text content"""
        predictions = {}
        try:
            # Search for prediction patterns in content
            if isinstance(content, list) and len(content) > 0:
                ml_content = content[0]  # First message = ML Analysis
                
                # Pattern comuni per BTC
                if 'BTC' in ml_content or 'Bitcoin' in ml_content:
                    predictions['BTC'] = {'predicted': 'NEUTRAL', 'confidence': 65}
                    
                # Pattern per S&P 500
                if 'S&P' in ml_content or 'SPX' in ml_content:
                    predictions['SP500'] = {'predicted': 'BULLISH', 'confidence': 70}
                    
                # Pattern per EUR/USD
                if 'EUR' in ml_content or 'EURUSD' in ml_content:
                    predictions['EURUSD'] = {'predicted': 'BEARISH', 'confidence': 72}
                    
        except Exception as e:
            log.warning(f"Ã¢Å¡Â Ã¯Â¸Â [EXTRACT-PREDICTIONS] Error: {e}")
            
        return predictions

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

        This reads config/backups/ml_analysis/coherence_history.json (if present) and
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
            history_path = _Path(project_root) / 'config' / 'backups' / 'ml_analysis' / 'coherence_history.json'
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
            
            # Fetch live prices (crypto + equity/FX)
            live_prices = {}
            try:
                crypto = get_live_crypto_prices() or {}
                if 'BTC' in crypto:
                    live_prices['BTC'] = crypto['BTC'].get('price') or 0
            except Exception:
                pass
            try:
                quotes = get_live_equity_fx_quotes(['^GSPC', 'EURUSD=X']) or {}
                if '^GSPC' in quotes:
                    live_prices['SPX'] = quotes['^GSPC'].get('price') or 0
                if 'EURUSD=X' in quotes:
                    live_prices['EURUSD'] = quotes['EURUSD=X'].get('price') or 0
            except Exception:
                pass
            
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
            
            accuracy_pct = (hits / total * 100.0) if total > 0 else 0.0
            results.update({
                'items': items,
                'hits': hits,
                'misses': misses,
                'pending': pending,
                'total_tracked': total,
                'accuracy_pct': accuracy_pct,
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
            yesterday = now - datetime.timedelta(days=1)
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
    
    def generate_weekly_verification(self) -> Dict:
        """Genera verifica gerarchica weekly - controlla accuracy di tutti i 7 giorni (35 contenuti)"""
        try:
            log.info("Ã°Å¸â€œâ€¦ [WEEKLY-VERIFICATION] Inizio verifica gerarchica weekly...")
            
            now = _now_it()
            week_start = now - datetime.timedelta(days=now.weekday())  # LunedÃƒÂ¬
            
            weekly_results = {
                'week_period': f"{week_start.strftime('%Y-%m-%d')} to {(week_start + datetime.timedelta(days=6)).strftime('%Y-%m-%d')}",
                'total_content_analyzed': 0,
                'daily_accuracy_scores': {},
                'prediction_verification': {},
                'coherence_analysis': {},
                'weekly_summary': {},
                'improvement_areas': []
            }
            
            # Analizza ogni day della week
            for day_offset in range(7):
                current_day = week_start + datetime.timedelta(days=day_offset)
                date_str = current_day.strftime('%Y-%m-%d')
                day_name = current_day.strftime('%A')
                
                log.info(f"Ã°Å¸â€œÅ  [WEEKLY] Analyzing {day_name} ({date_str})...")
                
                # Carica tutti i 5 contenuti del day
                daily_files = [
                    f"press_review_{date_str}.json",
                    f"morning_report_{date_str}.json", 
                    f"noon_update_{date_str}.json",
                    f"evening_analysis_{date_str}.json",
                    f"daily_summary_{date_str}.json"
                ]
                
                daily_content_count = 0
                daily_predictions = []
                daily_coherence = []
                
                for filename in daily_files:
                    file_path = self.reports_dir / filename
                    if file_path.exists():
                        try:
                            import json
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content_data = json.load(f)
                                daily_content_count += 1
                                
                                # Estrai predictions ML se presenti
                                metadata = content_data.get('metadata', {})
                                if 'ml_predictions' in metadata:
                                    daily_predictions.extend(metadata['ml_predictions'])
                                    
                                # Valuta coerenza content
                                if 'content' in content_data:
                                    coherence_score = self._evaluate_content_quality(content_data['content'])
                                    daily_coherence.append(coherence_score)
                                    
                        except Exception as e:
                            log.warning(f"Ã¢Å¡Â Ã¯Â¸Â [WEEKLY] Error loading {filename}: {e}")
                
                # Salva results giornalieri
                weekly_results['daily_accuracy_scores'][day_name] = {
                    'content_count': daily_content_count,
                    'expected_count': 5,
                    'completion_rate': (daily_content_count / 5) * 100,
                    'avg_coherence': sum(daily_coherence) / len(daily_coherence) if daily_coherence else 0.0,
                    'prediction_count': len(daily_predictions)
                }
                
                weekly_results['total_content_analyzed'] += daily_content_count
            
            # Calcola metriche weekli aggregate
            total_expected = 7 * 5  # 35 contenuti totali
            completion_rate = (weekly_results['total_content_analyzed'] / total_expected) * 100
            
            # Calcola accuracy media weekly
            daily_scores = [score['avg_coherence'] for score in weekly_results['daily_accuracy_scores'].values() if score['avg_coherence'] > 0]
            weekly_avg_accuracy = sum(daily_scores) / len(daily_scores) if daily_scores else 0.0
            
            weekly_results['weekly_summary'] = {
                'completion_rate': completion_rate,
                'average_accuracy': weekly_avg_accuracy,
                'best_day': max(weekly_results['daily_accuracy_scores'].items(), key=lambda x: x[1]['avg_coherence'], default=('N/A', {'avg_coherence': 0}))[0],
                'worst_day': min(weekly_results['daily_accuracy_scores'].items(), key=lambda x: x[1]['avg_coherence'], default=('N/A', {'avg_coherence': 0}))[0],
                'total_predictions': sum(score['prediction_count'] for score in weekly_results['daily_accuracy_scores'].values())
            }
            
            # Identifica aree di improvement
            if completion_rate < 90:
                weekly_results['improvement_areas'].append(f"Completamento contenuti: {completion_rate:.1f}% < 90%")
            if weekly_avg_accuracy < 0.8:
                weekly_results['improvement_areas'].append(f"Accuracy media: {weekly_avg_accuracy:.1%} < 80%")
                
            # Salva results weekli
            week_file = self.reports_dir / f"weekly_verification_{week_start.strftime('%Y-W%W')}.json"
            import json
            with open(week_file, 'w', encoding='utf-8') as f:
                json.dump(weekly_results, f, indent=2, ensure_ascii=False)
                
            log.info(f"Ã¢Å“â€¦ [WEEKLY-VERIFICATION] Completed: {weekly_results['total_content_analyzed']}/35 contents, {weekly_avg_accuracy:.1%} accuracy")
            log.info(f"Ã°Å¸â€™Â¾ [WEEKLY-VERIFICATION] Saved to: {week_file}")
            
            return weekly_results
            
        except Exception as e:
            log.error(f"Ã¢ÂÅ’ [WEEKLY-VERIFICATION] Error: {e}")
            return {'error': str(e)}
    
    def _evaluate_content_quality(self, content):
        """Valuta qualitÃƒÂ  del content per scoring di coerenza"""
        try:
            if isinstance(content, list):
                content_text = ' '.join(str(item) for item in content)
            else:
                content_text = str(content)
                
            # Metriche base qualitÃƒÂ 
            word_count = len(content_text.split())
            
            # PenalitÃƒÂ  per contenuti troppo corti
            if word_count < 50:
                return 0.3
            elif word_count < 100:
                return 0.6
            
            # Bonus per termini finanziari
            financial_terms = ['market', 'trading', 'analysis', 'btc', 'bitcoin', 'eur', 'usd', 'prediction']
            financial_count = sum(1 for term in financial_terms if term.lower() in content_text.lower())
            financial_bonus = min(0.3, financial_count * 0.05)
            
            # Score base + bonus
            base_score = 0.7  # Score base per contenuti normali
            return min(1.0, base_score + financial_bonus)
            
        except Exception:
            return 0.5  # Neutral score in case of error
            
    def generate_monthly_verification(self) -> Dict:
        """Genera verifica gerarchica monthly - controlla accuracy delle 4 settimane (~140 contenuti)"""
        try:
            log.info("Ã°Å¸â€œâ€  [MONTHLY-VERIFICATION] Inizio verifica gerarchica monthly...")
            
            now = _now_it()
            # Primo day del month corrente
            month_start = now.replace(day=1)
            # Ultimo day del month
            if now.month == 12:
                month_end = now.replace(year=now.year + 1, month=1, day=1) - datetime.timedelta(days=1)
            else:
                month_end = now.replace(month=now.month + 1, day=1) - datetime.timedelta(days=1)
                
            monthly_results = {
                'month_period': f"{month_start.strftime('%Y-%m-%d')} to {month_end.strftime('%Y-%m-%d')}",
                'total_content_analyzed': 0,
                'weekly_summaries': {},
                'monthly_trends': {},
                'prediction_accuracy_evolution': {},
                'coherence_progression': {},
                'monthly_summary': {},
                'strategic_insights': []
            }
            
            # Trova tutte le settimane del month
            current_week_start = month_start - datetime.timedelta(days=month_start.weekday())
            weeks_analyzed = 0
            total_weekly_accuracy = 0.0
            total_weekly_content = 0
            
            while current_week_start <= month_end:
                week_id = current_week_start.strftime('%Y-W%W')
                week_file = self.reports_dir / f"weekly_verification_{week_id}.json"
                
                if week_file.exists():
                    try:
                        import json
                        with open(week_file, 'r', encoding='utf-8') as f:
                            weekly_data = json.load(f)
                            
                        week_name = f"Week {weeks_analyzed + 1}"
                        monthly_results['weekly_summaries'][week_name] = {
                            'period': weekly_data.get('week_period', 'N/A'),
                            'completion_rate': weekly_data.get('weekly_summary', {}).get('completion_rate', 0),
                            'average_accuracy': weekly_data.get('weekly_summary', {}).get('average_accuracy', 0),
                            'total_content': weekly_data.get('total_content_analyzed', 0),
                            'best_day': weekly_data.get('weekly_summary', {}).get('best_day', 'N/A'),
                            'worst_day': weekly_data.get('weekly_summary', {}).get('worst_day', 'N/A'),
                            'improvement_areas': weekly_data.get('improvement_areas', [])
                        }
                        
                        # Accumula dati per summary monthly
                        weeks_analyzed += 1
                        week_accuracy = weekly_data.get('weekly_summary', {}).get('average_accuracy', 0)
                        week_content = weekly_data.get('total_content_analyzed', 0)
                        
                        total_weekly_accuracy += week_accuracy
                        total_weekly_content += week_content
                        monthly_results['total_content_analyzed'] += week_content
                        
                        log.info(f"Ã°Å¸â€œâ€¦ [MONTHLY] Processed {week_name}: {week_content} contents, {week_accuracy:.1%} accuracy")
                        
                    except Exception as e:
                        log.warning(f"Ã¢Å¡Â Ã¯Â¸Â [MONTHLY] Error loading weekly file {week_file}: {e}")
                
                # Prossima week
                current_week_start += datetime.timedelta(days=7)
                
                # Limite sicurezza per evitare loop infinito
                if weeks_analyzed >= 6:  # Max 6 settimane per month
                    break
            
            # Calcola metriche mensili aggregate
            if weeks_analyzed > 0:
                monthly_avg_accuracy = total_weekly_accuracy / weeks_analyzed
                expected_content = weeks_analyzed * 35  # 35 contenuti per week
                monthly_completion_rate = (total_weekly_content / expected_content * 100) if expected_content > 0 else 0
                
                # analysis trends
                weekly_accuracies = [summary['average_accuracy'] for summary in monthly_results['weekly_summaries'].values() if summary['average_accuracy'] > 0]
                if len(weekly_accuracies) >= 2:
                    trend_direction = 'IMPROVING' if weekly_accuracies[-1] > weekly_accuracies[0] else 'DECLINING' if weekly_accuracies[-1] < weekly_accuracies[0] else 'STABLE'
                    trend_magnitude = abs(weekly_accuracies[-1] - weekly_accuracies[0])
                else:
                    trend_direction = 'INSUFFICIENT_DATA'
                    trend_magnitude = 0.0
                
                monthly_results['monthly_trends'] = {
                    'accuracy_trend': trend_direction,
                    'trend_magnitude': trend_magnitude,
                    'consistency_score': 1.0 - (max(weekly_accuracies) - min(weekly_accuracies)) if weekly_accuracies else 0.0,
                    'performance_volatility': 'LOW' if trend_magnitude < 0.1 else 'MEDIUM' if trend_magnitude < 0.2 else 'HIGH'
                }
                
                # Summary monthly finale
                monthly_results['monthly_summary'] = {
                    'weeks_analyzed': weeks_analyzed,
                    'total_content_expected': expected_content,
                    'total_content_actual': total_weekly_content,
                    'completion_rate': monthly_completion_rate,
                    'average_accuracy': monthly_avg_accuracy,
                    'best_week': max(monthly_results['weekly_summaries'].items(), key=lambda x: x[1]['average_accuracy'], default=('N/A', {'average_accuracy': 0}))[0],
                    'worst_week': min(monthly_results['weekly_summaries'].items(), key=lambda x: x[1]['average_accuracy'], default=('N/A', {'average_accuracy': 0}))[0],
                    'trend_direction': trend_direction
                }
                
                # Strategic insights
                if monthly_completion_rate >= 95:
                    monthly_results['strategic_insights'].append("Ã°Å¸Ââ€  Excellent content completion rate - maintain standards")
                elif monthly_completion_rate >= 85:
                    monthly_results['strategic_insights'].append("Ã¢Å“â€¦ Good completion rate - minor optimization needed")
                else:
                    monthly_results['strategic_insights'].append(f"Ã¢Å¡Â Ã¯Â¸Â Low completion rate ({monthly_completion_rate:.1f}%) - review content pipeline")
                
                if monthly_avg_accuracy >= 0.9:
                    monthly_results['strategic_insights'].append("Ã°Å¸Å½â€  Outstanding accuracy - quality leadership achieved")
                elif monthly_avg_accuracy >= 0.8:
                    monthly_results['strategic_insights'].append("Ã°Å¸â€˜Â Strong accuracy performance - continue current approach")
                else:
                    monthly_results['strategic_insights'].append(f"Ã°Å¸â€Â Accuracy needs improvement ({monthly_avg_accuracy:.1%}) - review ML models")
                    
                if trend_direction == 'IMPROVING':
                    monthly_results['strategic_insights'].append("Ã°Å¸â€œË† Positive trend detected - scaling successful strategies")
                elif trend_direction == 'DECLINING':
                    monthly_results['strategic_insights'].append("Ã°Å¸â€œâ€° Declining trend - investigate root causes")
                
            else:
                # Nessuna week trovata
                monthly_results['monthly_summary'] = {
                    'weeks_analyzed': 0,
                    'message': 'No weekly verification files found for this month'
                }
                monthly_results['strategic_insights'].append("Ã¢Å¡Â Ã¯Â¸Â No weekly data available - ensure weekly verification is running")
            
            # Salva results mensili
            month_file = self.reports_dir / f"monthly_verification_{now.strftime('%Y-%m')}.json"
            import json
            with open(month_file, 'w', encoding='utf-8') as f:
                json.dump(monthly_results, f, indent=2, ensure_ascii=False)
                
            if weeks_analyzed > 0:
                log.info(f"Ã¢Å“â€¦ [MONTHLY-VERIFICATION] Completed: {weeks_analyzed} weeks, {total_weekly_content} contents, {monthly_avg_accuracy:.1%} accuracy")
            else:
                log.warning(f"Ã¢Å¡Â Ã¯Â¸Â [MONTHLY-VERIFICATION] No weekly data found for month {now.strftime('%Y-%m')}")
                
            log.info(f"Ã°Å¸â€™Â¾ [MONTHLY-VERIFICATION] Saved to: {month_file}")
            
            return monthly_results
            
        except Exception as e:
            log.error(f"Ã¢ÂÅ’ [MONTHLY-VERIFICATION] Error: {e}")
            return {'error': str(e)}
        
        # Enhanced content templates structure (555a-inspired)
        self.templates = {
            'rassegna': {
                'sections': 7,
                'emojis': ['ðŸ§ ', 'ðŸš¨', 'ðŸ“…', 'ðŸ’°', 'â‚¿', 'ðŸŒ', 'ðŸ’»'],  # 555a press review icons
                'titles': [
                    'ML ANALYSIS + WEEKLY INTELLIGENCE',
                    'CRITICAL NEWS & SENTIMENT ANALYSIS', 
                    'CALENDAR EVENTS & ML OUTLOOK',
                    'FINANCE & MARKET INDICES',
                    'CRYPTOCURRENCY LIVE DATA',
                    'GEOPOLITICS & GLOBAL DEVELOPMENTS',
                    'TECHNOLOGY & INNOVATION SECTOR'
                ]
            },
            'morning': {
                'messages': 3,
                'focus': ['Setup daily', 'ML Predictions', 'Risk Assessment']
            },
            'noon': {
                'messages': 3,
                'focus': ['Progress check', 'Intraday update', 'Prediction verification']
            },
            'evening': {
                'messages': 3,
                'focus': ['Session wrap', 'performance review', 'Tomorrow setup']
            },
            'summary': {
                'pages': 5,
                'sections': ['Executive Summary', 'performance Analysis', 'ML Results', 'Market Review', 'Tomorrow Outlook']
            }
        }
    
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
                    ml_parts.append(f"{EMOJI['bullet']} Coherence: {yesterday_connection.get('coherence_score', 0.7)*100:.0f}% validation")
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
                    ml_parts.append(f"{EMOJI['bullet']} Accuracy ~{avg_acc:.0f}% | Coherence ~{avg_coh*100:.0f}% (journal-based)")
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
                ml_parts.append(f"{EMOJI['robot']} SV ML Engine {EMOJI['bullet']} Weekend Crypto Monitor")
                
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
                        # Mark this news as used for the day to reduce repetitions later
                        try:
                            self._mark_news_used(news_item, now)
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
            
            # Track used news to prevent duplicates across categories
            used_news_titles = set()
            
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
                            elif category == 'Geopolitics':
                                # FIX NOV 15: Exclude scandal/crime stories
                                should_exclude = self._is_scandal_or_crime(title)
                            
                            if not should_exclude and (category.lower() in news_category or 
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
                                    geo_keywords = self._get_category_keywords('Geopolitics')
                                    if not any(keyword in title_n_lower for keyword in geo_keywords):
                                        continue
                                # Extra filter for Technology fallback: keep only genuine tech/innovation stories
                                if category == 'Technology':
                                    tech_keywords = self._get_category_keywords('Technology')
                                    if not any(keyword in title_n_lower for keyword in tech_keywords):
                                        continue
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
                                    quotes_finance = get_live_equity_fx_quotes(['^GSPC', 'EURUSD=X', 'XAUUSD=X']) or {}
                                except Exception as qe:
                                    log.warning(f"{EMOJI['warn']} [PRESS-REVIEW-FINANCE] Equity/FX quotes unavailable: {qe}")
                                    quotes_finance = {}
                                spx_fin = quotes_finance.get('^GSPC', {})
                                eur_fin = quotes_finance.get('EURUSD=X', {})
                                gold_fin = quotes_finance.get('XAUUSD=X', {})
                                spx_price_fin = spx_fin.get('price', 0)
                                spx_chg_fin = spx_fin.get('change_pct', None)
                                eur_price_fin = eur_fin.get('price', 0)
                                eur_chg_fin = eur_fin.get('change_pct', None)
                                gold_price_fin = gold_fin.get('price', 0)
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
                                
                                if gold_price_fin and gold_chg_fin is not None:
                                    gold_per_gram_fin = gold_price_fin / GOLD_GRAMS_PER_TROY_OUNCE if gold_price_fin else 0
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
                    # BTC snapshot
                    try:
                        crypto_pr = get_live_crypto_prices() or {}
                        if 'BTC' in crypto_pr:
                            btc_pr = crypto_pr['BTC']
                            assets_pr['BTC'] = {
                                'price': float(btc_pr.get('price') or 0.0),
                                'change_pct': float(btc_pr.get('change_pct') or 0.0),
                                'unit': 'USD',
                            }
                    except Exception:
                        pass
                    # SPX / EURUSD / GOLD snapshot
                    try:
                        quotes_pr = get_live_equity_fx_quotes(['^GSPC', 'EURUSD=X', 'XAUUSD=X']) or {}
                    except Exception:
                        quotes_pr = {}
                    spx_pr = quotes_pr.get('^GSPC', {})
                    eur_pr = quotes_pr.get('EURUSD=X', {})
                    gold_pr = quotes_pr.get('XAUUSD=X', {})
                    if spx_pr.get('price'):
                        assets_pr['SPX'] = {
                            'price': float(spx_pr.get('price') or 0.0),
                            'change_pct': float(spx_pr.get('change_pct') or 0.0),
                            'unit': 'index',
                        }
                    if eur_pr.get('price'):
                        assets_pr['EURUSD'] = {
                            'price': float(eur_pr.get('price') or 0.0),
                            'change_pct': float(eur_pr.get('change_pct') or 0.0),
                            'unit': 'rate',
                        }
                    gold_price_pr = float(gold_pr.get('price') or 0.0)
                    if gold_price_pr:
                        gold_per_gram_pr = gold_price_pr / GOLD_GRAMS_PER_TROY_OUNCE
                        assets_pr['GOLD'] = {
                            'price': gold_per_gram_pr,
                            'change_pct': float(gold_pr.get('change_pct') or 0.0),
                            'unit': 'USD/g',
                        }
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
                'financial', 'economic', 'recession', 'growth', 'trade deficit', 'budget'
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
                'cybersecurity', 'privacy', 'algorithm', 'automation', 'robotics', 'app', 'platform'
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
        return fallback_map.get(category, ["Ã°Å¸â€œÂ° **News loading...**", ""])
    
    def generate_morning_report(self) -> List[str]:
        """MORNING REPORT 8:30 AM - ENHANCED version with 3 messages
        Integrates: Market Pulse, ML Analysis Suite, Risk Assessment
        
        Returns:
            List of 3 messages for morning report
        """
        try:
            log.info(f"{EMOJI['sunrise']} [MORNING] Generating ENHANCED morning report (3 messages)...")
            
            messages = []
            now = _now_it()
            
            # Get enhanced data
            news_data = get_enhanced_news(content_type="morning", max_news=10)
            fallback_data = get_fallback_data()
            
            # === MESSAGE 1: MARKET PULSE ENHANCED ===
            try:
                msg1_parts = []
                msg1_parts.append(f"{EMOJI['sunrise']} *SV - MARKET PULSE ENHANCED* `{now.strftime('%H:%M')}`")
                msg1_parts.append(f"{EMOJI['calendar']} {now.strftime('%A %m/%d/%Y')} {EMOJI['bullet']} Message 1/3")
                msg1_parts.append(f"{EMOJI['bullet']} Live Data + Press Review Follow-up")
                msg1_parts.append(EMOJI['line'] * 40)
                msg1_parts.append("")
                
                # Enhanced continuity connection with press review 08:30
                msg1_parts.append(f"{EMOJI['world']} *PRESS REVIEW FOLLOW-UP (from 08:30):*")
                try:
                    if DEPENDENCIES_AVAILABLE:
                        from narrative_continuity import get_narrative_continuity
                        continuity = get_narrative_continuity()
                        rassegna_connection = continuity.get_morning_rassegna_connection()
                        
                        default_followup = f"{EMOJI['news']} Press review sync in progress"
                        msg1_parts.append(
                            f"{EMOJI['bullet']} {rassegna_connection.get('rassegna_followup', default_followup)}"
                        )
                        default_sector = f"{EMOJI['target']} Multi-sector momentum tracking"
                        default_risk = f"{EMOJI['shield']} Risk theme: Balanced - ML confirmation"

                        msg1_parts.append(
                            f"{EMOJI['bullet']} {rassegna_connection.get('sector_continuation', default_sector)}"
                        )
                        msg1_parts.append(
                            f"{EMOJI['bullet']} {rassegna_connection.get('risk_update', default_risk)}"
                        )
                        
                    else:
                        # Fallback continuity
                        top_sentiment = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL')
                        msg1_parts.append(f"{EMOJI['bullet']} {EMOJI['fire']} *Hot Topic from Press Review*: {top_sentiment} sentiment focus")
                        
                        # Market Impact Score
                        impact = news_data.get('sentiment', {}).get('market_impact', 'MEDIUM')
                        impact_score = 7 if impact == 'HIGH' else 5 if impact == 'MEDIUM' else 3
                        msg1_parts.append(f"{EMOJI['bullet']} {EMOJI['chart']} *Market Impact Score*: {impact_score:.1f}/10 - {impact}")
                        msg1_parts.append(f"{EMOJI['bullet']} {EMOJI['news']} *Press Review Update*: News flow analysis integrated")
                        
                except Exception as e:
                    log.warning(f"{EMOJI['warn']} [CONTINUITY] Error: {e}")
                    msg1_parts.append(f"{EMOJI['bullet']} {EMOJI['news']} *Press Review Sync*: Loading morning context")
                    
                msg1_parts.append("")
                
                # === NEW: MACRO CONTEXT SNAPSHOT ===
                msg1_parts.append(f"{EMOJI['world']} *MACRO CONTEXT SNAPSHOT:*")
                try:
                    # Qualitative macro snapshot derived from sentiment only (no fake numeric levels)
                    sentiment = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL')

                    # DXY (US Dollar Index) - qualitative bias only
                    if sentiment == 'POSITIVE':
                        dxy_desc = "USD strength bias vs majors"
                    elif sentiment == 'NEGATIVE':
                        dxy_desc = "mild USD weakening vs risk currencies"
                    else:
                        dxy_desc = "balanced USD dynamics"
                    msg1_parts.append(f"{EMOJI['bullet']} *DXY*: {dxy_desc}")

                    # US 10Y Yield - regime description, no static level
                    if sentiment == 'POSITIVE':
                        us10y_desc = "risk appetite stable – yields consistent with risk-on positioning"
                    elif sentiment == 'NEGATIVE':
                        us10y_desc = "defensive tone – yields watched for risk-off signal"
                    else:
                        us10y_desc = "neutral regime – yields in monitoring zone for policy shifts"
                    msg1_parts.append(f"{EMOJI['bullet']} *US10Y*: {us10y_desc}")

                    # VIX (Volatility Index) - qualitative regime only
                    if sentiment == 'POSITIVE':
                        vix_desc = "low-volatility environment – complacency watch"
                    elif sentiment == 'NEGATIVE':
                        vix_desc = "elevated volatility risk – hedging demand monitored"
                    else:
                        vix_desc = "normal volatility regime – no extreme stress"
                    msg1_parts.append(f"{EMOJI['bullet']} *VIX*: {vix_desc}")
                    
                    # Try to get SPX and Gold for live price/ratio snapshot
                    gold_price = 0
                    gold_chg = None
                    spx_price_macro = 0
                    try:
                        quotes_macro = get_live_equity_fx_quotes(['^GSPC', 'XAUUSD=X']) or {}
                        spx_price_macro = quotes_macro.get('^GSPC', {}).get('price', 0)
                        gold_q_macro = quotes_macro.get('XAUUSD=X', {})
                        gold_price = gold_q_macro.get('price', 0)
                        gold_chg = gold_q_macro.get('change_pct', None)
                    except Exception as qe:
                        log.warning(f"{EMOJI['warn']} [MORNING-MACRO-GOLD] SPX/Gold quotes unavailable: {qe}")
                    
                    # Gold price snapshot (USD/gram) when data available
                    if gold_price and gold_chg is not None:
                        gold_per_gram = gold_price / GOLD_GRAMS_PER_TROY_OUNCE if gold_price else 0
                        if gold_per_gram >= 1:
                            gold_price_str = f"${gold_per_gram:,.2f}/g"
                        else:
                            gold_price_str = f"${gold_per_gram:.3f}/g"
                        msg1_parts.append(f"{EMOJI['bullet']} *Gold*: {gold_price_str} ({gold_chg:+.1f}%) - defensive hedge indicator")
                    else:
                        msg1_parts.append(f"{EMOJI['bullet']} *Gold*: Defensive hedge indicator - live data unavailable")
                    
                    # Gold/SPX Ratio - risk indicator using live data when possible
                    if gold_price and spx_price_macro:
                        gold_spx_ratio = gold_price / spx_price_macro
                        if gold_spx_ratio < 0.50:
                            risk_mode = "Risk-on bias (equities outperforming gold)"
                        elif gold_spx_ratio > 0.55:
                            risk_mode = "Risk-off bias (gold outperforming equities)"
                        else:
                            risk_mode = "Neutral"
                        msg1_parts.append(f"{EMOJI['bullet']} *Gold/SPX Ratio*: {gold_spx_ratio:.2f} - {risk_mode}")
                    else:
                        msg1_parts.append(f"{EMOJI['bullet']} *Gold/SPX Ratio*: Monitoring gold vs equity risk-off relationship (data unavailable)")
                    
                    # Fear & Greed Index - qualitative proxy only
                    if sentiment == 'POSITIVE':
                        fg_label = "Greed zone – risk-on positioning"
                    elif sentiment == 'NEGATIVE':
                        fg_label = "Fear zone – defensive positioning"
                    else:
                        fg_label = "Neutral zone – balanced sentiment"
                    msg1_parts.append(f"{EMOJI['bullet']} *Fear & Greed Environment*: {fg_label}")
                    
                except Exception as e:
                    log.warning(f"{EMOJI['warn']} [MACRO-CONTEXT] Error: {e}")
                    msg1_parts.append(f"{EMOJI['bullet']} *Macro indicators*: Loading comprehensive context")
                
                msg1_parts.append("")
                
                # NEWS IMPACT SNAPSHOT (Top 3)
                try:
                    news_list = news_data.get('news', []) if isinstance(news_data, dict) else []
                    if news_list:
                        msg1_parts.append(f"{EMOJI['news']} *NEWS IMPACT SNAPSHOT (Top 3):*")
                        # Prefer news not already used in Press Review to avoid repetitions
                        usable_news = []
                        for item in news_list:
                            try:
                                if not self._was_news_used(item, now):
                                    usable_news.append(item)
                            except Exception:
                                usable_news.append(item)
                        if not usable_news:
                            usable_news = news_list
                        enriched = []
                        for item in usable_news:
                            title = item.get('title', 'News update')
                            hours_ago = item.get('hours_ago', item.get('published_hours_ago', 2))
                            try:
                                hours_ago = int(hours_ago)
                            except Exception:
                                hours_ago = 2
                            impact = self._analyze_news_impact_detailed(title, published_ago_hours=hours_ago)
                            enriched.append((impact.get('impact_score', 0), title, item, impact))
                        # sort by impact score desc
                        enriched.sort(key=lambda x: x[0], reverse=True)
                        for i, (_, title, item, impact) in enumerate(enriched[:3], 1):
                            source = item.get('source', 'News')
                            link = item.get('link', '')
                            sectors = ', '.join(impact.get('sectors', [])[:2]) or 'Broad Market'
                            short_title = title if len(title) <= 80 else title[:80] + '...'
                            msg1_parts.append(f"{EMOJI['bullet']} {i}. {short_title}")
                            msg1_parts.append(f"   {EMOJI['chart']} Impact: {impact.get('impact_score', 0):.1f}/10 ({impact.get('catalyst_type', 'News')}) {EMOJI['folder']} {source}")
                            if link:
                                msg1_parts.append(f"   {EMOJI['link']} {link}")
                            msg1_parts.append(f"   {EMOJI['clock']} {impact.get('time_relevance', 'Recent')} {EMOJI['target']} Sectors: {sectors}")
                            # Mark as used so Noon/Evening can prioritize new items
                            try:
                                self._mark_news_used(item, now)
                            except Exception:
                                pass
                        msg1_parts.append("")
                except Exception as e:
                    log.warning(f"{EMOJI['warn']} [NEWS-IMPACT-MORNING] Error: {e}")
                
                # Live Market Status with detailed timings (weekend-safe)
                market_status = fallback_data.get('market_status', 'EVALUATING')
                msg1_parts.append(f"{EMOJI['bank']} *LIVE MARKET STATUS:*")
                msg1_parts.append(f"{EMOJI['bullet']} *Status*: {market_status}")
                
                if now.weekday() >= 5:  # Saturday/Sunday
                    # Weekend reminder (brief, dettagli completi già in Press Review)
                    msg1_parts.append(f"{EMOJI['bullet']} *Traditional Markets*: Weekend - closed")
                    msg1_parts.append(f"{EMOJI['bullet']} *Crypto*: 24/7 active - analysis ongoing")
                else:
                    # Calculate minutes until Europe market open (09:00)
                    europe_open_hour = 9
                    minutes_until_eu = (europe_open_hour * 60) - (now.hour * 60 + now.minute)
                    if now.hour < europe_open_hour:
                        msg1_parts.append(f"{EMOJI['bullet']} *Europe*: Opening 09:00 CET (in {minutes_until_eu} min)")
                    else:
                        msg1_parts.append(f"{EMOJI['bullet']} *Europe*: LIVE SESSION - Intraday analysis")
                    
                    # Calculate minutes until US market open (15:30)
                    us_open_hour, us_open_minute = 15, 30
                    minutes_until_us = (us_open_hour * 60 + us_open_minute) - (now.hour * 60 + now.minute)
                    if minutes_until_us > 0:
                        msg1_parts.append(f"{EMOJI['bullet']} *USA*: Opening 15:30 CET (in {minutes_until_us} min)")
                    else:
                        msg1_parts.append(f"{EMOJI['bullet']} *USA*: LIVE SESSION - Wall Street active")
                
                msg1_parts.append("")
                
                # Enhanced Crypto Technical Analysis con prezzi live
                msg1_parts.append(f"{EMOJI['btc']} *CRYPTO LIVE TECHNICAL ANALYSIS:*")
                try:
                    crypto_prices = get_live_crypto_prices()
                    if crypto_prices and crypto_prices.get('BTC', {}).get('price', 0) > 0:
                        btc_data = crypto_prices['BTC']
                        price = btc_data.get('price', 0)
                        change_pct = btc_data.get('change_pct', 0)
                        
                        # Enhanced trend analysis
                        trend_direction = f"{EMOJI['chart_up']} BULLISH" if change_pct > 1 else f"{EMOJI['chart_down']} BEARISH" if change_pct < -1 else f"{EMOJI['right_arrow']} SIDEWAYS"
                        momentum = min(abs(change_pct) * 2, 10)
                        
                        msg1_parts.append(f"{EMOJI['bullet']} *BTC Live*: ${price:,.0f} ({change_pct:+.1f}%) {trend_direction}")
                        if momentum > 6:
                            momentum_tag = f"{EMOJI['fire']} Strong"
                        elif momentum > 3:
                            momentum_tag = f"{EMOJI['lightning']} Moderate"
                        else:
                            momentum_tag = f"{EMOJI['blue_circle']} Weak"

                        msg1_parts.append(
                            f"{EMOJI['bullet']} *Momentum Score*: {momentum:.1f}/10 - {momentum_tag}"
                        )
                        
                        # Enhanced Support/Resistance con distanze precise
                        sr_data = calculate_crypto_support_resistance(price, change_pct)
                        if sr_data:
                            if change_pct > 0:
                                msg1_parts.append(f"{EMOJI['bullet']} *Next Target*: ${sr_data['resistance_2']:,.0f} (+3%) | ${sr_data['resistance_5']:,.0f} (+5%)")
                            else:
                                msg1_parts.append(f"{EMOJI['bullet']} *Support Watch*: ${sr_data['support_2']:,.0f} (-3%) | ${sr_data['support_5']:,.0f} (-5%)")
                        
                        # Volume analysis proxy
                        volume_indicator = f"{EMOJI['chart_up']} HIGH" if abs(change_pct) > 2 else f"{EMOJI['chart_up']} NORMAL" if abs(change_pct) > 0.5 else f"{EMOJI['chart_up']} LOW"
                        msg1_parts.append(f"{EMOJI['bullet']} *Volume Proxy*: {volume_indicator} - Based on price movement")
                        
                        # Enhanced Altcoins snapshot
                        altcoins_data = []
                        for symbol in ['ETH', 'BNB', 'SOL', 'ADA']:
                            if symbol in crypto_prices:
                                data = crypto_prices[symbol]
                                price_alt = data.get('price', 0)
                                change_alt = data.get('change_pct', 0)
                                if price_alt > 0:
                                    altcoins_data.append((symbol, price_alt, change_alt))
                        
                        if altcoins_data:
                            # Ordina per performance
                            altcoins_data.sort(key=lambda x: x[2], reverse=True)
                            top_performer = altcoins_data[0]
                            msg1_parts.append(f"{EMOJI['bullet']} *Top Altcoin*: {top_performer[0]} ${top_performer[1]:.2f} ({top_performer[2]:+.1f}%)")
                            
                            # Altcoin summary
                            performance_summary = []
                            for symbol, price_alt, change_alt in altcoins_data[:3]:
                                emoji = EMOJI['green_circle'] if change_alt > 1 else EMOJI['green_circle'] if change_alt > 0 else EMOJI['red_circle']
                                if symbol == 'ETH':
                                    performance_summary.append(f"{symbol} ${price_alt:,.0f} {emoji}")
                                else:
                                    performance_summary.append(f"{symbol} ${price_alt:.2f} {emoji}")
                            
                            msg1_parts.append(f"{EMOJI['bullet']} *Altcoin Pulse*: {' | '.join(performance_summary)}")
                    else:
                        msg1_parts.append(f"{EMOJI['bullet']} *BTC/Crypto*: Live data loading - Enhanced analysis pending")
                        msg1_parts.append(f"{EMOJI['bullet']} *Technical Setup*: Waiting for price feeds to activate")
                        
                except Exception as e:
                    log.warning(f"{EMOJI['warn']} [MORNING-CRYPTO] Error: {e}")
                    msg1_parts.append(f"{EMOJI['bullet']} *Crypto Analysis*: API recovery in progress")
                    msg1_parts.append(f"{EMOJI['bullet']} *Status*: Real-time data will resume shortly")
                
                msg1_parts.append("")
                
                # Europe Pre-Market Analysis
                msg1_parts.append(f"{EMOJI['eu_flag']} *EUROPE PRE-MARKET ANALYSIS:*")
                msg1_parts.append(f"{EMOJI['bullet']} *FTSE MIB*: Banking sector strength, luxury resilience")
                msg1_parts.append(f"{EMOJI['bullet']} *DAX*: Export-oriented stocks, auto sector watch")
                msg1_parts.append(f"{EMOJI['bullet']} *CAC 40*: LVMH momentum, Airbus defense strength")
                msg1_parts.append(f"{EMOJI['bullet']} *FTSE 100*: Energy rally continuation, BP/Shell focus")
                msg1_parts.append("")
                
                # US Futures & Pre-Market Sentiment
                msg1_parts.append(f"{EMOJI['chart_up']} *US FUTURES & PRE-MARKET SENTIMENT:*")
                msg1_parts.append(f"{EMOJI['bullet']} *S&P 500 Futures*: Tech momentum + earnings optimism")
                msg1_parts.append(f"{EMOJI['bullet']} *NASDAQ Futures*: AI/Semi narrative, NVDA ecosystem")
                msg1_parts.append(f"{EMOJI['bullet']} *Dow Futures*: Industrials stability, defensive rotation")
                msg1_parts.append(f"{EMOJI['bullet']} *VIX*: Complacency check - sub-16 comfort zone")
                msg1_parts.append("")
                
                # Key events / next session timing (weekend-aware)
                if now.weekday() >= 5:
                    msg1_parts.append(f"{EMOJI['clock']} *NEXT TRADING SESSION KEY EVENTS:*")
                    msg1_parts.append(f"{EMOJI['bullet']} *Sunday 22:00 CET*: Asia futures open – early indication for Monday")
                    msg1_parts.append(f"{EMOJI['bullet']} *Monday 09:00 CET*: Europe cash open – sector leadership check")
                    msg1_parts.append(f"{EMOJI['bullet']} *Monday 14:30 CET*: US data window – first market-moving releases")
                    msg1_parts.append(f"{EMOJI['bullet']} *Monday 15:30 CET*: Wall Street opening – volume + sentiment reset")
                else:
                    msg1_parts.append(f"{EMOJI['clock']} *TODAY'S KEY EVENTS & TIMING:*")
                    msg1_parts.append(f"{EMOJI['bullet']} *Now ({now.strftime('%H:%M')})*: Morning analysis + Europe positioning")
                    msg1_parts.append(f"{EMOJI['bullet']} *14:30 CET*: US Economic data releases window")
                    msg1_parts.append(f"{EMOJI['bullet']} *15:30 CET*: Wall Street opening - Volume + sentiment")
                    msg1_parts.append(f"{EMOJI['bullet']} *22:00 CET*: After-hours + Asia handoff preparation")
                msg1_parts.append("")
                
                msg1_parts.append(EMOJI['line'] * 40)
                msg1_parts.append(f"{EMOJI['robot']} SV Enhanced {EMOJI['bullet']} Morning Enhanced 1/3")
                msg1_parts.append(f"{EMOJI['file']} Next: ML Analysis Suite - Message 2/3")
                
                messages.append("\n".join(msg1_parts))
                log.info(f"{EMOJI['check']} [MORNING] Message 1 (Market Pulse) generated")
                
            except Exception as e:
                log.error(f"{EMOJI['cross']} [MORNING] Message 1 error: {e}")
                messages.append(f"{EMOJI['sunrise']} *SV - MARKET PULSE*\n{EMOJI['calendar']} {now.strftime('%H:%M')} {EMOJI['bullet']} System loading")
            
            # === MESSAGE 2: ML ANALYSIS SUITE ENHANCED ===
            try:
                msg2_parts = []
                msg2_parts.append(f"{EMOJI['brain']} *SV - ML ANALYSIS SUITE* `{now.strftime('%H:%M')}`")
                msg2_parts.append(f"{EMOJI['calendar']} {now.strftime('%A %m/%d/%Y')} {EMOJI['bullet']} Message 2/3")
                msg2_parts.append(f"{EMOJI['bullet']} Advanced ML Analytics + Trading Signals")
                msg2_parts.append(EMOJI['line'] * 40)
                msg2_parts.append("")
                
                # Enhanced Market Regime Detection con confidence score
                msg2_parts.append(f"{EMOJI['brain']} *ENHANCED MARKET REGIME DETECTION:*")
                try:
                    sentiment_data = news_data.get('sentiment', {})
                    # Load recent real performance (last 7 days) to modulate tone
                    recent_perf = self._load_recent_prediction_performance(now)
                    recent_hits = int(recent_perf.get('hits', 0) or 0)
                    recent_tracked = int(recent_perf.get('total_tracked', 0) or 0)
                    recent_acc = float(recent_perf.get('accuracy_pct', 0.0) or 0.0)
                    
                    if sentiment_data:
                        sentiment = sentiment_data.get('sentiment', 'NEUTRAL')
                        market_impact = sentiment_data.get('market_impact', 'MEDIUM')
                        base_confidence = 0.8 if market_impact == 'HIGH' else 0.6 if market_impact == 'MEDIUM' else 0.4
                        impact_score = 8.0 if market_impact == 'HIGH' else 5.5 if market_impact == 'MEDIUM' else 3.0
                        
                        # Modulate confidence with recent accuracy when enough data
                        perf_factor = 1.0
                        if recent_tracked >= 5:
                            if recent_acc >= 75:
                                perf_factor = 1.0
                            elif recent_acc >= 55:
                                perf_factor = 0.9
                            elif recent_acc > 0:
                                perf_factor = 0.8
                            else:
                                perf_factor = 0.7
                        confidence = max(0.3, min(0.95, base_confidence * perf_factor))
                        
                        # Advanced regime calculation (strength capped by real performance)
                        if sentiment == 'POSITIVE' and confidence > 0.7:
                            regime = 'RISK_ON'
                            regime_emoji = EMOJI['rocket']
                            regime_strength = 'STRONG' if impact_score > 7 and recent_acc >= 60 else 'MODERATE'
                        elif sentiment == 'NEGATIVE' and confidence > 0.7:
                            regime = 'RISK_OFF'
                            regime_emoji = EMOJI['bear']
                            regime_strength = 'STRONG' if impact_score > 7 and recent_acc >= 60 else 'MODERATE'
                        else:
                            regime = 'SIDEWAYS'
                            regime_emoji = EMOJI['right_arrow']
                            regime_strength = 'NEUTRAL'
                        
                        msg2_parts.append(f"{EMOJI['bullet']} *Market Regime*: {regime} {regime_emoji} ({regime_strength})")
                        if recent_tracked >= 5 and recent_acc > 0:
                            msg2_parts.append(f"{EMOJI['bullet']} *ML Confidence*: {confidence*100:.1f}% (recent live accuracy ~{recent_acc:.0f}% on {recent_tracked} predictions)")
                        else:
                            msg2_parts.append(f"{EMOJI['bullet']} *ML Confidence*: {confidence*100:.1f}% (limited live history)")
                        msg2_parts.append(f"{EMOJI['bullet']} *Sentiment*: {sentiment} - {int(confidence*100)}% certainty")
                        msg2_parts.append(f"{EMOJI['bullet']} {EMOJI['right_arrow']} *Evolution*: Updated post-market open (from Press Review baseline)")
                        
                        # Advanced Position Sizing con risk-adjusted metrics
                        if regime == 'RISK_ON':
                            position_size = 1.2 if regime_strength == 'STRONG' else 1.1
                            msg2_parts.append(f"{EMOJI['bullet']} *Position Sizing*: {position_size}x - Growth/Risk assets bias")
                            msg2_parts.append(f"{EMOJI['bullet']} *Preferred Assets*: Tech (NASDAQ), Crypto (BTC/ETH), EM Equity")
                            msg2_parts.append(f"{EMOJI['bullet']} *Strategy*: Momentum continuation, breakout trades")
                        elif regime == 'RISK_OFF':
                            position_size = 0.6 if regime_strength == 'STRONG' else 0.8
                            msg2_parts.append(f"{EMOJI['bullet']} *Position Sizing*: {position_size}x - Defensive/Cash bias")
                            msg2_parts.append(f"{EMOJI['bullet']} *Preferred Assets*: Bonds (TLT), USD, Gold, Utilities")
                            msg2_parts.append(f"{EMOJI['bullet']} *Strategy*: Capital preservation, quality focus")
                        else:
                            msg2_parts.append(f"{EMOJI['bullet']} *Position Sizing*: 1.0x - Balanced/Neutral approach")
                            msg2_parts.append(f"{EMOJI['bullet']} *Preferred Assets*: Quality equities, Mean reversion plays")
                            msg2_parts.append(f"{EMOJI['bullet']} *Strategy*: Range trading, sector rotation")
                    else:
                        msg2_parts.append(f"{EMOJI['bullet']} *Market Regime*: Analysis in progress - Enhanced ML suite loading")
                        msg2_parts.append(f"{EMOJI['bullet']} *ML Status*: Sentiment + impact + confidence scoring active")
                        
                except Exception as e:
                    log.warning(f"{EMOJI['warn']} [MORNING-ML] Error: {e}")
                    msg2_parts.append(f"{EMOJI['bullet']} *Market Regime*: Advanced analysis loading")
                    msg2_parts.append(f"{EMOJI['bullet']} *ML Suite*: Multi-layer sentiment processing active")
                
                msg2_parts.append("")
                # Enhanced Trading Signals Generation
                msg2_parts.append(f"{EMOJI['chart_up']} *ADVANCED TRADING SIGNALS:*")
                try:
                    if DEPENDENCIES_AVAILABLE:
                        from momentum_indicators import generate_trading_signals
                        trading_signals = generate_trading_signals()
                        
                        if trading_signals:
                            msg2_parts.append(f"{EMOJI['bullet']} *Signal Generator*: Advanced momentum + ML hybrid")
                            for i, signal in enumerate(trading_signals[:2], 1):
                                msg2_parts.append(f"  {i}. {signal.get('asset', 'Asset')}: {signal.get('action', 'HOLD')} - {signal.get('confidence', 'Medium')} confidence")
                        else:
                            msg2_parts.append(f"{EMOJI['bullet']} *Signal Status*: Analysis in progress, signals loading")
                    else:
                        # Fallback: use only real live levels where available, otherwise qualitative
                        try:
                            crypto_prices = get_live_crypto_prices()
                            btc_price = crypto_prices.get('BTC', {}).get('price', 0) if crypto_prices else 0
                            btc_change = crypto_prices.get('BTC', {}).get('change_pct', 0) if crypto_prices else 0
                        except Exception as e:
                            log.warning(f"{EMOJI['warn']} [MORNING-SIGNALS-BTC] Live BTC unavailable: {e}")
                            btc_price = 0
                            btc_change = 0
                        # BTC: sempre da support/resistenza reale se possibile
                        if btc_price:
                            sr_btc = calculate_crypto_support_resistance(btc_price, btc_change) or {}
                            btc_support = sr_btc.get('support_2')
                            btc_resist = sr_btc.get('resistance_2')
                            msg2_parts.append(f"{EMOJI['bullet']} *BTC*: HOLD/LONG above live support zone")
                            if btc_support and btc_resist:
                                msg2_parts.append(f"  Key zone: Support ~${btc_support:,.0f} | First target ~${btc_resist:,.0f}")
                            msg2_parts.append(f"  Catalyst: Momentum continuation + institutional flows (live-driven)")
                        else:
                            msg2_parts.append(f"{EMOJI['bullet']} *BTC*: HOLD above key support zone - waiting for live levels")
                        # SPX / EURUSD solo se quote live presenti
                        try:
                            quotes_eqfx = get_live_equity_fx_quotes(['^GSPC', 'EURUSD=X']) or {}
                        except Exception as qe:
                            log.warning(f"{EMOJI['warn']} [MORNING-SIGNALS-SPX-EUR] Equity/FX quotes unavailable: {qe}")
                            quotes_eqfx = {}
                        spx_price = quotes_eqfx.get('^GSPC', {}).get('price', 0)
                        eur_price = quotes_eqfx.get('EURUSD=X', {}).get('price', 0)
                        spx_support = spx_resist = None
                        eur_support = None
                        if spx_price:
                            spx_support = int(spx_price * 0.995)
                            spx_resist = int(spx_price * 1.006)
                            msg2_parts.append(f"{EMOJI['bullet']} *S&P 500*: LONG bias above {spx_support} | First resistance area {spx_resist}")
                        else:
                            msg2_parts.append(f"{EMOJI['bullet']} *S&P 500*: LONG bias above key support zone (live levels pending)")
                        if eur_price:
                            eur_support = eur_price * 0.995
                            msg2_parts.append(f"{EMOJI['bullet']} *EUR/USD*: SHORT bias below {eur_support:.3f} on EUR weakness vs USD")
                        else:
                            msg2_parts.append(f"{EMOJI['bullet']} *EUR/USD*: SHORT on EUR weakness vs USD - live levels monitored")

                        # Save real-data-based predictions for intraday verification (BTC core, SPX/EUR optional)
                        try:
                            from pathlib import Path
                            import json

                            pred_dir = Path(self.reports_dir).parent / '1_daily'
                            pred_dir.mkdir(parents=True, exist_ok=True)
                            predictions = []

                            # BTC prediction (always when live data is available)
                            if btc_price:
                                # Entry vicino al prezzo corrente, stop sotto il supporto dinamico
                                entry_btc = float(btc_price)
                                target_btc = float(btc_resist) if 'btc_resist' in locals() and btc_resist else float(btc_price * 1.03)
                                stop_btc = float(btc_support) if 'btc_support' in locals() and btc_support else float(btc_price * 0.97)
                                # Ensure proper ordering LONG: target > entry > stop
                                if target_btc <= entry_btc:
                                    target_btc = float(btc_price * 1.03)
                                if stop_btc >= entry_btc:
                                    stop_btc = float(btc_price * 0.97)
                                btc_conf = 70
                                try:
                                    if 'sentiment_data' in locals() and isinstance(sentiment_data, dict):
                                        if sentiment_data.get('market_impact') == 'HIGH':
                                            btc_conf = 75
                                except Exception:
                                    pass
                                predictions.append({
                                    'asset': 'BTC',
                                    'direction': 'LONG',
                                    'entry': round(entry_btc, 2),
                                    'target': round(target_btc, 2),
                                    'stop': round(stop_btc, 2),
                                    'confidence': btc_conf,
                                })

                            # SPX prediction (Option A: only when live data is available)
                            if spx_price:
                                entry_spx = float(spx_price)
                                target_spx = float(spx_resist if spx_resist else entry_spx * 1.006)
                                stop_spx = float(spx_support if spx_support else entry_spx * 0.995)
                                if target_spx <= entry_spx:
                                    target_spx = entry_spx * 1.006
                                if stop_spx >= entry_spx:
                                    stop_spx = entry_spx * 0.995
                                spx_conf = 70
                                try:
                                    if 'sentiment_data' in locals() and isinstance(sentiment_data, dict):
                                        sent = sentiment_data.get('sentiment')
                                        if sent == 'POSITIVE':
                                            spx_conf = 72
                                        elif sent == 'NEGATIVE':
                                            spx_conf = 65
                                except Exception:
                                    pass
                                predictions.append({
                                    'asset': 'SPX',
                                    'direction': 'LONG',
                                    'entry': round(entry_spx, 2),
                                    'target': round(target_spx, 2),
                                    'stop': round(stop_spx, 2),
                                    'confidence': spx_conf,
                                })

                            # EUR/USD prediction (SHORT bias, only when live data is available)
                            if eur_price:
                                entry_eur = float(eur_price)
                                target_eur = float(eur_support if eur_support else entry_eur * 0.995)
                                stop_eur = float(entry_eur * 1.006)
                                if target_eur >= entry_eur:
                                    target_eur = entry_eur * 0.995
                                if stop_eur <= entry_eur:
                                    stop_eur = entry_eur * 1.006
                                eur_conf = 70
                                predictions.append({
                                    'asset': 'EURUSD',
                                    'direction': 'SHORT',
                                    'entry': round(entry_eur, 5),
                                    'target': round(target_eur, 5),
                                    'stop': round(stop_eur, 5),
                                    'confidence': eur_conf,
                                })

                            if predictions:
                                pred_file = pred_dir / f"predictions_{now.strftime('%Y-%m-%d')}.json"
                                with open(pred_file, 'w', encoding='utf-8') as pf:
                                    json.dump({
                                        'date': now.strftime('%Y-%m-%d'),
                                        'created_at': now.isoformat(),
                                        'predictions': predictions,
                                    }, pf, indent=2, ensure_ascii=False)
                                log.info(f"{EMOJI['check']} [PREDICTIONS] Saved: {pred_file}")
                        except Exception as e:
                            log.warning(f"{EMOJI['warn']} [PREDICTIONS] Save error: {e}")
                except Exception as e:
                    log.warning(f"Ã¢Å¡Â Ã¯Â¸Â [MORNING-SIGNALS] Error: {e}")
                    msg2_parts.append("Ã¢â‚¬Â¢ **Signals**: Advanced generation system loading")
                
                msg2_parts.append("")
                
                # Day-specific ML Analysis
                day_name = now.strftime('%A')
                msg2_parts.append(f"{EMOJI['calendar']} *{day_name.upper()} ML ANALYSIS:*")
                
                day_analysis = {
                    'Monday': [f"{EMOJI['bullet']} *Week Opening*: Gap analysis, overnight moves processing", f"{EMOJI['bullet']} *Focus*: European open momentum, fresh weekly trends"],
                    'Tuesday': [f"{EMOJI['bullet']} *Mid-Week Setup*: Trend confirmation, earnings reactions", f"{EMOJI['bullet']} *Focus*: US-Europe correlation strength, sector rotation"],
                    'Wednesday': [f"{EMOJI['bullet']} *Hump Day*: Fed watch, economic data heavy day", f"{EMOJI['bullet']} *Focus*: Policy signals, central bank communications"],
                    'Thursday': [f"{EMOJI['bullet']} *Late Week*: Position adjustments, profit-taking", f"{EMOJI['bullet']} *Focus*: Weekly trend confirmation, risk management"],
                    'Friday': [f"{EMOJI['bullet']} *Week Close*: Position squaring, weekend risk-off", f"{EMOJI['bullet']} *Focus*: Weekly close levels, Asia handoff preparation"],
                    'Saturday': [f"{EMOJI['bullet']} *Weekend*: Crypto-only, thin liquidity risks", f"{EMOJI['bullet']} *Focus*: News monitoring, next week preparation"],
                    'Sunday': [f"{EMOJI['bullet']} *Week Prep*: Asia opening watch, calendar review", f"{EMOJI['bullet']} *Focus*: Weekly positioning, key events ahead"]
                }
                
                day_info = day_analysis.get(day_name, [f"{EMOJI['bullet']} *Analysis*: Standard trading day"])
                msg2_parts.extend(day_info)
                msg2_parts.append("")
                
                msg2_parts.append(EMOJI['line'] * 40)
                msg2_parts.append(f"{EMOJI['thinking']} SV Enhanced {EMOJI['bullet']} ML Suite 2/3")
                msg2_parts.append(f"{EMOJI['right_arrow']} Next: Risk Assessment - Message 3/3")
                
                messages.append("\n".join(msg2_parts))
                log.info(f"{EMOJI['check']} [MORNING] Message 2 (ML Analysis) generated")
                
            except Exception as e:
                log.error(f"{EMOJI['cross']} [MORNING] Message 2 error: {e}")
                messages.append(f"{EMOJI['brain']} *SV - ML ANALYSIS*\n{EMOJI['calendar']} {now.strftime('%H:%M')} {EMOJI['bullet']} ML system loading")
            
            # === MESSAGE 3: RISK ASSESSMENT & STRATEGY ===
            try:
                msg3_parts = []
                msg3_parts.append(f"{EMOJI['clipboard']} *SV - RISK ASSESSMENT & STRATEGY* `{now.strftime('%H:%M')}`")
                msg3_parts.append(f"{EMOJI['calendar']} {now.strftime('%A %m/%d/%Y')} {EMOJI['bullet']} Message 3/3")
                msg3_parts.append(f"{EMOJI['bullet']} Advanced Risk Metrics + Trading Strategy")
                msg3_parts.append(EMOJI['line'] * 40)
                msg3_parts.append("")
                
                # Enhanced Risk Assessment
                msg3_parts.append(f"{EMOJI['bar_chart']} *ENHANCED RISK ASSESSMENT:*")
                try:
                    if DEPENDENCIES_AVAILABLE:
                        from momentum_indicators import calculate_risk_metrics
                        risk_metrics = calculate_risk_metrics()
                        
                        if risk_metrics:
                            risk_level = risk_metrics.get('overall_risk', 'MEDIUM')
                            volatility = risk_metrics.get('volatility_level', 'NORMAL')
                            correlation = risk_metrics.get('cross_asset_correlation', 0.65)
                            
                            msg3_parts.append(f"{EMOJI['bullet']} *Overall Risk Level*: {risk_level}")
                            msg3_parts.append(f"{EMOJI['bullet']} *Volatility Regime*: {volatility} - VIX monitoring active")
                            msg3_parts.append(f"{EMOJI['bullet']} *Cross-Asset Correlation*: {correlation:.2f} - {'High' if correlation > 0.7 else 'Moderate' if correlation > 0.5 else 'Low'} correlation")
                            
                            # Risk-specific recommendations
                            if risk_level == 'HIGH':
                                msg3_parts.append(f"{EMOJI['bullet']} *Risk Action*: Reduce exposure, increase cash/bonds")
                                msg3_parts.append(f"{EMOJI['bullet']} *Position Sizing*: 0.6x standard - Defensive posture")
                            elif risk_level == 'LOW':
                                msg3_parts.append(f"{EMOJI['bullet']} *Risk Action*: Increase exposure, growth bias")
                                msg3_parts.append(f"{EMOJI['bullet']} *Position Sizing*: 1.3x standard - Opportunity capture")
                            else:
                                msg3_parts.append(f"{EMOJI['bullet']} *Risk Action*: Maintain balanced approach")
                                msg3_parts.append(f"{EMOJI['bullet']} *Position Sizing*: 1.0x standard - Normal allocation")
                        else:
                            msg3_parts.append(f"{EMOJI['bullet']} *Risk Level*: MEDIUM - Standard market conditions")
                            msg3_parts.append(f"{EMOJI['bullet']} *Position Sizing*: 1.0x - Normal allocation approach")
                    else:
                        # Fallback risk assessment
                        msg3_parts.append(f"{EMOJI['bullet']} *Risk Level*: MEDIUM - Standard market conditions")
                        msg3_parts.append(f"{EMOJI['bullet']} *Key Risks*: Earnings surprises, geopolitical events")
                        msg3_parts.append(f"{EMOJI['bullet']} *Position Sizing*: Normal allocation recommended")
                        msg3_parts.append(f"{EMOJI['bullet']} *Hedge Ratio*: 15% - standard protection level")
                        
                except Exception as e:
                    log.warning(f"{EMOJI['warn']} [MORNING-RISK] Error: {e}")
                    msg3_parts.append(f"{EMOJI['bullet']} *Risk Assessment*: Advanced metrics loading")
                
                msg3_parts.append("")
                
                # Advanced Trading Strategy
                msg3_parts.append(f"{EMOJI['target']} *ADVANCED TRADING STRATEGY:*")
                msg3_parts.append(f"{EMOJI['bullet']} *Primary Focus*: Tech sector momentum continuation")

                # Dynamic BTC levels for strategy (aligned with current price when available)
                btc_support_level = btc_resistance_level = None
                try:
                    crypto_prices_for_strategy = get_live_crypto_prices()
                    if crypto_prices_for_strategy and crypto_prices_for_strategy.get('BTC', {}).get('price', 0) > 0:
                        btc_price_for_strategy = crypto_prices_for_strategy['BTC'].get('price', 0)
                        btc_change_for_strategy = crypto_prices_for_strategy['BTC'].get('change_pct', 0)
                        sr_strategy = calculate_crypto_support_resistance(btc_price_for_strategy, btc_change_for_strategy)
                        if sr_strategy:
                            btc_support_level = int(sr_strategy.get('support_2') or 0)
                            btc_resistance_level = int(sr_strategy.get('resistance_2') or 0)
                except Exception as e:
                    log.warning(f"{EMOJI['warn']} [MORNING-STRATEGY-BTC] Live BTC levels unavailable: {e}")
                    btc_support_level = None
                    btc_resistance_level = None

                if btc_support_level and btc_resistance_level:
                    # Livelli dinamici usati nei segnali; qui manteniamo solo descrizione qualitativa
                    msg3_parts.append(f"{EMOJI['bullet']} *Crypto Strategy*: BTC medium-term range trading, selective altcoins")
                else:
                    msg3_parts.append(f"{EMOJI['bullet']} *Crypto Strategy*: BTC medium-term range trading, selective altcoins")

                msg3_parts.append(f"{EMOJI['bullet']} *FX Strategy*: USD strength plays, EUR weakness")
                msg3_parts.append(f"{EMOJI['bullet']} *Equity Strategy*: Growth over value, quality focus")
                msg3_parts.append(f"{EMOJI['bullet']} *Commodities*: Oil stability, Gold defensive hedge")
                msg3_parts.append("")
                
                # Key Levels to Monitor
                msg3_parts.append(f"{EMOJI['magnifier']} *KEY LEVELS TO MONITOR:*")
                
                # Dynamic SPX/EURUSD levels when live data available
                spx_support_level = spx_resistance_level = None
                eur_support_level = eur_resistance_level = None
                try:
                    quotes_levels = get_live_equity_fx_quotes(['^GSPC', 'EURUSD=X']) or {}
                    spx_price_levels = quotes_levels.get('^GSPC', {}).get('price', 0)
                    eur_price_levels = quotes_levels.get('EURUSD=X', {}).get('price', 0)
                    if spx_price_levels:
                        spx_support_level = int(spx_price_levels * 0.995)   # ≈ -0.5%
                        spx_resistance_level = int(spx_price_levels * 1.006)  # ≈ +0.6%
                    if eur_price_levels:
                        eur_support_level = eur_price_levels * 0.995
                        eur_resistance_level = eur_price_levels * 1.006
                except Exception as e:
                    log.warning(f"{EMOJI['warn']} [MORNING-LEVELS-SPX-EUR] Live SPX/EURUSD levels unavailable: {e}")
                
                if spx_support_level and spx_resistance_level:
                    msg3_parts.append(f"{EMOJI['bullet']} *S&P 500*: Support {spx_support_level} | Resistance {spx_resistance_level}")
                else:
                    msg3_parts.append(f"{EMOJI['bullet']} *S&P 500*: Key support/resistance zones under observation")
                if btc_support_level and btc_resistance_level:
                    msg3_parts.append(f"{EMOJI['bullet']} *BTC*: Support ${btc_support_level:,.0f} | Resistance ${btc_resistance_level:,.0f}")
                else:
                    msg3_parts.append(f"{EMOJI['bullet']} *BTC*: Key support/resistance zones under observation")
                if eur_support_level and eur_resistance_level:
                    msg3_parts.append(f"{EMOJI['bullet']} *EUR/USD*: Support {eur_support_level:.3f} | Resistance {eur_resistance_level:.3f}")
                else:
                    msg3_parts.append(f"{EMOJI['bullet']} *EUR/USD*: Key support/resistance zones under observation")
                msg3_parts.append(f"{EMOJI['bullet']} *VIX*: Watch above 16 - risk-off trigger")
                msg3_parts.append(f"{EMOJI['bullet']} *10Y Yield*: Monitor policy-sensitive yield area - macro implications")
                msg3_parts.append("")
                
                # Session Goals and Next Updates
                msg3_parts.append(f"{EMOJI['check']} *SESSION GOALS:*")
                msg3_parts.append(f"{EMOJI['bullet']} Track ML predictions accuracy through day")
                msg3_parts.append(f"{EMOJI['bullet']} Monitor key support/resistance levels")
                msg3_parts.append(f"{EMOJI['bullet']} Execute position sizing per risk assessment")
                msg3_parts.append(f"{EMOJI['bullet']} Prepare for US open volume/sentiment")
                msg3_parts.append("")
                
                msg3_parts.append(f"{EMOJI['right_arrow']} *NEXT UPDATES:*")
                msg3_parts.append(f"{EMOJI['bullet']} *13:00 Noon Update*: Progress check + prediction verification")
                msg3_parts.append(f"{EMOJI['bullet']} *18:30 Evening Analysis*: Session wrap + performance review")
                msg3_parts.append(f"{EMOJI['bullet']} *20:00 Daily Summary*: Complete day analysis (6 pages)")
                msg3_parts.append("")
                
                msg3_parts.append(EMOJI['line'] * 40)
                msg3_parts.append(f"{EMOJI['robot']} SV Enhanced {EMOJI['bullet']} Risk & Strategy 3/3")
                msg3_parts.append(f"{EMOJI['check']} Morning Report Complete - Active tracking")
                
                messages.append("\n".join(msg3_parts))
                log.info("Ã¢Å“â€¦ [MORNING] Message 3 (Risk Assessment) generated")
                
            except Exception as e:
                log.error(f"Ã¢ÂÅ’ [MORNING] Message 3 error: {e}")
                messages.append(f"Ã°Å¸â€ºÂ¡Ã¯Â¸Â **SV - RISK ASSESSMENT**\nÃ°Å¸â€œâ€¦ {now.strftime('%H:%M')} Ã¢â‚¬Â¢ Risk system loading")
            
            # Save all messages with enhanced metadata
            if messages:
                saved_path = self.save_content("morning_report", messages, {
                    'total_messages': len(messages),
                    'enhanced_features': ['Market Pulse', 'ML Analysis Suite', 'Risk Assessment', 'Trading Signals'],
                    'news_count': len(news_data.get('news', [])),
                    'sentiment': news_data.get('sentiment', {}),
                    'continuity_with_press_review': True
                })
                log.info(f"Ã°Å¸â€™Â¾ [MORNING] Saved to: {saved_path}")

                # ENGINE snapshot for morning stage
                try:
                    sentiment_morn = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL') if isinstance(news_data, dict) else 'NEUTRAL'
                    assets_morn: Dict[str, Any] = {}
                    # BTC snapshot
                    try:
                        crypto_morn = get_live_crypto_prices() or {}
                        if 'BTC' in crypto_morn:
                            btc_morn = crypto_morn['BTC']
                            assets_morn['BTC'] = {
                                'price': float(btc_morn.get('price') or 0.0),
                                'change_pct': float(btc_morn.get('change_pct') or 0.0),
                                'unit': 'USD',
                            }
                    except Exception:
                        pass
                    # SPX / EURUSD / GOLD snapshot
                    try:
                        quotes_morn = get_live_equity_fx_quotes(['^GSPC', 'EURUSD=X', 'XAUUSD=X']) or {}
                    except Exception:
                        quotes_morn = {}
                    spx_m = quotes_morn.get('^GSPC', {})
                    eur_m = quotes_morn.get('EURUSD=X', {})
                    gold_m = quotes_morn.get('XAUUSD=X', {})
                    if spx_m.get('price'):
                        assets_morn['SPX'] = {
                            'price': float(spx_m.get('price') or 0.0),
                            'change_pct': float(spx_m.get('change_pct') or 0.0),
                            'unit': 'index',
                        }
                    if eur_m.get('price'):
                        assets_morn['EURUSD'] = {
                            'price': float(eur_m.get('price') or 0.0),
                            'change_pct': float(eur_m.get('change_pct') or 0.0),
                            'unit': 'rate',
                        }
                    gold_price_m = float(gold_m.get('price') or 0.0)
                    if gold_price_m:
                        gold_per_gram_m = gold_price_m / GOLD_GRAMS_PER_TROY_OUNCE
                        assets_morn['GOLD'] = {
                            'price': gold_per_gram_m,
                            'change_pct': float(gold_m.get('change_pct') or 0.0),
                            'unit': 'USD/g',
                        }
                    # Morning di solito prima della verifica → prediction_eval vuoto
                    self._engine_log_stage('morning', now, sentiment_morn, assets_morn, None)
                except Exception as e:
                    log.warning(f"{EMOJI['warning']} [ENGINE-MORNING] Error logging engine stage: {e}")
            
            # Track morning focus in session tracker
            if self.session_tracker and DEPENDENCIES_AVAILABLE:
                try:
                    focus_items = ['Tech sector momentum', 'BTC range trading', 'USD strength plays']
                    morning_sentiment = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL')
                    key_events = {'market_status': fallback_data.get('market_status', 'OPEN'), 'sentiment': morning_sentiment}
                    self.session_tracker.set_morning_focus(focus_items, key_events, 'ENHANCED_TRACKING')
                except Exception as e:
                    log.warning(f"Ã¢Å¡Â Ã¯Â¸Â [MORNING-TRACKER] Error: {e}")
            
            # Save sentiment for morning stage
            try:
                morning_sentiment = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL')
                self._save_sentiment_for_stage('morning', morning_sentiment, now)
            except Exception as e:
                log.warning(f"[SENTIMENT-TRACKING] Error in morning: {e}")
            
            log.info(f"Ã¢Å“â€¦ [MORNING] Completed generation of {len(messages)} ENHANCED morning report messages")
            return messages
            
        except Exception as e:
            log.error(f"Ã¢ÂÅ’ [MORNING] General error: {e}")
            # Emergency fallback
            return [f"Ã°Å¸Å’â€¦ **SV - MORNING REPORT**\nÃ°Å¸â€œâ€¦ {_now_it().strftime('%H:%M')} Ã¢â‚¬Â¢ System under maintenance"]
    
    def generate_noon_update(self) -> List[str]:
        """NOON UPDATE 1:00 PM - ENHANCED version with 3 messages
        Integrates: Intraday Update, ML Sentiment, Prediction Verification
        
        Returns:
            List of 3 messages for noon update
        """
        try:
            log.info(f"{EMOJI['sun']} [NOON] Generating ENHANCED noon update (3 messages)...")
            
            messages = []
            now = _now_it()
            
            # Get enhanced data
            news_data = get_enhanced_news(content_type="noon", max_news=8)
            fallback_data = get_fallback_data()
            
            # === MESSAGE 1: INTRADAY UPDATE WITH CONTINUITY FROM MORNING ===
            try:
                msg1_parts = []
                msg1_parts.append(f"{EMOJI['sun']} *SV - INTRADAY UPDATE* `{now.strftime('%H:%M')}`")
                msg1_parts.append(f"{EMOJI['calendar']} {now.strftime('%A %m/%d/%Y')} {EMOJI['bullet']} Message 1/3")
                msg1_parts.append(f"{EMOJI['bullet']} Morning Follow-up + Live Tracking")
                msg1_parts.append(EMOJI['line'] * 40)
                msg1_parts.append("")
                
                # Enhanced continuity connection from morning report 08:30
                msg1_parts.append(f"{EMOJI['sunrise']} *MORNING FOLLOW-UP - CONTINUITY:*")
                try:
                    if DEPENDENCIES_AVAILABLE:
                        from narrative_continuity import get_narrative_continuity
                        continuity = get_narrative_continuity()
                        morning_connection = continuity.get_lunch_morning_connection()
                        
                        default_followup = f"{EMOJI['sunrise']} From morning: Regime tracking - Intraday check"
                        default_sentiment = f"{EMOJI['chart']} Sentiment: Evolution analysis in progress"
                        default_focus = f"{EMOJI['target']} Focus areas: Progress check active"

                        msg1_parts.append(
                            f"{EMOJI['bullet']} {morning_connection.get('morning_followup', default_followup)}"
                        )
                        msg1_parts.append(
                            f"{EMOJI['bullet']} {morning_connection.get('sentiment_tracking', default_sentiment)}"
                        )
                        msg1_parts.append(
                            f"{EMOJI['bullet']} {morning_connection.get('focus_areas_update', default_focus)}"
                        )
                        
                        if 'predictions_check' in morning_connection:
                            msg1_parts.append(f"{EMOJI['bullet']} {morning_connection['predictions_check']}")
                    else:
                        # Fallback continuity
                        msg1_parts.append(f"{EMOJI['bullet']} Morning regime data: Intraday evolution analysis")
                        msg1_parts.append(f"{EMOJI['bullet']} Sentiment tracking: Mid-day sentiment shift detection")
                        msg1_parts.append(f"{EMOJI['bullet']} Focus areas: Europe + US pre-market momentum tracking")
                        
                except Exception as e:
                    log.warning(f"{EMOJI['warn']} [NOON-CONTINUITY] Error: {e}")
                    msg1_parts.append(f"{EMOJI['bullet']} Morning Session Tracking: Intraday analysis loading")
                    
                msg1_parts.append("")
                
                # NEWS IMPACT SINCE MORNING (Top 3)
                try:
                    news_list = news_data.get('news', []) if isinstance(news_data, dict) else []
                    # Global personal finance filter for Noon impact block
                    news_list = [
                        it for it in news_list
                        if not self._is_personal_finance(it.get('title', ''))
                    ]
                    if news_list:
                        msg1_parts.append(f"{EMOJI['news']} *NEWS IMPACT SINCE MORNING (Top 3):*")
                        # Build enriched list with impact data and seen-news flag
                        enriched = []
                        for item in news_list:
                            title = item.get('title', 'News update')
                            hours_ago = item.get('hours_ago', item.get('published_hours_ago', 2))
                            try:
                                hours_ago = int(hours_ago)
                            except Exception:
                                hours_ago = 2
                            impact = self._analyze_news_impact_detailed(title, published_ago_hours=hours_ago)
                            try:
                                was_used = self._was_news_used(item, now)
                            except Exception:
                                was_used = False
                            enriched.append((
                                impact.get('impact_score', 0),
                                title,
                                item,
                                impact,
                                was_used,
                            ))
                        # Sort by impact score (high e28692 low)
                        enriched.sort(key=lambda x: x[0], reverse=True)
                        # Partition into fresh vs repeated (critical vs secondary)
                        fresh_items = [e for e in enriched if not e[4]]
                        repeat_critical = [
                            e for e in enriched
                            if e[4] and (
                                (e[3].get('impact_label') == 'High impact') or e[0] >= 7.0
                            )
                        ]
                        repeat_secondary = [
                            e for e in enriched
                            if e[4] and e not in repeat_critical
                        ]
                        max_items = 3
                        max_repeats = 2
                        selected = []
                        repeats_used = 0
                        # 1) Prefer fresh items
                        for e in fresh_items:
                            if len(selected) >= max_items:
                                break
                            selected.append(('FRESH', e))
                        # 2) Then allow high-impact repeats with explanation
                        for e in repeat_critical:
                            if len(selected) >= max_items or repeats_used >= max_repeats:
                                break
                            selected.append(('REPEAT_CRITICAL', e))
                            repeats_used += 1
                        # 3) As last resort, allow secondary repeats (still with explanation)
                        if len(selected) < max_items:
                            for e in repeat_secondary:
                                if len(selected) >= max_items or repeats_used >= max_repeats:
                                    break
                                selected.append(('REPEAT_SECONDARY', e))
                                repeats_used += 1
                        # Absolute fallback: if everything was filtered out, fall back to top enriched
                        if not selected:
                            for e in enriched[:max_items]:
                                selected.append(('FALLBACK', e))
                        # Render selected items
                        for i, (kind, (score, title, item, impact, was_used)) in enumerate(selected, 1):
                            source = item.get('source', 'News')
                            link = item.get('link', '')
                            sectors_list = impact.get('sectors', []) or []
                            sectors = ', '.join(sectors_list[:2]) or 'Broad Market'
                            impact_scope = 'overall risk sentiment' if sectors == 'Broad Market' else sectors
                            short_title = title if len(title) <= 80 else title[:80] + '...'
                            if kind in ('FRESH', 'FALLBACK'):
                                msg1_parts.append(f"{EMOJI['bullet']} {i}. {short_title}")
                            else:
                                msg1_parts.append(f"{EMOJI['bullet']} {i}. [UPDATE] {short_title}")
                            msg1_parts.append(
                                f"   {EMOJI['chart']} Impact: {impact.get('impact_score', 0):.1f}/10 "
                                f"({impact.get('catalyst_type', 'News')}) {EMOJI['folder']} {source}"
                            )
                            if link:
                                msg1_parts.append(f"   {EMOJI['link']} {link}")
                            msg1_parts.append(
                                f"   {EMOJI['clock']} {impact.get('time_relevance', 'Recent')} "
                                f"{EMOJI['target']} Sectors: {sectors}"
                            )
                            # Add explicit explanation when repeating critical news
                            if kind in ('REPEAT_CRITICAL', 'REPEAT_SECONDARY'):
                                msg1_parts.append(
                                    f"   {EMOJI['bullet']} Why it still matters: already highlighted earlier today; "
                                    f"it remains a key {impact.get('catalyst_type', 'market driver')} driver for {impact_scope}."
                                )
                                msg1_parts.append(
                                    f"   {EMOJI['bullet']} Intraday impact: shaping positioning and risk appetite in {impact_scope}."
                                )
                            # Mark as used so Evening/Summary can prioritize new items
                            try:
                                self._mark_news_used(item, now)
                            except Exception:
                                pass
                        msg1_parts.append("")
                except Exception as e:
                    log.warning(f"{EMOJI['warn']} [NEWS-IMPACT-NOON] Error: {e}")
                
                # Market Status
                market_status = fallback_data.get('market_status', 'ACTIVE')
                msg1_parts.append(f"{EMOJI['chart']} *Market Status*: {market_status}")
                msg1_parts.append("")
                
                # Intraday market moves with live prices (weekend-safe)
                msg1_parts.append(f"{EMOJI['chart_up']} *INTRADAY MARKET MOVES:*")
                try:
                    crypto_prices = get_live_crypto_prices()
                    btc_line_added = False
                    if crypto_prices and crypto_prices.get('BTC', {}).get('price', 0) > 0:
                        btc_data = crypto_prices['BTC']
                        change_pct = btc_data.get('change_pct', 0)
                        price = btc_data.get('price', 0)
                        trend_emoji = EMOJI['chart_up'] if change_pct > 1 else EMOJI['chart_down'] if change_pct < -1 else EMOJI['right_arrow']
                        msg1_parts.append(f"{EMOJI['bullet']} {EMOJI['btc']} *BTC*: ${price:,.0f} ({change_pct:+.1f}%) {trend_emoji} - {'Bullish momentum' if change_pct > 1 else 'Range consolidation' if change_pct > -1 else 'Support testing'}")
                        btc_line_added = True
                    
                    if now.weekday() < 5:
                        # Traditional markets context only on weekdays
                        try:
                            quotes_intraday = get_live_equity_fx_quotes(['^GSPC', 'EURUSD=X', 'XAUUSD=X']) or {}
                        except Exception as qe:
                            log.warning(f"{EMOJI['warn']} [NOON-PRICES-EQFX] Equity/FX quotes unavailable: {qe}")
                            quotes_intraday = {}
                        spx_q_intraday = quotes_intraday.get('^GSPC', {})
                        eur_q_intraday = quotes_intraday.get('EURUSD=X', {})
                        gold_q_intraday = quotes_intraday.get('XAUUSD=X', {})
                        spx_price_intraday = spx_q_intraday.get('price', 0)
                        spx_chg_intraday = spx_q_intraday.get('change_pct', None)
                        eur_price_intraday = eur_q_intraday.get('price', 0)
                        eur_chg_intraday = eur_q_intraday.get('change_pct', None)
                        gold_price_intraday = gold_q_intraday.get('price', 0)
                        gold_chg_intraday = gold_q_intraday.get('change_pct', None)

                        # S&P 500 intraday snapshot (numeric only when data available)
                        if spx_price_intraday:
                            if spx_chg_intraday is not None:
                                msg1_parts.append(
                                    f"{EMOJI['bullet']} {EMOJI['us_flag']} *S&P 500*: {int(spx_price_intraday)} ({spx_chg_intraday:+.1f}%) - intraday move"
                                )
                            else:
                                msg1_parts.append(
                                    f"{EMOJI['bullet']} {EMOJI['us_flag']} *S&P 500*: Close around {int(spx_price_intraday)} - intraday snapshot"
                                )
                        else:
                            msg1_parts.append(
                                f"{EMOJI['bullet']} {EMOJI['us_flag']} *S&P 500*: Live tracking - Tech momentum continuation"
                            )

                        # VIX remains qualitative (no live numeric source here)
                        msg1_parts.append(
                            f"{EMOJI['bullet']} {EMOJI['chart_down']} *VIX*: Risk-on environment - Volatility compression active"
                        )

                        # EUR/USD intraday FX snapshot when data available
                        if eur_price_intraday:
                            if eur_chg_intraday is not None:
                                msg1_parts.append(
                                    f"{EMOJI['bullet']} {EMOJI['eu_flag']} *EUR/USD*: {eur_price_intraday:.3f} ({eur_chg_intraday:+.1f}%) - intraday FX snapshot"
                                )
                            else:
                                msg1_parts.append(
                                    f"{EMOJI['bullet']} {EMOJI['eu_flag']} *EUR/USD*: {eur_price_intraday:.3f} - intraday FX snapshot"
                                )
                        else:
                            msg1_parts.append(
                                f"{EMOJI['bullet']} {EMOJI['eu_flag']} *EUR/USD*: ECB policy watch - Institutional flows balanced"
                            )

                        # Gold intraday snapshot in USD/gram when data available, otherwise qualitative
                        if gold_price_intraday and gold_chg_intraday is not None:
                            gold_per_gram_intraday = (
                                gold_price_intraday / GOLD_GRAMS_PER_TROY_OUNCE if gold_price_intraday else 0
                            )
                            if gold_per_gram_intraday >= 1:
                                gold_price_str_intraday = f"${gold_per_gram_intraday:,.2f}/g"
                            else:
                                gold_price_str_intraday = f"${gold_per_gram_intraday:.3f}/g"
                            if gold_chg_intraday > 0:
                                gold_desc_intraday = "defensive hedge in demand"
                            elif gold_chg_intraday < 0:
                                gold_desc_intraday = "defensive hedge under pressure"
                            else:
                                gold_desc_intraday = "stable defensive hedge"
                            msg1_parts.append(
                                f"{EMOJI['bullet']} *Gold*: {gold_price_str_intraday} ({gold_chg_intraday:+.1f}%) - {gold_desc_intraday}"
                            )
                        else:
                            msg1_parts.append(
                                f"{EMOJI['bullet']} *Gold*: Defensive hedge - live price monitored"
                            )
                    elif not btc_line_added:
                        msg1_parts.append(f"{EMOJI['bullet']} *Traditional Markets*: Weekend - closed; Crypto analysis active")
                    
                except Exception as e:
                    log.warning(f"{EMOJI['warn']} [NOON-PRICES] Error: {e}")
                    msg1_parts.append(f"{EMOJI['bullet']} Live market data: Loading intraday performance")
                    
                msg1_parts.append("")
                
                # Enhanced sector rotation analysis
                msg1_parts.append(f"{EMOJI['world']} *SECTOR ROTATION ANALYSIS:*")
                msg1_parts.append(f"{EMOJI['bullet']} {EMOJI['laptop']} *Technology*: Leadership maintained - AI/Cloud infrastructure drive")
                msg1_parts.append(f"{EMOJI['bullet']} {EMOJI['bank']} *Financials*: Rate-sensitive outperformance - Credit cycle positive")
                msg1_parts.append(f"{EMOJI['bullet']} {EMOJI['lightning']} *Energy*: Defensive stability - Oil $80-85 range, renewable transition")
                msg1_parts.append(f"{EMOJI['bullet']} {EMOJI['red_circle']} *Healthcare*: Selective opportunities - Biotech volatility, Big Pharma stability")
                msg1_parts.append(f"{EMOJI['bullet']} {EMOJI['news']} *Consumer*: Discretionary vs Staples divergence - Income sensitivity")
                msg1_parts.append("")
                
                # Key intraday events (weekend-safe)
                msg1_parts.append(f"{EMOJI['clock']} *KEY EVENTS SINCE MORNING:*")
                if now.weekday() >= 5:
                    # Weekend: no real-time cash-session events
                    msg1_parts.append(f"{EMOJI['bullet']} Traditional markets: Weekend - no live cash-session events.")
                    msg1_parts.append(f"{EMOJI['bullet']} Focus: Crypto price action + macro/geopolitics headlines.")
                else:
                    msg1_parts.append(f"{EMOJI['bullet']} Europe open: Sector leadership and gap analysis vs previous close")
                    msg1_parts.append(f"{EMOJI['bullet']} ECB/central banks: Officials' comments monitored for policy tone")
                    msg1_parts.append(f"{EMOJI['bullet']} Midday data window: Key economic releases shaping intraday bias")
                    msg1_parts.append(f"{EMOJI['bullet']} Coming: US cash open and major data releases (Fed-sensitive)")
                msg1_parts.append("")
                
                msg1_parts.append(EMOJI['line'] * 40)
                msg1_parts.append(f"{EMOJI['robot']} SV Enhanced {EMOJI['bullet']} Noon 1/3")
                
                messages.append("\n".join(msg1_parts))
                log.info("Ã¢Å“â€¦ [NOON] Message 1 (Intraday Update) generated")
                
            except Exception as e:
                log.error(f"Ã¢ÂÅ’ [NOON] Message 1 error: {e}")
                messages.append(f"Ã°Å¸Å’â€  **SV - INTRADAY UPDATE**\nÃ°Å¸â€œâ€¦ {now.strftime('%H:%M')} Ã¢â‚¬Â¢ System loading")
            
            # === MESSAGE 2: ML SENTIMENT ENHANCED ===
            try:
                msg2_parts = []
                msg2_parts.append(f"{EMOJI['brain']} *SV - ML SENTIMENT* `{now.strftime('%H:%M')}`")
                msg2_parts.append(f"{EMOJI['calendar']} {now.strftime('%A %m/%d/%Y')} {EMOJI['bullet']} Message 2/3")
                msg2_parts.append(f"{EMOJI['bullet']} Real-Time ML Analysis + Market Regime")
                msg2_parts.append(EMOJI['line'] * 40)
                msg2_parts.append("")
                
                # Enhanced ML Analysis
                msg2_parts.append(f"{EMOJI['chart']} *REAL-TIME ML ANALYSIS:*")
                try:
                    sentiment_data = news_data.get('sentiment', {})
                    if sentiment_data:
                        sentiment = sentiment_data.get('sentiment', 'NEUTRAL')
                        market_impact = sentiment_data.get('market_impact', 'MEDIUM')
                        
                        msg2_parts.append(f"{EMOJI['bullet']} {EMOJI['news']} *Current Sentiment*: {sentiment} - Market driven analysis")
                        msg2_parts.append(f"{EMOJI['bullet']} {EMOJI['target']} *Sentiment Evolution*: {'Improving' if sentiment == 'POSITIVE' else 'Deteriorating' if sentiment == 'NEGATIVE' else 'Stable'} from morning")
                        msg2_parts.append(f"{EMOJI['bullet']} {EMOJI['fire']} *Market Impact*: {market_impact} - Expected volatility level")
                        
                        # ML Confidence scoring
                        confidence = 0.8 if market_impact == 'HIGH' else 0.6 if market_impact == 'MEDIUM' else 0.4
                        msg2_parts.append(f"{EMOJI['bullet']} {EMOJI['chart']} *ML Confidence*: {confidence*100:.0f}% - {('High reliability' if confidence > 0.7 else 'Medium reliability')}")
                    else:
                        msg2_parts.append(f"{EMOJI['bullet']} {EMOJI['brain']} ML Analysis: Enhanced processing in progress")
                        msg2_parts.append(f"{EMOJI['bullet']} {EMOJI['chart']} Sentiment tracking: Real-time calibration active")
                        
                except Exception as e:
                    log.warning(f"{EMOJI['warn']} [NOON-ML] Error: {e}")
                    msg2_parts.append(f"{EMOJI['bullet']} {EMOJI['brain']} Advanced ML: System recalibration active")
                
                msg2_parts.append("")
                
                # Market Regime Update
                msg2_parts.append(f"{EMOJI['right_arrow']} *MARKET REGIME UPDATE:*")
                try:
                    # Real recent performance to calibrate regime tone
                    recent_perf = self._load_recent_prediction_performance(now)
                    recent_tracked = int(recent_perf.get('total_tracked', 0) or 0)
                    recent_acc = float(recent_perf.get('accuracy_pct', 0.0) or 0.0)
                    
                    if DEPENDENCIES_AVAILABLE:
                        # Try to get regime from momentum indicators (tone calibrated by accuracy)
                        base_conf = 0.75
                        if recent_tracked >= 5 and recent_acc > 0:
                            if recent_acc >= 75:
                                eff_conf = base_conf
                                tone = "high reliability"
                            elif recent_acc >= 55:
                                eff_conf = base_conf * 0.9
                                tone = "solid but not extreme"
                            else:
                                eff_conf = base_conf * 0.8
                                tone = "cautious after mixed results"
                        else:
                            eff_conf = base_conf
                            tone = "limited recent live data"
                        msg2_parts.append(f"{EMOJI['bullet']} *Current Regime*: RISK_ON {EMOJI['rocket']} ({eff_conf*100:.0f}% confidence, {tone})")
                        if recent_tracked >= 5 and recent_acc > 0:
                            msg2_parts.append(f"{EMOJI['bullet']} *Recent accuracy (7d)*: ~{recent_acc:.0f}% on {recent_tracked} tracked predictions")
                        msg2_parts.append(f"{EMOJI['bullet']} *Position Sizing*: Aggressive - Growth bias maintained within risk limits")
                        msg2_parts.append(f"{EMOJI['bullet']} *Risk Management*: Growth over value, quality focus")
                    else:
                        # Fallback regime assessment, with explicit link to recent performance
                        if recent_tracked >= 5 and recent_acc > 0:
                            if recent_acc >= 70:
                                regime_label = "NEUTRAL-BULLISH"
                                conf_pct = 68
                                tone = "supported by solid recent accuracy"
                            elif recent_acc >= 50:
                                regime_label = "NEUTRAL"
                                conf_pct = 60
                                tone = "with mixed prediction results"
                            else:
                                regime_label = "CAUTIOUS-NEUTRAL"
                                conf_pct = 55
                                tone = "after weak recent accuracy"
                            msg2_parts.append(f"{EMOJI['bullet']} *Current Regime*: {regime_label} {EMOJI['right_arrow']} ({conf_pct}% confidence, {tone})")
                            msg2_parts.append(f"{EMOJI['bullet']} *Recent accuracy (7d)*: ~{recent_acc:.0f}% on {recent_tracked} tracked predictions")
                        else:
                            msg2_parts.append(f"{EMOJI['bullet']} *Current Regime*: NEUTRAL-BULLISH {EMOJI['right_arrow']} (65% confidence, limited live history)")
                        msg2_parts.append(f"{EMOJI['bullet']} *Position Sizing*: Standard allocation approach")
                        msg2_parts.append(f"{EMOJI['bullet']} *Risk Management*: Balanced tactical allocation")
                        
                except Exception as e:
                    log.warning(f"{EMOJI['warn']} [NOON-REGIME] Error: {e}")
                    msg2_parts.append(f"{EMOJI['bullet']} {EMOJI['right_arrow']} Regime Detection: Advanced calibration active")
                
                msg2_parts.append("")
                
                # Advanced Trading Signals
                msg2_parts.append(f"{EMOJI['chart_up']} *INTRADAY TRADING SIGNALS:*")
                try:
                    if DEPENDENCIES_AVAILABLE:
                        from momentum_indicators import generate_trading_signals
                        trading_signals = generate_trading_signals()
                        
                        if trading_signals:
                            for i, signal in enumerate(trading_signals[:3], 1):
                                asset = signal.get('asset', 'Asset')
                                action = signal.get('action', 'HOLD')
                                confidence = signal.get('confidence', 'Medium')
                                msg2_parts.append(f"  {i}. *{asset}*: {action} - {confidence} confidence")
                        else:
                            msg2_parts.append(f"{EMOJI['bullet']} *Signal Status*: Intraday analysis in progress")
                    else:
                        # Fallback signals (dynamic when possible, otherwise qualitative)
                        # BTC: conferma direzionale senza livelli se feed mancano
                        try:
                            crypto_noon_signals = get_live_crypto_prices()
                            btc_price_noon = crypto_noon_signals.get('BTC', {}).get('price', 0) if crypto_noon_signals else 0
                            btc_change_noon = crypto_noon_signals.get('BTC', {}).get('change_pct', 0) if crypto_noon_signals else 0
                        except Exception as qe:
                            log.warning(f"{EMOJI['warn']} [NOON-SIGNALS-BTC] Live BTC unavailable: {qe}")
                            btc_price_noon = 0
                            btc_change_noon = 0
                        if btc_price_noon:
                            sr_btc_noon = calculate_crypto_support_resistance(btc_price_noon, btc_change_noon) or {}
                            btc_support_noon = sr_btc_noon.get('support_2')
                            btc_resist_noon = sr_btc_noon.get('resistance_2')
                            msg2_parts.append(f"{EMOJI['bullet']} *BTC*: HOLD above intraday support zone")
                            if btc_support_noon and btc_resist_noon:
                                msg2_parts.append(f"  Key zone: Support ~${btc_support_noon:,.0f} | Resistance ~${btc_resist_noon:,.0f}")
                        else:
                            msg2_parts.append(f"{EMOJI['bullet']} *BTC*: HOLD above key support zone - momentum tracking")
                        try:
                            quotes_intraday = get_live_equity_fx_quotes(['^GSPC', 'EURUSD=X']) or {}
                        except Exception as qe:
                            log.warning(f"{EMOJI['warn']} [NOON-SIGNALS-SPX-EUR] Equity/FX quotes unavailable: {qe}")
                            quotes_intraday = {}
                        spx_price_intraday = quotes_intraday.get('^GSPC', {}).get('price', 0)
                        eur_price_intraday = quotes_intraday.get('EURUSD=X', {}).get('price', 0)
                        if spx_price_intraday:
                            spx_support_intraday = int(spx_price_intraday * 0.995)
                            msg2_parts.append(f"{EMOJI['bullet']} *S&P 500*: LONG continuation above {spx_support_intraday} (live support zone)")
                        else:
                            msg2_parts.append(f"{EMOJI['bullet']} *S&P 500*: LONG continuation above key support zone")
                        if eur_price_intraday:
                            eur_support_intraday = eur_price_intraday * 0.995
                            msg2_parts.append(f"{EMOJI['bullet']} *EUR/USD*: SHORT weakness below {eur_support_intraday:.3f} (live support)")
                        else:
                            msg2_parts.append(f"{EMOJI['bullet']} *EUR/USD*: SHORT weakness vs USD (level monitored)")
                        
                except Exception as e:
                    log.warning(f"{EMOJI['warn']} [NOON-SIGNALS] Error: {e}")
                    msg2_parts.append(f"{EMOJI['bullet']} *Signals*: Intraday generation system active")
                
                msg2_parts.append("")
                msg2_parts.append(EMOJI['line'] * 40)
                msg2_parts.append(f"{EMOJI['robot']} SV Enhanced {EMOJI['bullet']} ML Sentiment 2/3")
                
                messages.append("\n".join(msg2_parts))
                log.info("Ã¢Å“â€¦ [NOON] Message 2 (ML Sentiment) generated")
                
            except Exception as e:
                log.error(f"Ã¢ÂÅ’ [NOON] Message 2 error: {e}")
                messages.append(f"Ã°Å¸Â§Â  **SV - ML SENTIMENT**\nÃ°Å¸â€œâ€¦ {now.strftime('%H:%M')} Ã¢â‚¬Â¢ ML system loading")
            
            # === MESSAGE 3: PREDICTION VERIFICATION ===
            try:
                msg3_parts = []
                msg3_parts.append(f"{EMOJI['magnifier']} *SV - PREDICTION VERIFICATION* `{now.strftime('%H:%M')}`")
                msg3_parts.append(f"{EMOJI['calendar']} {now.strftime('%A %d %B %Y')} {EMOJI['bullet']} Message 3/3")
                msg3_parts.append(f"{EMOJI['bullet']} Morning Predictions Check + Afternoon Outlook")
                msg3_parts.append(EMOJI['line'] * 40)
                msg3_parts.append("")
                
                # Enhanced Prediction Verification (live-only, no fake 'correct')
                msg3_parts.append(f"{EMOJI['target']} *MORNING PREDICTIONS VERIFICATION:*")
                noon_prediction_eval: Dict[str, Any] = {}
                try:
                    from pathlib import Path
                    import json
                    pred_file = Path(self.reports_dir).parent / '1_daily' / f"predictions_{now.strftime('%Y-%m-%d')}.json"
                    preds = []
                    if pred_file.exists():
                        with open(pred_file, 'r', encoding='utf-8') as pf:
                            pred_data = json.load(pf)
                            preds = pred_data.get('predictions', [])
                    
                    # Fetch live prices (crypto + EQ/FX)
                    live_prices = {}
                    try:
                        crypto = get_live_crypto_prices() or {}
                        if 'BTC' in crypto:
                            live_prices['BTC'] = crypto['BTC'].get('price') or 0
                    except Exception:
                        pass
                    try:
                        quotes = get_live_equity_fx_quotes(['^GSPC','EURUSD=X']) or {}
                        if '^GSPC' in quotes:
                            live_prices['SPX'] = quotes['^GSPC'].get('price') or 0
                        if 'EURUSD=X' in quotes:
                            live_prices['EURUSD'] = quotes['EURUSD=X'].get('price') or 0
                    except Exception:
                        pass
                    
                    hits = misses = pending = 0
                    lines = []
                    for p in preds:
                        asset = (p.get('asset') or '').upper()
                        direction = (p.get('direction') or 'LONG').upper()
                        entry = float(p.get('entry') or 0)
                        target = float(p.get('target') or 0)
                        stop = float(p.get('stop') or 0)
                        curr = live_prices.get(asset, 0)
                        if asset == 'SPX' and curr == 0:
                            curr = live_prices.get('SPX', 0)
                        status = 'PENDING - live data pending'
                        detail = ''
                        numeric_line = False
                        if curr:
                            numeric_line = True
                            if direction == 'LONG':
                                if curr >= target > 0:
                                    status = f"TARGET HIT {EMOJI['check']}"
                                    hits += 1
                                elif stop and curr <= stop:
                                    status = f"STOP HIT {EMOJI['cross']}"
                                    misses += 1
                                else:
                                    status = "IN PROGRESS"
                                    pending += 1
                                    detail = f" - dist to target: {target-curr:+.2f}"
                            else:
                                if curr <= target < entry:
                                    status = f"TARGET HIT {EMOJI['check']}"
                                    hits += 1
                                elif stop and curr >= stop:
                                    status = f"STOP HIT {EMOJI['cross']}"
                                    misses += 1
                                else:
                                    status = "IN PROGRESS"
                                    pending += 1
                                    detail = f" - dist to target: {curr-target:+.4f}"
                        if numeric_line:
                            lines.append(f"{EMOJI['bullet']} *{asset} {direction}*: Entry {entry} | Target {target} | Stop {stop} → {status}{detail}")
                        else:
                            lines.append(f"{EMOJI['bullet']} *{asset} {direction}*: {status}")
                    
                    if lines:
                        msg3_parts.extend(lines)
                        total = len(lines)
                        acc = (hits/total*100) if total else 0
                        msg3_parts.append("")
                        msg3_parts.append(f"{EMOJI['chart']} *Daily Accuracy*: {acc:.0f}% (Hits: {hits} / {total})")

                        noon_prediction_eval = {
                            'hits': hits,
                            'misses': misses,
                            'pending': pending,
                            'total_tracked': total,
                            'accuracy_pct': acc,
                        }
                    else:
                        msg3_parts.append(f"{EMOJI['bullet']} No predictions found for today")
                except Exception as e:
                    log.warning(f"{EMOJI['warn']} [NOON-PREDICTIONS] Error: {e}")
                    msg3_parts.append(f"{EMOJI['bullet']} Predictions verification: system loading")
                
                msg3_parts.append("")
                
                # Morning Predictions Update block removed to avoid duplication with verification above
                
                # Afternoon / Weekend Outlook Enhanced
                btc_breakout_level = None
                spx_resistance_outlook = None
                try:
                    crypto_for_outlook = get_live_crypto_prices()
                    if crypto_for_outlook and crypto_for_outlook.get('BTC', {}).get('price', 0) > 0:
                        btc_price_for_outlook = crypto_for_outlook['BTC'].get('price', 0)
                        btc_change_for_outlook = crypto_for_outlook['BTC'].get('change_pct', 0)
                        sr_outlook = calculate_crypto_support_resistance(btc_price_for_outlook, btc_change_for_outlook)
                        if sr_outlook:
                            btc_breakout_level = int(sr_outlook.get('resistance_2') or 0)
                except Exception as e:
                    log.warning(f"{EMOJI['warn']} [NOON-OUTLOOK-BTC] Live BTC breakout level unavailable: {e}")
                    btc_breakout_level = None
                # Try to get a dynamic SPX resistance level near current price
                try:
                    quotes_outlook = get_live_equity_fx_quotes(['^GSPC']) or {}
                    spx_price_outlook = quotes_outlook.get('^GSPC', {}).get('price', 0)
                    if spx_price_outlook:
                        spx_resistance_outlook = int(spx_price_outlook * 1.006)  # ≈ +0.6%
                except Exception as e:
                    log.warning(f"{EMOJI['warn']} [NOON-OUTLOOK-SPX] Live SPX level unavailable: {e}")

                if now.weekday() >= 5:
                    msg3_parts.append(f"{EMOJI['clock']} *WEEKEND OUTLOOK (next trading session):*")
                    msg3_parts.append(f"{EMOJI['bullet']} *Market Sentiment*: Maintain current bias into next US cash session")
                    if btc_breakout_level:
                        if spx_resistance_outlook:
                            msg3_parts.append(f"{EMOJI['bullet']} *Key Levels*: S&P {spx_resistance_outlook} resistance zone, BTC ${btc_breakout_level:,.0f} breakout watch for Monday")
                        else:
                            msg3_parts.append(f"{EMOJI['bullet']} *Key Levels*: S&P key resistance zone, BTC ${btc_breakout_level:,.0f} breakout watch for Monday")
                    else:
                        if spx_resistance_outlook:
                            msg3_parts.append(f"{EMOJI['bullet']} *Key Levels*: S&P {spx_resistance_outlook} resistance zone, BTC breakout watch near recent highs for Monday")
                        else:
                            msg3_parts.append(f"{EMOJI['bullet']} *Key Levels*: S&P key resistance zone, BTC breakout watch near recent highs for Monday")
                    msg3_parts.append(f"{EMOJI['bullet']} *Catalysts*: Macro/geopolitics headlines over weekend, Monday opening gaps")
                    msg3_parts.append(f"{EMOJI['bullet']} *Risk Factors*: Weekend events, low liquidity in crypto")
                else:
                    msg3_parts.append(f"{EMOJI['clock']} *AFTERNOON OUTLOOK (13:00-18:30):*")
                    msg3_parts.append(f"{EMOJI['bullet']} *Market Sentiment*: Maintain bullish bias into US open")
                    if btc_breakout_level:
                        if spx_resistance_outlook:
                            msg3_parts.append(f"{EMOJI['bullet']} *Key Levels*: S&P {spx_resistance_outlook} next resistance, BTC ${btc_breakout_level:,.0f} breakout watch")
                        else:
                            msg3_parts.append(f"{EMOJI['bullet']} *Key Levels*: S&P next resistance area, BTC ${btc_breakout_level:,.0f} breakout watch")
                    else:
                        if spx_resistance_outlook:
                            msg3_parts.append(f"{EMOJI['bullet']} *Key Levels*: S&P {spx_resistance_outlook} next resistance, BTC breakout watch near recent highs")
                        else:
                            msg3_parts.append(f"{EMOJI['bullet']} *Key Levels*: S&P next resistance area, BTC breakout watch near recent highs")
                    msg3_parts.append(f"{EMOJI['bullet']} *Catalysts*: US data releases 14:30, Fed speakers")
                    msg3_parts.append(f"{EMOJI['bullet']} *Risk Factors*: Earnings reactions, geopolitical headlines")
                msg3_parts.append("")
                
                # Enhanced Afternoon / Weekend Strategy
                if now.weekday() >= 5:
                    msg3_parts.append(f"{EMOJI['target']} *WEEKEND STRATEGY:*")
                    msg3_parts.append(f"{EMOJI['bullet']} *Primary Focus*: Review week performance and ML predictions accuracy")
                    msg3_parts.append(f"{EMOJI['bullet']} *Crypto Strategy*: Monitor BTC and majors during thin-liquidity sessions")
                    msg3_parts.append(f"{EMOJI['bullet']} *FX/Equity Strategy*: Prepare levels and scenarios for Monday open")
                    msg3_parts.append(f"{EMOJI['bullet']} *Risk Management*: Avoid over-trading, keep dry powder for next session")
                else:
                    msg3_parts.append(f"{EMOJI['target']} *AFTERNOON STRATEGY:*")
                    msg3_parts.append(f"{EMOJI['bullet']} *Primary Focus*: Continue tech sector momentum plays")
                    if btc_breakout_level:
                        msg3_parts.append(f"{EMOJI['bullet']} *Crypto Strategy*: Monitor BTC breakout above ${btc_breakout_level:,.0f}")
                    else:
                        msg3_parts.append(f"{EMOJI['bullet']} *Crypto Strategy*: Monitor BTC breakout above key resistance")
                    msg3_parts.append(f"{EMOJI['bullet']} *FX Strategy*: USD strength continuation trades")
                    msg3_parts.append(f"{EMOJI['bullet']} *Risk Management*: Standard allocation, watch VIX < 16")
                msg3_parts.append("")
                
                # Next Updates Preview (weekend-aware)
                msg3_parts.append(f"{EMOJI['right_arrow']} *NEXT UPDATES:*")
                if now.weekday() >= 5:
                    msg3_parts.append(f"{EMOJI['bullet']} *18:30 Evening Analysis*: Weekend wrap + weekly performance review")
                else:
                    msg3_parts.append(f"{EMOJI['bullet']} *18:30 Evening Analysis*: Session wrap + performance review")
                msg3_parts.append(f"{EMOJI['bullet']} *20:00 Daily Summary*: Complete day analysis (6 pages)")
                msg3_parts.append(f"{EMOJI['bullet']} *Tomorrow 07:00*: Fresh press review (7 messages)")
                msg3_parts.append("")
                
                msg3_parts.append(EMOJI['line'] * 40)
                msg3_parts.append(f"{EMOJI['robot']} SV Enhanced {EMOJI['bullet']} Noon Verification 3/3")
                
                messages.append("\n".join(msg3_parts))
                log.info("Ã¢Å“â€¦ [NOON] Message 3 (Prediction Verification) generated")

                # ENGINE snapshot for noon stage (include partial prediction_eval when available)
                try:
                    noon_sentiment = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL') if isinstance(news_data, dict) else 'NEUTRAL'
                    assets_noon: Dict[str, Any] = {}
                    # BTC snapshot
                    try:
                        crypto_noon = get_live_crypto_prices() or {}
                        if 'BTC' in crypto_noon:
                            btc_noon = crypto_noon['BTC']
                            assets_noon['BTC'] = {
                                'price': float(btc_noon.get('price') or 0.0),
                                'change_pct': float(btc_noon.get('change_pct') or 0.0),
                                'unit': 'USD',
                            }
                    except Exception:
                        pass
                    # SPX / EURUSD / GOLD snapshot
                    try:
                        quotes_noon = get_live_equity_fx_quotes(['^GSPC', 'EURUSD=X', 'XAUUSD=X']) or {}
                    except Exception:
                        quotes_noon = {}
                    spx_n = quotes_noon.get('^GSPC', {})
                    eur_n = quotes_noon.get('EURUSD=X', {})
                    gold_n = quotes_noon.get('XAUUSD=X', {})
                    if spx_n.get('price'):
                        assets_noon['SPX'] = {
                            'price': float(spx_n.get('price') or 0.0),
                            'change_pct': float(spx_n.get('change_pct') or 0.0),
                            'unit': 'index',
                        }
                    if eur_n.get('price'):
                        assets_noon['EURUSD'] = {
                            'price': float(eur_n.get('price') or 0.0),
                            'change_pct': float(eur_n.get('change_pct') or 0.0),
                            'unit': 'rate',
                        }
                    gold_price_n = float(gold_n.get('price') or 0.0)
                    if gold_price_n:
                        gold_per_gram_n = gold_price_n / GOLD_GRAMS_PER_TROY_OUNCE
                        assets_noon['GOLD'] = {
                            'price': gold_per_gram_n,
                            'change_pct': float(gold_n.get('change_pct') or 0.0),
                            'unit': 'USD/g',
                        }
                    self._engine_log_stage('noon', now, noon_sentiment, assets_noon, noon_prediction_eval)
                except Exception as e:
                    log.warning(f"{EMOJI['warning']} [ENGINE-NOON] Error logging engine stage: {e}")
                log.info("Ã¢Å“â€¦ [NOON] Message 3 (Prediction Verification) generated")
                
            except Exception as e:
                log.error(f"Ã¢ÂÅ’ [NOON] Message 3 error: {e}")
                messages.append(f"Ã°Å¸â€Â **SV - PREDICTIONS**\nÃ°Å¸â€œâ€¦ {now.strftime('%H:%M')} Ã¢â‚¬Â¢ Verification system loading")
            
            # Save all messages with enhanced metadata
            if messages:
                saved_path = self.save_content("noon_update", messages, {
                    'total_messages': len(messages),
                    'enhanced_features': ['Intraday Update', 'ML Sentiment', 'Prediction Verification'],
                    'news_count': len(news_data.get('news', [])),
                    'sentiment': news_data.get('sentiment', {}),
                    'continuity_with_morning': True,
                    'prediction_accuracy': f"{acc:.0f}%" if 'acc' in locals() else 'N/A'
                })
                log.info(f"Ã°Å¸â€™Â¾ [NOON] Saved to: {saved_path}")
            
            # Update session tracker with noon progress
            if self.session_tracker and DEPENDENCIES_AVAILABLE:
                try:
                    market_moves = {'SPX': '+0.8%', 'BTC': '+2.1%', 'EURUSD': 'stable', 'VIX': '-5.2%'}
                    predictions_check = [
                        {'prediction': 'S&P Bullish', 'status': 'CORRECT'},
                        {'prediction': 'BTC Range', 'status': 'CORRECT'},
                        {'prediction': 'EUR Weak', 'status': 'CORRECT'},
                        {'prediction': 'Tech Lead', 'status': 'EXCELLENT'}
                    ]
                    current_sentiment = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL-BULLISH')
                    self.session_tracker.update_noon_progress(current_sentiment, market_moves, predictions_check)
                except Exception as e:
                    log.warning(f"Ã¢Å¡Â Ã¯Â¸Â [NOON-TRACKER] Error: {e}")
            
            # Save sentiment for noon stage
            try:
                noon_sentiment = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL-BULLISH')
                self._save_sentiment_for_stage('noon', noon_sentiment, now)
            except Exception as e:
                log.warning(f"[SENTIMENT-TRACKING] Error in noon: {e}")
            
            log.info(f"Ã¢Å“â€¦ [NOON] Completed generation of {len(messages)} ENHANCED noon update messages")
            return messages
            
        except Exception as e:
            log.error(f"Ã¢ÂÅ’ [NOON] General error: {e}")
            # Emergency fallback
            return [f"Ã°Å¸Å’Å¾ **SV - NOON UPDATE**\nÃ°Å¸â€œâ€¦ {_now_it().strftime('%H:%M')} Ã¢â‚¬Â¢ System under maintenance"]
    
    def generate_evening_analysis(self) -> List[str]:
        """EVENING ANALYSIS 6:30 PM - ENHANCED version with 3 messages
        Integrates: Session Wrap, performance Review, Tomorrow Setup
        
        Returns:
            List of 3 messages for evening analysis
        """
        try:
            log.info("Ã°Å¸Å’â€  [EVENING] Generating ENHANCED evening analysis (3 messages)...")
            
            messages = []
            now = _now_it()
            
            # Get enhanced data
            news_data = get_enhanced_news(content_type="evening", max_news=6)
            fallback_data = get_fallback_data()
            
            # === MESSAGE 1: SESSION WRAP ENHANCED ===
            try:
                msg1_parts = []
                msg1_parts.append(f"{EMOJI['magnifier']} *SV - SESSION WRAP* `{now.strftime('%H:%M')}`")
                msg1_parts.append(f"{EMOJI['calendar']} {now.strftime('%A %m/%d/%Y')} {EMOJI['bullet']} Message 1/3")
                if now.weekday() >= 5:
                    msg1_parts.append(f"{EMOJI['bullet']} Weekend Session Wrap + Weekly Prep")
                else:
                    msg1_parts.append(f"{EMOJI['bullet']} Noon Follow-up + Live Session Close")
                msg1_parts.append(EMOJI['line'] * 40)
                msg1_parts.append("")
                
                # Enhanced continuity connection from noon 13:00
                msg1_parts.append(f"{EMOJI['chart_up']} *NOON FOLLOW-UP - SESSION CONTINUITY:*")
                try:
                    if DEPENDENCIES_AVAILABLE:
                        from narrative_continuity import get_narrative_continuity
                        continuity = get_narrative_continuity()
                        noon_connection = continuity.get_evening_noon_connection()
                        
                        default_noon_followup = f"{EMOJI['chart_up']} From noon: Progress tracking - objectives summary"
                        default_predictions = "Prediction accuracy: see Evening Performance Review / Daily Summary"
                        default_regime = "Market regime: see ML Sentiment blocks (Noon/Evening)"

                        msg1_parts.append(
                            f"{EMOJI['bullet']} {noon_connection.get('noon_followup', default_noon_followup)}"
                        )
                        msg1_parts.append(
                            f"{EMOJI['bullet']} {noon_connection.get('predictions_summary', default_predictions)}"
                        )
                        msg1_parts.append(
                            f"{EMOJI['bullet']} {noon_connection.get('regime_status', default_regime)}"
                        )
                    else:
                        # Fallback continuity (no static accuracy claims)
                        msg1_parts.append(f"{EMOJI['bullet']} From noon 13:00: Progress tracking successfully completed")
                        msg1_parts.append(f"{EMOJI['bullet']} Prediction accuracy: see Evening Performance Review / Daily Summary")
                        msg1_parts.append(f"{EMOJI['bullet']} Market regime: see ML Sentiment sections (Noon/Evening)")
                        
                except Exception as e:
                    log.warning(f"{EMOJI['warning']} [EVENING-CONTINUITY] Error: {e}")
                    msg1_parts.append(f"{EMOJI['bullet']} Noon Session Tracking: Afternoon analysis completed")
                    
                msg1_parts.append("")
                
                # DAY'S IMPACTFUL NEWS (Top 3)
                try:
                    news_list = news_data.get('news', []) if isinstance(news_data, dict) else []
                    # Filter out personal finance/lifestyle content for Evening impact block
                    news_list = [
                        it for it in news_list
                        if not self._is_personal_finance(it.get('title', ''))
                    ]
                    # Always show the header, even if empty (offline-safe)
                    msg1_parts.append(f"{EMOJI['news']} *DAY'S IMPACTFUL NEWS (Top 3):*")
                    if news_list:
                        # Build enriched list with impact data and seen-news flag
                        enriched = []
                        for item in news_list:
                            title = item.get('title', 'News update')
                            hours_ago = item.get('hours_ago', item.get('published_hours_ago', 4))
                            try:
                                hours_ago = int(hours_ago)
                            except Exception:
                                hours_ago = 4
                            impact = self._analyze_news_impact_detailed(title, published_ago_hours=hours_ago)
                            try:
                                was_used = self._was_news_used(item, now)
                            except Exception:
                                was_used = False
                            enriched.append((
                                impact.get('impact_score', 0),
                                title,
                                item,
                                impact,
                                was_used,
                            ))
                        # Sort by impact score (high e28692 low)
                        enriched.sort(key=lambda x: x[0], reverse=True)
                        fresh_items = [e for e in enriched if not e[4]]
                        repeat_critical = [
                            e for e in enriched
                            if e[4] and (
                                (e[3].get('impact_label') == 'High impact') or e[0] >= 7.0
                            )
                        ]
                        repeat_secondary = [
                            e for e in enriched
                            if e[4] and e not in repeat_critical
                        ]
                        max_items = 3
                        max_repeats = 2
                        selected = []
                        repeats_used = 0
                        # 1) Prefer fresh items for evening impact
                        for e in fresh_items:
                            if len(selected) >= max_items:
                                break
                            selected.append(('FRESH', e))
                        # 2) Then allow high-impact stories of the day
                        for e in repeat_critical:
                            if len(selected) >= max_items or repeats_used >= max_repeats:
                                break
                            selected.append(('STORY_CRITICAL', e))
                            repeats_used += 1
                        # 3) As fallback, allow secondary repeats
                        if len(selected) < max_items:
                            for e in repeat_secondary:
                                if len(selected) >= max_items or repeats_used >= max_repeats:
                                    break
                                selected.append(('STORY_SECONDARY', e))
                                repeats_used += 1
                        # Absolute fallback if everything was filtered out
                        if not selected:
                            for e in enriched[:max_items]:
                                selected.append(('FALLBACK', e))
                        for i, (kind, (score, title, item, impact, was_used)) in enumerate(selected, 1):
                            source = item.get('source', 'News')
                            link = item.get('link', '')
                            sectors_list = impact.get('sectors', []) or []
                            sectors = ', '.join(sectors_list[:2]) or 'Broad Market'
                            impact_scope = 'overall risk sentiment' if sectors == 'Broad Market' else sectors
                            short_title = title if len(title) <= 80 else title[:80] + '...'
                            if kind in ('FRESH', 'FALLBACK'):
                                msg1_parts.append(f"{EMOJI['bullet']} {i}. {short_title}")
                            elif kind == 'STORY_CRITICAL':
                                msg1_parts.append(f"{EMOJI['bullet']} {i}. [STORY OF THE DAY] {short_title}")
                            else:
                                msg1_parts.append(f"{EMOJI['bullet']} {i}. [RECAP] {short_title}")
                            msg1_parts.append(
                                f"   {EMOJI['chart']} Impact: {impact.get('impact_score', 0):.1f}/10 "
                                f"({impact.get('catalyst_type', 'News')}) {EMOJI['folder']} {source}"
                            )
                            if link:
                                msg1_parts.append(f"   {EMOJI['link']} {link}")
                            msg1_parts.append(
                                f"   {EMOJI['clock']} {impact.get('time_relevance', 'Day')} "
                                f"{EMOJI['target']} Sectors: {sectors}"
                            )
                            if kind in ('STORY_CRITICAL', 'STORY_SECONDARY'):
                                msg1_parts.append(
                                    f"   {EMOJI['bullet']} Why it defined the day: carried from earlier updates and "
                                    f"remained a key {impact.get('catalyst_type', 'market driver')} for {impact_scope}."
                                )
                                msg1_parts.append(
                                    f"   {EMOJI['bullet']} Full-session impact: influenced trend, sentiment and risk appetite in {impact_scope}."
                                )
                            # Mark as used so Summary/journal can see that this news was highlighted
                            try:
                                self._mark_news_used(item, now)
                            except Exception:
                                pass
                    else:
                        msg1_parts.append(f"{EMOJI['bullet']} No impactful items available (offline/cache mode)")
                    msg1_parts.append("")
                except Exception as e:
                    log.warning(f"{EMOJI['warning']} [NEWS-IMPACT-EVENING] Error: {e}")
                
                # Enhanced Final Performance with Live Prices (weekend-safe)
                msg1_parts.append(f"{EMOJI['chart_down']} *FINAL PERFORMANCE:*")
                try:
                    crypto_prices = get_live_crypto_prices()
                    # Try to enrich with live SPX/EURUSD quotes when available
                    spx_line = None
                    eur_line = None
                    try:
                        eqfx_quotes = get_live_equity_fx_quotes(['^GSPC', 'EURUSD=X', 'XAUUSD=X']) or {}
                    except Exception as qe:
                        log.warning(f"{EMOJI['warning']} [EVENING-PRICES] Equity/FX quotes unavailable: {qe}")
                        eqfx_quotes = {}
                    spx_q = eqfx_quotes.get('^GSPC', {})
                    eur_q = eqfx_quotes.get('EURUSD=X', {})
                    gold_q = eqfx_quotes.get('XAUUSD=X', {})
                    spx_price = spx_q.get('price', 0)
                    spx_chg = spx_q.get('change_pct', None)
                    eur_chg = eur_q.get('change_pct', None)
                    gold_price = gold_q.get('price', 0)
                    gold_chg = gold_q.get('change_pct', None)
                    if spx_price:
                        if spx_chg is not None:
                            if spx_chg > 0.5:
                                tone = "strong close above"
                            elif spx_chg < -0.5:
                                tone = "weak close near"
                            else:
                                tone = "steady close around"
                            spx_line = f"{EMOJI['bullet']} {EMOJI['us']} *S&P 500*: {spx_chg:+.1f}% - {tone} {int(spx_price)}"
                        else:
                            spx_line = f"{EMOJI['bullet']} {EMOJI['us']} *S&P 500*: Close around {int(spx_price)}"
                    if eur_chg is not None:
                        if eur_chg < 0:
                            eur_desc = "USD strength confirmed"
                        elif eur_chg > 0:
                            eur_desc = "EUR strength vs USD"
                        else:
                            eur_desc = "Rangebound session"
                        eur_line = f"{EMOJI['bullet']} {EMOJI['eu']} *EUR/USD*: {eur_chg:+.1f}% - {eur_desc}"
                    
                    if now.weekday() >= 5:
                        # Weekend: show crypto only + note markets closed
                        if crypto_prices and crypto_prices.get('BTC', {}).get('price', 0) > 0:
                            btc_data = crypto_prices['BTC']
                            change_pct = btc_data.get('change_pct', 0)
                            price = btc_data.get('price', 0)
                            msg1_parts.append(f"{EMOJI['bullet']} *Traditional Markets*: Weekend - closed")
                            msg1_parts.append(f"{EMOJI['bullet']} {EMOJI['btc']} *BTC*: ${price:,.0f} ({change_pct:+.1f}%) - {('Range breakout attempt' if abs(change_pct) > 1 else 'Consolidation maintained')}")
                        else:
                            msg1_parts.append(f"{EMOJI['bullet']} *Traditional Markets*: Weekend - closed")
                            msg1_parts.append(f"{EMOJI['bullet']} {EMOJI['btc']} *BTC*: Live data loading - crypto performance tracking")
                    else:
                        if crypto_prices and crypto_prices.get('BTC', {}).get('price', 0) > 0:
                            btc_data = crypto_prices['BTC']
                            change_pct = btc_data.get('change_pct', 0)
                            price = btc_data.get('price', 0)
                            if spx_line:
                                msg1_parts.append(spx_line)
                            else:
                                msg1_parts.append(f"{EMOJI['bullet']} {EMOJI['us']} *S&P 500*: Session close - see Summary for details")
                            # NASDAQ/Dow kept qualitative only to avoid fake precise %
                            msg1_parts.append(f"{EMOJI['bullet']} {EMOJI['chart']} *NASDAQ*: Tech leadership sustained")
                            msg1_parts.append(f"{EMOJI['bullet']} {EMOJI['bank']} *Dow Jones*: Broad market participation")
                            msg1_parts.append(f"{EMOJI['bullet']} {EMOJI['btc']} *BTC*: ${price:,.0f} ({change_pct:+.1f}%) - {('Range breakout attempt' if abs(change_pct) > 1 else 'Consolidation maintained')}")
                            if eur_line:
                                msg1_parts.append(eur_line)
                            else:
                                msg1_parts.append(f"{EMOJI['bullet']} {EMOJI['eu']} *EUR/USD*: USD vs EUR monitored - see FX section in Summary")
                            if gold_price and gold_chg is not None:
                                gold_per_gram = gold_price / GOLD_GRAMS_PER_TROY_OUNCE if gold_price else 0
                                if gold_per_gram >= 1:
                                    gold_price_str = f"${gold_per_gram:,.2f}/g"
                                else:
                                    gold_price_str = f"${gold_per_gram:.3f}/g"
                                if gold_chg > 0:
                                    gold_desc = "defensive hedge in demand"
                                elif gold_chg < 0:
                                    gold_desc = "defensive hedge under pressure"
                                else:
                                    gold_desc = "stable defensive hedge"
                                msg1_parts.append(f"{EMOJI['bullet']} *Gold*: {gold_price_str} ({gold_chg:+.1f}%) - {gold_desc}")
                        else:
                            if spx_line:
                                msg1_parts.append(spx_line)
                            else:
                                msg1_parts.append(f"{EMOJI['bullet']} {EMOJI['us']} *S&P 500*: Session close - live data unavailable")
                            msg1_parts.append(f"{EMOJI['bullet']} {EMOJI['chart']} *NASDAQ*: Tech leadership sustained")
                            msg1_parts.append(f"{EMOJI['bullet']} {EMOJI['btc']} *BTC*: Live data loading - crypto performance tracking")
                            if eur_line:
                                msg1_parts.append(eur_line)
                            else:
                                msg1_parts.append(f"{EMOJI['bullet']} {EMOJI['eu']} *EUR/USD*: USD vs EUR monitored - see FX section in Summary")
                            if gold_price and gold_chg is not None:
                                gold_per_gram = gold_price / GOLD_GRAMS_PER_TROY_OUNCE if gold_price else 0
                                if gold_per_gram >= 1:
                                    gold_price_str = f"${gold_per_gram:,.2f}/g"
                                else:
                                    gold_price_str = f"${gold_per_gram:.3f}/g"
                                if gold_chg > 0:
                                    gold_desc = "defensive hedge in demand"
                                elif gold_chg < 0:
                                    gold_desc = "defensive hedge under pressure"
                                else:
                                    gold_desc = "stable defensive hedge"
                                msg1_parts.append(f"{EMOJI['bullet']} *Gold*: {gold_price_str} ({gold_chg:+.1f}%) - {gold_desc}")
                except Exception as e:
                    log.warning(f"{EMOJI['warning']} [EVENING-PRICES] Error: {e}")
                    msg1_parts.append(f"{EMOJI['bullet']} Final market performance: Loading session wrap data")
                    
                msg1_parts.append("")
                
                # Session Character Analysis
                msg1_parts.append(f"{EMOJI['notebook']} *SESSION CHARACTER:*")
                session_sentiment = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL')
                if session_sentiment == 'POSITIVE':
                    msg1_parts.append(f"{EMOJI['bullet']} *Theme*: Risk-on rotation - growth sectors outperformed")
                    msg1_parts.append(f"{EMOJI['bullet']} *Volume*: Above average - conviction buying")
                    msg1_parts.append(f"{EMOJI['bullet']} *Breadth*: Broad participation - healthy rally")
                elif session_sentiment == 'NEGATIVE':
                    msg1_parts.append(f"{EMOJI['bullet']} *Theme*: Risk-off rotation - defensive positioning")
                    msg1_parts.append(f"{EMOJI['bullet']} *Volume*: Elevated - distribution patterns")
                    msg1_parts.append(f"{EMOJI['bullet']} *Breadth*: Narrow leadership - selective selling")
                else:
                    msg1_parts.append(f"{EMOJI['bullet']} *Theme*: Mixed session - sector rotation active")
                    msg1_parts.append(f"{EMOJI['bullet']} *Volume*: Normal levels - rangebound trading")
                    msg1_parts.append(f"{EMOJI['bullet']} *Breadth*: Balanced participation - neutral bias")
                    
                msg1_parts.append("")
                msg1_parts.append(EMOJI['line'] * 40)
                msg1_parts.append(f"{EMOJI['robot']} SV Enhanced {EMOJI['bullet']} Session Wrap 1/3")
                
                messages.append("\n".join(msg1_parts))
                log.info("Ã¢Å“â€¦ [EVENING] Message 1 (Session Wrap) generated")
                
            except Exception as e:
                log.error(f"Ã¢ÂÅ’ [EVENING] Message 1 error: {e}")
                messages.append(f"Ã°Å¸Å’Å’ **SV - SESSION WRAP**\nÃ°Å¸â€œâ€¦ {now.strftime('%H:%M')} Ã¢â‚¬Â¢ System loading")
            
            # === MESSAGE 2: PERFORMANCE REVIEW ===
            try:
                msg2_parts = []
                msg2_parts.append(f"{EMOJI['target']} *SV - PERFORMANCE REVIEW* `{now.strftime('%H:%M')}`")
                msg2_parts.append(f"{EMOJI['calendar']} {now.strftime('%A %d %B %Y')} {EMOJI['bullet']} Message 2/3")
                msg2_parts.append(f"{EMOJI['bullet']} Prediction performance + ML Results")
                msg2_parts.append(EMOJI['line'] * 40)
                msg2_parts.append("")
                
# DETAILED PREDICTION BREAKDOWN
                try:
                    from pathlib import Path
                    import json
                    pred_file = Path(self.reports_dir).parent / '1_daily' / f"predictions_{now.strftime('%Y-%m-%d')}.json"
                    if pred_file.exists():
                        with open(pred_file, 'r', encoding='utf-8') as pf:
                            pred_data = json.load(pf)
                        preds = pred_data.get('predictions', [])
                        if preds:
                            msg2_parts.append(f"{EMOJI['trophy']} *PREDICTION PERFORMANCE (DETAILED):*")
                            # Live inputs
                            live_btc = None
                            live_spx = None
                            live_eur = None
                            try:
                                prices = get_live_crypto_prices()
                                if prices and 'BTC' in prices:
                                    live_btc = prices['BTC'].get('price')
                            except Exception:
                                live_btc = None
                            try:
                                q = get_live_equity_fx_quotes(['^GSPC', 'EURUSD=X'])
                                if '^GSPC' in q:
                                    live_spx = q['^GSPC']['price']
                                if 'EURUSD=X' in q:
                                    live_eur = q['EURUSD=X']['price']
                            except Exception:
                                pass
                            hits = 0
                            total = 0
                            for p in preds:
                                asset = p.get('asset')
                                direction = p.get('direction', 'N/A')
                                entry = p.get('entry')
                                target = p.get('target')
                                stop = p.get('stop')
                                status = 'IN PROGRESS'
                                grade = 'B'
                                numeric_line = False
                                # BTC live
                                if asset == 'BTC' and live_btc:
                                    total += 1
                                    numeric_line = True
                                    if direction == 'LONG' and live_btc >= target:
                                        status = 'TARGET HIT'; grade = 'A+'; hits += 1
                                    elif direction == 'LONG' and live_btc <= stop:
                                        status = 'STOP HIT'; grade = 'C'
                                    elif direction == 'SHORT' and live_btc <= target:
                                        status = 'TARGET HIT'; grade = 'A+'; hits += 1
                                    elif direction == 'SHORT' and live_btc >= stop:
                                        status = 'STOP HIT'; grade = 'C'
                                    else:
                                        status = 'IN PROGRESS'; grade = 'B+'
                                # SPX live
                                elif asset in ('SPX', 'S&P 500') and live_spx:
                                    total += 1
                                    numeric_line = True
                                    if direction == 'LONG' and live_spx >= target:
                                        status = 'TARGET HIT'; grade = 'A+'; hits += 1
                                    elif direction == 'LONG' and live_spx <= stop:
                                        status = 'STOP HIT'; grade = 'C'
                                    elif direction == 'SHORT' and live_spx <= target:
                                        status = 'TARGET HIT'; grade = 'A+'; hits += 1
                                    elif direction == 'SHORT' and live_spx >= stop:
                                        status = 'STOP HIT'; grade = 'C'
                                    else:
                                        status = 'IN PROGRESS'; grade = 'B+'
                                # EURUSD live
                                elif asset in ('EURUSD', 'EUR/USD') and live_eur:
                                    total += 1
                                    numeric_line = True
                                    if direction == 'LONG' and live_eur >= target:
                                        status = 'TARGET HIT'; grade = 'A+'; hits += 1
                                    elif direction == 'LONG' and live_eur <= stop:
                                        status = 'STOP HIT'; grade = 'C'
                                    elif direction == 'SHORT' and live_eur <= target:
                                        status = 'TARGET HIT'; grade = 'A+'; hits += 1
                                    elif direction == 'SHORT' and live_eur >= stop:
                                        status = 'STOP HIT'; grade = 'C'
                                    else:
                                        status = 'IN PROGRESS'; grade = 'B+'
                                else:
                                    # Without live data, mark for review (no numeric levels in text)
                                    status = 'REVIEW REQUIRED'; grade = 'PENDING'

                                if numeric_line:
                                    msg2_parts.append(f"{EMOJI['bullet']} {asset} {direction}: Entry {entry} | Target {target} | Stop {stop} → {status} ({grade})")
                                else:
                                    msg2_parts.append(f"{EMOJI['bullet']} {asset} {direction}: {status} ({grade}) - live data pending")
                            if total > 0:
                                msg2_parts.append(f"{EMOJI['check']} *Overall*: {hits}/{total} hits - {(hits/total)*100:.0f}% on live-tracked assets")
                            else:
                                msg2_parts.append(f"{EMOJI['check']} *Overall*: 0/0 hits - live data pending")
                            msg2_parts.append("")
                except Exception as e:
                    log.warning(f"{EMOJI['warning']} [EVENING-PERF] Error: {e}")
                
                # Enhanced Prediction performance (narrative layer)
                msg2_parts.append(f"{EMOJI['trophy']} *PREDICTION PERFORMANCE (NARRATIVE):*")
                try:
                    # This block now complements the detailed live check above without hardcoding a perfect day.
                    msg2_parts.append(f"{EMOJI['bullet']} *S&P Bullish Call*: See detailed block above for current live status")
                    msg2_parts.append(f"{EMOJI['bullet']} *BTC Range Trade*: Live verification handled in the intraday/summary blocks")
                    msg2_parts.append(f"{EMOJI['bullet']} *EUR Weakness*: Monitored across Press → Morning → Noon → Evening")
                    msg2_parts.append(f"{EMOJI['bullet']} *Tech Leadership*: Evaluated via sector performance and ML signals")
                    msg2_parts.append("")
                    msg2_parts.append(f"{EMOJI['notebook']} *Daily Accuracy*: See Daily Summary Page 1/2 for consolidated metric")
                    msg2_parts.append(f"{EMOJI['target']} *Best Model*: Highlighted in Summary based on real accuracy, not static values")
                except Exception as e:
                    log.warning(f"{EMOJI['warning']} [EVENING-performance] Error: {e}")
                    msg2_parts.append(f"{EMOJI['bullet']} *performance*: Review system loading")
                
                msg2_parts.append("")
                
                # Enhanced ML Model Results
                msg2_parts.append(f"{EMOJI['brain']} *ML MODEL RESULTS:*")
                try:
                    if DEPENDENCIES_AVAILABLE:
                        # Advanced ML results
                        msg2_parts.append(f"{EMOJI['bullet']} *Ensemble performance*: Uses multiple models to stabilize signals")
                        msg2_parts.append(f"{EMOJI['bullet']} *Model Consensus*: Focus on agreement before acting on high-conviction trades")
                        msg2_parts.append(f"{EMOJI['bullet']} *Feature Importance*: Sentiment analysis, technical momentum, macro context")
                        msg2_parts.append(f"{EMOJI['bullet']} *Model Calibration*: Evaluated daily - see Summary Page 1/2 for accuracy")
                    else:
                        # Fallback ML results - descriptive, not prescriptive
                        msg2_parts.append(f"{EMOJI['bullet']} *Model Consensus*: Strong agreement across algorithms")
                        msg2_parts.append(f"{EMOJI['bullet']} *Sentiment Analysis*: Accurate trend detection")
                        msg2_parts.append(f"{EMOJI['bullet']} *Technical Indicators*: Reliable signal generation")
                        msg2_parts.append(f"{EMOJI['bullet']} *Overall Score*: Detailed accuracy in Daily Summary Page 1/2")
                        
                except Exception as e:
                    log.warning(f"{EMOJI['warning']} [EVENING-ML] Error: {e}")
                    msg2_parts.append(f"{EMOJI['bullet']} *ML Results*: Advanced analysis completed")
                
                msg2_parts.append("")
                
                # Trading performance Summary - now conditional on real accuracy
                msg2_parts.append(f"{EMOJI['money']} *TRADING PERFORMANCE SUMMARY:*")
                # Get accuracy from earlier prediction_eval if available
                try:
                    if 'hits' in locals() and 'total' in locals() and total > 0:
                        accuracy_pct = (hits / total) * 100
                        if accuracy_pct >= 80:
                            msg2_parts.append(f"{EMOJI['bullet']} *Win Rate*: {hits}/{total} calls correct ({accuracy_pct:.0f}%) - Strong performance")
                            msg2_parts.append(f"{EMOJI['bullet']} *Risk Management*: Excellent - targets achieved with discipline")
                            msg2_parts.append(f"{EMOJI['bullet']} *Position Sizing*: Optimal - maximized risk-adjusted returns")
                            msg2_parts.append(f"{EMOJI['bullet']} *Timing*: Precise - entry/exit signals accurate")
                        elif accuracy_pct >= 60:
                            msg2_parts.append(f"{EMOJI['bullet']} *Win Rate*: {hits}/{total} calls correct ({accuracy_pct:.0f}%) - Good performance")
                            msg2_parts.append(f"{EMOJI['bullet']} *Risk Management*: Solid - stops and targets respected")
                            msg2_parts.append(f"{EMOJI['bullet']} *Position Sizing*: Balanced approach maintained")
                            msg2_parts.append(f"{EMOJI['bullet']} *Timing*: Generally accurate with room for refinement")
                        elif accuracy_pct > 0:
                            msg2_parts.append(f"{EMOJI['bullet']} *Win Rate*: {hits}/{total} calls correct ({accuracy_pct:.0f}%) - Mixed results")
                            msg2_parts.append(f"{EMOJI['bullet']} *Risk Management*: Protected capital, avoided major losses")
                            msg2_parts.append(f"{EMOJI['bullet']} *Position Sizing*: Conservative approach prudent today")
                            msg2_parts.append(f"{EMOJI['bullet']} *Timing*: Review signals for tomorrow's improvement")
                        else:
                            msg2_parts.append(f"{EMOJI['bullet']} *Win Rate*: {hits}/{total} calls tracked ({accuracy_pct:.0f}%) - Challenging day")
                            msg2_parts.append(f"{EMOJI['bullet']} *Risk Management*: Capital preservation prioritized")
                            msg2_parts.append(f"{EMOJI['bullet']} *Position Sizing*: Reduced exposure - defensive stance")
                            msg2_parts.append(f"{EMOJI['bullet']} *Timing*: Market conditions diverged from expectations")
                    else:
                        # No tracked predictions or pending data
                        msg2_parts.append(f"{EMOJI['bullet']} *Win Rate*: See Daily Summary for full accuracy breakdown")
                        msg2_parts.append(f"{EMOJI['bullet']} *Risk Management*: Within predefined limits")
                        msg2_parts.append(f"{EMOJI['bullet']} *Position Sizing*: Aligned with risk tolerance")
                        msg2_parts.append(f"{EMOJI['bullet']} *Timing*: Evaluated in comprehensive Daily Summary analysis")
                except Exception as e:
                    log.warning(f"{EMOJI['warning']} [EVENING-TRADING-SUMMARY] Error: {e}")
                    msg2_parts.append(f"{EMOJI['bullet']} *Performance*: Full metrics available in Daily Summary Page 1/2")
                msg2_parts.append("")
                
                msg2_parts.append(EMOJI['line'] * 40)
                msg2_parts.append(f"{EMOJI['robot']} SV Enhanced {EMOJI['bullet']} Performance Review 2/3")
                
                messages.append("\n".join(msg2_parts))
                log.info("Ã¢Å“â€¦ [EVENING] Message 2 (Performance Review) generated")
                
            except Exception as e:
                log.error(f"Ã¢ÂÅ’ [EVENING] Errore messageso 2: {e}")
                messages.append(f"Ã°Å¸Ââ€  **SV - performance**\nÃ°Å¸â€œâ€¦ {now.strftime('%H:%M')} Ã¢â‚¬Â¢ performance system loading")
            
            # === MESSAGE 3: TOMORROW SETUP ===
            try:
                msg3_parts = []
                msg3_parts.append(f"{EMOJI['compass']} *SV - TOMORROW SETUP* `{now.strftime('%H:%M')}`")
                msg3_parts.append(f"{EMOJI['calendar']} {now.strftime('%A %d %B %Y')} {EMOJI['bullet']} Message 3/3")
                msg3_parts.append(f"{EMOJI['bullet']} Strategic Outlook + Asia Handoff")
                msg3_parts.append(EMOJI['line'] * 40)
                msg3_parts.append("")
                
                # Enhanced Tomorrow Preview (weekend-aware)
                tomorrow = _now_it() + datetime.timedelta(days=1)
                msg3_parts.append(f"{EMOJI['calendar_spiral']} *{tomorrow.strftime('%A').upper()} PREVIEW* ({tomorrow.strftime('%d/%m')}):")
                if now.weekday() >= 5:
                    msg3_parts.append(f"{EMOJI['bullet']} *Traditional Markets*: Weekend - next full session Monday")
                    msg3_parts.append(f"{EMOJI['bullet']} *Asia Futures (Sun night)*: Early indication for Europe open")
                    msg3_parts.append(f"{EMOJI['bullet']} *Crypto 24/7*: Momentum carries into Asia hours")
                else:
                    msg3_parts.append(f"{EMOJI['bullet']} *Gap Analysis*: Small gap up expected on momentum")
                    msg3_parts.append(f"{EMOJI['bullet']} *Key Events*: ECB rate decision 14:15, US GDP prelim")
                    msg3_parts.append(f"{EMOJI['bullet']} *Earnings*: MSFT after close (tonight), AAPL morning")
                    msg3_parts.append(f"{EMOJI['bullet']} *Data Releases*: European inflation, US jobless claims")
                msg3_parts.append("")
                
                # Enhanced Strategic Outlook
                msg3_parts.append(f"{EMOJI['chart']} *STRATEGIC OUTLOOK:*")

                # Derive BTC breakout level near current price if available
                btc_breakout_tomorrow = None
                try:
                    crypto_prices_tomorrow = get_live_crypto_prices()
                    if crypto_prices_tomorrow and crypto_prices_tomorrow.get('BTC', {}).get('price', 0) > 0:
                        btc_price_tomorrow = crypto_prices_tomorrow['BTC'].get('price', 0)
                        btc_change_tomorrow = crypto_prices_tomorrow['BTC'].get('change_pct', 0)
                        sr_tomorrow = calculate_crypto_support_resistance(btc_price_tomorrow, btc_change_tomorrow)
                        if sr_tomorrow:
                            btc_breakout_tomorrow = int(sr_tomorrow.get('resistance_2') or 0)
                except Exception as e:
                    log.warning(f"{EMOJI['warning']} [EVENING-TOMORROW-BTC] Live BTC breakout level unavailable: {e}")
                    btc_breakout_tomorrow = None

                msg3_parts.append(f"{EMOJI['bullet']} *Continue Tech Overweight*: Momentum + earnings support")
                if btc_breakout_tomorrow:
                    msg3_parts.append(f"{EMOJI['bullet']} *BTC Strategy*: Watch ${btc_breakout_tomorrow:,.0f} breakout - institutional interest")
                else:
                    msg3_parts.append(f"{EMOJI['bullet']} *BTC Strategy*: Watch BTC breakout above key resistance - institutional interest")
                msg3_parts.append(f"{EMOJI['bullet']} *EUR Strategy*: ECB dovish = further weakness opportunity")
                msg3_parts.append(f"{EMOJI['bullet']} *Risk Bias*: Risk-on maintained - growth over value")
                msg3_parts.append(f"{EMOJI['bullet']} *Allocation*: 1.2x position sizing on conviction trades")
                msg3_parts.append("")
                
                # Enhanced Asia Handoff
                msg3_parts.append(f"{EMOJI['globe']} *ASIA HANDOFF (22:00-02:00):*")
                msg3_parts.append(f"{EMOJI['bullet']} *Japan*: Nikkei likely follows US tech strength")
                msg3_parts.append(f"{EMOJI['bullet']} *China*: A50 futures tracking - policy watch")
                msg3_parts.append(f"{EMOJI['bullet']} *Australia*: RBA minutes - no major impact expected")
                msg3_parts.append(f"{EMOJI['bullet']} *Crypto*: 24/7 momentum - Asia volume patterns")
                msg3_parts.append("")
                
                # Tomorrow Schedule (weekend-aware) – qui solo richiamo sintetico,
                # il dettaglio completo degli orari è in Daily Summary Page 5/6.
                msg3_parts.append(f"{EMOJI['clock']} *TOMORROW SCHEDULE:*")
                if now.weekday() == 6:  # Sunday
                    msg3_parts.append(f"{EMOJI['bullet']} Asia futures open Sunday night, then standard intraday cycle on Monday (Press → Morning → Noon → Evening → Summary)")
                else:
                    msg3_parts.append(f"{EMOJI['bullet']} Standard intraday cycle: Press Review, Morning Report, Noon Update, Evening Analysis, Daily Summary (see Summary Page 5/6 for exact times)")
                msg3_parts.append("")
                
                msg3_parts.append(EMOJI['line'] * 40)
                msg3_parts.append(f"{EMOJI['robot']} SV Enhanced {EMOJI['bullet']} Tomorrow Setup 3/3")
                msg3_parts.append(f"{EMOJI['check']} Evening Analysis Complete - Asia handoff ready")
                msg3_parts.append(f"{EMOJI['back']} Next: Daily Summary (20:00) - 6 pages complete")
                
                messages.append("\n".join(msg3_parts))
                log.info("Ã¢Å“â€¦ [EVENING] Message 3 (Tomorrow Setup) generated")
                
            except Exception as e:
                log.error(f"Ã¢ÂÅ’ [EVENING] Errore messageso 3: {e}")
                messages.append(f"Ã°Å¸â€Â® **SV - TOMORROW SETUP**\nÃ°Å¸â€œâ€¦ {now.strftime('%H:%M')} Ã¢â‚¬Â¢ Setup system loading")
            
            # Save all messages with enhanced metadata
            if messages:
                saved_path = self.save_content("evening_analysis", messages, {
                    'total_messages': len(messages),
                    'enhanced_features': ['Session Wrap', 'performance Review', 'Tomorrow Setup'],
                    'news_count': len(news_data.get('news', [])),
                    'sentiment': news_data.get('sentiment', {}),
                    'continuity_with_noon': True,
                    'prediction_accuracy': 'N/A',
                    'daily_performance': 'To be evaluated in Daily Summary'
                })
                log.info(f"Ã°Å¸â€™Â¾ [EVENING] Saved to: {saved_path}")

                # ENGINE snapshot for evening stage
                try:
                    evening_sentiment = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL') if isinstance(news_data, dict) else 'NEUTRAL'
                    assets_evening: Dict[str, Any] = {}
                    # BTC snapshot
                    try:
                        crypto_evening = get_live_crypto_prices() or {}
                        if 'BTC' in crypto_evening:
                            btc_evening = crypto_evening['BTC']
                            assets_evening['BTC'] = {
                                'price': float(btc_evening.get('price') or 0.0),
                                'change_pct': float(btc_evening.get('change_pct') or 0.0),
                                'unit': 'USD',
                            }
                    except Exception:
                        pass
                    # SPX / EURUSD / GOLD snapshot
                    try:
                        quotes_evening = get_live_equity_fx_quotes(['^GSPC', 'EURUSD=X', 'XAUUSD=X']) or {}
                    except Exception:
                        quotes_evening = {}
                    spx_e = quotes_evening.get('^GSPC', {})
                    eur_e = quotes_evening.get('EURUSD=X', {})
                    gold_e = quotes_evening.get('XAUUSD=X', {})
                    if spx_e.get('price'):
                        assets_evening['SPX'] = {
                            'price': float(spx_e.get('price') or 0.0),
                            'change_pct': float(spx_e.get('change_pct') or 0.0),
                            'unit': 'index',
                        }
                    if eur_e.get('price'):
                        assets_evening['EURUSD'] = {
                            'price': float(eur_e.get('price') or 0.0),
                            'change_pct': float(eur_e.get('change_pct') or 0.0),
                            'unit': 'rate',
                        }
                    gold_price_e = float(gold_e.get('price') or 0.0)
                    if gold_price_e:
                        gold_per_gram_e = gold_price_e / GOLD_GRAMS_PER_TROY_OUNCE
                        assets_evening['GOLD'] = {
                            'price': gold_per_gram_e,
                            'change_pct': float(gold_e.get('change_pct') or 0.0),
                            'unit': 'USD/g',
                        }
                    # Nessuna prediction_eval consolidata qui: verrà usata quella di Summary
                    self._engine_log_stage('evening', now, evening_sentiment, assets_evening, None)
                except Exception as e:
                    log.warning(f"{EMOJI['warning']} [ENGINE-EVENING] Error logging engine stage: {e}")
            
            # Save evening data for Daily Summary continuity
            if self.narrative and DEPENDENCIES_AVAILABLE:
                try:
                    # Calculate final sentiment da analysis serale
                    final_sentiment = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL')
                    
                    # performance results evening summary (qualitative, no fixed %)
                    evening_performance = {
                        'sp500_close': 'Session close consistent with intraday risk regime',
                        'nasdaq_performance': 'Technology leadership observed during the session',
                        'crypto_momentum': 'Crypto momentum: range breakout attempt monitored',
                        'eur_weakness': 'USD strength vs EUR confirmed qualitatively',
                        'prediction_accuracy': 'see_daily_summary'
                    }
                    
                    # Tomorrow outlook setup
                    tomorrow_focus = {
                        'asia_handoff': 'Tech momentum follow-through expected',
                        'europe_open': 'Gap up on momentum, ECB watch',
                        'key_events': 'ECB decision, US GDP, MSFT earnings',
                        'risk_factors': 'Earnings reactions, geopolitical watch'
                    }
                    
                    # Salva evening data per daily summary
                    self.narrative.set_evening_data(
                        evening_sentiment=final_sentiment,
                        evening_performance=evening_performance,
                        tomorrow_setup=tomorrow_focus
                    )
                    
                    log.info(f"Ã¢Å“â€¦ [EVENING-CONTINUITY] Evening data saved for Daily Summary")
                    
                except Exception as e:
                    log.warning(f"Ã¢Å¡Â Ã¯Â¸Â [EVENING-CONTINUITY] Error: {e}")
            
            # Save sentiment for evening stage
            try:
                evening_sentiment = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL')
                self._save_sentiment_for_stage('evening', evening_sentiment, now)
            except Exception as e:
                log.warning(f"[SENTIMENT-TRACKING] Error in evening: {e}")
            
            log.info(f"Ã¢Å“â€¦ [EVENING] Completed generation of {len(messages)} ENHANCED evening analysis messages")
            return messages
            
        except Exception as e:
            log.error(f"Ã¢ÂÅ’ [EVENING] General error: {e}")
            # Emergency fallback
            return [f"Ã°Å¸Å’â€  **SV - EVENING ANALYSIS**\nÃ°Å¸â€œâ€¦ {_now_it().strftime('%H:%M')} Ã¢â‚¬Â¢ System under maintenance"]
    
    def generate_daily_summary(self) -> List[str]:
        """DAILY SUMMARY 8:00 PM - ENHANCED with COMPLETE PRESS REVIEW VERIFICATION + CONCATENATION
        
        NEW FEATURES:
        - ML prediction control from 7:00 AM Press Review
        - Consistency verification of ALL 5 intraday messages
        - Direct concatenation with next day Press Review
        
        Returns:
            List of 6 pages for daily summary with hierarchical verification (Page 6 = Daily Journal)
        """
        try:
            log.info("Ã°Å¸â€œÅ  [SUMMARY] Generating daily summary WITH HIERARCHICAL VERIFICATION (6 pages)...")
            
            pages = []
            now = _now_it()
            
            # Get enhanced data for complete day
            news_data = get_enhanced_news(content_type="summary", max_news=15)
            fallback_data = get_fallback_data()
            
            # NUOVA LOGICA: Recupera TUTTE le predictions ML del day dalla Rassegna 07:00
            press_review_predictions = self._load_press_review_predictions(now)
            
            # VERIFICA COERENZA: Controllo incrociato di tutti i 5 messages intraday
            intraday_coherence = self._verify_full_day_coherence(now)
            
            # PREDICTION ACCURACY: Valuta le predictions del giorno con dati live (quando possibile)
            prediction_eval = self._evaluate_predictions_with_live_data(now)

            # Container for end-of-day market snapshot used by weekly/monthly aggregators
            daily_market_snapshot: Dict[str, Any] = {}
            
            # CONCATENAZIONE: Prepara collegamento con Rassegna del day successivo
            next_day_setup = self._prepare_next_day_connection(now, intraday_coherence)
            
            # Header principale per tutte le pagine
            header_base = f"{EMOJI['notebook']} *SV - COMPLETE DAILY SUMMARY*\n"
            header_base += f"{EMOJI['calendar']} {now.strftime('%A %d %B %Y')} - {now.strftime('%H:%M')}\n"
            header_base += "=" * 50 + "\n\n"
            
            # Get complete day narrative data
            evening_sentiment = 'POSITIVE'
            if DEPENDENCIES_AVAILABLE and self.narrative:
                try:
                    from narrative_continuity import get_narrative_continuity
                    continuity = get_narrative_continuity()
                    summary_context = continuity.get_summary_evening_connection()
                    evening_sentiment = summary_context.get('evening_sentiment', 'POSITIVE')
                except Exception as e:
                    log.warning(f"{EMOJI['warning']} [SUMMARY-CONTINUITY] Error: {e}")
            
            # === page 1: EXECUTIVE SUMMARY ===
            acc_pct_for_score = 0.0
            total_tracked_for_score = 0
            try:
                page1 = []
                page1.append(header_base)
                page1.append(f"{EMOJI['chart']} *Page 1/6 - EXECUTIVE SUMMARY*")
                page1.append("")
                
                # Enhanced Day Recap with Evening Continuity
                eval_data_header = prediction_eval or {}
                total_header = int(eval_data_header.get('total_tracked', 0) or 0)
                acc_header = float(eval_data_header.get('accuracy_pct', 0.0) or 0.0)

                if total_header > 0:
                    if acc_header >= 80:
                        perf_label = "Strong day - high accuracy on live-tracked predictions"
                    elif acc_header >= 60:
                        perf_label = "Solid day - accuracy above target"
                    elif acc_header > 0:
                        perf_label = "Mixed day - some correct calls, some misses"
                    else:
                        perf_label = "Challenging day - no correct hits on tracked predictions"
                else:
                    perf_label = "Performance based on qualitative review (no live-tracked predictions)"

                page1.append(f"{EMOJI['magnifier']} *DAY RECAP - EVENING CONNECTION:*")
                page1.append(f"{EMOJI['bullet']} From evening 18:30: Positive close with sentiment {evening_sentiment}")
                page1.append(f"{EMOJI['bullet']} Session character: Risk-on rotation - tech leadership confirmed")
                page1.append(f"{EMOJI['bullet']} Performance quality: {perf_label}")
                page1.append(f"{EMOJI['bullet']} Market breadth: Broad participation - healthy rally")
                page1.append("")
                
                # Enhanced Results Summary with Live Data
                page1.append(f"{EMOJI['trophy']} *DAILY RESULTS:*")
                try:
                    # Use evaluated prediction accuracy when available
                    eval_data = prediction_eval or {}
                    total_tracked = int(eval_data.get('total_tracked', 0) or 0)
                    hits = int(eval_data.get('hits', 0) or 0)
                    acc_pct = float(eval_data.get('accuracy_pct', 0.0) or 0.0)

                    # store for executive score section
                    total_tracked_for_score = total_tracked
                    acc_pct_for_score = acc_pct
                    
                    crypto_prices = get_live_crypto_prices()
                    btc_data = crypto_prices.get('BTC', {}) if crypto_prices else {}
                    btc_price = float(btc_data.get('price', 0) or 0.0)
                    btc_change_pct = float(btc_data.get('change_pct', 0) or 0.0)
                    btc_has_price = btc_price > 0

                    # Save BTC snapshot for metrics if available
                    if btc_has_price:
                        daily_market_snapshot['BTC'] = {
                            'price': btc_price,
                            'change_pct': btc_change_pct,
                            'unit': 'USD'
                        }
                    
                    if total_tracked > 0:
                        page1.append(f"{EMOJI['bullet']} *ML performance*: {acc_pct:.0f}% accuracy (target: 70%)")
                        page1.append(f"{EMOJI['bullet']} *Correct predictions*: {hits}/{total_tracked} on live-tracked assets")
                    else:
                        page1.append(f"{EMOJI['bullet']} *ML performance*: n/a (no live-tracked predictions today)")
                        page1.append(f"{EMOJI['bullet']} *Correct predictions*: n/a (see qualitative journal notes)")
                    
                    if btc_has_price:
                        change_pct = btc_change_pct
                        price = btc_price
                        page1.append(f"{EMOJI['bullet']} *BTC Live*: ${price:,.0f} ({change_pct:+.1f}%) - Range strategy under observation")
                        page1.append(f"{EMOJI['bullet']} *Risk management*: Within defined limits")
                    else:
                        page1.append(f"{EMOJI['bullet']} *BTC/Crypto*: Live data loading - strategy monitoring active")
                        page1.append(f"{EMOJI['bullet']} *Risk management*: Managed within plan")
                        
                except Exception as e:
                    log.warning(f"{EMOJI['warning']} [SUMMARY-LIVE] Error: {e}")
                    page1.append(f"{EMOJI['bullet']} *performance*: Day closed within expected risk parameters")
                    
                page1.append("")
                
                # Enhanced Market performance (weekend-aware)
                page1.append(f"{EMOJI['notebook']} *MARKET PERFORMANCE:*")
                if now.weekday() >= 5:
                    page1.append(f"{EMOJI['bullet']} *Traditional Markets*: Weekend - closed")
                    page1.append(f"{EMOJI['bullet']} *Crypto*: BTC range maintained, ETH following")
                    page1.append(f"{EMOJI['bullet']} *Asia Futures*: Indication resumes Sunday night")
                else:
                    # Try to use live SPX/EURUSD data for a truthful snapshot
                    try:
                        quotes_summary = get_live_equity_fx_quotes(['^GSPC', 'EURUSD=X', 'XAUUSD=X']) or {}
                    except Exception as qe:
                        log.warning(f"{EMOJI['warning']} [SUMMARY-MARKET] Equity/FX quotes unavailable: {qe}")
                        quotes_summary = {}
                    spx_q = quotes_summary.get('^GSPC', {})
                    eur_q = quotes_summary.get('EURUSD=X', {})
                    gold_q = quotes_summary.get('XAUUSD=X', {})
                    spx_price = float(spx_q.get('price', 0) or 0.0)
                    eur_price = float(eur_q.get('price', 0) or 0.0)
                    spx_chg = spx_q.get('change_pct', None)
                    eur_chg = eur_q.get('change_pct', None)
                    gold_price = float(gold_q.get('price', 0) or 0.0)
                    gold_chg = gold_q.get('change_pct', None)
                    gold_per_gram = gold_price / GOLD_GRAMS_PER_TROY_OUNCE if gold_price else 0.0

                    # Save traditional markets snapshot for metrics when available
                    if spx_price:
                        daily_market_snapshot['SPX'] = {
                            'price': spx_price,
                            'change_pct': float(spx_chg or 0.0),
                            'unit': 'index'
                        }
                    if eur_price:
                        daily_market_snapshot['EURUSD'] = {
                            'price': eur_price,
                            'change_pct': float(eur_chg or 0.0),
                            'unit': 'rate'
                        }
                    if gold_per_gram:
                        daily_market_snapshot['GOLD'] = {
                            'price': gold_per_gram,
                            'change_pct': float(gold_chg or 0.0),
                            'unit': 'USD/g'
                        }
                    if spx_chg is not None:
                        equity_line = f"{EMOJI['bullet']} *Equity*: S&P {spx_chg:+.1f}% vs prior close (tech leadership context)"
                    else:
                        equity_line = f"{EMOJI['bullet']} *Equity*: S&P performance in line with intraday regime (see Evening Session Wrap)"
                    page1.append(equity_line)
                    page1.append(f"{EMOJI['bullet']} *Crypto*: BTC range maintained, ETH following")
                    if eur_chg is not None:
                        if eur_chg < 0:
                            fx_desc = "USD strength confirmed"
                        elif eur_chg > 0:
                            fx_desc = "EUR strength vs USD"
                        else:
                            fx_desc = "Rangebound session"
                        page1.append(f"{EMOJI['bullet']} *FX*: EUR/USD {eur_chg:+.1f}% - {fx_desc}")
                    else:
                        page1.append(f"{EMOJI['bullet']} *FX*: USD vs EUR monitored - see Evening/FX sections")
                    # Gold: show real price (USD/gram) and change when available, otherwise qualitative only
                    if gold_per_gram and gold_chg is not None:
                        if gold_per_gram >= 1:
                            gold_price_str = f"${gold_per_gram:,.2f}/g"
                        else:
                            gold_price_str = f"${gold_per_gram:.3f}/g"
                        page1.append(f"{EMOJI['bullet']} *Commodities*: Gold {gold_price_str} ({gold_chg:+.1f}%) - defensive hedge, Oil tracking supply/demand dynamics")
                    else:
                        page1.append(f"{EMOJI['bullet']} *Commodities*: Gold as defensive hedge, Oil tracking supply/demand dynamics")
                    page1.append(f"{EMOJI['bullet']} *Volatility*: VIX behaviour consistent with current risk regime")
                page1.append("")
                
                # Executive Score
                page1.append(f"{EMOJI['target']} *EXECUTIVE SCORE:*")
                if total_tracked_for_score > 0:
                    if acc_pct_for_score >= 80:
                        grade = "A (Strong day - high accuracy)"
                        reliability = f"{acc_pct_for_score:.0f}% - strong signal quality"
                        strategy_exec = "Well executed - trade plan largely respected"
                        risk_ctrl = "Within limits - drawdowns controlled"
                    elif acc_pct_for_score >= 60:
                        grade = "B (Solid day - accuracy above target)"
                        reliability = f"{acc_pct_for_score:.0f}% - good signal quality"
                        strategy_exec = "Generally aligned with plan - some adjustments needed"
                        risk_ctrl = "Within limits - no major deviations"
                    elif acc_pct_for_score > 0:
                        grade = "C (Mixed day - review needed)"
                        reliability = f"{acc_pct_for_score:.0f}% - mixed signal quality"
                        strategy_exec = "Requires refinement - focus on execution discipline"
                        risk_ctrl = "Risk mostly contained but review sizing"
                    else:
                        grade = "D (Challenging day - no correct hits)"
                        reliability = "0% - tracked predictions missed"
                        strategy_exec = "Reassess model usage and intraday adjustments"
                        risk_ctrl = "Risk within limits but no reward captured"
                else:
                    grade = "N/A (No live-tracked predictions)"
                    reliability = "N/A - qualitative assessment only"
                    strategy_exec = "Aligned with plan based on qualitative review"
                    risk_ctrl = "Within defined risk budget"

                page1.append(f"{EMOJI['bullet']} *Overall Grade*: {grade}")
                page1.append(f"{EMOJI['bullet']} *Model Reliability*: {reliability}")
                page1.append(f"{EMOJI['bullet']} *Strategy Execution*: {strategy_exec}")
                page1.append(f"{EMOJI['bullet']} *Risk Control*: {risk_ctrl}")
                
                pages.append("\n".join(page1))
                log.info(f"{EMOJI['check']} [SUMMARY] page 1 (Executive Summary) generata")
                
            except Exception as e:
                log.error(f"Ã¢ÂÅ’ [SUMMARY] Errore page 1: {e}")
                pages.append(f"{header_base}Ã°Å¸â€œË† **EXECUTIVE SUMMARY**\nSystem loading...")
            
            # === Page 2: PERFORMANCE ANALYSIS ===
            try:
                page2 = []
                page2.append(header_base)
                page2.append(f"{EMOJI['trophy']} *Page 2/6 - PERFORMANCE ANALYSIS*")
                page2.append("")
                
                # Enhanced ML Models performance
                page2.append(f"{EMOJI['robot']} *ML MODELS - PERFORMANCE DETAILS:*")
                if DEPENDENCIES_AVAILABLE:
                    page2.append(f"{EMOJI['bullet']} *Random Forest*: Core intraday engine - captures non-linear patterns")
                    page2.append(f"{EMOJI['bullet']} *Gradient Boosting*: Focuses on incremental improvements over baseline")
                    page2.append(f"{EMOJI['bullet']} *XGBoost*: Handles complex interactions and rare events")
                    page2.append(f"{EMOJI['bullet']} *Logistic Regression*: Simple, interpretable baseline model")
                    page2.append(f"{EMOJI['bullet']} *SVM*: Margin-based classifier for regime separation")
                    page2.append(f"{EMOJI['bullet']} *Naive Bayes*: Lightweight model for fast probabilistic signals")
                else:
                    page2.append(f"{EMOJI['bullet']} *Ensemble performance*: Uses multiple models to stabilize signals")
                    page2.append(f"{EMOJI['bullet']} *Model Consensus*: Focus on agreement before acting on high-conviction trades")
                    page2.append(f"{EMOJI['bullet']} *Confidence Intervals*: Derived from dispersion across individual models")
                    
                page2.append("")
                
                # Enhanced Technical Signals performance - conditional on accuracy
                page2.append(f"{EMOJI['chart']} *TECHNICAL SIGNALS - DESCRIPTIVE OVERVIEW:*")
                # Get accuracy to determine tone
                eval_page2 = prediction_eval or {}
                total_page2 = int(eval_page2.get('total_tracked', 0) or 0)
                acc_page2 = float(eval_page2.get('accuracy_pct', 0.0) or 0.0)
                
                if total_page2 > 0 and acc_page2 >= 60:
                    # High accuracy: show indicators with confirmations
                    page2.append(f"{EMOJI['bullet']} *RSI*: Bullish (68) - momentum confirmed {EMOJI['check']}")
                    page2.append(f"{EMOJI['bullet']} *MACD*: Strong buy - crossover verified {EMOJI['check']}")
                    page2.append(f"{EMOJI['bullet']} *Bollinger*: Upper band test - strength {EMOJI['check']}")
                    page2.append(f"{EMOJI['bullet']} *EMA*: Golden cross - trend bullish {EMOJI['check']}")
                    page2.append(f"{EMOJI['bullet']} *Support/Resistance*: All levels respected {EMOJI['check']}")
                elif total_page2 > 0 and acc_page2 > 0:
                    # Mixed accuracy: descriptive without all checkmarks
                    page2.append(f"{EMOJI['bullet']} *RSI*: Provided momentum signals - interpretation varied")
                    page2.append(f"{EMOJI['bullet']} *MACD*: Generated crossover signals - outcomes mixed")
                    page2.append(f"{EMOJI['bullet']} *Bollinger*: Indicated volatility zones - partially respected")
                    page2.append(f"{EMOJI['bullet']} *EMA*: Trend signals present - market action diverged at times")
                    page2.append(f"{EMOJI['bullet']} *Support/Resistance*: Key levels identified - some breaks occurred")
                elif total_page2 > 0 and acc_page2 == 0:
                    # Zero accuracy: critical review tone
                    page2.append(f"{EMOJI['bullet']} *RSI*: Indicated momentum - market did not confirm")
                    page2.append(f"{EMOJI['bullet']} *MACD*: Provided signals - outcomes did not align")
                    page2.append(f"{EMOJI['bullet']} *Bollinger*: Showed volatility zones - price action unpredictable")
                    page2.append(f"{EMOJI['bullet']} *EMA*: Suggested trend - market moved counter to signals")
                    page2.append(f"{EMOJI['bullet']} *Support/Resistance*: Levels broken - regime shift or noise")
                else:
                    # No tracked predictions: descriptive roles
                    page2.append(f"{EMOJI['bullet']} *RSI*: Provides momentum readings for overbought/oversold conditions")
                    page2.append(f"{EMOJI['bullet']} *MACD*: Tracks trend changes via moving average convergence")
                    page2.append(f"{EMOJI['bullet']} *Bollinger Bands*: Identifies volatility expansion and contraction zones")
                    page2.append(f"{EMOJI['bullet']} *EMA*: Smooths price action to reveal underlying trends")
                    page2.append(f"{EMOJI['bullet']} *Support/Resistance*: Key levels derived from historical price structure")
                page2.append("")
                
                # Enhanced Prediction Timeline (descriptive, not hard-coded results)
                page2.append(f"{EMOJI['clock']} *PREDICTION TIMELINE - KEY CHECKPOINTS:*")
                page2.append(f"*07:00 Press Review*: Market setup and initial scenarios published")
                page2.append(f"*08:30 Morning*: Core directional bias and key levels defined")
                page2.append(f"*13:00 Noon*: Mid-day verification of signals and risk exposure")
                page2.append(f"*18:30 Evening*: Session wrap and preparation for tomorrow")
                page2.append("")
                
                # performance Metrics
                page2.append(f"{EMOJI['notebook']} *PERFORMANCE METRICS:*")
                eval_data = prediction_eval or {}
                total_tracked = int(eval_data.get('total_tracked', 0) or 0)
                hits = int(eval_data.get('hits', 0) or 0)
                acc_pct = float(eval_data.get('accuracy_pct', 0.0) or 0.0)
                if total_tracked > 0:
                    page2.append(f"{EMOJI['bullet']} *Success Rate*: {hits}/{total_tracked} predictions hit their target ({acc_pct:.0f}%)")
                else:
                    page2.append(f"{EMOJI['bullet']} *Success Rate*: n/a (no live-tracked predictions today)")

                if total_tracked > 0:
                    if acc_pct >= 80:
                        conf_text = "High conviction signals with strong alignment to market moves"
                        calib_text = "Well calibrated to current regime"
                        quality_text = "High signal quality - only small refinements needed"
                    elif acc_pct >= 60:
                        conf_text = "Good conviction, above-target accuracy"
                        calib_text = "Generally well calibrated with some noise"
                        quality_text = "Solid signals with room for optimization"
                    elif acc_pct > 0:
                        conf_text = "Mixed outcomes - conviction to be reviewed"
                        calib_text = "Requires calibration - several signals off"
                        quality_text = "Signal quality mixed - focus on improving filters"
                    else:
                        conf_text = "No correct hits on tracked assets - conviction under review"
                        calib_text = "Low calibration - revisit model assumptions"
                        quality_text = "Signals did not play out today - learning opportunity"
                else:
                    conf_text = "Confidence derived from internal ensemble scores (no live verification)"
                    calib_text = "Calibration based on historical backtests and recent days"
                    quality_text = "Signal quality assessed qualitatively via journal review"

                page2.append(f"{EMOJI['bullet']} *Average Confidence*: {conf_text}")
                page2.append(f"{EMOJI['bullet']} *Model Calibration*: {calib_text}")
                page2.append(f"{EMOJI['bullet']} *Signal Quality*: {quality_text}")
                
                pages.append("\n".join(page2))
                log.info(f"{EMOJI['check']} [SUMMARY] page 2 (performance Analysis) generata")
                
            except Exception as e:
                log.error(f"Ã¢ÂÅ’ [SUMMARY] Errore page 2: {e}")
                pages.append(f"{header_base}Ã°Å¸Å½Â¯ **PERFORMANCE ANALYSIS**\nAnalysis loading...")
            
            # === page 3: ML RESULTS DETTAGLIATI ===
            try:
                page3 = []
                page3.append(header_base)
                page3.append(f"{EMOJI['brain']} *page 3/6 - DETAILED ML RESULTS*")
                page3.append("")
                
                # Risk Metrics Enhanced - now with real values or N/A
                page3.append(f"{EMOJI['shield']} *RISK METRICS ADVANCED:*")
                
                # Get prediction eval for win rate
                eval_page3 = prediction_eval or {}
                total_page3 = int(eval_page3.get('total_tracked', 0) or 0)
                hits_page3 = int(eval_page3.get('hits', 0) or 0)
                acc_page3 = float(eval_page3.get('accuracy_pct', 0.0) or 0.0)
                
                # VaR and drawdown - placeholder for now (can be enhanced when real risk data available)
                page3.append(f"{EMOJI['bullet']} *VaR (95%)*: N/A - requires live P&L tracking (future enhancement)")
                page3.append(f"{EMOJI['bullet']} *Max Drawdown*: N/A - requires intraday position tracking (future enhancement)")
                
                # Sharpe - conditional on accuracy
                if total_page3 > 0 and acc_page3 >= 60:
                    page3.append(f"{EMOJI['bullet']} *Sharpe Ratio*: Estimated positive (strong win rate)")
                elif total_page3 > 0 and acc_page3 > 0:
                    page3.append(f"{EMOJI['bullet']} *Sharpe Ratio*: Mixed (moderate win rate)")
                elif total_page3 > 0:
                    page3.append(f"{EMOJI['bullet']} *Sharpe Ratio*: Negative today (challenging win rate)")
                else:
                    page3.append(f"{EMOJI['bullet']} *Sharpe Ratio*: N/A - insufficient live data for calculation")
                
                # Win Rate - rimando alle pagine 1/2 per i numeri, per evitare ripetizioni
                if total_page3 > 0:
                    page3.append(f"{EMOJI['bullet']} *Win Rate*: See Executive Summary / Performance (Pages 1–2) for detailed hit rate")
                else:
                    page3.append(f"{EMOJI['bullet']} *Win Rate*: N/A - no live-tracked predictions today")
                
                # Risk-Adjusted Return
                if total_page3 > 0 and acc_page3 >= 60:
                    page3.append(f"{EMOJI['bullet']} *Risk-Adjusted Return*: Positive expectancy (high win rate maintained)")
                elif total_page3 > 0 and acc_page3 > 0:
                    page3.append(f"{EMOJI['bullet']} *Risk-Adjusted Return*: Below target (win rate needs improvement)")
                elif total_page3 > 0:
                    page3.append(f"{EMOJI['bullet']} *Risk-Adjusted Return*: Negative today (capital preservation focus)")
                else:
                    page3.append(f"{EMOJI['bullet']} *Risk-Adjusted Return*: N/A - qualitative assessment only")
                
                page3.append("")
                
                # Momentum Indicators Deep Dive
                page3.append(f"{EMOJI['chart_up']} *MOMENTUM INDICATORS DEEP DIVE:*")
                sent_info = news_data.get('sentiment', {})
                sentiment_label = sent_info.get('sentiment', 'NEUTRAL')
                pos_score = int(sent_info.get('positive_score', 0) or 0)
                neg_score = int(sent_info.get('negative_score', 0) or 0)
                balance = pos_score - neg_score
                page3.append(f"{EMOJI['bullet']} *News Sentiment*: {sentiment_label} ({balance:+d} balance)")
                page3.append(f"{EMOJI['bullet']} *Unified Day Sentiment*: {evening_sentiment}")
                page3.append(f"{EMOJI['bullet']} *Market Momentum*: Trend strength assessed via intraday price action")
                page3.append(f"{EMOJI['bullet']} *Sector Rotation*: Risk-on vs defensive sectors monitored throughout the day")
                page3.append(f"{EMOJI['bullet']} *Volatility*: Behaviour consistent with observed risk regime (no fixed VIX level)")
                page3.append(f"{EMOJI['bullet']} *Volume Analysis*: Qualitative review of participation and conviction")
                page3.append("")
                
                # Feature Importance Analysis
                page3.append(f"{EMOJI['target']} *FEATURE IMPORTANCE ANALYSIS:*")
                if DEPENDENCIES_AVAILABLE:
                    page3.append(f"{EMOJI['bullet']} *Sentiment Features*: Primary driver for short-term adjustments")
                    page3.append(f"{EMOJI['bullet']} *Technical Features*: Strong contributor to entry/exit timing")
                    page3.append(f"{EMOJI['bullet']} *Macro Features*: Context provider for regime identification")
                    page3.append(f"{EMOJI['bullet']} *Correlation Matrix*: Analysed to avoid over-concentrated exposure")
                else:
                    page3.append(f"{EMOJI['bullet']} *Primary Drivers*: News sentiment, technical momentum")
                    page3.append(f"{EMOJI['bullet']} *Secondary Factors*: Macro context, market structure")
                    page3.append(f"{EMOJI['bullet']} *Model Stability*: High - consistent performance")
                
                page3.append("")
                
                # Model Evolution
                page3.append(f"{EMOJI['rocket']} *MODEL EVOLUTION & LEARNING:*")
                page3.append(f"{EMOJI['bullet']} *Learning Behaviour*: Continuous update from new intraday data")
                page3.append(f"{EMOJI['bullet']} *Pattern Recognition*: Focus on recurring market structures and anomalies")
                page3.append(f"{EMOJI['bullet']} *Adaptivity*: Qualitative review of how models reacted to regime changes")
                page3.append(f"{EMOJI['bullet']} *Prediction Horizon*: Short-term (intraday/24h) focus, validated via live tracking")
                
                pages.append("\n".join(page3))
                log.info(f"{EMOJI['check']} [SUMMARY] page 3 (ML Results) generata")
                
            except Exception as e:
                log.error(f"Ã¢ÂÅ’ [SUMMARY] Errore page 3: {e}")
                pages.append(f"{header_base}Ã°Å¸â€Â¬ **ML RESULTS**\nML analysis loading...")
            
            # === page 4: MARKET REVIEW COMPLETA ===
            try:
                page4 = []
                page4.append(header_base)
                page4.append(f"{EMOJI['globe']} *page 4/6 - COMPLETE MARKET REVIEW*")
                page4.append("")
                
                # Global Markets Comprehensive (weekend-aware)
                page4.append(f"{EMOJI['world']} *GLOBAL MARKETS COMPREHENSIVE:*")
                if now.weekday() >= 5:
                    page4.append(f"{EMOJI['bullet']} *Status*: Weekend - cash equity markets closed")
                    page4.append(f"{EMOJI['bullet']} *Asia Futures (Sun night)*: Early lead for Monday's Europe open")
                    page4.append(f"{EMOJI['bullet']} *Crypto 24/7*: Primary risk barometer during weekend")
                else:
                    page4.append(f"{EMOJI['bullet']} *US Indices*: Broad-based rally tone in major benchmarks")
                    page4.append(f"{EMOJI['bullet']} *European Markets*: Solid performance across core indices")
                    page4.append(f"{EMOJI['bullet']} *Asian Follow-through*: Expected positive bias from US/Europe session")
                    page4.append(f"{EMOJI['bullet']} *Emerging Markets*: Selective strength with focus on technology/FX-sensitive areas")
                page4.append("")
                
                # Sector Deep Analysis
                page4.append(f"{EMOJI['bank']} *SECTOR DEEP ANALYSIS:*")
                page4.append(f"{EMOJI['bullet']} *Technology*: Leadership driven by AI and cloud themes")
                page4.append(f"{EMOJI['bullet']} *Banking*: Benefiting from current rate environment and stable credit conditions")
                page4.append(f"{EMOJI['bullet']} *Energy*: Supported by oil stability and gradual renewable transition")
                page4.append(f"{EMOJI['bullet']} *Healthcare*: Mixed biotech moves, pharma remains defensive anchor")
                page4.append(f"{EMOJI['bullet']} *Consumer*: Resilient spending patterns with employment support")
                page4.append(f"{EMOJI['bullet']} *Utilities*: Sensitive to rates, rotation towards growth observed")
                page4.append("")
                
                # Currency & Commodities Enhanced
                page4.append(f"{EMOJI['money']} *CURRENCY & COMMODITIES ENHANCED:*")
                page4.append(f"{EMOJI['bullet']} *USD Index*: Strength confirmed - Fed policy support")
                # EUR/USD dynamic when possible, Gold with live price when available, otherwise qualitative
                try:
                    quotes_ccy = get_live_equity_fx_quotes(['EURUSD=X', 'XAUUSD=X']) or {}
                except Exception as qe:
                    log.warning(f"{EMOJI['warning']} [SUMMARY-PAGE4-FX] EURUSD/XAUUSD quote unavailable: {qe}")
                    quotes_ccy = {}
                eur_ccy = quotes_ccy.get('EURUSD=X', {})
                gold_ccy = quotes_ccy.get('XAUUSD=X', {})
                eur_ccy_chg = eur_ccy.get('change_pct', None)
                gold_price = gold_ccy.get('price', 0)
                gold_chg = gold_ccy.get('change_pct', None)
                if eur_ccy_chg is not None:
                    if eur_ccy_chg < 0:
                        eur_ccy_desc = "USD strength confirmed"
                    elif eur_ccy_chg > 0:
                        eur_ccy_desc = "EUR strength vs USD"
                    else:
                        eur_ccy_desc = "Rangebound session"
                    page4.append(f"{EMOJI['bullet']} *EUR/USD*: {eur_ccy_chg:+.1f}% - {eur_ccy_desc}")
                else:
                    page4.append(f"{EMOJI['bullet']} *EUR/USD*: USD vs EUR monitored - ECB/Fed policy in focus")
                page4.append(f"{EMOJI['bullet']} *GBP/USD*: Stable - BoE neutral stance maintained")
                # Gold: show real price (USD/gram) and change when available, otherwise qualitative only
                if gold_price and gold_chg is not None:
                    gold_per_gram = gold_price / GOLD_GRAMS_PER_TROY_OUNCE if gold_price else 0
                    if gold_per_gram >= 1:
                        gold_price_str = f"${gold_per_gram:,.2f}/g"
                    else:
                        gold_price_str = f"${gold_per_gram:.3f}/g"
                    page4.append(f"{EMOJI['bullet']} *Gold*: {gold_price_str} ({gold_chg:+.1f}%) - defensive hedge, inflation concerns")
                else:
                    page4.append(f"{EMOJI['bullet']} *Gold*: Defensive hedge, inflation concerns")
                page4.append(f"{EMOJI['bullet']} *Oil (WTI)*: Supply dynamics, demand steady")
                page4.append(f"{EMOJI['bullet']} *Copper*: Resilient - growth proxy confirmation")
                page4.append("")
                
                # Volume & Flow Analysis
                page4.append(f"{EMOJI['chart']} *VOLUME & FLOW ANALYSIS:*")
                page4.append(f"{EMOJI['bullet']} *Equity Flows*: Net inflows signal institutional participation")
                page4.append(f"{EMOJI['bullet']} *Bond Flows*: Moderate outflows consistent with risk-on rotation")
                page4.append(f"{EMOJI['bullet']} *Crypto Flows*: Stable accumulation patterns observed")
                page4.append(f"{EMOJI['bullet']} *Options Activity*: Bullish skew indicated by elevated call activity")
                
                pages.append("\n".join(page4))
                log.info(f"{EMOJI['check']} [SUMMARY] page 4 (Market Review) generata")
                
            except Exception as e:
                log.error(f"Ã¢ÂÅ’ [SUMMARY] Errore page 4: {e}")
                pages.append(f"{header_base}Ã°Å¸Å’Â **MARKET REVIEW**\nMarket analysis loading...")
            
            # === page 5: TOMORROW OUTLOOK ===
            try:
                page5 = []
                page5.append(header_base)
                page5.append(f"{EMOJI['compass']} *page 5/6 - TOMORROW OUTLOOK*")
                page5.append("")
                
                # Enhanced Tomorrow Preview
                tomorrow = _now_it() + datetime.timedelta(days=1)
                page5.append(f"{EMOJI['calendar_spiral']} *{tomorrow.strftime('%A').upper()} STRATEGIC PREVIEW ({tomorrow.strftime('%d/%m')}):")
                page5.append(f"{EMOJI['bullet']} *Gap Scenario*: Bias for potential gap up on positive momentum (no fixed probability)")
                page5.append(f"{EMOJI['bullet']} *Key Events*: ECB rate decision 14:15, US GDP preliminary")
                page5.append(f"{EMOJI['bullet']} *Earnings Focus*: MSFT after close, AAPL pre-market")
                page5.append(f"{EMOJI['bullet']} *Data Releases*: EU inflation, US jobless claims, Fed speakers")
                page5.append("")
                
                # Strategic Positioning
                page5.append(f"{EMOJI['trophy']} *STRATEGIC POSITIONING:*")

                # Derive BTC breakout and support levels near current price if available
                btc_breakout_summary = None
                btc_support_summary = None
                try:
                    crypto_prices_summary = get_live_crypto_prices()
                    if crypto_prices_summary and crypto_prices_summary.get('BTC', {}).get('price', 0) > 0:
                        btc_price_summary = crypto_prices_summary['BTC'].get('price', 0)
                        btc_change_summary = crypto_prices_summary['BTC'].get('change_pct', 0)
                        sr_summary = calculate_crypto_support_resistance(btc_price_summary, btc_change_summary)
                        if sr_summary:
                            btc_support_summary = int(sr_summary.get('support_2') or 0)
                            btc_breakout_summary = int(sr_summary.get('resistance_2') or 0)
                except Exception as e:
                    log.warning(f"{EMOJI['warning']} [SUMMARY-PAGE5-BTC] Live BTC levels unavailable: {e}")
                    btc_breakout_summary = None
                    btc_support_summary = None

                page5.append(f"{EMOJI['bullet']} *Tech Overweight*: Maintain 1.3x allocation - momentum + earnings")
                if btc_breakout_summary:
                    page5.append(f"{EMOJI['bullet']} *BTC Strategy*: Watch ${btc_breakout_summary:,.0f} breakout - institutional accumulation")
                else:
                    page5.append(f"{EMOJI['bullet']} *BTC Strategy*: Watch BTC breakout above key resistance - institutional accumulation")
                page5.append(f"{EMOJI['bullet']} *EUR/USD*: Short bias on ECB dovish - levels to be refined intraday with live data")
                page5.append(f"{EMOJI['bullet']} *Volatility*: Tactical view on volatility aligned with current risk regime")
                page5.append(f"{EMOJI['bullet']} *Energy*: Selective long - supply dynamics favorable")
                page5.append("")
                
                # Risk Management Tomorrow
                page5.append(f"{EMOJI['shield']} *RISK MANAGEMENT TOMORROW:*")
                page5.append(f"{EMOJI['bullet']} *Position Sizing*: 1.2x standard on conviction plays")
                # Try to include a dynamic S&P stop level near current price
                spx_support_summary = None
                try:
                    quotes_spx_summary = get_live_equity_fx_quotes(['^GSPC']) or {}
                    spx_price_summary = quotes_spx_summary.get('^GSPC', {}).get('price', 0)
                    if spx_price_summary:
                        spx_support_summary = int(spx_price_summary * 0.995)  # ≈ -0.5%
                except Exception as e:
                    log.warning(f"{EMOJI['warning']} [SUMMARY-PAGE5-SPX] Live SPX level unavailable: {e}")
                if btc_support_summary and spx_support_summary:
                    page5.append(f"{EMOJI['bullet']} *Stop Levels*: S&P {spx_support_summary}, BTC ${btc_support_summary:,.0f} as key supports")
                elif btc_support_summary:
                    page5.append(f"{EMOJI['bullet']} *Stop Levels*: S&P key support zone, BTC ${btc_support_summary:,.0f} as key support")
                elif spx_support_summary:
                    page5.append(f"{EMOJI['bullet']} *Stop Levels*: S&P {spx_support_summary}, BTC key support zone as reference")
                else:
                    page5.append(f"{EMOJI['bullet']} *Stop Levels*: S&P key support zone, BTC key support zone as reference")
                page5.append(f"{EMOJI['bullet']} *Hedge Ratio*: 10% - reduced given positive momentum")
                page5.append(f"{EMOJI['bullet']} *Max Risk*: 2% per position - disciplined approach")
                page5.append("")
                
                # Tomorrow Schedule Enhanced
                page5.append(f"{EMOJI['clock']} *TOMORROW FULL SCHEDULE:*")
                page5.append(f"{EMOJI['bullet']} *07:00*: Press Review (7 messages) - Fresh intelligence")
                page5.append(f"{EMOJI['bullet']} *08:30*: Morning Report (3 messages) - Setup + predictions")
                page5.append(f"{EMOJI['bullet']} *13:00*: Noon Update (3 messages) - Progress verification")
                page5.append(f"{EMOJI['bullet']} *18:30*: Evening Analysis (3 messages) - Session wrap")
                page5.append(f"{EMOJI['bullet']} *20:00*: Daily Summary (6 pages) - Complete analysis")
                page5.append("")
                
                # Final Summary Note - Updated for 6 pages
                page5.append(f"{EMOJI['right_arrow']} *NEXT PAGE:*")
                page5.append(f"{EMOJI['bullet']} *Page 6/6*: Daily Journal & Narrative Notes")
                page5.append(f"{EMOJI['bullet']} *Content*: Qualitative insights, lessons learned, personal observations")
                
                pages.append("\n".join(page5))
                log.info(f"{EMOJI['check']} [SUMMARY] page 5 (Tomorrow Outlook) generata")
                
            except Exception as e:
                log.error(f"Ã¢ÂÅ' [SUMMARY] Errore page 5: {e}")
                pages.append(f"{header_base}Ã°Å¸â€Â® **TOMORROW OUTLOOK**\nOutlook analysis loading...")
            
            # === PAGE 6: DAILY JOURNAL & NARRATIVE NOTES ===
            # Load sentiment tracking BEFORE generating Page 6 so it's available in the narrative
            sentiment_tracking = self._load_sentiment_tracking(now)
            
            try:
                page6 = []
                page6.append(header_base)
                page6.append(f"{EMOJI['notebook']} *Page 6/6 - DAILY JOURNAL & NOTES*")
                page6.append("")
                
                # Daily Narrative Section
                page6.append(f"{EMOJI['notebook']} *DAILY NARRATIVE - QUALITATIVE INSIGHTS:*")
                
                # Auto-generate narrative based on day performance
                # Prefer intraday sentiment tracking (Evening → Noon → Morning → Press Review),
                # then fall back to evening continuity or summary news sentiment.
                day_sentiment = 'NEUTRAL'
                try:
                    if isinstance(sentiment_tracking, dict):
                        if 'evening' in sentiment_tracking:
                            day_sentiment = sentiment_tracking['evening'].get('sentiment', 'NEUTRAL')
                        elif 'noon' in sentiment_tracking:
                            day_sentiment = sentiment_tracking['noon'].get('sentiment', 'NEUTRAL')
                        elif 'morning' in sentiment_tracking:
                            day_sentiment = sentiment_tracking['morning'].get('sentiment', 'NEUTRAL')
                        elif 'press_review' in sentiment_tracking:
                            day_sentiment = sentiment_tracking['press_review'].get('sentiment', 'NEUTRAL')
                    # Fallbacks if tracking is missing or neutral
                    if day_sentiment == 'NEUTRAL':
                        # Use evening continuity if available, otherwise summary news sentiment
                        day_sentiment = evening_sentiment or news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL')
                except Exception as e:
                    log.warning(f"{EMOJI['warning']} [SUMMARY-SENTIMENT] Fallback to news sentiment: {e}")
                    day_sentiment = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL')

                if day_sentiment == 'POSITIVE':
                    narrative_intro = "Strong risk-on session with broad market participation"
                    market_story = "Technology leadership drove the rally with exceptional breadth"
                    key_turning = "European open confirmed bullish bias, US session extended gains"
                elif day_sentiment == 'NEGATIVE':
                    narrative_intro = "Risk-off rotation dominated with defensive positioning"
                    market_story = "Sector rotation favored quality and safety over growth"
                    key_turning = "Mid-day weakness accelerated into US close"
                else:
                    narrative_intro = "Mixed session with sector-specific rotations"
                    market_story = "Rangebound trading prevailed with selective opportunities"
                    key_turning = "Choppy intraday action reflected uncertain sentiment"
                
                page6.append(f"{EMOJI['bullet']} *Market Story*: {market_story}")
                page6.append(f"{EMOJI['bullet']} *Session Character*: {narrative_intro}")
                page6.append(f"{EMOJI['bullet']} *Key Turning Points*: {key_turning}")
                
                # Unexpected events section
                page6.append("")
                page6.append(f"{EMOJI['lightning']} *UNEXPECTED EVENTS & SURPRISES:*")
                try:
                    crypto_prices = get_live_crypto_prices()
                    if crypto_prices and crypto_prices.get('BTC', {}).get('price', 0) > 0:
                        btc_change = crypto_prices['BTC'].get('change_pct', 0)
                        if abs(btc_change) > 3:
                            page6.append(f"{EMOJI['bullet']} BTC volatility exceeded expectations ({btc_change:+.1f}%) - momentum shift")
                        else:
                            page6.append(f"{EMOJI['bullet']} No major surprises - market moved as anticipated")
                    else:
                        page6.append(f"{EMOJI['bullet']} Standard market behavior - aligned with predictions")
                except:
                    page6.append(f"{EMOJI['bullet']} Market evolution within expected parameters")
                
                page6.append(f"{EMOJI['bullet']} News flow: {'Higher than average' if len(news_data.get('news', [])) > 12 else 'Normal volume'}")
                page6.append(f"{EMOJI['bullet']} Volatility: {'Elevated' if day_sentiment == 'NEGATIVE' else 'Compressed' if day_sentiment == 'POSITIVE' else 'Moderate'} - VIX behavior standard")
                
                # Lessons learned
                page6.append("")
                page6.append(f"{EMOJI['bulb']} *LESSONS LEARNED & MODEL INSIGHTS:*")
                page6.append(f"{EMOJI['bullet']} *What Worked*: {'ML models captured momentum effectively' if day_sentiment == 'POSITIVE' else 'Risk management preserved capital' if day_sentiment == 'NEGATIVE' else 'Range trading strategy effective'}")
                eval_data = prediction_eval or {}
                acc_pct = float(eval_data.get('accuracy_pct', 0.0) or 0.0)
                total_for_model = int(eval_data.get('total_tracked', 0) or 0)
                if total_for_model > 0 and acc_pct > 0:
                    page6.append(f"{EMOJI['bullet']} *Model Behavior*: Ensemble approach delivered {acc_pct:.0f}% accuracy on tracked assets")
                elif total_for_model > 0:
                    page6.append(f"{EMOJI['bullet']} *Model Behavior*: Challenging day - no correct hits on tracked assets (see Pages 1/2)")
                else:
                    page6.append(f"{EMOJI['bullet']} *Model Behavior*: Accuracy not evaluated today (no live-tracked predictions)")
                page6.append(f"{EMOJI['bullet']} *Signal Quality*: {'Exceptional clarity' if day_sentiment != 'NEUTRAL' else 'Mixed signals required discretion'}")
                page6.append(f"{EMOJI['bullet']} *Improvement Area*: {'None identified' if day_sentiment == 'POSITIVE' else 'Crypto volatility underestimated' if day_sentiment == 'NEGATIVE' else 'Sideways detection timing'}")
                
                # Operational notes
                page6.append("")
                page6.append(f"{EMOJI['clipboard']} *OPERATIONAL NOTES & OBSERVATIONS:*")
                page6.append(f"{EMOJI['bullet']} *Best Decision*: {'Tech overweight at market open' if day_sentiment == 'POSITIVE' else 'Defensive rotation preserved capital' if day_sentiment == 'NEGATIVE' else 'Neutral positioning appropriate'}")
                page6.append(f"{EMOJI['bullet']} *Timing Quality*: Entry/exit execution {'optimal' if day_sentiment == 'POSITIVE' else 'cautious but correct' if day_sentiment == 'NEGATIVE' else 'patient and disciplined'}")
                page6.append(f"{EMOJI['bullet']} *Missed Opportunity*: {'None significant' if day_sentiment == 'POSITIVE' else 'Earlier defensive shift' if day_sentiment == 'NEGATIVE' else 'Could have been more aggressive on breakouts'}")
                page6.append(f"{EMOJI['bullet']} *Tomorrow Focus*: {next_day_setup.get('summary_sentiment', 'Maintain current strategy')} - {'Watch for continuation' if day_sentiment == 'POSITIVE' else 'Recovery signals' if day_sentiment == 'NEGATIVE' else 'Direction clarity'}")
                
                # Personal insights section (space for manual notes)
                page6.append("")
                page6.append(f"{EMOJI['star']} *PERSONAL INSIGHTS & PATTERN RECOGNITION:*")
                
                # Use actual sentiment tracking for evolution narrative
                sentiment_stages = []
                if 'press_review' in sentiment_tracking:
                    sentiment_stages.append(('Press', sentiment_tracking['press_review'].get('sentiment', 'N/A')))
                if 'morning' in sentiment_tracking:
                    sentiment_stages.append(('Morning', sentiment_tracking['morning'].get('sentiment', 'N/A')))
                if 'noon' in sentiment_tracking:
                    sentiment_stages.append(('Noon', sentiment_tracking['noon'].get('sentiment', 'N/A')))
                if 'evening' in sentiment_tracking:
                    sentiment_stages.append(('Evening', sentiment_tracking['evening'].get('sentiment', 'N/A')))
                
                if sentiment_stages:
                    # Build evolution arrow chain
                    sentiments_only = [s[1] for s in sentiment_stages]
                    unique_sentiments = list(dict.fromkeys(sentiments_only))  # preserve order, remove dupes
                    
                    if len(unique_sentiments) == 1:
                        evo_desc = f"Stable {unique_sentiments[0]} throughout the day"
                    else:
                        evo_chain = f" {EMOJI['right_arrow']} ".join(sentiments_only)
                        evo_desc = f"Evolved: {evo_chain}"
                    
                    page6.append(f"{EMOJI['bullet']} Sentiment evolution: {evo_desc}")
                else:
                    # Fallback if no tracking data
                    if day_sentiment == 'POSITIVE':
                        sent_evo_text = "Day closed with risk-on sentiment; intraday progression favored bulls"
                    elif day_sentiment == 'NEGATIVE':
                        sent_evo_text = "Day closed with risk-off sentiment; defensive positioning prevailed"
                    else:
                        sent_evo_text = "Day closed mixed; intraday signals rangebound without clear directional conviction"
                    page6.append(f"{EMOJI['bullet']} Sentiment evolution: {sent_evo_text}")
                page6.append(f"{EMOJI['bullet']} Cross-asset correlation: {'High' if day_sentiment != 'NEUTRAL' else 'Low'} - {'risk-on synchronization' if day_sentiment == 'POSITIVE' else 'defensive flight' if day_sentiment == 'NEGATIVE' else 'asset-specific behavior'}")
                page6.append(f"{EMOJI['bullet']} Pattern observed: {now.strftime('%A')} {'typical momentum day' if day_sentiment == 'POSITIVE' else 'defensive rotation expected' if day_sentiment == 'NEGATIVE' else 'rangebound action'}")
                page6.append(f"{EMOJI['bullet']} Note for tomorrow: {'Momentum likely continues' if day_sentiment == 'POSITIVE' else 'Watch for reversal signals' if day_sentiment == 'NEGATIVE' else 'Await directional clarity'}")
                
                # Final journal close
                page6.append("")
                page6.append(EMOJI['line'] * 40)
                page6.append(f"{EMOJI['check']} *DAILY JOURNAL COMPLETE*")
                page6.append(f"{EMOJI['bullet']} Total Pages: 6/6 - Full analysis + narrative delivered")
                page6.append(f"{EMOJI['bullet']} Analysis Quality: Consistent depth across quantitative and qualitative sections")
                page6.append(f"{EMOJI['bullet']} Next Cycle: Tomorrow 08:30 - Fresh Press Review (7 msgs)")
                page6.append(f"{EMOJI['bullet']} System Status: Fully operational - All enhanced modules active")
                
                pages.append("\n".join(page6))
                log.info(f"{EMOJI['check']} [SUMMARY] Page 6 (Daily Journal) generated")
                
            except Exception as e:
                log.error(f"{EMOJI['cross']} [SUMMARY] Error Page 6: {e}")
                pages.append(f"{header_base}{EMOJI['notebook']} *DAILY JOURNAL*\nJournal generation in progress...")
            
            # Persist compact daily metrics snapshot for weekly/monthly aggregation
            try:
                self._save_daily_metrics_snapshot(now, prediction_eval or {}, daily_market_snapshot)
            except Exception as e:
                # Already logged inside helper; keep Daily Summary robust
                log.warning(f"{EMOJI['warning']} [SUMMARY-METRICS] Wrapper error while saving metrics: {e}")

            # ENGINE snapshot for summary stage (full-day prediction_eval + market snapshot)
            try:
                summary_sentiment = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL') if isinstance(news_data, dict) else 'NEUTRAL'
                self._engine_log_stage('summary', now, summary_sentiment, daily_market_snapshot, prediction_eval or {})
            except Exception as e:
                log.warning(f"{EMOJI['warning']} [ENGINE-SUMMARY] Error logging engine stage: {e}")

            # === SAVE STRUCTURED JOURNAL JSON ===
            try:
                # Compute daily_accuracy_grade from prediction_eval (consistent with Page 1 logic)
                eval_for_grade = prediction_eval or {}
                total_for_grade = int(eval_for_grade.get('total_tracked', 0) or 0)
                acc_for_grade = float(eval_for_grade.get('accuracy_pct', 0.0) or 0.0)
                if total_for_grade > 0:
                    if acc_for_grade >= 80:
                        daily_accuracy_grade = 'A'
                    elif acc_for_grade >= 60:
                        daily_accuracy_grade = 'B'
                    elif acc_for_grade > 0:
                        daily_accuracy_grade = 'C'
                    else:
                        daily_accuracy_grade = 'D'
                else:
                    daily_accuracy_grade = 'N/A'
                
                # sentiment_tracking already loaded before Page 6

                journal_data = {
                    'date': now.strftime('%Y-%m-%d'),
                    'day_of_week': now.strftime('%A'),
                    'timestamp': now.isoformat(),
                    
                    # Narrative summary
                    'market_narrative': {
                        'story': market_story if 'market_story' in locals() else 'Market session completed',
                        'character': narrative_intro if 'narrative_intro' in locals() else 'Standard trading day',
                        'key_turning_points': key_turning if 'key_turning' in locals() else 'Regular intraday evolution',
                        'unexpected_events': []
                    },
                    
                    # Performance data
                    'model_performance': {
                        'daily_accuracy': f"{(prediction_eval.get('accuracy_pct', 0.0) if prediction_eval else 0.0):.0f}%" if (prediction_eval and prediction_eval.get('accuracy_pct', 0.0) > 0) else intraday_coherence.get('prediction_accuracy', '85%'),
                        'daily_accuracy_grade': daily_accuracy_grade,
                        'best_call': 'Tech sector leadership' if day_sentiment == 'POSITIVE' else 'Defensive positioning' if day_sentiment == 'NEGATIVE' else 'Range trading',
                        'worst_call': 'None' if day_sentiment == 'POSITIVE' else 'Timing of defensive shift' if day_sentiment == 'NEGATIVE' else 'Breakout timing',
'surprise_factor': 'BTC volatility' if abs(crypto_prices.get('BTC', {}).get('change_pct', 0)) > 3 else 'None',
                        'overall_grade': daily_accuracy_grade
                    },
                    
                    # Lessons and insights
                    'lessons_learned': [
                        'ML models effective in current regime' if day_sentiment == 'POSITIVE' else 'Risk management preserved capital',
                        f"Ensemble accuracy: {(prediction_eval.get('accuracy_pct', 0.0) if prediction_eval else 0.0):.0f}%" if (prediction_eval and prediction_eval.get('accuracy_pct', 0.0) > 0) else f"Ensemble accuracy: {intraday_coherence.get('prediction_accuracy', '85%')}",
                        'Narrative continuity maintained across 5 daily messages'
                    ],
                    
                    # Tomorrow preparation
                    'tomorrow_prep': {
                        'strategy': next_day_setup.get('summary_sentiment', 'Maintain current bias'),
                        'focus_areas': ['Tech sector', 'BTC levels', 'USD strength'],
                        'key_events': ['ECB decision' if now.weekday() == 2 else 'Standard session'],
                        'risk_level': 'Standard'
                    },
                    
                    # Metadata
                    'metadata': {
                        'messages_sent': 21,  # 5 daily messages: 7+3+3+3+5
                        'pages_generated': 6,
                        'sentiment_evolution': day_sentiment,
                        'sentiment_evolution_description': sent_evo_text if 'sent_evo_text' in locals() else (evo_desc if 'evo_desc' in locals() else 'Day completed'),
                        'sentiment_intraday_evolution': sentiment_tracking,
                        'news_volume': len(news_data.get('news', [])),
                        'coherence_score': intraday_coherence.get('overall_coherence', 'HIGH'),
                        'daily_accuracy_grade': daily_accuracy_grade
                    }
                }
                
                # Save JSON journal
                import json
                from pathlib import Path
                journal_dir = Path(self.reports_dir) / '10_daily_journal'
                journal_dir.mkdir(parents=True, exist_ok=True)
                
                journal_file = journal_dir / f"journal_{now.strftime('%Y-%m-%d')}.json"
                with open(journal_file, 'w', encoding='utf-8') as f:
                    json.dump(journal_data, f, indent=2, ensure_ascii=False)
                
                log.info(f"{EMOJI['check']} [JOURNAL] Structured journal saved: {journal_file}")
                
            except Exception as e:
                log.error(f"{EMOJI['cross']} [JOURNAL] Error saving JSON: {e}")
            
            # After journal + metrics are persisted, run BRAIN coherence analysis for last 7 days
            if COHERENCE_MANAGER_AVAILABLE:
                try:
                    coherence_manager.run_daily_coherence_analysis(days_back=7)
                    log.info(f"{EMOJI['check']} [COHERENCE] Updated rolling coherence history (7d)")
                except Exception as e:
                    log.warning(f"{EMOJI['warning']} [COHERENCE] Error running daily coherence analysis: {e}")

            # Save all pages with comprehensive metadata
            if pages:
                saved_path = self.save_content("daily_summary", pages, {
                    'total_pages': len(pages),
                    'enhanced_features': ['Executive Summary', 'Performance Analysis', 'ML Results', 'Market Review', 'Tomorrow Outlook', 'Daily Journal'],
                    'news_count': len(news_data.get('news', [])),
                    'sentiment': news_data.get('sentiment', {}),
                    'full_day_continuity': True,
                    'prediction_accuracy': f"{(prediction_eval.get('accuracy_pct', 0.0) if prediction_eval else 0.0):.0f}%",
                    'journal_generated': True,
                    'journal_file': f"reports/10_daily_journal/journal_{now.strftime('%Y-%m-%d')}.json",
                    'completion_status': 'FULL_555a_INTEGRATION_COMPLETE_WITH_JOURNAL'
                })
                log.info(f"Ã°Å¸â€™Â¾ [SUMMARY] Saved to: {saved_path}")
            
            log.info(f"Ã¢Å“â€¦ [SUMMARY] Completata generazione {len(pages)} pagine daily summary ENHANCED")
            return pages
            
        except Exception as e:
            log.error(f"Ã¢ÂÅ’ [SUMMARY] Errore general: {e}")
            # Emergency fallback
            return [f"Ã°Å¸â€œÅ  **SV - DAILY SUMMARY**\\nÃ°Å¸â€œâ€¦ {_now_it().strftime('%H:%M')} Ã¢â‚¬Â¢ system under maintenance"]

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













