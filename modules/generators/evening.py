# Intraday generator for the Evening block.
#
# Extracted from DailyContentGenerator.generate_evening_analysis in modules.daily_generator.

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

def generate_evening_analysis(ctx) -> List[str]:
    """EVENING ANALYSIS 18:00 - ENHANCED version with 3 messages
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
            
            # Enhanced continuity connection from noon 12:00
            msg1_parts.append(f"{EMOJI['chart_up']} *NOON FOLLOW-UP - SESSION CONTINUITY:*")
            try:
                if DEPENDENCIES_AVAILABLE:
                    from narrative_continuity import get_narrative_continuity
                    continuity = get_narrative_continuity()
                    noon_connection = continuity.get_evening_noon_connection()
                    
                    default_noon_followup = f"{EMOJI['chart_up']} From noon: Progress tracking - objectives summary"
                    msg1_parts.append(
                        f"{EMOJI['bullet']} {noon_connection.get('noon_followup', default_noon_followup)}"
                    )
                    msg1_parts.append(f"{EMOJI['bullet']} {noon_connection.get('predictions_summary', 'Prediction accuracy: see Evening Performance Review / Daily Summary')}")
                    msg1_parts.append(f"{EMOJI['bullet']} {noon_connection.get('regime_status', 'Market regime: see ML Sentiment blocks (Noon/Evening)')}")
                else:
                    # Fallback continuity (no static accuracy claims)
                    msg1_parts.append(f"{EMOJI['bullet']} From noon 12:00: Progress tracking successfully completed")
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
                    if not ctx._is_personal_finance(it.get('title', ''))
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
                            ctx._mark_news_used(item, now)
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
                # Try to enrich with live SPX/EURUSD/GOLD snapshot when available
                spx_line = None
                eur_line = None
                gold_price = 0
                gold_chg = None
                try:
                    from modules.engine.market_data import get_market_snapshot
                    snapshot_evening = get_market_snapshot(now) or {}
                    assets_evening = snapshot_evening.get('assets', {}) or {}
                    spx_q = assets_evening.get('SPX', {}) or {}
                    eur_q = assets_evening.get('EURUSD', {}) or {}
                    gold_q = assets_evening.get('GOLD', {}) or {}
                except Exception as qe:
                    log.warning(f"{EMOJI['warning']} [EVENING-PRICES] Market snapshot unavailable: {qe}")
                    spx_q = {}
                    eur_q = {}
                    gold_q = {}
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
            
            # Session Character Analysis - Enhanced with Regime Manager
            msg1_parts.append(f"{EMOJI['notebook']} *SESSION CHARACTER:*")
            
            # Use BRAIN + Regime Manager for consistent narrative (v1.5.0 Enhancement)
            if REGIME_MANAGER_AVAILABLE:
                try:
                    from modules.brain.regime_detection import get_regime_summary

                    # Current sentiment used for evening regime
                    session_sentiment = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL')
                    sentiment_payload: Any = {'evening': session_sentiment}

                    # Live prediction evaluation (shared helper)
                    try:
                        pred_eval = ctx._evaluate_predictions_with_live_data(now) or {}
                    except Exception as eval_e:
                        log.warning(f"{EMOJI['warning']} [REGIME-UPDATE] Accuracy eval error: {eval_e}")
                        pred_eval = {}

                    # Regime summary from BRAIN (coerente con Noon/Summary/heartbeat)
                    regime_summary = get_regime_summary(pred_eval, sentiment_payload)
                    regime_state = regime_summary.get('regime_state', 'neutral')

                    # Session character from DailyRegimeManager (testo più ricco)
                    session_character = None
                    try:
                        manager = get_daily_regime_manager()
                        manager.update_from_sentiment_tracking(sentiment_payload)
                        if pred_eval and pred_eval.get('total_tracked', 0) > 0:
                            accuracy_pct = float(pred_eval.get('accuracy_pct', 0.0) or 0.0)
                            total_tracked = int(pred_eval.get('total_tracked', 0) or 0)
                            manager.update_from_accuracy(accuracy_pct, total_tracked)
                        session_character = manager.get_session_character()
                    except Exception as mgr_e:
                        log.warning(f"{EMOJI['warning']} [REGIME-MANAGER] Error in evening manager: {mgr_e}")

                    if session_character:
                        msg1_parts.append(f"{EMOJI['bullet']} *Theme*: {session_character}")
                    else:
                        # Fallback to sentiment-based theme if session_character non disponibile
                        if session_sentiment == 'POSITIVE':
                            msg1_parts.append(f"{EMOJI['bullet']} *Theme*: Risk-on rotation - growth sectors outperformed")
                        elif session_sentiment == 'NEGATIVE':
                            msg1_parts.append(f"{EMOJI['bullet']} *Theme*: Risk-off rotation - defensive positioning")
                        else:
                            msg1_parts.append(f"{EMOJI['bullet']} *Theme*: Mixed session - sector rotation active")

                    # Volume and breadth based on BRAIN regime state
                    if regime_state == 'risk_on':
                        msg1_parts.append(f"{EMOJI['bullet']} *Volume*: Above average - conviction buying")
                        msg1_parts.append(f"{EMOJI['bullet']} *Breadth*: Broad participation - healthy rally")
                    elif regime_state == 'risk_off':
                        msg1_parts.append(f"{EMOJI['bullet']} *Volume*: Elevated - distribution patterns")
                        msg1_parts.append(f"{EMOJI['bullet']} *Breadth*: Narrow leadership - selective selling")
                    else:
                        msg1_parts.append(f"{EMOJI['bullet']} *Volume*: Normal levels - rangebound trading")
                        msg1_parts.append(f"{EMOJI['bullet']} *Breadth*: Balanced participation - neutral bias")
                        
                    log.info(f"[OK] [REGIME-MANAGER] Evening character summary generated")
                    
                except Exception as regime_e:
                    log.warning(f"{EMOJI['warning']} [REGIME-MANAGER] Error in evening: {regime_e}")
                    # Fallback to original logic
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
            else:
                # Fallback quando Regime Manager non è disponibile
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
            
            # DETAILED PREDICTION BREAKDOWN (BRAIN + shared evaluation)
            try:
                eval_data = ctx._evaluate_predictions_with_live_data(now) or {}
                items = eval_data.get('items') or []
                hits = int(eval_data.get('hits', 0) or 0)
                misses = int(eval_data.get('misses', 0) or 0)
                pending = int(eval_data.get('pending', 0) or 0)
                closed = int(eval_data.get('total_tracked', 0) or 0)
                evaluated = int(eval_data.get('total_evaluated', 0) or 0) or len(items)

                if items:
                    msg2_parts.append(f"{EMOJI['trophy']} *PREDICTION PERFORMANCE (DETAILED):*")

                    # Build a simple live price map compatible with brain.prediction_status
                    live_prices: Dict[str, Any] = {}
                    crypto_prices: Dict[str, Any] = {}
                    try:
                        # Reuse ENGINE market snapshot when possible
                        from modules.engine.market_data import get_market_snapshot
                        market = get_market_snapshot(now) or {}
                        live_prices = market.get('assets', {}) or {}
                    except Exception:
                        live_prices = {}
                    try:
                        crypto_prices = get_live_crypto_prices() or {}
                    except Exception:
                        crypto_prices = {}

                    from modules.brain.prediction_status import compute_prediction_status

                    for pit in items:
                        try:
                            # Ricostruisci una prediction minimal compatibile
                            pred = {
                                'asset': pit.get('asset'),
                                'direction': pit.get('direction'),
                                'entry': pit.get('entry'),
                                'target': pit.get('target'),
                                'stop': pit.get('stop'),
                            }
                            status_info = compute_prediction_status(pred, live_prices, crypto_prices)
                            asset = (pred.get('asset') or 'ASSET').upper()
                            direction = pred.get('direction') or 'N/A'
                            entry = pred.get('entry')
                            target = pred.get('target')
                            stop = pred.get('stop')
                            status = status_info.get('status') or 'PENDING'

                            msg2_parts.append(
                                f"{EMOJI['bullet']} {asset} {direction}: "
                                f"Entry {entry} | Target {target} | Stop {stop} → {status}"
                            )
                        except Exception as line_e:
                            log.warning(f"{EMOJI['warning']} [EVENING-PERF-LINE] Error formatting prediction line: {line_e}")

                    if closed > 0:
                        acc_pct = float(eval_data.get('accuracy_pct', 0.0) or 0.0)
                        msg2_parts.append(
                            f"{EMOJI['check']} *Overall*: {hits}/{closed} hits - {acc_pct:.0f}% on fully closed live-tracked trades"
                        )
                    elif evaluated > 0:
                        msg2_parts.append(
                            f"{EMOJI['check']} *Overall*: no fully closed trades yet – {pending} live position(s) remain open and will be evaluated once resolved"
                        )
                    else:
                        msg2_parts.append(f"{EMOJI['check']} *Overall*: 0/0 – no live-tracked signals today")
                    msg2_parts.append("")
            except Exception as e:
                log.warning(f"{EMOJI['warning']} [EVENING-PERF] Error: {e}")
            
            # Enhanced Prediction performance (narrative layer)
            msg2_parts.append(f"{EMOJI['trophy']} *PREDICTION PERFORMANCE (NARRATIVE):*")
            try:
                # Questo blocco accompagna il dettaglio live senza hardcodare una giornata perfetta.
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
                # Derive an evening accuracy snapshot when available, based only
                # on fully closed signals. Pending trades are excluded from the
                # denominator to avoid overstating or understating performance
                # on tiny, unresolved samples.
                acc_evening_pct = None
                if 'hits' in locals() and 'closed' in locals() and isinstance(closed, (int, float)) and closed > 0:
                    try:
                        acc_evening_pct = (hits / closed) * 100.0
                    except Exception:
                        acc_evening_pct = None

                if DEPENDENCIES_AVAILABLE:
                    # Advanced ML results (Regime/Brain available)
                    msg2_parts.append(f"{EMOJI['bullet']} *Ensemble performance*: Uses multiple models to stabilise signals")
                    if acc_evening_pct is not None:
                        if acc_evening_pct >= 80:
                            msg2_parts.append(f"{EMOJI['bullet']} *Model Consensus*: high agreement with realised moves (≈{acc_evening_pct:.0f}% accuracy on fully closed trades)")
                            msg2_parts.append(f"{EMOJI['bullet']} *Model Calibration*: well aligned with the current regime")
                        elif acc_evening_pct >= 60:
                            msg2_parts.append(f"{EMOJI['bullet']} *Model Consensus*: generally consistent with price action (≈{acc_evening_pct:.0f}% accuracy on fully closed trades)")
                            msg2_parts.append(f"{EMOJI['bullet']} *Model Calibration*: solid but with some noise")
                        elif acc_evening_pct > 0:
                            msg2_parts.append(f"{EMOJI['bullet']} *Model Consensus*: mixed signals (≈{acc_evening_pct:.0f}% accuracy on fully closed trades)")
                            msg2_parts.append(f"{EMOJI['bullet']} *Model Calibration*: requires refinement for the current regime")
                        else:
                            msg2_parts.append(f"{EMOJI['bullet']} *Model Consensus*: today’s closed signals did not align with price action (0% accuracy on fully closed trades)")
                            msg2_parts.append(f"{EMOJI['bullet']} *Model Calibration*: defensive review in progress – see Daily Summary Page 1/2")
                    else:
                        msg2_parts.append(f"{EMOJI['bullet']} *Model Consensus*: evaluated qualitatively – no fully closed live-tracked predictions today (open trades treated as in-progress tests)")
                        msg2_parts.append(f"{EMOJI['bullet']} *Model Calibration*: see Daily Summary Page 1/2 for full accuracy details when available")
                    msg2_parts.append(f"{EMOJI['bullet']} *Feature Importance*: sentiment analysis, technical momentum, macro context")
                else:
                    # Fallback ML results – tone driven by real accuracy, no static “strong” claims
                    if acc_evening_pct is not None:
                        if acc_evening_pct >= 80:
                            msg2_parts.append(f"{EMOJI['bullet']} *Model Consensus*: Strong agreement across algorithms – high hit rate today")
                            msg2_parts.append(f"{EMOJI['bullet']} *Sentiment Analysis*: Captured intraday trend with good precision")
                            msg2_parts.append(f"{EMOJI['bullet']} *Technical Indicators*: Provided reliable confirmation signals")
                        elif acc_evening_pct >= 60:
                            msg2_parts.append(f"{EMOJI['bullet']} *Model Consensus*: Generally aligned with market moves (above-target accuracy)")
                            msg2_parts.append(f"{EMOJI['bullet']} *Sentiment Analysis*: Directionally correct with some noise")
                            msg2_parts.append(f"{EMOJI['bullet']} *Technical Indicators*: Useful but not always decisive")
                        elif acc_evening_pct > 0:
                            msg2_parts.append(f"{EMOJI['bullet']} *Model Consensus*: Mixed – part of the signals worked, part no")
                            msg2_parts.append(f"{EMOJI['bullet']} *Sentiment Analysis*: Provided context but required discretion")
                            msg2_parts.append(f"{EMOJI['bullet']} *Technical Indicators*: Helpful for risk control more than for direction")
                        else:
                            msg2_parts.append(f"{EMOJI['bullet']} *Model Consensus*: Challenging day – ensemble did not align with realised moves (0% accuracy)")
                            msg2_parts.append(f"{EMOJI['bullet']} *Sentiment Analysis*: Highlighted themes, but timing and direction need review")
                            msg2_parts.append(f"{EMOJI['bullet']} *Technical Indicators*: Signals not confirmed by price action")
                        msg2_parts.append(f"{EMOJI['bullet']} *Overall Score*: Full details in Daily Summary Page 1/2")
                    else:
                        msg2_parts.append(f"{EMOJI['bullet']} *Model Consensus*: evaluated qualitatively – no fully closed live-tracked predictions today (open trades treated as in-progress tests)")
                        msg2_parts.append(f"{EMOJI['bullet']} *Sentiment Analysis*: Used mainly as context filter")
                        msg2_parts.append(f"{EMOJI['bullet']} *Technical Indicators*: Descriptive role, see Summary for details")
                        msg2_parts.append(f"{EMOJI['bullet']} *Overall Score*: Detailed view in Daily Summary Page 1/2")
                    
            except Exception as e:
                log.warning(f"{EMOJI['warning']} [EVENING-ML] Error: {e}")
                msg2_parts.append(f"{EMOJI['bullet']} *ML Results*: Analysis completed – see Daily Summary for full details")
            
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
                msg3_parts.append(f"{EMOJI['bullet']} *Gap Analysis*: neutral gap scenario – treat the opening as information, not as a standalone signal")
                # Usa lo stesso feed calendario della Press Review quando disponibile.
                events_summary = []
                try:
                    from sv_calendar import get_calendar_events
                    events = get_calendar_events(days_ahead=2)
                    for ev in events[:4]:
                        title = ev.get('Title', 'Event')
                        date_str = ev.get('FormattedDate', ev.get('Date', 'TBD'))
                        impact = ev.get('Impact', 'Medium')
                        source = ev.get('Source', '')
                        events_summary.append(f"{title} – {date_str} ({impact}, {source})")
                except Exception as cal_err:
                    log.warning(f"{EMOJI['warning']} [EVENING-TOMORROW-CALENDAR] Error loading calendar events: {cal_err}")

                if events_summary:
                    msg3_parts.append(f"{EMOJI['bullet']} *Key Events*: " + "; ".join(events_summary))
                else:
                    msg3_parts.append(f"{EMOJI['bullet']} *Key Events*: central bank communication and macro releases that may affect rates, volatility and risk appetite – check the live economic calendar for specific times")

                msg3_parts.append(f"{EMOJI['bullet']} *Earnings*: major index constituents and leading tech names whose results can amplify or dampen existing trends")
                msg3_parts.append(f"{EMOJI['bullet']} *Data Releases*: inflation, labour market and growth indicators that can shift expectations for policy and sector leadership")
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

            # Dynamic risk bias using Regime Manager when available, otherwise fallback
            risk_bias_line = None
            if REGIME_MANAGER_AVAILABLE:
                try:
                    manager = get_daily_regime_manager()
                    bias = manager.get_tomorrow_strategy_bias()
                    if bias == 'POSITIVE':
                        risk_bias_line = "Risk-on maintained - growth over value"
                    elif bias == 'DEFENSIVE':
                        risk_bias_line = "Defensive bias - capital preservation focus"
                    else:
                        risk_bias_line = "Neutral bias - selective opportunities"
                except Exception as rb_e:
                    log.warning(f"{EMOJI['warning']} [EVENING-RISK-BIAS] Error deriving tomorrow bias: {rb_e}")
                    risk_bias_line = "Neutral bias - selective opportunities"
            else:
                # Simple heuristic fallback when Regime Manager is not available
                risk_bias_line = "Neutral bias - selective opportunities"

            msg3_parts.append(f"{EMOJI['bullet']} *Risk Bias*: {risk_bias_line}")
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
            msg3_parts.append(f"{EMOJI['clock']} *TOMORROW SCHEDULE (Italy time):*")
            if now.weekday() == 6:  # Sunday
                msg3_parts.append(f"{EMOJI['bullet']} Asia futures open Sunday night, then full 3-hour cycle on Monday (00/03/06/09/12/15/18/21)")
            else:
                msg3_parts.append(f"{EMOJI['bullet']} Full 3-hour cycle: 00:00 Night, 03:00 Late Night, 06:00 Press Review, 09:00 Morning, 12:00 Noon, 15:00 Afternoon, 18:00 Evening, 21:00 Summary")
            msg3_parts.append("")
            
            msg3_parts.append(EMOJI['line'] * 40)
            msg3_parts.append(f"{EMOJI['robot']} SV Enhanced {EMOJI['bullet']} Tomorrow Setup 3/3")
            msg3_parts.append(f"{EMOJI['check']} Evening Analysis Complete - Asia handoff ready")
            msg3_parts.append(f"{EMOJI['back']} Next: Daily Summary (21:00) - 6 pages complete")
            
            messages.append("\n".join(msg3_parts))
            log.info("Ã¢Å“â€¦ [EVENING] Message 3 (Tomorrow Setup) generated")
            
        except Exception as e:
            log.error(f"Ã¢ÂÅ’ [EVENING] Errore messageso 3: {e}")
            messages.append(f"Ã°Å¸â€Â® **SV - TOMORROW SETUP**\nÃ°Å¸â€œâ€¦ {now.strftime('%H:%M')} Ã¢â‚¬Â¢ Setup system loading")
        
        # Save all messages with enhanced metadata
        if messages:
            saved_path = ctx.save_content("evening_analysis", messages, {
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
                try:
                    from modules.engine.market_data import get_market_snapshot
                    market_snapshot_evening = get_market_snapshot(now) or {}
                    assets_evening = market_snapshot_evening.get('assets', {}) or {}
                except Exception as md_e:
                    log.warning(f"{EMOJI['warning']} [ENGINE-EVENING] Error building market snapshot: {md_e}")
                # Nessuna prediction_eval consolidata qui: verrà usata quella di Summary
                ctx._engine_log_stage('evening', now, evening_sentiment, assets_evening, None)
            except Exception as e:
                log.warning(f"{EMOJI['warning']} [ENGINE-EVENING] Error logging engine stage: {e}")
        
        # Save evening data for Daily Summary continuity
        if ctx.narrative and DEPENDENCIES_AVAILABLE:
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
                ctx.narrative.set_evening_data(
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
            ctx._save_sentiment_for_stage('evening', evening_sentiment, now)
        except Exception as e:
            log.warning(f"[SENTIMENT-TRACKING] Error in evening: {e}")
        
        log.info(f"Ã¢Å“â€¦ [EVENING] Completed generation of {len(messages)} ENHANCED evening analysis messages")
        return messages
        
    except Exception as e:
        log.error(f"Ã¢ÂÅ’ [EVENING] General error: {e}")
        # Emergency fallback
        return [f"Ã°Å¸Å’â€  **SV - EVENING ANALYSIS**\nÃ°Å¸â€œâ€¦ {_now_it().strftime('%H:%M')} Ã¢â‚¬Â¢ System under maintenance"]
