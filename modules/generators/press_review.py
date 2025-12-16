# Intraday generator for the Press Review block.
#
# Extracted from DailyContentGenerator.generate_press_review in modules.daily_generator.

from typing import Any, Dict, List
import json

from modules import daily_generator as dg

EMOJI = dg.EMOJI
log = dg.log
_now_it = dg._now_it
project_root = dg.project_root
SV_ENHANCED_ENABLED = getattr(dg, "SV_ENHANCED_ENABLED", False)

get_enhanced_news = dg.get_enhanced_news
get_fallback_data = dg.get_fallback_data
get_live_crypto_prices = dg.get_live_crypto_prices
calculate_crypto_support_resistance = dg.calculate_crypto_support_resistance
format_crypto_price_line = dg.format_crypto_price_line


def _generate_press_review(self) -> List[str]:
    """
    PRESS REVIEW 06:00 - ENHANCED from 555a with 7 messages
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



def generate_press_review(ctx) -> List[str]:
    """Public entrypoint used by DailyContentGenerator to generate Press Review."""
    return _generate_press_review(ctx)
