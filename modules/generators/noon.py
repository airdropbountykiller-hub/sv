# Intraday generator for the Noon block.
#
# Extracted from DailyContentGenerator.generate_noon_update in modules.daily_generator.

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

def generate_noon_update(ctx) -> List[str]:
    """NOON UPDATE 12:00 - ENHANCED version with 3 messages
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
            
            # Enhanced continuity connection from morning report 09:00
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
                # Global personal finance + gadget/low-impact filter for Noon impact block
                news_list = [
                    it for it in news_list
                    if not ctx._is_personal_finance(it.get('title', ''))
                    and not ctx._is_low_impact_gadget_or_lifestyle(it.get('title', ''))
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
                        impact = ctx._analyze_news_impact_detailed(title, published_ago_hours=hours_ago)
                        try:
                            was_used = ctx._was_news_used(item, now)
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
                            ctx._mark_news_used(item, now)
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
                        from modules.engine.market_data import get_market_snapshot
                        snapshot_intraday = get_market_snapshot(now) or {}
                        assets_intraday = snapshot_intraday.get('assets', {}) or {}
                        spx_q_intraday = assets_intraday.get('SPX', {}) or {}
                        eur_q_intraday = assets_intraday.get('EURUSD', {}) or {}
                        gold_q_intraday = assets_intraday.get('GOLD', {}) or {}
                    except Exception as qe:
                        log.warning(f"{EMOJI['warn']} [NOON-PRICES-EQFX] Market snapshot unavailable: {qe}")
                        spx_q_intraday = {}
                        eur_q_intraday = {}
                        gold_q_intraday = {}
                    spx_price_intraday = spx_q_intraday.get('price', 0)
                    spx_chg_intraday = spx_q_intraday.get('change_pct', None)
                    eur_price_intraday = eur_q_intraday.get('price', 0)
                    eur_chg_intraday = eur_q_intraday.get('change_pct', None)
                    gold_per_gram_intraday = gold_q_intraday.get('price', 0)
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
                msg1_parts.append(f"{EMOJI['bullet']} Europe open: sector leadership and gap analysis versus the previous close")
                msg1_parts.append(f"{EMOJI['bullet']} ECB/central banks: officials' comments monitored for policy tone")
                msg1_parts.append(f"{EMOJI['bullet']} Midday data window: key economic releases shaping intraday bias")
                # Dopo la chiusura USA non ha senso parlare di "coming US cash open";
                # adattiamo il testo in base all'orario locale.
                if now.hour < 15 or (now.hour == 15 and now.minute < 30):
                    msg1_parts.append(f"{EMOJI['bullet']} Coming: US cash open and major data releases (Fed-sensitive)")
                else:
                    msg1_parts.append(f"{EMOJI['bullet']} US cash session: already in play or completed – focus shifts to after-hours flows and Asia handoff")
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
                    msg2_parts.append(f"{EMOJI['bullet']} {EMOJI['chart']} *ML Confidence*: {confidence*100:.0f}% - indicative directional score, not an exact probability of success (especially with limited live history)")
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
                # Real recent performance (fallback only, used when live eval is unavailable)
                recent_perf = ctx._load_recent_prediction_performance(now)
                recent_tracked = int(recent_perf.get('total_tracked', 0) or 0)
                recent_acc = float(recent_perf.get('accuracy_pct', 0.0) or 0.0)

                # Build sentiment payload: prefer full-day tracking, otherwise Noon sentiment
                try:
                    tracking = ctx._load_sentiment_tracking(now) or {}
                except Exception:
                    tracking = {}
                if isinstance(tracking, dict) and tracking:
                    sentiment_payload: Any = tracking
                else:
                    try:
                        noon_sentiment = (
                            (news_data.get('sentiment', {}) or {}).get('sentiment', 'NEUTRAL')
                            if isinstance(news_data, dict)
                            else 'NEUTRAL'
                        )
                    except Exception:
                        noon_sentiment = 'NEUTRAL'
                    sentiment_payload = {'noon': noon_sentiment}

                # Live prediction evaluation used when possible
                try:
                    eval_data = ctx._evaluate_predictions_with_live_data(now) or {}
                except Exception as eval_e:
                    log.warning(f"{EMOJI['warning']} [NOON-REGIME] Live accuracy eval error: {eval_e}")
                    eval_data = {}

                # If no live-tracked predictions, fall back to recent performance
                try:
                    live_total = int(eval_data.get('total_tracked', 0) or 0)
                except Exception:
                    live_total = 0
                if live_total <= 0 and (recent_tracked or recent_acc):
                    eval_data = dict(eval_data or {})
                    eval_data['total_tracked'] = recent_tracked
                    eval_data['accuracy_pct'] = recent_acc

                # Ask BRAIN layer for a compact regime summary
                from modules.brain.regime_detection import get_regime_summary
                regime_summary = get_regime_summary(eval_data, sentiment_payload)

                regime_state = regime_summary.get('regime_state', 'neutral')
                regime_label = regime_summary.get('regime_label', 'NEUTRAL')
                conf_pct = int(regime_summary.get('confidence_pct', 60) or 60)
                tone = str(regime_summary.get('tone', 'limited live history') or 'limited live history')
                acc_live = float(regime_summary.get('accuracy_pct', 0.0) or 0.0)
                tracked_live = int(regime_summary.get('total_tracked', 0) or 0)

                # Map regime_state to arrow emoji for Noon narrative
                if regime_state == 'risk_on':
                    arrow_emoji = EMOJI['rocket']
                elif regime_state == 'risk_off':
                    arrow_emoji = EMOJI['warning']
                else:
                    arrow_emoji = EMOJI['right_arrow']

                msg2_parts.append(
                    f"{EMOJI['bullet']} *Current Regime*: {regime_label} {arrow_emoji} ({conf_pct}% confidence, {tone})"
                )

                if tracked_live > 0:
                    # When the number of tracked predictions is very small, treat
                    # the accuracy figure as indicative only, not as a structural verdict.
                    if tracked_live <= 3:
                        msg2_parts.append(
                            f"{EMOJI['bullet']} *Recent accuracy (live)*: ~{acc_live:.0f}% on {tracked_live} fully closed predictions – very limited sample, interpret with caution"
                        )
                    else:
                        msg2_parts.append(
                            f"{EMOJI['bullet']} *Recent accuracy (live)*: ~{acc_live:.0f}% on {tracked_live} fully closed predictions"
                        )
                else:
                    msg2_parts.append(
                        f"{EMOJI['bullet']} *Recent accuracy (live)*: n/a (insufficient closed predictions to assess)"
                    )

                pos_text = regime_summary.get('position_sizing', 'Standard allocation approach')
                risk_text = regime_summary.get('risk_management', 'Balanced tactical allocation')
                msg2_parts.append(f"{EMOJI['bullet']} *Position Sizing*: {pos_text}")
                msg2_parts.append(f"{EMOJI['bullet']} *Risk Management*: {risk_text}")

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
                        from modules.engine.market_data import get_market_snapshot
                        snapshot_intraday = get_market_snapshot(now) or {}
                        assets_intraday = snapshot_intraday.get('assets', {}) or {}
                        spx_price_intraday = assets_intraday.get('SPX', {}).get('price', 0)
                        eur_price_intraday = assets_intraday.get('EURUSD', {}).get('price', 0)
                    except Exception as qe:
                        log.warning(f"{EMOJI['warn']} [NOON-SIGNALS-SPX-EUR] Market snapshot unavailable: {qe}")
                        spx_price_intraday = 0
                        eur_price_intraday = 0
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
                # Reuse the shared prediction evaluation helper so that
                # Noon, Evening, Summary and Dashboard all see the same
                # accuracy statistics and per-prediction statuses.
                eval_data = ctx._evaluate_predictions_with_live_data(now) or {}
                items = eval_data.get('items') or []

                hits = int(eval_data.get('hits', 0) or 0)
                misses = int(eval_data.get('misses', 0) or 0)
                pending = int(eval_data.get('pending', 0) or 0)
                closed = int(eval_data.get('total_tracked', 0) or 0)
                evaluated = int(eval_data.get('total_evaluated', 0) or 0) or len(items)
                acc = float(eval_data.get('accuracy_pct', 0.0) or 0.0)

                lines: List[str] = []
                for it in items:
                    asset = (it.get('asset') or '').upper()
                    direction = (it.get('direction') or 'LONG').upper()
                    entry = it.get('entry')
                    target = it.get('target')
                    stop = it.get('stop')
                    curr = it.get('current')
                    status = str(it.get('status') or 'PENDING')
                    distance = it.get('distance_to_target')

                    # Decorate status with emojis for Noon text
                    display_status = status
                    if 'TARGET HIT' in status:
                        display_status = f"TARGET HIT {EMOJI['check']}"
                    elif 'STOP HIT' in status:
                        display_status = f"STOP HIT {EMOJI['cross']}"
                    elif 'IN PROGRESS' in status:
                        display_status = "IN PROGRESS"
                    elif 'PENDING' in status.upper():
                        display_status = 'PENDING - live data pending'

                    detail = ''
                    if distance is not None and isinstance(distance, (int, float)):
                        try:
                            # Distance is already signed; keep formatting similar to old logic
                            if isinstance(distance, float):
                                detail = f" - dist to target: {distance:+.4f}" if abs(distance) < 1 else f" - dist to target: {distance:+.2f}"
                            else:
                                detail = f" - dist to target: {float(distance):+.2f}"
                        except Exception:
                            detail = ''

                    if curr is not None and curr != 0:
                        lines.append(
                            f"{EMOJI['bullet']} *{asset} {direction}*: Entry {entry} | Target {target} | Stop {stop} 4 {display_status}{detail}"
                        )
                    else:
                        lines.append(f"{EMOJI['bullet']} *{asset} {direction}*: {display_status}")

                if lines:
                    msg3_parts.extend(lines)
                    msg3_parts.append("")

                    # Report daily accuracy only on fully closed signals. Pending
                    # trades are tracked separately and excluded from the
                    # denominator to avoid misleading hit rates on tiny or
                    # unresolved samples.
                    if closed > 0:
                        msg3_parts.append(f"{EMOJI['chart']} *Daily Accuracy*: {acc:.0f}% (Hits: {hits} / {closed})")
                    elif evaluated > 0:
                        msg3_parts.append(f"{EMOJI['chart']} *Daily Accuracy*: n/a (no fully closed signals yet – {pending} trade(s) still in progress)")
                    else:
                        msg3_parts.append(f"{EMOJI['chart']} *Daily Accuracy*: n/a (no live-tracked signals today)")

                    noon_prediction_eval = {
                        'hits': hits,
                        'misses': misses,
                        'pending': pending,
                        'total_tracked': closed,
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
                from modules.engine.market_data import get_market_snapshot
                snapshot_outlook = get_market_snapshot(now) or {}
                assets_outlook = snapshot_outlook.get('assets', {}) or {}
                spx_price_outlook = assets_outlook.get('SPX', {}).get('price', 0)
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
                msg3_parts.append(f"{EMOJI['clock']} *AFTERNOON OUTLOOK (12:00-15:00):*")
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
                msg3_parts.append(f"{EMOJI['bullet']} *18:00 Evening Analysis*: Weekend wrap + weekly performance review")
            else:
                msg3_parts.append(f"{EMOJI['bullet']} *15:00 Afternoon Update*: Mid-session tracking + ML checkpoint")
                msg3_parts.append(f"{EMOJI['bullet']} *18:00 Evening Analysis*: Session wrap + performance review")
            msg3_parts.append(f"{EMOJI['bullet']} *21:00 Daily Summary*: Complete day analysis (6 pages)")
            msg3_parts.append(f"{EMOJI['bullet']} *Tomorrow 06:00*: Fresh press review (7 messages)")
            msg3_parts.append("")
            
            msg3_parts.append(EMOJI['line'] * 40)
            msg3_parts.append(f"{EMOJI['robot']} SV Enhanced {EMOJI['bullet']} Noon Verification 3/3")
            
            messages.append("\n".join(msg3_parts))
            log.info("Ã¢Å“â€¦ [NOON] Message 3 (Prediction Verification) generated")

            # ENGINE snapshot for noon stage (include partial prediction_eval when available)
            try:
                noon_sentiment = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL') if isinstance(news_data, dict) else 'NEUTRAL'
                assets_noon: Dict[str, Any] = {}
                try:
                    from modules.engine.market_data import get_market_snapshot
                    market_snapshot_noon = get_market_snapshot(now) or {}
                    assets_noon = market_snapshot_noon.get('assets', {}) or {}
                except Exception as md_e:
                    log.warning(f"{EMOJI['warning']} [ENGINE-NOON] Error building market snapshot: {md_e}")
                ctx._engine_log_stage('noon', now, noon_sentiment, assets_noon, noon_prediction_eval)
            except Exception as e:
                log.warning(f"{EMOJI['warning']} [ENGINE-NOON] Error logging engine stage: {e}")
            log.info("Ã¢Å“â€¦ [NOON] Message 3 (Prediction Verification) generated")
            
        except Exception as e:
            log.error(f"Ã¢ÂÅ’ [NOON] Message 3 error: {e}")
            messages.append(f"Ã°Å¸â€Â **SV - PREDICTIONS**\nÃ°Å¸â€œâ€¦ {now.strftime('%H:%M')} Ã¢â‚¬Â¢ Verification system loading")
        
        # Save all messages with enhanced metadata
        if messages:
            saved_path = ctx.save_content("noon_update", messages, {
                'total_messages': len(messages),
                'enhanced_features': ['Intraday Update', 'ML Sentiment', 'Prediction Verification'],
                'news_count': len(news_data.get('news', [])),
                'sentiment': news_data.get('sentiment', {}),
                'continuity_with_morning': True,
                'prediction_accuracy': f"{acc:.0f}%" if 'acc' in locals() else 'N/A'
            })
            log.info(f"Ã°Å¸â€™Â¾ [NOON] Saved to: {saved_path}")
        
        # Update session tracker with noon progress
        if ctx.session_tracker and DEPENDENCIES_AVAILABLE:
            try:
                market_moves = {'SPX': '+0.8%', 'BTC': '+2.1%', 'EURUSD': 'stable', 'VIX': '-5.2%'}
                predictions_check = [
                    {'prediction': 'S&P Bullish', 'status': 'CORRECT'},
                    {'prediction': 'BTC Range', 'status': 'CORRECT'},
                    {'prediction': 'EUR Weak', 'status': 'CORRECT'},
                    {'prediction': 'Tech Lead', 'status': 'EXCELLENT'}
                ]
                current_sentiment = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL-BULLISH')
                ctx.session_tracker.update_noon_progress(current_sentiment, market_moves, predictions_check)
            except Exception as e:
                log.warning(f"Ã¢Å¡Â Ã¯Â¸Â [NOON-TRACKER] Error: {e}")
        
        # Save sentiment for noon stage
        try:
            noon_sentiment = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL-BULLISH')
            ctx._save_sentiment_for_stage('noon', noon_sentiment, now)
        except Exception as e:
            log.warning(f"[SENTIMENT-TRACKING] Error in noon: {e}")
        
        log.info(f"Ã¢Å“â€¦ [NOON] Completed generation of {len(messages)} ENHANCED noon update messages")
        return messages
        
    except Exception as e:
        log.error(f"Ã¢ÂÅ’ [NOON] General error: {e}")
        # Emergency fallback
        return [f"Ã°Å¸Å’Å¾ **SV - NOON UPDATE**\nÃ°Å¸â€œâ€¦ {_now_it().strftime('%H:%M')} Ã¢â‚¬Â¢ System under maintenance"]
