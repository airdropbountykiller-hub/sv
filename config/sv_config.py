#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - Configuration System
Centralized system for all configurations SV
"""

import os
import json
from typing import Dict, List, Optional

# === PROJECT PATHS ===
def get_project_root():
    """Get project root directory"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_config_file_path(filename: str) -> str:
    """Get path to config file"""
    return os.path.join(get_project_root(), 'config', filename)

# === RSS FEEDS CONFIGURATION ===
RSS_FEEDS_CONFIG = {
    "Finanza": [
        "https://feeds.reuters.com/reuters/businessNews",
        "https://www.investing.com/rss/news_285.rss",
        "https://www.marketwatch.com/rss/topstories",
        "https://feeds.finance.yahoo.com/rss/2.0/headline",
        "https://feeds.bloomberg.com/markets/news.rss",
        "https://rss.cnn.com/rss/money_latest.rss",
        "https://seekingalpha.com/market_currents.xml",
        # Additions (small step): broaden market coverage
        "https://feeds.reuters.com/reuters/marketsNews",
        "https://www.cnbc.com/id/10001147/device/rss/rss.html",   # CNBC Markets
        "https://www.cnbc.com/id/100003114/device/rss/rss.html", # CNBC Top News
        "https://finance.yahoo.com/news/rssindex",               # Yahoo Finance index
        "https://www.barrons.com/feeds/latest.xml?mod=hp_latestrss",
        "https://www.morningstar.com/articles/rss",
        # Extra finance/macroeconomics coverage
        "https://www.economist.com/finance-and-economics/rss.xml",
        "https://www.ft.com/markets?format=rss",
        "https://www.wsj.com/xml/rss/3_7031.xml",  # WSJ Markets
        "https://www.bloomberg.com/feed/podcast/odd-lots",       # Bloomberg macro/markets podcast feed
        "https://www.bbc.co.uk/news/business/rss.xml",
        "https://www.imf.org/external/pubs/ft/survey/eng/rss/rss.aspx"
    ],
    "Criptovalute": [
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://cointelegraph.com/rss",
        "https://cryptoslate.com/feed/",
        "https://bitcoinist.com/feed/",
        "https://cryptopotato.com/feed/",
        "https://decrypt.co/feed",
        "https://www.cryptonews.com/news/feed/",
        "https://ambcrypto.com/feed/",
        # Additions (small step): increase crypto breadth
        "https://news.bitcoin.com/feed/",
        "https://u.today/rss",
        "https://coinjournal.net/news/feed/",
        "https://blog.coinbase.com/feed",
        "https://blog.kraken.com/feed",
        "https://www.coingecko.com/en/news.rss",
        # Atlas21 – Bitcoin/crypto research & news (EN)
        "https://atlas21.com/feed/",
        # Extra crypto/DeFi/market structure coverage
        "https://blockworks.co/feed",              # Blockworks
        "https://thedefiant.io/feed",              # The Defiant (DeFi)
        "https://www.theblock.co/rss",             # The Block
        "https://messari.io/rss",                  # Messari research updates
        "https://banklesshq.com/feed",             # Bankless
        "https://newsletter.glassnode.com/feed"    # Glassnode on-chain insights
    ],
    "Geopolitica": [
        "https://feeds.reuters.com/Reuters/worldNews",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "http://feeds.bbci.co.uk/news/world/rss.xml",
        "http://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://feeds.bbci.co.uk/news/rss.xml",
        "https://rss.cnn.com/rss/edition.rss",
        "https://feeds.npr.org/1001/rss.xml",
        # Additions (small step): broaden geopolitics coverage
        "https://feeds.reuters.com/Reuters/PoliticsNews",
        "https://rss.dw.com/rdf/rss-en-all",
        "https://www.theguardian.com/politics/rss",
        "https://www.economist.com/international/rss.xml",
        "https://www.politico.eu/feed/",
        "https://www.cfr.org/rss/blog",
        "https://www.nato.int/cps/en/natohq/news.xml",
        "https://www.ft.com/world?format=rss",
        "https://www.cnbc.com/id/100727362/device/rss/rss.html",
        "https://news.yahoo.com/world/rss/",
        "https://feeds.washingtonpost.com/rss/world",
        # Extra geopolitics/foreign policy coverage
        "https://foreignpolicy.com/feed/",
        "https://www.economist.com/middle-east-and-africa/rss.xml",
        "https://www.economist.com/asia/rss.xml",
        "https://www.chathamhouse.org/rss/all",
        "https://www.csis.org/rss/analysis",
        "https://www.brookings.edu/feed/"
    ],
    "Economia Italia": [
        "https://www.ilsole24ore.com/rss/news.xml",
        "https://feeds.reuters.com/reuters/ITtopNews",
        "https://www.corriere.it/rss/economia.xml",
        # Extra Italian economy/business coverage
        "https://www.repubblica.it/rss/economia/rss2.0.xml",
        "https://www.milanofinanza.it/rss/ultimora",
        "https://www.ansa.it/sito/ansait_rss.xml",
        "https://www.borsaitaliana.it/borsa/notizie/listeati.rss",
        "https://www.ilfoglio.it/rss/economia.xml"
    ],
    "Energia e Commodities": [
        "https://www.mining.com/feed/",
        "https://oilprice.com/rss/main",
        "https://feeds.reuters.com/reuters/commoditiesNews",
        # Extra energy/commodities coverage
        "https://www.platts.com/rssfeed",
        "https://www.spglobal.com/commodityinsights/en/rss",
        "https://www.ft.com/commodities?format=rss",
        "https://www.bloomberg.com/feed/podcast/commodities-edge",
        "https://www.wsj.com/xml/rss/3_7014.xml"  # WSJ Commodities/Energy
    ],
}

