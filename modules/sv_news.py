#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - News System Module
News system per Content Creation Engine
Estratto dalle migliori funzionalitÃ  di 555.py e 555a_server.py
"""

import datetime
from datetime import timezone, timedelta
import feedparser
import requests
import pytz
import logging
import os
import json

# Optional config import for RSS feeds
try:
    from config.sv_config import get_rss_feeds as get_config_rss_feeds
except Exception:
    get_config_rss_feeds = None

# Setup logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

ITALY_TZ = pytz.timezone("Europe/Rome")

def _now_it():
    """Get current time in Italian timezone"""
    return datetime.datetime.now(ITALY_TZ)

class SVNewsSystem:
    """
    Sistema news per SV Content Creation Engine
    """
    
    def __init__(self):
        """Initialize SV News System"""
        self.setup_rss_feeds()
        self.setup_news_cache()
        
    def setup_rss_feeds(self):
        """Setup RSS feeds.
        - Start from robust defaults
        - Merge in config-defined feeds (config/sv_config.py) with category aliasing
        - Deduplicate while preserving order
        """
        # 1) Defaults (kept to ensure baseline coverage even without config)
        default_feeds = {
            "Finance": [
                "https://feeds.reuters.com/reuters/businessNews",
                "https://www.investing.com/rss/news_285.rss",
                "https://www.marketwatch.com/rss/topstories",
                "https://feeds.finance.yahoo.com/rss/2.0/headline",
                "https://feeds.bloomberg.com/markets/news.rss",
                "https://rss.cnn.com/rss/money_latest.rss",
                "https://seekingalpha.com/market_currents.xml",
                "https://feeds.ft.com/rss/home",
                "https://www.nasdaq.com/rss",
                "https://feeds.wsj.com/wsj/xml/rss/3_7455.xml",
                "https://feeds.feedburner.com/fool/AllFool",
                "https://feeds.benzinga.com/benzinga"
            ],
            "Cryptocurrency": [
                "https://www.coindesk.com/arc/outboundfeeds/rss/",
                "https://cointelegraph.com/rss",
                "https://cryptoslate.com/feed/",
                "https://bitcoinist.com/feed/",
                "https://cryptopotato.com/feed/",
                "https://decrypt.co/feed",
                "https://www.cryptonews.com/news/feed/",
                "https://ambcrypto.com/feed/",
                "https://blockworks.co/rss.xml",
                "https://www.coinbureau.com/feed/",
                "https://thedefiant.io/api/rss",
                "https://cryptobriefing.com/feed/"
            ],
            "Geopolitics": [
                "https://feeds.reuters.com/Reuters/worldNews",
                "https://www.aljazeera.com/xml/rss/all.xml",
                "http://feeds.bbci.co.uk/news/world/rss.xml",
                "http://rss.nytimes.com/services/xml/rss/nyt/World.xml",
                "https://feeds.bbci.co.uk/news/rss.xml",
                "https://rss.cnn.com/rss/edition.rss",
                "https://feeds.npr.org/1001/rss.xml",
                "https://feeds.washingtonpost.com/rss/world",
                "https://www.reuters.com/rssFeed/worldNews",
                "https://feeds.theguardian.com/theguardian/world/rss"
            ],
            "Technology": [
                # Core tech/innovation feeds (very high quality, widely cited)
                "https://www.technologyreview.com/feed/",  # MIT Technology Review – deep tech & AI
                "https://feeds.feedburner.com/techcrunch/",
                "https://feeds.arstechnica.com/arstechnica/index",
                "https://www.wired.com/feed/rss",
                "https://feeds.mashable.com/Mashable",
                "https://feeds.feedburner.com/venturebeat/SZYF",
                "https://www.theverge.com/rss/index.xml",
                "https://feeds.feedburner.com/GizmodoRSS",
                "https://feeds.engadget.com/rss.xml",
                "https://feeds.feedburner.com/oreilly/radar",
                "https://hbr.org/feed"
            ],
            "Economia Italia": [
                "https://www.ilsole24ore.com/rss/news.xml",
                "https://feeds.reuters.com/reuters/ITtopNews",
                "https://www.corriere.it/rss/economia.xml",
                "https://www.repubblica.it/rss/economia/rss2.0.xml",
                "https://www.ansa.it/web/news/rubriche/economia/economia_rss.xml"
            ],
            "Energia e Commodities": [
                "https://www.mining.com/feed/",
                "https://oilprice.com/rss/main",
                "https://feeds.reuters.com/reuters/commoditiesNews",
                "https://www.energyworld.com/rss.xml",
                "https://feeds.feedburner.com/platts/metals",
                "https://www.kitco.com/rss/KitcoNews.xml"
            ]
        }
        # Start with defaults
        self.RSS_FEEDS = {k: v[:] for k, v in default_feeds.items()}

        # 2) Merge config-defined feeds (if available)
        try:
            config_feeds = get_config_rss_feeds() if get_config_rss_feeds else None
        except Exception as e:
            log.warning(f"[SV-NEWS] Could not load config RSS feeds: {e}")
            config_feeds = None

        if isinstance(config_feeds, dict) and config_feeds:
            # Map config categories (Italian) to internal categories
            category_aliases = {
                'Finanza': 'Finance',
                'Criptovalute': 'Cryptocurrency',
                'Geopolitica': 'Geopolitics',
                'Economia Italia': 'Economia Italia',
                'Energia e Commodities': 'Energia e Commodities',
                'Tecnologia': 'Technology',
                'Technology': 'Technology'
            }
            for cfg_cat, urls in config_feeds.items():
                target_cat = category_aliases.get(cfg_cat, cfg_cat)
                self.RSS_FEEDS.setdefault(target_cat, [])
                for url in urls or []:
                    if url and url not in self.RSS_FEEDS[target_cat]:
                        self.RSS_FEEDS[target_cat].append(url)

        # Log summary
        total_feeds = sum(len(v) for v in self.RSS_FEEDS.values())
        log.info(f"[SV-NEWS] RSS setup: {len(self.RSS_FEEDS)} categories, {total_feeds} feeds")
        
    def setup_news_cache(self):
        """Setup news caching system - now correctly in data/news_cache"""
        # From modules/ directory, go up to project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.cache_dir = os.path.join(project_root, 'data', 'news_cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # NOTE: attualmente non usato dal flusso intraday; previsto per futuri
        # meccanismi di tracking/cache (rate limiting, deduplicazione, ecc.).
        self.news_tracking_file = os.path.join(self.cache_dir, 'news_tracking.json')
        
    def is_highlighted_news(self, title):
        """
        Determine se una notizia Ã¨ critica/important
        Algoritmo combinato da 555.py e 555a_server.py
        """
        critical_keywords = [
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
            
            # Economia Generatele (peso medio)
            "gdp", "unemployment", "job", "employment", "cpi", "ppi", "retail sales",
            "housing", "oil price", "energy crisis", "supply chain", "shortage",
            
            # Termini di Urgenza (peso critico)
            "alert", "emergency", "urgent", "breaking", "exclusive", "scandal",
            "investigation", "fraud", "manipulation", "insider trading",
            
            # AI & Tech 2025 terms (nuovo da 555a_server.py)
            "ai breakthrough", "artificial intelligence", "quantum computing",
            "nvidia earnings", "chip demand", "tech innovation"
        ]
        
        return any(keyword.lower() in title.lower() for keyword in critical_keywords)
    
    def is_recent_news(self, entry, hours_threshold=24):
        """
        Verifica se la notizia Ã¨ recente (latest N ore)
        Algoritmo migliorato da 555.py
        """
        try:
            now_utc = datetime.datetime.now(timezone.utc)
            threshold = now_utc - timedelta(hours=hours_threshold)
            
            # Prova published_parsed prima
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                news_time = datetime.datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                return news_time >= threshold
            
            # Fallback su updated_parsed
            if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                news_time = datetime.datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                return news_time >= threshold
            
            # Prova a parsare published come stringa
            if entry.get('published'):
                try:
                    from email.utils import parsedate_to_datetime
                    news_time = parsedate_to_datetime(entry.published)
                    if news_time.tzinfo is None:
                        news_time = news_time.replace(tzinfo=timezone.utc)
                    return news_time >= threshold
                except:
                    pass
            
            # Se non riusciamo a Determinere la data, assumiamo che sia recente
            return True
            
        except Exception as e:
            log.warning(f"Errore parsing data notizia: {e}")
            return True  # In caso di errore, includiamo la notizia
    
    def get_critical_news(self, max_news=8, hours_threshold=24):
        """
        Retrieve news critical dalle latest N ore
        Algoritmo ottimizzato combinando 555.py e 555a_server.py
        """
        critical_news = []
        now_it = _now_it()
        
        log.info(f"[NEWS] [SV-NEWS] Retrieving critical news latest {hours_threshold}h")
        
        # Algoritmo dinamico per orario (da 555a_server.py) - ENHANCED
        if now_it.hour < 10:  # Mattina: massima copertura
            feeds_per_category = 6
            entries_per_feed = 12
        elif now_it.hour < 16:  # Pomeriggio: buona copertura
            feeds_per_category = 5
            entries_per_feed = 10
        else:  # Sera: copertura essenziale
            feeds_per_category = 4
            entries_per_feed = 8
        
        # PrioritÃ  categorie dinamica per orario
        if now_it.hour < 12:  # Mattina: Asia + Crypto + Finanza
            category_priority = ["Finance", "Cryptocurrency", "Geopolitics", "Technology", "Economia Italia", "Energia e Commodities"]
        else:  # Pomeriggio/Sera: Europa + USA + Italia
            category_priority = ["Finance", "Technology", "Economia Italia", "Geopolitics", "Cryptocurrency", "Energia e Commodities"]
        
        for category in category_priority:
            if category in self.RSS_FEEDS and len(critical_news) < max_news:
                feed_urls = self.RSS_FEEDS[category]
                
                log.info(f"[SCAN] [SV-NEWS] Processing {category}: {len(feed_urls)} feeds available")
                
                for url in feed_urls[:feeds_per_category]:
                    if len(critical_news) >= max_news:
                        break
                        
                    try:
                        parsed = feedparser.parse(url)
                        if parsed.bozo or not parsed.entries:
                            continue
                        
                        source_name = parsed.feed.get("title", url.split('/')[2] if '/' in url else "Unknown")
                        
                        news_found_this_feed = 0
                        for entry in parsed.entries[:entries_per_feed]:
                            if len(critical_news) >= max_news:
                                break
                                
                            title = entry.get("title", "")
                            
                            if self.is_recent_news(entry, hours_threshold) and self.is_highlighted_news(title):
                                link = entry.get("link", "")
                                
                                news_item = {
                                    "titolo": title,
                                    "link": link,
                                    "source": source_name,
                                    "category": category,
                                    "timestamp": now_it.strftime("%H:%M:%S"),
                                    "date": now_it.strftime("%Y-%m-%d")
                                }
                                
                                critical_news.append(news_item)
                                news_found_this_feed += 1
                        
                        if news_found_this_feed > 0:
                            log.info(f"  [NEWS] {news_found_this_feed} relevant news from {source_name}")
                                
                    except Exception as e:
                        log.warning(f"Errore feed {url}: {e}")
                        continue
        
        # Ordinamento per rilevanza temporale
        critical_news.sort(key=lambda x: x.get('timestamp', '00:00'), reverse=True)
        
        result_count = len(critical_news)
        log.info(f"[OK] [SV-NEWS] Found {result_count} critical news")
        
        return critical_news[:max_news]
    
    def analyze_news_sentiment(self, news_list):
        """
        Analyze sentiment delle news
        Algoritmo base da 555a_server.py
        """
        if not news_list:
            return {
                "sentiment": "NEUTRAL",
                "market_impact": "LOW",
                "summary": "Nessuna notizia critica disponibile"
            }
        
        # Keywords per sentiment analysis
        positive_keywords = [
            "surge", "rally", "bullish", "growth", "success", "recovery", "expansion",
            "breakthrough", "record high", "approval", "deal", "agreement", "cooperation"
        ]
        
        negative_keywords = [
            "crash", "recession", "crisis", "bankruptcy", "war", "sanctions", "hack",
            "bearish", "sell-off", "correction", "volatility spike", "default", "conflict"
        ]
        
        positive_score = 0
        negative_score = 0
        
        for news in news_list:
            title_lower = news["titolo"].lower()
            
            # Conta keywords positive
            for keyword in positive_keywords:
                if keyword in title_lower:
                    positive_score += 1
            
            # Conta keywords negative
            for keyword in negative_keywords:
                if keyword in title_lower:
                    negative_score += 1
        
        # Determine sentiment
        if positive_score > negative_score:
            sentiment = "POSITIVE"
        elif negative_score > positive_score:
            sentiment = "NEGATIVE"
        else:
            sentiment = "NEUTRAL"
        
        # Determine impatto
        total_score = positive_score + negative_score
        if total_score >= 5:
            market_impact = "HIGH"
        elif total_score >= 2:
            market_impact = "MEDIUM"
        else:
            market_impact = "LOW"
        
        return {
            "sentiment": sentiment,
            "market_impact": market_impact,
            "positive_score": positive_score,
            "negative_score": negative_score,
            "total_news": len(news_list),
            "summary": f"sentiment {sentiment} con impatto {market_impact}"
        }
    
    def get_morning_news_summary(self, max_news=6):
        """
        Generate summary news per morning report
        """
        news = self.get_critical_news(max_news=max_news)
        sentiment = self.analyze_news_sentiment(news)
        
        return {
            "news": news,
            "sentiment": sentiment,
            "timestamp": _now_it().isoformat()
        }
    
    def get_news_for_content(self, content_type="daily", max_news=None):
        """
        Get news specifiche per tipo di contenuto
        """
        if max_news is None:
            max_news = {
                "rassegna": 8,
                "morning": 5,
                "noon": 4,
                "evening": 6,
                "summary": 10,
                "weekly": 12,
                "monthly": 15
            }.get(content_type, 6)
        
        return self.get_critical_news(max_news=max_news)
    
    def get_all_news(self, max_news=150):
        """
        Get tutte le news da tutte le categorie per dashboard
        """
        all_news = []
        
        try:
            for category_name, rss_feeds in self.RSS_FEEDS.items():
                for rss_url in rss_feeds[:4]:  # Max 4 feeds per category per piÃ¹ news
                    try:
                        parsed = feedparser.parse(rss_url)
                        if hasattr(parsed, 'entries') and parsed.entries:
                            for entry in parsed.entries[:8]:  # Max 8 news per feed
                                title = entry.get('title', '').strip()
                                if title and len(title) > 20:  # Filter short titles
                                    # Check if news is critical/important
                                    is_critical = self.is_highlighted_news(title)
                                    
                                    news_item = {
                                        'titolo': title,
                                        'category': category_name,
                                        'source': parsed.feed.get('title', 'Unknown'),
                                        'data': entry.get('published', _now_it().strftime('%Y-%m-%d %H:%M')),
                                        'link': entry.get('link', ''),
                                        'critica': is_critical  # Flag per news critical
                                    }
                                    all_news.append(news_item)
                                    
                                    if len(all_news) >= max_news:
                                        return all_news[:max_news]
                    except Exception as e:
                        log.error(f"Error fetching from {rss_url}: {e}")
                        continue
            
            return all_news
            
        except Exception as e:
            log.error(f"Error in get_all_news: {e}")
            return []

# Singleton instance
sv_news_system = None

def get_sv_news_system() -> SVNewsSystem:
    """Get singleton instance of SV News System"""
    global sv_news_system
    if sv_news_system is None:
        sv_news_system = SVNewsSystem()
    return sv_news_system

# Helper functions for easy access
def get_critical_news(max_news=8):
    """Get critical news - quick access"""
    return get_sv_news_system().get_critical_news(max_news=max_news)

def get_news_for_content(content_type="daily", max_news=None):
    """
    Get news for specific content type - normalizza formato per daily_Generatetor
    """
    news_system = get_sv_news_system()
    raw_news = news_system.get_news_for_content(content_type=content_type, max_news=max_news)
    sentiment = news_system.analyze_news_sentiment(raw_news)
    
    # Normalizza formato per compatibilitÃ  con daily_Generatetor
    normalized_news = []
    for news_item in raw_news:
        normalized_item = {
            'title': news_item.get('titolo', 'News update'),  # titolo -> title
            'source': news_item.get('source', 'News Source'),  # source -> source
            'link': news_item.get('link', ''),
            'category': news_item.get('category', 'Generatel'),
            'timestamp': news_item.get('timestamp', ''),
            'date': news_item.get('date', '')
        }
        normalized_news.append(normalized_item)
    
    return {
        'news': normalized_news,
        'sentiment': sentiment,
        'has_real_news': len(normalized_news) > 0
    }

def get_morning_news_summary():
    """Get morning news summary"""
    return get_sv_news_system().get_morning_news_summary()

# Test function
def test_sv_news():
    """Test SV News System"""
    print("ðŸ§ª [TEST] Testing SV News System...")
    
    try:
        news_system = get_sv_news_system()
        
        # Test critical news
        news = news_system.get_critical_news(max_news=3)
        print(f"âœ… [TEST] Retrieved {len(news)} critical news")
        
        if news:
            print(f"âœ… [TEST] First news: {news[0]['titolo'][:50]}...")
            
            # Test sentiment analysis
            sentiment = news_system.analyze_news_sentiment(news)
            print(f"âœ… [TEST] sentiment: {sentiment['sentiment']} (Impact: {sentiment['market_impact']})")
        
        print("âœ… [TEST] SV News System working correctly")
        return True
        
    except Exception as e:
        print(f"âŒ [TEST] News system error: {e}")
        return False

if __name__ == '__main__':
    test_sv_news()




