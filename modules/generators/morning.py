# Intraday generator for the Morning block.
#
# Extracted from DailyContentGenerator.generate_morning_report in modules.daily_generator.

from typing import Any, Dict, List
import datetime

from modules import daily_generator as dg

EMOJI = dg.EMOJI
log = dg.log
_now_it = dg._now_it
get_enhanced_news = dg.get_enhanced_news
get_fallback_data = dg.get_fallback_data
get_live_crypto_prices = dg.get_live_crypto_prices
get_live_equity_fx_quotes = dg.get_live_equity_fx_quotes
calculate_crypto_support_resistance = dg.calculate_crypto_support_resistance
GOLD_GRAMS_PER_TROY_OUNCE = dg.GOLD_GRAMS_PER_TROY_OUNCE

# Optional dependency flags (mirrors modules.daily_generator)
DEPENDENCIES_AVAILABLE = getattr(dg, "DEPENDENCIES_AVAILABLE", False)
PERIOD_AGGREGATOR_AVAILABLE = getattr(dg, "PERIOD_AGGREGATOR_AVAILABLE", False)
COHERENCE_MANAGER_AVAILABLE = getattr(dg, "COHERENCE_MANAGER_AVAILABLE", False)
REGIME_MANAGER_AVAILABLE = getattr(dg, "REGIME_MANAGER_AVAILABLE", False)
PORTFOLIO_MANAGER_AVAILABLE = getattr(dg, "PORTFOLIO_MANAGER_AVAILABLE", False)

get_portfolio_manager = getattr(dg, "get_portfolio_manager", None)
get_daily_regime_manager = getattr(dg, "get_daily_regime_manager", None)
coherence_manager = getattr(dg, "coherence_manager", None)
period_aggregator = getattr(dg, "period_aggregator", None)