# === NEWS SENTIMENT KEYWORDS ===
SENTIMENT_KEYWORDS_CONFIG = {
    "critical_keywords": [
        # Finanza e Banche Centrali (peso alto)
        "crisis", "inflation", "deflation", "recession", "fed", "ecb", "boe", "boj",
        "interest rate", "rates", "monetary policy", "quantitative easing", "tapering",
        "bank", "banking", "credit", "default", "bankruptcy", "bailout", "stimulus",
        
        # Mercati e Trading (peso alto)
        "crash", "collapse", "plunge", "surge", "volatility", "bubble", "correction",
        "bear market", "bull market", "rally", "selloff", "margin call",
        
        # Geopolitica e Conflitti (peso critico)
        "war", "conflict", "sanctions", "trade war", "tariff", "embargo", "invasion",
        "military", "nuclear", "terrorist", "coup", "revolution", "protest",
        
        # Criptovalute (peso medio-alto)
        "hack", "hacked", "exploit", "rug pull", "defi", "smart contract", "fork",
        "regulation", "ban", "etf", "mining", "staking", "liquidation",
        
        # Economia Generale (peso medio)
        "gdp", "unemployment", "job", "employment", "cpi", "ppi", "retail sales",
        "housing", "oil price", "energy crisis", "supply chain", "shortage",
        
        # Termini di Urgenza (peso critico)
        "alert", "emergency", "urgent", "breaking", "exclusive", "scandal",
        "investigation", "fraud", "manipulation", "insider trading",
        
        # AI & Tech 2025 terms
        "ai breakthrough", "artificial intelligence", "quantum computing",
        "nvidia earnings", "chip demand", "tech innovation"
    ],
    "positive_keywords": [
        "surge", "rally", "bullish", "growth", "success", "recovery", "expansion",
        "breakthrough", "record high", "approval", "deal", "agreement", "cooperation"
    ],
    "negative_keywords": [
        "crash", "recession", "crisis", "bankruptcy", "war", "sanctions", "hack",
        "bearish", "sell-off", "correction", "volatility spike", "default", "conflict"
    ]
}

# === CONTENT SCHEDULE CONFIGURATION ===
CONTENT_SCHEDULE_CONFIG = {
    # 3-hour cycle (Italy time)
    "night": "00:00",             # Night (after-hours / crypto)
    "late_night": "03:00",        # Late Night (Asia session check)
    "press_review": "06:00",      # Press Review (7 sections)
    "morning": "09:00",          # Morning Report (3 messages)
    "noon": "12:00",             # Noon Update (3 messages)
    "afternoon": "15:00",        # Afternoon Update (3 messages)
    "evening": "18:00",          # Evening Analysis (3 messages)
    "summary": "21:00",          # Daily Summary (6 pages)

    # Periodic reports
    "weekly": "09:05",            # Weekly Report (Monday only)
    "monthly": "09:10",           # Monthly Report (typically last day of month)
    "quarterly": "09:15",         # Quarterly Report (1st day of quarter)
    "semestral": "09:20",         # Semestral Report (1st day of semester)
}

# === MARKET HOURS CONFIGURATION ===
MARKET_HOURS_CONFIG = {
    "europe": {"open": 9, "close": 17.5},  # 9:00-17:30 CET
    "us_premarket": {"open": 10, "close": 15.5},  # 10:00-15:30 CET
    "us_regular": {"open": 15.5, "close": 22},  # 15:30-22:00 CET
    "asia": {"open": 2, "close": 9}  # 02:00-09:00 CET
}

# === CONTENT TEMPLATE CONFIGURATION ===
CONTENT_TEMPLATES_CONFIG = {
    'press_review': {
        'sections': 7,
        'emojis': ['ðŸ“°', 'ðŸŒ', 'ðŸ’°', 'ðŸ“Š', 'ðŸ¦', 'âš¡', 'ðŸŽ¯'],
        'titles': [
            'BREAKING NEWS GLOBALI',
            'MERCATI FINANZIARI',
            'CRYPTO & DIGITAL ASSETS', 
            'TECHNICAL ANALYSIS',
            'BANCHE CENTRALI',
            'MOMENTUM SETTORIALI',
            'DAILY OUTLOOK'
        ]
    },
    'morning': {
        'messages': 3,
        'focus': ['Daily setup', 'ML Predictions', 'Risk Assessment']
    },
    'noon': {
        'messages': 3,
        'focus': ['Progress check', 'Intraday update', 'Prediction verification']
    },
    'evening': {
        'messages': 3,
        'focus': ['Session wrap', 'Performance review', 'Tomorrow setup']
    },
    'summary': {
        'pages': 6,
        'sections': ['Executive Summary', 'Performance Analysis', 'ML Results', 'Market Review', 'Tomorrow Outlook', 'Daily Journal & Notes']
    }
}

