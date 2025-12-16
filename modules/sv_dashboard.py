#!/usr/bin/env python3
"""
SV Dashboard - Web interface for SV Trading System
Simplified dashboard with real-time data integration
"""

from flask import Flask, render_template, jsonify, redirect
import json
import os
import sys
from datetime import datetime
import logging
import traceback
import webbrowser
import threading
import time

# Import SV modules with correct paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)  # repository root
config_dir = os.path.join(project_root, "config")
sys.path.insert(0, project_root)  # Enable imports from modules package at repo root
sys.path.insert(0, config_dir)    # Add config for sv_paths and settings

try:
    from modules.sv_news import get_sv_news_system
    from modules.sv_calendar import get_sv_calendar_system
    from modules.daily_generator import (
        get_live_crypto_prices,
    )
    from modules.engine.market_data import get_market_snapshot
    from modules.portfolio_manager import get_portfolio_manager
    SV_MODULES_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("SV modules imported successfully")
except ImportError as e:
    SV_MODULES_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"SV modules not available: {e}")

# Import BRAIN helpers for prediction evaluation/status (independent from SV_MODULES_AVAILABLE)
from modules.brain.prediction_status import (
    calculate_prediction_accuracy,
    compute_prediction_status,
)
from config import sv_paths

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Base directories
BASE_DIR = project_root
TEMPLATES_DIR = sv_paths.TEMPLATES_DIR
DATA_DIR = os.path.join(BASE_DIR, 'data')

app = Flask(__name__, template_folder=TEMPLATES_DIR)
app.config['DEBUG'] = True
# Ensure UTF-8 JSON to avoid emoji/glyph corruption
app.config['JSON_AS_ASCII'] = False

def get_current_crypto_prices():
    """Get current crypto prices using SV crypto system.
    Returns an empty mapping when live data is unavailable (no fake fallbacks)."""
    try:
        if SV_MODULES_AVAILABLE:
            prices = get_live_crypto_prices()
            if prices:
                logger.info(f"Retrieved {len(prices)} crypto prices from SV system")
                return prices
        
        # No reliable data available: return empty mapping instead of fake prices
        logger.warning("Crypto prices unavailable from SV system; returning empty mapping")
        return {}
    except Exception as e:
        logger.error(f"Error getting crypto prices: {e}")
        return {}


def get_key_assets_prices():
    """Return a consolidated mapping for BTC, SPX, EURUSD, GOLD with price and change_pct if available.

    This now reuses the ENGINE market snapshot helper to avoid duplication,
    while preserving the external structure used by dashboard and ML endpoints.
    """
    try:
        result = {}

        # BTC still comes from the crypto subsystem (so we preserve behaviour when
        # SV_MODULES_AVAILABLE is False and return an empty/partial mapping).
        prices = get_current_crypto_prices() or {}
        if 'BTC' in prices:
            result['BTC'] = {
                'price': prices['BTC'].get('price', 0),
                'change_pct': prices['BTC'].get('change_pct', 0),
            }

        assets = {}
        if SV_MODULES_AVAILABLE:
            try:
                market = get_market_snapshot() or {}
                if isinstance(market, dict):
                    assets = market.get('assets', {}) or {}
            except Exception as e:
                logger.warning(f"ENGINE market snapshot unavailable: {e}")
                assets = {}

        # SPX
        spx = assets.get('SPX') if isinstance(assets, dict) else None
        if spx:
            result['SPX'] = {
                'price': spx.get('price', 0),
                'change_pct': spx.get('change_pct', 0),
            }
        else:
            # No fake fallback levels: expose 0 so clients can treat as "data unavailable"
            result['SPX'] = {'price': 0, 'change_pct': 0}

        # EURUSD
        eur = assets.get('EURUSD') if isinstance(assets, dict) else None
        if eur:
            result['EURUSD'] = {
                'price': eur.get('price', 0),
                'change_pct': eur.get('change_pct', 0),
            }
        else:
            result['EURUSD'] = {'price': 0, 'change_pct': 0}

        # GOLD (always USD/gram)
        gold = assets.get('GOLD') if isinstance(assets, dict) else None
        if gold:
            result['GOLD'] = {
                'price': gold.get('price', 0),
                'change_pct': gold.get('change_pct', 0),
                'unit': 'USD/g',
            }
        else:
            result['GOLD'] = {'price': 0, 'change_pct': 0, 'unit': 'USD/g'}

        return result
    except Exception as e:
        logger.error(f"Error getting key assets prices: {e}")
        return {}