def generate_morning_report(ctx) -> List[str]:
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
                    
                    msg1_parts.append(f"{EMOJI['bullet']} {rassegna_connection.get('rassegna_followup', f'{EMOJI["news"]} Press review sync in progress')}")
                    msg1_parts.append(f"{EMOJI['bullet']} {rassegna_connection.get('sector_continuation', f'{EMOJI["target"]} Multi-sector momentum tracking')}")
                    msg1_parts.append(f"{EMOJI['bullet']} {rassegna_connection.get('risk_update', f'{EMOJI["shield"]} Risk theme: Balanced - ML confirmation')}")
                    
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
                
                # Try to get SPX and Gold for live price/ratio snapshot.
                # NOTE: questo è uno dei pochi casi "special feed" dove usiamo ancora
                # get_live_equity_fx_quotes direttamente, perché ci serve il prezzo
                # raw per costruire il Gold/SPX ratio macro; tutti gli snapshot
                # standard SPX/EURUSD/GOLD passano da engine.market_data.get_market_snapshot.
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
                            if not ctx._was_news_used(item, now):
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
                        impact = ctx._analyze_news_impact_detailed(title, published_ago_hours=hours_ago)
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
                            ctx._mark_news_used(item, now)
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
                    msg1_parts.append(f"{EMOJI['bullet']} *Momentum Score*: {momentum:.1f}/10 - {f'{EMOJI["fire"]} Strong' if momentum > 6 else f'{EMOJI["lightning"]} Moderate' if momentum > 3 else f'{EMOJI["blue_circle"]} Weak'}")
                    
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
                recent_perf = ctx._load_recent_prediction_performance(now)
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
                        msg2_parts.append(f"{EMOJI['bullet']} *Preferred Assets*: Gold (XAUUSD), Bonds (TLT), USD, Utilities")
                        msg2_parts.append(f"{EMOJI['bullet']} *Strategy*: Safe haven accumulation, capital preservation")
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
                    # SPX / EURUSD solo se quote live presenti.
                    # NOTE: uso intenzionale del feed diretto per calcolare livelli
                    # di trading (supporti/resistenze intraday) e costruire le
                    # previsioni/predictions del giorno; gli snapshot descrittivi
                    # usano già engine.market_data.get_market_snapshot.
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
                    
                    # Gold signals (feed diretto solo per costruire livelli operativi).
                    try:
                        gold_quotes = get_live_equity_fx_quotes(['XAUUSD=X']) or {}
                        gold_price = gold_quotes.get('XAUUSD=X', {}).get('price', 0)
                        if gold_price:
                            gold_target = gold_price * 1.015
                            msg2_parts.append(f"{EMOJI['bullet']} *GOLD*: LONG accumulation above ${gold_price:,.2f} | Target ~${gold_target:,.2f}")
                            msg2_parts.append(f"  Safe haven strategy: Dollar hedge + inflation protection")
                        else:
                            msg2_parts.append(f"{EMOJI['bullet']} *GOLD*: LONG accumulation strategy - safe haven positioning (live levels monitored)")
                    except Exception as gold_err:
                        log.warning(f"{EMOJI['warn']} [MORNING-SIGNALS-GOLD] Gold quotes unavailable: {gold_err}")
                        msg2_parts.append(f"{EMOJI['bullet']} *GOLD*: LONG accumulation strategy - safe haven positioning (live levels monitored)")

                        # Save real-data-based predictions for intraday verification (BTC core, SPX/EUR optional)
                    try:
                        from pathlib import Path
                        import json

                        pred_dir = Path(ctx.reports_dir).parent / '1_daily'
                        pred_dir.mkdir(parents=True, exist_ok=True)
                        predictions = []
                        
                        # Initialize portfolio manager for automatic position opening
                        portfolio_manager = None
                        if PORTFOLIO_MANAGER_AVAILABLE:
                            try:
                                portfolio_manager = get_portfolio_manager()
                                log.info(f"{EMOJI['dollar']} [PORTFOLIO] Portfolio manager initialized for signal tracking")
                            except Exception as pm_error:
                                log.warning(f"{EMOJI['warning']} [PORTFOLIO] Error initializing portfolio manager: {pm_error}")

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
                            btc_prediction = {
                                'asset': 'BTC',
                                'direction': 'LONG',
                                'entry': round(entry_btc, 2),
                                'target': round(target_btc, 2),
                                'stop': round(stop_btc, 2),
                                'confidence': btc_conf,
                            }
                            predictions.append(btc_prediction)
                            
                            # Open portfolio position automatically
                            if portfolio_manager:
                                try:
                                    position_id = portfolio_manager.open_position(btc_prediction, btc_price)
                                    if position_id:
                                        log.info(f"{EMOJI['dollar']} [PORTFOLIO] Opened BTC position: {position_id} (${btc_price:,.2f})")
                                    else:
                                        log.info(f"{EMOJI['info']} [PORTFOLIO] BTC position not opened (insufficient size/balance)")
                                except Exception as pos_error:
                                    log.warning(f"{EMOJI['warning']} [PORTFOLIO] Error opening BTC position: {pos_error}")

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
                            spx_prediction = {
                                'asset': 'SPX',
                                'direction': 'LONG',
                                'entry': round(entry_spx, 2),
                                'target': round(target_spx, 2),
                                'stop': round(stop_spx, 2),
                                'confidence': spx_conf,
                            }
                            predictions.append(spx_prediction)
                            
                            # Open portfolio position automatically
                            if portfolio_manager:
                                try:
                                    position_id = portfolio_manager.open_position(spx_prediction, spx_price)
                                    if position_id:
                                        log.info(f"{EMOJI['dollar']} [PORTFOLIO] Opened SPX position: {position_id} (${spx_price:,.2f})")
                                    else:
                                        log.info(f"{EMOJI['info']} [PORTFOLIO] SPX position not opened (insufficient size/balance)")
                                except Exception as pos_error:
                                    log.warning(f"{EMOJI['warning']} [PORTFOLIO] Error opening SPX position: {pos_error}")

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
                            eur_prediction = {
                                'asset': 'EURUSD',
                                'direction': 'SHORT',
                                'entry': round(entry_eur, 5),
                                'target': round(target_eur, 5),
                                'stop': round(stop_eur, 5),
                                'confidence': eur_conf,
                            }
                            predictions.append(eur_prediction)
                            
                            # Open portfolio position automatically
                            if portfolio_manager:
                                try:
                                    position_id = portfolio_manager.open_position(eur_prediction, eur_price)
                                    if position_id:
                                        log.info(f"{EMOJI['dollar']} [PORTFOLIO] Opened EURUSD position: {position_id} ({eur_price:.5f})")
                                    else:
                                        log.info(f"{EMOJI['info']} [PORTFOLIO] EURUSD position not opened (insufficient size/balance)")
                                except Exception as pos_error:
                                    log.warning(f"{EMOJI['warning']} [PORTFOLIO] Error opening EURUSD position: {pos_error}")

                        # Gold prediction (LONG bias - safe haven accumulation).
                        # Anche qui usiamo il feed diretto solo per definire entry/target/stop;
                        # gli snapshot di mercato restano centralizzati in engine.market_data.
                        try:
                            gold_quotes = get_live_equity_fx_quotes(['XAUUSD=X']) or {}
                            gold_price = gold_quotes.get('XAUUSD=X', {}).get('price', 0)
                            if gold_price:
                                entry_gold = float(gold_price)
                                target_gold = float(entry_gold * 1.015)  # 1.5% target for gold
                                stop_gold = float(entry_gold * 0.992)   # 0.8% stop for gold (less volatile)
                                gold_conf = 65  # Conservative confidence for gold accumulation
                                
                                # Increase confidence in risk-off conditions
                                try:
                                    if 'sentiment_data' in locals() and isinstance(sentiment_data, dict):
                                        sent = sentiment_data.get('sentiment')
                                        if sent == 'NEGATIVE':
                                            gold_conf = 72  # Higher confidence in risk-off
                                except Exception:
                                    pass
                                    
                                gold_prediction = {
                                    'asset': 'GOLD',
                                    'direction': 'LONG',
                                    'entry': round(entry_gold, 2),
                                    'target': round(target_gold, 2),
                                    'stop': round(stop_gold, 2),
                                    'confidence': gold_conf,
                                }
                                predictions.append(gold_prediction)
                                
                                # Open portfolio position automatically
                                if portfolio_manager:
                                    try:
                                        position_id = portfolio_manager.open_position(gold_prediction, gold_price)
                                        if position_id:
                                            log.info(f"{EMOJI['dollar']} [PORTFOLIO] Opened GOLD position: {position_id} (${gold_price:,.2f})")
                                        else:
                                            log.info(f"{EMOJI['info']} [PORTFOLIO] GOLD position not opened (insufficient size/balance)")
                                    except Exception as pos_error:
                                        log.warning(f"{EMOJI['warning']} [PORTFOLIO] Error opening GOLD position: {pos_error}")
                            else:
                                log.info(f"{EMOJI['info']} [PORTFOLIO] Gold price unavailable - skipping GOLD prediction")
                        except Exception as gold_error:
                            log.warning(f"{EMOJI['warning']} [PORTFOLIO] Error with Gold prediction: {gold_error}")

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
                log.warning(f"{EMOJI['warn']} [MORNING-SIGNALS] Error: {e}")
                msg2_parts.append(f"{EMOJI['bullet']} **Signals**: Advanced generation system loading")
            
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
                from modules.engine.market_data import get_market_snapshot
                snapshot_levels = get_market_snapshot(now) or {}
                assets_levels = snapshot_levels.get('assets', {}) or {}
                spx_price_levels = assets_levels.get('SPX', {}).get('price', 0)
                eur_price_levels = assets_levels.get('EURUSD', {}).get('price', 0)
                if spx_price_levels:
                    spx_support_level = int(spx_price_levels * 0.995)   # ≈ -0.5%
                    spx_resistance_level = int(spx_price_levels * 1.006)  # ≈ +0.6%
                if eur_price_levels:
                    eur_support_level = eur_price_levels * 0.995
                    eur_resistance_level = eur_price_levels * 1.006
            except Exception as e:
                log.warning(f"{EMOJI['warn']} [MORNING-LEVELS-SPX-EUR] Market snapshot unavailable: {e}")
            
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
            saved_path = ctx.save_content("morning_report", messages, {
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
                try:
                    from modules.engine.market_data import get_market_snapshot
                    market_snapshot_morn = get_market_snapshot(now) or {}
                    assets_morn = market_snapshot_morn.get('assets', {}) or {}
                except Exception as md_e:
                    log.warning(f"{EMOJI['warning']} [ENGINE-MORNING] Error building market snapshot: {md_e}")
                # Morning di solito prima della verifica   prediction_eval vuoto
                ctx._engine_log_stage('morning', now, sentiment_morn, assets_morn, None)
            except Exception as e:
                log.warning(f"{EMOJI['warning']} [ENGINE-MORNING] Error logging engine stage: {e}")
        
        # Track morning focus in session tracker
        if ctx.session_tracker and DEPENDENCIES_AVAILABLE:
            try:
                focus_items = ['Tech sector momentum', 'BTC range trading', 'USD strength plays']
                morning_sentiment = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL')
                key_events = {'market_status': fallback_data.get('market_status', 'OPEN'), 'sentiment': morning_sentiment}
                ctx.session_tracker.set_morning_focus(focus_items, key_events, 'ENHANCED_TRACKING')
            except Exception as e:
                log.warning(f"Ã¢Å¡Â Ã¯Â¸Â [MORNING-TRACKER] Error: {e}")
        
        # Save sentiment for morning stage
        try:
            morning_sentiment = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL')
            ctx._save_sentiment_for_stage('morning', morning_sentiment, now)
        except Exception as e:
            log.warning(f"[SENTIMENT-TRACKING] Error in morning: {e}")
        
        log.info(f"Ã¢Å“â€¦ [MORNING] Completed generation of {len(messages)} ENHANCED morning report messages")
        return messages
        
    except Exception as e:
        log.error(f"Ã¢ÂÅ’ [MORNING] General error: {e}")
        # Emergency fallback
        return [f"Ã°Å¸Å’â€¦ **SV - MORNING REPORT**\nÃ°Å¸â€œâ€¦ {_now_it().strftime('%H:%M')} Ã¢â‚¬Â¢ System under maintenance"]