# === NEWS LIMITS CONFIGURATION ===
NEWS_LIMITS_CONFIG = {
    "press_review": 8,
    "morning": 5,
    "noon": 4,
    "evening": 6,
    "summary": 10,
    "weekly": 12,
    "monthly": 15
}

# === TELEGRAM CONFIGURATION ===
TELEGRAM_CONFIG = {
    'max_message_length': 4096,  # Limite Telegram
    'retry_attempts': 3,
    'retry_delay': 5,  # secondi
    'enable_preview': False,  # Disabilita preview link per default
    'parse_mode': 'Markdown',  # Supporta formatting
    'timeout': 10  # timeout richieste
}

# === CONTENT EMOJI CONFIGURATION ===
CONTENT_EMOJIS_CONFIG = {
    'press_review': 'ðŸ“°',
    'morning': 'ðŸŒ…', 
    'noon': 'ðŸŒž',
    'evening': 'ðŸŒ†',
    'summary': 'ðŸ“Š',
    'weekly': 'ðŸ“ˆ',
    'monthly': 'ðŸ“‹',
    'error': 'âŒ',
    'success': 'âœ…',
    'warning': 'âš ï¸'
}

# === CONFIGURATION LOADER ===
def load_custom_config(config_name: str) -> Optional[Dict]:
    """Load custom configuration from JSON file"""
    try:
        config_path = get_config_file_path(f"{config_name}.json")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"âš ï¸ [CONFIG] Error loading {config_name}: {e}")
    return None

def get_rss_feeds() -> Dict[str, List[str]]:
    """Get RSS feeds configuration with custom override"""
    custom_feeds = load_custom_config('rss_feeds')
    return custom_feeds if custom_feeds else RSS_FEEDS_CONFIG

def get_sentiment_keywords() -> Dict[str, List[str]]:
    """Get sentiment keywords with custom override"""
    custom_keywords = load_custom_config('sentiment_keywords')
    return custom_keywords if custom_keywords else SENTIMENT_KEYWORDS_CONFIG

def get_content_schedule() -> Dict[str, str]:
    """Get content schedule with custom override"""
    custom_schedule = load_custom_config('content_schedule')
    return custom_schedule if custom_schedule else CONTENT_SCHEDULE_CONFIG

def get_news_limits() -> Dict[str, int]:
    """Get news limits with custom override"""
    custom_limits = load_custom_config('news_limits')
    return custom_limits if custom_limits else NEWS_LIMITS_CONFIG

def get_telegram_config() -> Dict:
    """Get Telegram configuration"""
    custom_telegram = load_custom_config('telegram_config')
    return custom_telegram if custom_telegram else TELEGRAM_CONFIG

# === PRIVATE CONFIGURATION ===
def load_private_config(config_file: str = 'private.txt') -> Dict[str, str]:
    """Load private configuration from text file"""
    config = {}
    project_root = get_project_root()
    config_path = os.path.join(project_root, config_file)
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
    except Exception as e:
        print(f"âš ï¸ [PRIVATE-CONFIG] Error loading private config: {e}")
    
    return config

def get_telegram_credentials() -> Dict[str, str]:
    """Get Telegram credentials from private config or environment"""
    private_config = load_private_config()
    
    return {
        'bot_token': (
            private_config.get('TELEGRAM_BOT_TOKEN') or 
            os.environ.get('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
        ),
        'chat_id': (
            private_config.get('TELEGRAM_CHAT_ID') or 
            os.environ.get('TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID_HERE')
        )
    }

# === CONFIGURATION VALIDATION ===
def validate_config():
    """Validate all configurations"""
    print("ðŸ§ª [CONFIG] Validating SV configurations...")
    
    # Test RSS feeds
    rss_feeds = get_rss_feeds()
    total_feeds = sum(len(feeds) for feeds in rss_feeds.values())
    print(f"âœ… [CONFIG] RSS Feeds: {len(rss_feeds)} categories, {total_feeds} total feeds")
    
    # Test sentiment keywords
    sentiment = get_sentiment_keywords()
    critical_count = len(sentiment.get('critical_keywords', []))
    print(f"âœ… [CONFIG] Sentiment Keywords: {critical_count} critical keywords")
    
    # Test schedule
    schedule = get_content_schedule()
    print(f"âœ… [CONFIG] Content Schedule: {len(schedule)} content types")
    
    # Test Telegram config
    telegram_creds = get_telegram_credentials()
    has_real_token = 'YOUR_BOT_TOKEN_HERE' not in telegram_creds['bot_token']
    print(f"âœ… [CONFIG] Telegram: {'Configured' if has_real_token else 'Placeholder tokens'}")
    
    print("âœ… [CONFIG] Configuration validation complete")

if __name__ == '__main__':
    validate_config()