def get_real_predictions():
    """Load real ML predictions from SV system"""
    try:
        # Check for today's predictions
        today = datetime.now().strftime("%Y-%m-%d")
        predictions_file = os.path.join(BASE_DIR, 'reports', '1_daily', f'predictions_{today}.json')
        
        if os.path.exists(predictions_file):
            with open(predictions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data.get('predictions', []))} real predictions from {predictions_file}")
                return data.get('predictions', [])
        
        logger.warning(f"No predictions file found: {predictions_file}")
        return []
    except Exception as e:
        logger.error(f"Error loading predictions: {e}")
        return []

def get_ml_trading_signals():
    """Get real ML trading signals from SV momentum indicators"""
    try:
        if SV_MODULES_AVAILABLE:
            from modules.momentum_indicators import (
                calculate_news_momentum,
                detect_news_catalysts,
                Generatete_trading_signals as generate_trading_signals,
                calculate_risk_metrics
            )
            from modules.sv_news import get_sv_news_system
            
            # Get recent news for analysis
            news_system = get_sv_news_system()
            recent_news = news_system.get_all_news(max_news=50)
            
            # Convert to format expected by momentum indicators
            analyzed_news = []
            for news in recent_news:
                analyzed_news.append({
                    'title': news.get('titolo', ''),
                    'category': news.get('category', 'General'),
                    'sentiment': 'POSITIVE' if 'bullish' in news.get('titolo', '').lower() else 
                               'NEGATIVE' if 'bearish' in news.get('titolo', '').lower() else 'NEUTRAL',
                    'impact': 'HIGH' if news.get('critica', False) else 'MEDIUM'
                })
            
            # Calculate momentum and catalysts
            momentum = calculate_news_momentum(analyzed_news)
            
            category_weights = {
                'Finance': 2.0, 'Crypto': 1.8, 'Technology': 1.5, 
                'Politics': 1.2, 'General': 1.0
            }
            catalysts = detect_news_catalysts(analyzed_news, category_weights)
            
            # Mock market regime (could be enhanced with real data)
            market_regime = {
                'name': 'BULL MARKET' if momentum['momentum_score'] > 0.2 else 
                       'BEAR MARKET' if momentum['momentum_score'] < -0.2 else 
                       'HIGH VOLATILITY',
                'position_sizing': 1.0
            }
            
            # Generate trading signals
            trading_signals = generate_trading_signals(market_regime, momentum, catalysts)
            
            # Calculate risk metrics
            risk_metrics = calculate_risk_metrics(analyzed_news, market_regime)
            
            logger.info(f"Generated {len(trading_signals)} ML trading signals")
            
            return {
                'trading_signals': trading_signals,
                'momentum': momentum,
                'catalysts': catalysts,
                'risk_metrics': risk_metrics,
                'market_regime': market_regime,
                'news_analyzed': len(analyzed_news)
            }
        
        # Fallback mock signals
        return {
            'trading_signals': ["📊 **STANDARD**: Monitor market conditions"],
            'momentum': {'momentum_direction': 'SIDEWAYS', 'momentum_score': 0},
            'catalysts': {'has_major_catalyst': False, 'top_catalysts': []},
            'risk_metrics': {'risk_level': 'MEDIUM', 'risk_score': 1.0},
            'market_regime': {'name': 'NEUTRAL'},
            'news_analyzed': 0
        }
    except Exception as e:
        logger.error(f"Error getting ML trading signals: {e}")
        return {
            'trading_signals': ["⚠️ **ERROR**: Unable to generate signals"],
            'momentum': {'momentum_direction': 'UNKNOWN', 'momentum_score': 0},
            'catalysts': {'has_major_catalyst': False, 'top_catalysts': []},
            'risk_metrics': {'risk_level': 'UNKNOWN', 'risk_score': 1.0},
            'market_regime': {'name': 'UNKNOWN'},
            'news_analyzed': 0
        }



@app.route('/')
def dashboard_page():
    """Landing page that frames navigation across sections"""
    try:
        template_path = os.path.join(TEMPLATES_DIR, 'dashboard.html')
        if not os.path.exists(template_path):
            logger.error(f"Template not found: {template_path}")
            return f"<h1>SV Dashboard</h1><p>Template not found: {template_path}</p>", 404
        return render_template('dashboard.html')
    except Exception as e:
        logger.error(f"Dashboard page error: {e}")
        traceback.print_exc()
        return f"<h1>Dashboard Page Error</h1><p>{str(e)}</p>", 500


@app.route('/news')
def news_page():
    """Standalone news page"""
    try:
        template_path = os.path.join(TEMPLATES_DIR, 'news.html')
        if not os.path.exists(template_path):
            logger.error(f"Template not found: {template_path}")
            return f"<h1>SV News</h1><p>Template not found: {template_path}</p>", 404
        return render_template('news.html')
    except Exception as e:
        logger.error(f"News page error: {e}")
        traceback.print_exc()
        return f"<h1>News Page Error</h1><p>{str(e)}</p>", 500


@app.route('/portfolio')
def portfolio_page():
    """Redirect to the unified dashboard (single source of truth)."""
    # Keep /portfolio as a stable entry-point, but render everything inside dashboard.html
    return redirect('/?tab=portfolio', code=302)

@app.route('/ml')
def ml_page():
    """Daily Signals Results page"""
    try:
        template_path = os.path.join(TEMPLATES_DIR, 'ml.html')
        if not os.path.exists(template_path):
            # Fallback minimal page consuming /api/ml
            return ("""
            <html><head><meta charset='utf-8'><title>SV - Daily Signals</title></head>
            <body>
            <h2>SV - Daily Signals</h2>
            <div id='content'>Loading...</div>
            <script>
            fetch('/api/ml').then(r=>r.json()).then(d=>{
              const rows = (d.live_predictions||[]).map(p=>`<tr><td>${p.asset}</td><td>${p.direction}</td><td>${p.entry}</td><td>${p.target}</td><td>${p.stop}</td><td>${p.current_price}</td><td>${p.accuracy}%</td><td>${p.status}</td></tr>`).join('');
              document.getElementById('content').innerHTML = `<table border='1' cellpadding='6'><tr><th>Asset</th><th>Dir</th><th>Entry</th><th>Target</th><th>Stop</th><th>Live</th><th>Accuracy</th><th>Status</th></tr>${rows}</table>`;
            }).catch(e=>{document.getElementById('content').innerText='Error: '+e});
            </script>
            </body></html>
            """), 200
        return render_template('ml.html')
    except Exception as e:
        logger.error(f"ML page error: {e}")
        return f"<h1>ML Page Error</h1><p>{str(e)}</p>", 500

@app.route('/api/status')
def get_status():
    """System status endpoint"""
    try:
        current_time = datetime.now()
        
        # Determine market status based on time
        if current_time.weekday() >= 5:  # Weekend
            market_status = "WEEKEND"
        elif 9 <= current_time.hour < 17:  # Business hours
            market_status = "OPEN"
        else:
            market_status = "CLOSED"
        
        logger.info(f"Status requested - Market: {market_status}")
        
        return jsonify({
            "timestamp": current_time.isoformat(),
            "market_status": market_status,
            "system_online": True,
            "sv_version": "1.0.0",
            "scheduler": {
                "market_intelligence": {
                    "market_status": market_status
                },
                "pending_content": []
            }
        })
    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/news')
def get_news():
    """News endpoint with real SV data"""
    try:
        # Try to get real SV news data
        if SV_MODULES_AVAILABLE:
            logger.info("Fetching real SV news data")
            news_system = get_sv_news_system()
            
            # Get all news for dashboard
            all_news = news_system.get_all_news(max_news=100)
            
            # Organize by category
            by_category = {}
            latest_news = []
            
            for news_item in all_news:
                # Normalize news format for frontend
                normalized_item = {
                    "titolo": news_item.get('titolo', 'News Update'),
                    "categoria": news_item.get('category', 'General'),
                    "fonte": news_item.get('source', 'Unknown Source'),
                    "link": news_item.get('link', '#'),
                    "data": news_item.get('data', datetime.now().strftime("%H:%M")),
                    "critica": news_item.get('critica', False)
                }
                latest_news.append(normalized_item)
                
                # Count by category
                category = normalized_item['categoria']
                by_category[category] = by_category.get(category, 0) + 1
            
            logger.info(f"Retrieved {len(latest_news)} real news items from {len(by_category)} categories")
            
            return jsonify({
                "latest_news": latest_news,
                "by_category": by_category,
                "source": "sv_real_data",
                "timestamp": datetime.now().isoformat()
            })
        
        # Try to read cached news data
        news_file = os.path.join(DATA_DIR, 'processed_news.json')
        if os.path.exists(news_file):
            logger.info(f"Reading cached news from: {news_file}")
            with open(news_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return jsonify(data)
        
        # Fallback mock data
        logger.info("Using fallback mock news data")
        mock_news = {
            "latest_news": [
                {
                    "titolo": "🚀 SV Dashboard System Online",
                    "categoria": "System",
                    "fonte": "SV Core",
                    "link": "#",
                    "data": datetime.now().strftime("%H:%M"),
                    "critica": False
                },
                {
                    "titolo": "📊 Real-time RSS Integration Active",
                    "categoria": "Finance",
                    "fonte": "SV News System",
                    "link": "#",
                    "data": datetime.now().strftime("%H:%M"),
                    "critica": True
                }
            ],
            "by_category": {
                "System": 1,
                "Finance": 1
            },
            "source": "mock_data"
        }
        
        return jsonify(mock_news)
        
    except Exception as e:
        logger.error(f"News error: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/calendar')
def get_calendar():
    """Calendar endpoint with real SV data"""
    try:
        # Try to get real SV calendar data
        if SV_MODULES_AVAILABLE:
            logger.info("Fetching real SV calendar data")
            calendar_system = get_sv_calendar_system()
            
            # Get market status
            market_status, market_message = calendar_system.get_market_status()
            
            # Get day context
            day_context = calendar_system.get_day_context()
            
            # Get upcoming events (next 14 days)
            upcoming_events = calendar_system.get_events_next_days(days=14)
            
            # Get calendar impact analysis
            calendar_impact = calendar_system.analyze_calendar_impact(upcoming_events)
            
            logger.info(f"Retrieved market status: {market_status}, {len(upcoming_events)} events")
            
            return jsonify({
                "market_status": market_status,
                "market_message": market_message,
                "upcoming_events": upcoming_events,
                "day_context": day_context,
                "calendar_impact": calendar_impact,
                "source": "sv_real_data",
                "timestamp": datetime.now().isoformat()
            })
        
        # Try to read cached calendar data
        calendar_file = os.path.join(DATA_DIR, 'calendar_analysis.json')
        if os.path.exists(calendar_file):
            logger.info(f"Reading cached calendar from: {calendar_file}")
            with open(calendar_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return jsonify(data)
        
        # Fallback mock data
        logger.info("Using fallback mock calendar data")
        current_time = datetime.now()
        
        # Market status logic
        if current_time.weekday() >= 5:
            market_status = "WEEKEND"
            market_message = "Markets closed for weekend"
        elif 9 <= current_time.hour < 17:
            market_status = "OPEN"
            market_message = "European markets are active"
        else:
            market_status = "CLOSED"
            market_message = "Markets closed - after hours"
        
        mock_calendar = {
            "market_status": market_status,
            "market_message": market_message,
            "upcoming_events": [
                {
                    "Title": "SV Calendar System - Real Data Integration",
                    "Impact": "High",
                    "Category": "System",
                    "Icon": "🚀",
                    "Source": "SV Calendar",
                    "days_from_now": 0
                }
            ],
            "day_context": {
                "desc": "Dashboard Integration Day",
                "focus": "Real Data Integration",
                "tone": "Technical",
                "content_priority": "High"
            },
            "source": "mock_data"
        }
        
        return jsonify(mock_calendar)
        
    except Exception as e:
        logger.error(f"Calendar error: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/ml')
def get_ml():
    """ML Analysis endpoint with real predictions and asset prices"""
    try:
        # Get real crypto prices from SV system
        crypto_prices = get_current_crypto_prices()
        # Get key cross-asset prices (SPX, EURUSD, GOLD) from unified helper
        key_prices = get_key_assets_prices() or {}
        
        # Load real ML predictions
        predictions = get_real_predictions()
        
        # Get real ML trading signals
        ml_signals = get_ml_trading_signals()
        
        # Process predictions with live prices
        prediction_analysis = []
        total_accuracy = 0
        valid_predictions = 0
        
        for pred in predictions:
            asset = pred.get('asset', '')
            direction = pred.get('direction', 'LONG')
            entry = pred.get('entry', 0)
            target = pred.get('target', 0)
            stop = pred.get('stop', 0)
            confidence = pred.get('confidence', 50)
            
            # Get current price for this asset
            current_price = 0
            price_change = 0
            
            if asset in crypto_prices:
                current_price = crypto_prices[asset].get('price', 0)
                price_change = crypto_prices[asset].get('change_pct', 0)
            elif asset == 'SPX':
                kp = key_prices.get('SPX', {})
                current_price = kp.get('price', 0)
                price_change = kp.get('change_pct', 0)
            elif asset == 'EURUSD':
                kp = key_prices.get('EURUSD', {})
                current_price = kp.get('price', 0)
                price_change = kp.get('change_pct', 0)
            elif asset == 'GOLD':
                kp = key_prices.get('GOLD', {})
                current_price = kp.get('price', 0)
                price_change = kp.get('change_pct', 0)
            
            # Calculate prediction accuracy
            accuracy_info = calculate_prediction_accuracy(pred, current_price)
            
            if accuracy_info['accuracy'] > 0:
                total_accuracy += accuracy_info['accuracy']
                valid_predictions += 1
            
            prediction_analysis.append({
                'asset': asset,
                'direction': direction,
                'entry': entry,
                'target': target,
                'stop': stop,
                'confidence': confidence,
                'current_price': current_price,
                'price_change_24h': price_change,
                'accuracy': accuracy_info['accuracy'],
                'status': accuracy_info['status'],
                'distance_to_target': abs(target - current_price) if current_price > 0 else 0,
                'risk_reward': abs(target - entry) / abs(entry - stop) if stop != entry else 1
            })
        
        # Add baseline tracking for key assets even when predictions are missing
        required_assets = {'BTC', 'SPX', 'EURUSD', 'GOLD'}
        present_assets = set(p['asset'] for p in prediction_analysis)

        for asset in sorted(required_assets - present_assets):
            price_info = key_prices.get(asset, {}) or crypto_prices.get(asset, {})
            current_price = price_info.get('price', 0)
            price_change = price_info.get('change_pct', 0)

            prediction_analysis.append({
                'asset': asset,
                'direction': 'HOLD',
                'entry': current_price,
                'target': current_price,
                'stop': current_price,
                'confidence': 0,
                'current_price': current_price,
                'price_change_24h': price_change,
                'accuracy': 0,
                'status': 'DATA ONLY',
                'distance_to_target': 0,
                'risk_reward': 1,
            })
            logger.info(f"Added baseline ML snapshot for {asset} with live pricing only")

        # Calculate overall accuracy
        overall_accuracy = round(total_accuracy / valid_predictions, 1) if valid_predictions > 0 else 0
        
        # Create ML analysis with real data
        ml_data = {
            "predictions_active": len(predictions),
            "overall_accuracy": overall_accuracy,
            "assets_tracked": len(set(p['asset'] for p in prediction_analysis)),
            "predictions_made": len(predictions),
            "coherence_score": 85 if overall_accuracy > 70 else 70 if overall_accuracy > 50 else 55,
            "live_predictions": prediction_analysis,
            "trading_signals": ml_signals['trading_signals'],
            "momentum_analysis": {
                "direction": ml_signals['momentum']['momentum_direction'],
                "score": ml_signals['momentum']['momentum_score'],
                "emoji": ml_signals['momentum'].get('momentum_emoji', '📊')
            },
            "catalysts": {
                "has_major_catalyst": ml_signals['catalysts']['has_major_catalyst'],
                "top_catalysts": ml_signals['catalysts']['top_catalysts'][:3],
                "total_found": ml_signals['catalysts']['total_catalysts']
            },
            "risk_assessment": {
                "level": ml_signals['risk_metrics']['risk_level'],
                "score": ml_signals['risk_metrics']['risk_score'],
                "emoji": ml_signals['risk_metrics']['risk_emoji'],
                "geopolitical_events": ml_signals['risk_metrics']['geopolitical_events'],
                "financial_stress": ml_signals['risk_metrics']['financial_stress_events']
            },
            "market_regime": ml_signals['market_regime']['name'],
            "news_analyzed": ml_signals['news_analyzed'],
            "market_sentiment": {
                "crypto": "Bullish" if any(crypto_prices.get(asset, {}).get('change_pct', 0) > 0 for asset in ['BTC', 'ETH']) else "Bearish",
                "traditional": "Mixed",
                "overall_bias": "Risk-On" if overall_accuracy > 65 else "Cautious"
            },
            "price_summary": {
                **{
                    asset: {
                        "price": data.get('price', 0),
                        "change_24h": data.get('change_pct', 0)
                    } for asset, data in crypto_prices.items() if asset != 'TOTAL_MARKET_CAP'
                },
                **{
                    asset: {
                        "price": data.get('price', 0),
                        "change_24h": data.get('change_pct', 0)
                    } for asset, data in key_prices.items() if asset in {'SPX', 'EURUSD', 'GOLD'}
                }
            }
        }
        
        logger.info(f"ML Analysis: {len(predictions)} predictions, {overall_accuracy}% accuracy")
        return jsonify(ml_data)
        
    except Exception as e:
        logger.error(f"ML error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/ml/daily_verification')
def ml_daily_verification():
    """Aggregate today's predictions and compute Hit/Miss/Pending status using live prices."""
    try:
        # Load predictions (base)
        predictions = get_real_predictions()
        live = get_key_assets_prices()
        crypto = get_current_crypto_prices()
        verified = []
        hits = misses = pending = 0
        for pred in predictions:
            status_info = compute_prediction_status(pred, live, crypto)
            item = {
                'asset': pred.get('asset'),
                'direction': pred.get('direction'),
                'entry': pred.get('entry'),
                'target': pred.get('target'),
                'stop': pred.get('stop'),
                'current_price': status_info['current_price'],
                'status': status_info['status'],
                'progress_pct': status_info['progress_pct'],
                'accuracy': status_info['accuracy'],
                'risk_reward': status_info['rr'],
            }
            if status_info['status'] == 'Hit target':
                hits += 1
            elif status_info['status'] == 'Stopped out':
                misses += 1
            else:
                pending += 1
            verified.append(item)
        return jsonify({
            'date': datetime.now().strftime('%Y-%m-%d'),
            'counts': {'hits': hits, 'misses': misses, 'pending': pending},
            'items': verified
        })
    except Exception as e:
        logger.error(f"ML daily verification error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/ml/asset_results')
def ml_asset_results():
    """Group today's prediction results per asset, with hit/miss/pending counts and hit rate."""
    try:
        predictions = get_real_predictions()
        live = get_key_assets_prices()
        crypto = get_current_crypto_prices()
        groups = {}
        for pred in predictions:
            asset = (pred.get('asset') or 'UNKNOWN').upper()
            info = compute_prediction_status(pred, live, crypto)
            g = groups.setdefault(asset, {
                'counts': {'hits': 0, 'misses': 0, 'pending': 0, 'total': 0},
                'items': []
            })
            g['counts']['total'] += 1
            st = info.get('status')
            if st == 'Hit target':
                g['counts']['hits'] += 1
            elif st == 'Stopped out':
                g['counts']['misses'] += 1
            else:
                g['counts']['pending'] += 1
            g['items'].append({
                'direction': pred.get('direction'),
                'entry': pred.get('entry'),
                'target': pred.get('target'),
                'stop': pred.get('stop'),
                'current_price': info.get('current_price'),
                'status': st,
                'progress_pct': info.get('progress_pct'),
                'risk_reward': info.get('rr')
            })
        # Compute hit rate per asset
        for a, g in groups.items():
            total = g['counts']['total'] or 1
            g['hit_rate'] = round((g['counts']['hits'] / total) * 100, 1)
        return jsonify({
            'date': datetime.now().strftime('%Y-%m-%d'),
            'assets': groups
        })
    except Exception as e:
        logger.error(f"ML asset results error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio_snapshot')
def get_portfolio_snapshot_api():
    """Get current portfolio snapshot with $10K tracking"""
    try:
        if not SV_MODULES_AVAILABLE:
            return jsonify({'error': 'Portfolio manager not available'}), 503
        
        # Get portfolio manager
        portfolio_manager = get_portfolio_manager(BASE_DIR)
        
        # Update positions with live prices
        live_prices = get_key_assets_prices()
        if live_prices:
            portfolio_manager.update_positions(live_prices)
        
        # Get snapshot
        snapshot = portfolio_manager.get_portfolio_snapshot()
        
        # Add additional dashboard metrics
        snapshot['initial_capital'] = portfolio_manager.initial_capital
        snapshot['timestamp'] = datetime.now().isoformat()
        
        logger.info(f"Portfolio snapshot: ${snapshot['current_balance']:.2f} ({snapshot['total_pnl_pct']:.2f}%)")
        return jsonify(snapshot)
        
    except Exception as e:
        logger.error(f"Portfolio snapshot error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio_positions')
def get_portfolio_positions():
    """Get detailed view of active positions"""
    try:
        if not SV_MODULES_AVAILABLE:
            return jsonify({'error': 'Portfolio manager not available'}), 503
        
        portfolio_manager = get_portfolio_manager(BASE_DIR)
        
        # Update with live prices
        live_prices = get_key_assets_prices()
        if live_prices:
            portfolio_manager.update_positions(live_prices)
        
        snapshot = portfolio_manager.get_portfolio_snapshot()
        positions = snapshot.get('positions', [])
        
        # Format positions for dashboard display
        formatted_positions = []
        for pos in positions:
            formatted_positions.append({
                'id': pos.get('id', ''),
                'asset': pos.get('asset', ''),
                'direction': pos.get('direction', ''),
                'entry_price': pos.get('entry_price', 0),
                'target_price': pos.get('target_price', 0),
                'stop_price': pos.get('stop_price', 0),
                'current_price': pos.get('current_price', 0),
                'position_size': pos.get('position_size', 0),
                'units': pos.get('units', 0),
                'current_pnl': pos.get('current_pnl', 0),
                'pnl_percentage': pos.get('pnl_percentage', 0),
                'confidence': pos.get('confidence', 0),
                'entry_time': pos.get('entry_time', ''),
                'status': pos.get('status', 'UNKNOWN'),
                'max_favorable': pos.get('max_favorable', 0),
                'max_adverse': pos.get('max_adverse', 0),
                # These are "ideal" in a simulated portfolio (intended execution venue/settings)
                'broker': pos.get('broker', 'IG'),
                'ideal_broker': pos.get('broker', 'IG'),
                'leverage': pos.get('leverage', 0),
            })
        
        return jsonify({
            'positions': formatted_positions,
            'total_positions': len(formatted_positions),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Portfolio positions error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/intraday_timeline')
def get_intraday_timeline():
    """Get intraday performance timeline from engine logs"""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        engine_file = os.path.join(BASE_DIR, 'reports', 'metrics', f'engine_{today}.json')
        
        timeline_events = []
        
        if os.path.exists(engine_file):
            with open(engine_file, 'r', encoding='utf-8') as f:
                engine_data = json.load(f)
            
            stages = engine_data.get('stages', [])
            
            # Group stages by type and get latest timestamp for each
            stage_latest = {}
            for stage in stages:
                stage_type = stage.get('stage', '')
                stage_time = stage.get('timestamp', '')
                
                if not stage_latest.get(stage_type) or stage_time > stage_latest[stage_type]['timestamp']:
                    stage_latest[stage_type] = stage
            
            # Create timeline from unique stages
            stage_order = ['night', 'late_night', 'press_review', 'morning', 'noon', 'afternoon', 'evening', 'summary']
            stage_names = {
                'night': 'Night Report',
                'late_night': 'Late Night Update',
                'press_review': 'Press Review',
                'morning': 'Morning Report',
                'noon': 'Noon Update',
                'afternoon': 'Afternoon Update',
                'evening': 'Evening Analysis',
                'summary': 'Daily Summary'
            }
            
            for stage_key in stage_order:
                if stage_key in stage_latest:
                    stage = stage_latest[stage_key]
                    timestamp = stage.get('timestamp', '')
                    time_str = timestamp[11:16] if len(timestamp) > 16 else '--:--'  # Extract HH:MM
                    
                    prediction_eval = stage.get('prediction_eval', {})
                    accuracy = prediction_eval.get('accuracy_pct')
                    accuracy_str = f"{accuracy:.0f}%" if accuracy is not None else '--'
                    
                    timeline_events.append({
                        'time': time_str,
                        'event': stage_names.get(stage_key, stage_key.title()),
                        'accuracy': accuracy_str,
                        'sentiment': stage.get('sentiment', 'UNKNOWN'),
                        'status': 'completed',
                        'stage_key': stage_key
                    })
        
        # Add expected stages that haven't occurred yet
        current_hour = datetime.now().hour
        expected_stages = [
            ('00:00', 'night', 'Night Report'),
            ('03:00', 'late_night', 'Late Night Update'),
            ('06:00', 'press_review', 'Press Review'),
            ('09:00', 'morning', 'Morning Report'),
            ('12:00', 'noon', 'Noon Update'),
            ('15:00', 'afternoon', 'Afternoon Update'),
            ('18:00', 'evening', 'Evening Analysis'),
            ('21:00', 'summary', 'Daily Summary')
        ]
        
        existing_stages = {event['stage_key'] for event in timeline_events}
        
        for expected_time, stage_key, stage_name in expected_stages:
            if stage_key not in existing_stages:
                expected_hour = int(expected_time.split(':')[0])
                status = 'pending' if current_hour < expected_hour else 'scheduled'
                
                timeline_events.append({
                    'time': expected_time,
                    'event': stage_name,
                    'accuracy': '--',
                    'sentiment': 'PENDING',
                    'status': status,
                    'stage_key': stage_key
                })
        
        # Sort by time
        timeline_events.sort(key=lambda x: x['time'])
        
        return jsonify({
            'timeline': timeline_events,
            'date': today,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Intraday timeline error: {e}")
        return jsonify({'error': str(e)}), 500

def check_dependencies():
    """Check required dependencies"""
    try:
        import flask
        logger.info(f"Flask version: {flask.__version__}")
        return True
    except ImportError as e:
        logger.error(f"Missing dependencies: {e}")
        return False

def setup_directories():
    """Setup required directories"""
    # Data directory creation is intentionally disabled; callers must provision it if needed
    if not os.path.exists(DATA_DIR):
        logger.warning(f"Data directory missing: {DATA_DIR} (creation skipped per configuration)")

def open_browser():
    """Open browser after a short delay (only in main process)"""
    # Only open browser in main process, not in Flask reloader subprocess
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        time.sleep(2)  # Wait for Flask to start
        try:
            webbrowser.open('http://localhost:5000')
            logger.info("Browser opened automatically")
        except Exception as e:
            logger.warning(f"Could not open browser automatically: {e}")

def main():
    """Run the dashboard"""
    print("🚀 Starting SV Dashboard...")
    print(f"📁 Base directory: {BASE_DIR}")
    print(f"📁 Templates: {TEMPLATES_DIR}")
    print(f"📁 Data: {DATA_DIR}")
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Error: Install Flask with 'pip install flask'")
        return
    
    # Setup directories
    setup_directories()
    
    # Check templates
    dashboard_template = os.path.join(TEMPLATES_DIR, 'dashboard.html')
    news_template = os.path.join(TEMPLATES_DIR, 'news.html')
    portfolio_template = os.path.join(TEMPLATES_DIR, 'portfolio.html')
    if not os.path.exists(dashboard_template):
        print(f"⚠️  Template not found: {dashboard_template}")
    if not os.path.exists(news_template):
        print(f"⚠️  Template not found: {news_template}")
    if not os.path.exists(portfolio_template):
        print(f"⚠️  Template not found: {portfolio_template}")

    print("\n📊 Dashboard starting at:")
    print("   - http://localhost:5000 (dashboard)")
    print("   - http://localhost:5000/news (news)")
    print("   - http://localhost:5000/portfolio (portfolio)")
    print("   - http://localhost:5000/api/status (system status)")
    print("   - http://localhost:5000/api/news (news feed)")
    print("   - http://localhost:5000/api/calendar (calendar events)")
    print("\n🌍 Browser will open automatically in 2 seconds...")
    print("🔄 Debug mode active - auto-restart enabled")
    print("⏹️  Use Ctrl+C to stop\n")
    
    # Start browser opening in background thread
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    try:
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=True
        )
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()