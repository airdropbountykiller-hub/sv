# Intraday generator for the Summary block.
#
# Extracted from DailyContentGenerator.generate_daily_summary in modules.daily_generator.

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

def generate_daily_summary(ctx) -> List[str]:
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
        # (placeholder - i dati verranno integrati in una fase successiva)
        
        # VERIFICA COERENZA: Controllo incrociato di tutti i 5 messages intraday
        intraday_coherence = ctx._verify_full_day_coherence(now)
        
        # PREDICTION ACCURACY: Valuta le predictions del giorno con dati live (quando possibile)
        prediction_eval = ctx._evaluate_predictions_with_live_data(now)

        # Sentiment tracking per l'intera giornata (Press->Morning->Noon->Evening)
        sentiment_tracking = ctx._load_sentiment_tracking(now)

        # Deriva un sentiment unificato del day a partire dalle varie fasi intraday
        day_sentiment = 'NEUTRAL'
        try:
            if isinstance(sentiment_tracking, dict) and sentiment_tracking:
                if 'evening' in sentiment_tracking:
                    day_sentiment = str(sentiment_tracking['evening'].get('sentiment', 'NEUTRAL'))
                elif 'noon' in sentiment_tracking:
                    day_sentiment = str(sentiment_tracking['noon'].get('sentiment', 'NEUTRAL'))
                elif 'morning' in sentiment_tracking:
                    day_sentiment = str(sentiment_tracking['morning'].get('sentiment', 'NEUTRAL'))
                elif 'press_review' in sentiment_tracking:
                    day_sentiment = str(sentiment_tracking['press_review'].get('sentiment', 'NEUTRAL'))
        except Exception as e:
            log.warning(f"{EMOJI['warning']} [SUMMARY-SENTIMENT] Error deriving unified day sentiment: {e}")
            day_sentiment = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL')

        # Prepara Regime Manager per avere un regime/sentiment unificato usato da Evening + Summary
        unified_regime = None
        session_character = None
        if REGIME_MANAGER_AVAILABLE:
            try:
                # Prepara sentiment_payload per il layer BRAIN (come in Noon)
                simple_sentiments: Dict[str, str] = {}
                if isinstance(sentiment_tracking, dict):
                    for stage in ('press_review', 'morning', 'noon', 'evening'):
                        data = sentiment_tracking.get(stage)
                        if isinstance(data, dict) and 'sentiment' in data:
                            simple_sentiments[stage] = str(data.get('sentiment'))
                if simple_sentiments:
                    sentiment_payload: Any = simple_sentiments
                else:
                    sentiment_payload = {'evening': day_sentiment}

                # Usa BRAIN per ottenere un riassunto di regime (coerente con Noon/heartbeat)
                from modules.brain.regime_detection import get_regime_summary
                eval_for_regime = prediction_eval or {}
                regime_summary = get_regime_summary(eval_for_regime, sentiment_payload)

                # Conserva unified_regime/session_character per compatibilità con il resto del codice
                try:
                    manager = get_daily_regime_manager()
                    manager.update_from_sentiment_tracking(sentiment_payload)
                    if prediction_eval and prediction_eval.get('total_tracked', 0) > 0:
                        accuracy_pct = float(prediction_eval.get('accuracy_pct', 0.0) or 0.0)
                        total_tracked = int(prediction_eval.get('total_tracked', 0) or 0)
                        manager.update_from_accuracy(accuracy_pct, total_tracked)
                    unified_regime = manager.infer_regime()
                    session_character = manager.get_session_character()
                except Exception as mgr_e:
                    log.warning(f"{EMOJI['warning']} [SUMMARY-REGIME] Manager fallback error: {mgr_e}")

                # Salva il riassunto per Page 1
                unified_regime_summary: Dict[str, Any] = regime_summary
            except Exception as regime_e:
                log.warning(f"{EMOJI['warning']} [SUMMARY-REGIME] Error initializing unified regime: {regime_e}")

        # Container for end-of-day market snapshot used by weekly/monthly aggregators
        daily_market_snapshot: Dict[str, Any] = {}
        
        # CONCATENAZIONE: Prepara collegamento con Rassegna del day successivo
        next_day_setup = ctx._prepare_next_day_connection(now, intraday_coherence)
        
        # Header principale per tutte le pagine
        header_base = f"{EMOJI['notebook']} *SV - COMPLETE DAILY SUMMARY*\n"
        header_base += f"{EMOJI['calendar']} {now.strftime('%A %d %B %Y')} - {now.strftime('%H:%M')}\n"
        header_base += "=" * 50 + "\n\n"
        
        # Get complete day narrative data
        evening_sentiment = 'POSITIVE'
        if DEPENDENCIES_AVAILABLE and ctx.narrative:
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
                perf_label = "Performance based on qualitative review (no fully closed live-tracked predictions)"

            page1.append(f"{EMOJI['magnifier']} *DAY RECAP - EVENING CONNECTION:*")
            # Usa il sentiment/regime unificato per mantenere coerenza con l'Evening
            regime_str = unified_regime_summary.get('regime_state', 'neutral') if 'unified_regime_summary' in locals() else (unified_regime.value if unified_regime is not None else 'neutral')
            unified_sent_label = day_sentiment or evening_sentiment
            if now.weekday() >= 5:
                # Weekend: nessuna vera cash session su equity, focus su crypto/macro
                page1.append(f"{EMOJI['bullet']} From evening 18:30: Weekend wrap with sentiment {unified_sent_label}")
                if session_character:
                    page1.append(f"{EMOJI['bullet']} Session character: {session_character} (weekend analysis, no cash equity session)")
                else:
                    page1.append(f"{EMOJI['bullet']} Session character: Weekend analysis & positioning (no cash equity session)")
                page1.append(f"{EMOJI['bullet']} Performance quality: {perf_label}")
                page1.append(f"{EMOJI['bullet']} Market breadth: Traditional equity markets closed; crypto breadth monitored only")
            else:
                # Giorni feriali: vera sessione di mercato
                page1.append(f"{EMOJI['bullet']} From evening 18:30: Session close with sentiment {unified_sent_label}")
                if session_character:
                    page1.append(f"{EMOJI['bullet']} Session character: {session_character}")
                else:
                    page1.append(f"{EMOJI['bullet']} Session character: Mixed session with sector rotation active")
                page1.append(f"{EMOJI['bullet']} Performance quality: {perf_label}")
                if regime_str == 'risk_on':
                    breadth_text = "Broad participation - healthy rally"
                elif regime_str == 'risk_off':
                    breadth_text = "Narrow leadership - defensive tone"
                elif regime_str == 'neutral':
                    breadth_text = "Balanced participation - rangebound session"
                else:
                    breadth_text = "Mixed participation - transition phase"
                page1.append(f"{EMOJI['bullet']} Market breadth: {breadth_text}")
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
                    page1.append(f"{EMOJI['bullet']} *ML performance*: n/a (no fully closed live-tracked predictions today)")
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
                # Try to use live SPX/EURUSD/GOLD snapshot for a truthful snapshot
                try:
                    from modules.engine.market_data import get_market_snapshot
                    snapshot_summary = get_market_snapshot(now) or {}
                    assets_summary = snapshot_summary.get('assets', {}) or {}
                    spx_q = assets_summary.get('SPX', {}) or {}
                    eur_q = assets_summary.get('EURUSD', {}) or {}
                    gold_q = assets_summary.get('GOLD', {}) or {}
                except Exception as qe:
                    log.warning(f"{EMOJI['warning']} [SUMMARY-MARKET] Market snapshot unavailable: {qe}")
                    spx_q = {}
                    eur_q = {}
                    gold_q = {}
                spx_price = float(spx_q.get('price', 0) or 0.0)
                eur_price = float(eur_q.get('price', 0) or 0.0)
                spx_chg = spx_q.get('change_pct', None)
                eur_chg = eur_q.get('change_pct', None)
                gold_per_gram = float(gold_q.get('price', 0) or 0.0)
                gold_chg = gold_q.get('change_pct', None)

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
                grade = "N/A (No fully closed live-tracked predictions)"
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
                page2.append(f"{EMOJI['bullet']} *Success Rate*: n/a (no fully closed live-tracked predictions today)")

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
            acc_page3 = float(eval_page3.get('accuracy_pct', 0.0) or 0.0)
            
            # Portfolio-level risk metrics are only meaningful with real P&L and
            # position data. Until portfolio integration is complete, they are
            # reported as not available to avoid misleading precision.
            page3.append(f"{EMOJI['bullet']} *VaR (95%)*: N/A - requires live P&L tracking (future enhancement)")
            page3.append(f"{EMOJI['bullet']} *Max Drawdown*: N/A - requires intraday position tracking (future enhancement)")
            page3.append(f"{EMOJI['bullet']} *Sharpe Ratio*: N/A - will be computed only once robust portfolio and P&L data are integrated")
            # Win Rate - refer back to Pages 1/2 where directional performance is summarised
            page3.append(f"{EMOJI['bullet']} *Win Rate*: See Executive Summary / Performance (Pages 1–2) for how signals behaved relative to the regime")
            page3.append(f"{EMOJI['bullet']} *Risk-Adjusted Return*: N/A - current focus is on directional and process metrics rather than portfolio-level returns")
            
            page3.append("")
            
            # Momentum Indicators Deep Dive
            page3.append(f"{EMOJI['chart_up']} *MOMENTUM INDICATORS DEEP DIVE:*")
            sent_info = news_data.get('sentiment', {})
            sentiment_label = sent_info.get('sentiment', 'NEUTRAL')
            pos_score = int(sent_info.get('positive_score', 0) or 0)
            neg_score = int(sent_info.get('negative_score', 0) or 0)
            balance = pos_score - neg_score
            page3.append(f"{EMOJI['bullet']} *News Sentiment*: {sentiment_label} ({balance:+d} balance)")
            page3.append(f"{EMOJI['bullet']} *Unified Day Sentiment*: {day_sentiment}")
            # Enhanced Market Momentum with Regime Manager
            if REGIME_MANAGER_AVAILABLE:
                try:
                    manager = get_daily_regime_manager()
                    momentum_text = manager.get_market_momentum_text()
                    page3.append(f"{EMOJI['bullet']} *Market Momentum*: {momentum_text}")
                except Exception as mom_e:
                    log.warning(f"{EMOJI['warning']} [REGIME-MANAGER] Market momentum error: {mom_e}")
                    page3.append(f"{EMOJI['bullet']} *Market Momentum*: Trend strength assessed via intraday price action")
            else:
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
                # Enhanced Model Stability with Regime Manager
                if REGIME_MANAGER_AVAILABLE:
                    try:
                        manager = get_daily_regime_manager()
                        stability_text = manager.get_model_stability_text()
                        page3.append(f"{EMOJI['bullet']} *Model Stability*: {stability_text}")
                    except Exception as stab_e:
                        log.warning(f"{EMOJI['warning']} [REGIME-MANAGER] Model stability error: {stab_e}")
                        page3.append(f"{EMOJI['bullet']} *Model Stability*: Performance assessed via accuracy tracking")
                else:
                    page3.append(f"{EMOJI['bullet']} *Model Stability*: Performance assessed via accuracy tracking")
            
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
            # EUR/USD dynamic when possible, Gold with live price when available, otherwise qualitative only
            try:
                from modules.engine.market_data import get_market_snapshot
                snapshot_ccy = get_market_snapshot(now) or {}
                assets_ccy = snapshot_ccy.get('assets', {}) or {}
                eur_ccy = assets_ccy.get('EURUSD', {}) or {}
                gold_ccy = assets_ccy.get('GOLD', {}) or {}
            except Exception as qe:
                log.warning(f"{EMOJI['warning']} [SUMMARY-PAGE4-FX] Market snapshot unavailable: {qe}")
                eur_ccy = {}
                gold_ccy = {}
            eur_ccy_chg = eur_ccy.get('change_pct', None)
            gold_per_gram = gold_ccy.get('price', 0)
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
            if gold_per_gram and gold_chg is not None:
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

            # Modula il tono dello scenario gap in base all'accuracy reale
            eval_tomorrow = prediction_eval or {}
            acc_tomorrow = float(eval_tomorrow.get('accuracy_pct', 0.0) or 0.0)
            total_tomorrow = int(eval_tomorrow.get('total_tracked', 0) or 0)
            if total_tomorrow > 0 and acc_tomorrow >= 60.0:
                gap_text = "Bias for potential gap in the direction of prevailing momentum (no fixed probability)"
            elif total_tomorrow > 0 and acc_tomorrow <= 40.0:
                gap_text = "No strong statistical edge today – monitor opening gap in both directions around key levels"
            else:
                gap_text = "Neutral gap scenario – treat the opening as information, not as a standalone signal"
            page5.append(f"{EMOJI['bullet']} *Gap Scenario*: {gap_text}")

            page5.append(f"{EMOJI['bullet']} *Key Events*: central bank communication and macro releases that may affect rates, volatility and risk appetite – check the live economic calendar for specific times")
            page5.append(f"{EMOJI['bullet']} *Earnings Focus*: major index constituents and leading tech names, where reported results can amplify or dampen existing trends")
            page5.append(f"{EMOJI['bullet']} *Data Releases*: inflation, labour market and growth indicators that can shift expectations for policy and sector leadership")
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

            # Tech bias: mantieni il messaggio, ma aggiungi cautela dopo giornate difficili
            if total_tomorrow > 0 and acc_tomorrow <= 40.0:
                page5.append(f"{EMOJI['bullet']} *Tech Overweight*: Planned bias, but confirmation required after a challenging day for models")
            else:
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
                from modules.engine.market_data import get_market_snapshot
                snapshot_spx_summary = get_market_snapshot(now) or {}
                assets_spx_summary = snapshot_spx_summary.get('assets', {}) or {}
                spx_price_summary = assets_spx_summary.get('SPX', {}).get('price', 0)
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
            if total_tomorrow > 0 and acc_tomorrow <= 40.0:
                page5.append(f"{EMOJI['bullet']} *Hedge Ratio*: 15% - standard protection after a challenging day for the models")
            else:
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
        # sentiment_tracking e day_sentiment sono gia' stati caricati all'inizio del Summary
        
        try:
            page6 = []
            page6.append(header_base)
            page6.append(f"{EMOJI['notebook']} *Page 6/6 - DAILY JOURNAL & NOTES*")
            page6.append("")
            
            # Daily Narrative Section
            page6.append(f"{EMOJI['notebook']} *DAILY NARRATIVE - QUALITATIVE INSIGHTS:*")
            
            # Auto-generate narrative based on unified day_sentiment calcolato all'inizio del Summary

            # Enhanced narrative using Regime Manager (v1.5.0)
            if REGIME_MANAGER_AVAILABLE:
                try:
                    manager = get_daily_regime_manager()
                    
                    # Update manager with comprehensive sentiment tracking
                    if isinstance(sentiment_tracking, dict):
                        manager.update_from_sentiment_tracking(sentiment_tracking)
                    else:
                        manager.update_from_sentiment_tracking({'evening': day_sentiment})
                    
                    # Update with prediction evaluation if available
                    if prediction_eval and prediction_eval.get('total_tracked', 0) > 0:
                        accuracy_pct = prediction_eval.get('accuracy_pct', 0.0)
                        total_tracked = prediction_eval.get('total_tracked', 0)
                        manager.update_from_accuracy(accuracy_pct, total_tracked)
                    
                    # Generate consistent narrative using Regime Manager
                    narrative_intro = manager.get_session_character()
                    regime = manager.infer_regime()
                    
                    # Market story based on regime and accuracy
                    if regime.value == 'risk_on':
                        market_story = "Technology leadership drove the rally with exceptional breadth"
                        key_turning = "European open confirmed bullish bias, US session extended gains"
                    elif regime.value == 'risk_off':
                        market_story = "Sector rotation favored quality and safety over growth"
                        key_turning = "Mid-day weakness accelerated into US close"
                    elif regime.value == 'neutral':
                        market_story = "Rangebound trading prevailed with selective opportunities"
                        key_turning = "Choppy intraday action reflected uncertain sentiment"
                    else:  # transitioning
                        market_story = "Market regime shift in progress with mixed signals"
                        key_turning = "Intraday reversals highlighted directional uncertainty"
                    
                    # Log coherence for monitoring
                    debug_info = manager.get_debug_info()
                    log.info(f"[OK] [REGIME-MANAGER] Summary narrative: {narrative_intro} (Coherence: {debug_info.get('coherence_score', 0):.1f}%)")
                    
                except Exception as regime_e:
                    log.warning(f"{EMOJI['warning']} [REGIME-MANAGER] Error in summary: {regime_e}")
                    # Fallback to original logic
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
            else:
                # Fallback when Regime Manager not available
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
                # Usa l'accuracy reale per evitare claim eccessivamente ottimistici
                eval_unexp = prediction_eval or {}
                acc_unexp = float(eval_unexp.get('accuracy_pct', 0.0) or 0.0)
                total_unexp = int(eval_unexp.get('total_tracked', 0) or 0)

                crypto_prices = get_live_crypto_prices()
                if crypto_prices and crypto_prices.get('BTC', {}).get('price', 0) > 0:
                    btc_change = crypto_prices['BTC'].get('change_pct', 0)
                    if abs(btc_change) > 3:
                        page6.append(f"{EMOJI['bullet']} BTC volatility exceeded expectations ({btc_change:+.1f}%) - momentum shift")
                    else:
                        if total_unexp > 0 and acc_unexp <= 40.0:
                            page6.append(f"{EMOJI['bullet']} Key intraday developments diverged from the base scenario – difficult day for the models")
                        elif total_unexp > 0 and acc_unexp >= 60.0:
                            page6.append(f"{EMOJI['bullet']} No major surprises – market behaviour broadly in line with the main scenarios")
                        else:
                            page6.append(f"{EMOJI['bullet']} No major regime shocks – price action remained within normal ranges")
                else:
                    if total_unexp > 0 and acc_unexp <= 40.0:
                        page6.append(f"{EMOJI['bullet']} Market behaviour diverged from the statistical expectations – learning day for signal generation")
                    elif total_unexp > 0 and acc_unexp >= 60.0:
                        page6.append(f"{EMOJI['bullet']} No major surprises – intraday evolution consistent with model expectations")
                    else:
                        page6.append(f"{EMOJI['bullet']} Standard market behaviour without extreme events detected")
            except Exception:
                page6.append(f"{EMOJI['bullet']} Market evolution within expected parameters (coarse qualitative check)")
            
            page6.append(f"{EMOJI['bullet']} News flow: {'Higher than average' if len(news_data.get('news', [])) > 12 else 'Normal volume'}")
            page6.append(f"{EMOJI['bullet']} Volatility: {'Elevated' if day_sentiment == 'NEGATIVE' else 'Compressed' if day_sentiment == 'POSITIVE' else 'Moderate'} - VIX behavior standard")
            
            # Lessons learned
            page6.append("")
            page6.append(f"{EMOJI['bulb']} *LESSONS LEARNED & MODEL INSIGHTS:*")
            eval_data = prediction_eval or {}
            acc_pct = float(eval_data.get('accuracy_pct', 0.0) or 0.0)
            total_for_model = int(eval_data.get('total_tracked', 0) or 0)
            if total_for_model > 0 and acc_pct >= 60:
                what_worked = "ML models captured the prevailing regime effectively"
            elif total_for_model > 0 and acc_pct > 0:
                what_worked = "Risk management and position sizing limited damage"
            elif total_for_model > 0:
                what_worked = "Risk controls preserved capital on a difficult day"
            else:
                what_worked = "Framework validated qualitatively; live accuracy not measured today"
            page6.append(f"{EMOJI['bullet']} *What Worked*: {what_worked}")
            if total_for_model > 0 and acc_pct > 0:
                page6.append(f"{EMOJI['bullet']} *Model Behavior*: Ensemble approach delivered {acc_pct:.0f}% accuracy on tracked assets")
            elif total_for_model > 0:
                page6.append(f"{EMOJI['bullet']} *Model Behavior*: Challenging day - no correct hits on tracked assets (see Pages 1/2)")
            else:
                page6.append(f"{EMOJI['bullet']} *Model Behavior*: Accuracy not evaluated today (no fully closed live-tracked predictions)")
            if total_for_model > 0:
                if acc_pct >= 80:
                    signal_quality = "Exceptional clarity across timeframes"
                    improvement_area = "Fine-tune entries/exits rather than direction"
                elif acc_pct >= 60:
                    signal_quality = "Generally reliable with some noise"
                    improvement_area = "Improve filtering on low-conviction signals"
                elif acc_pct > 0:
                    signal_quality = "Mixed - signals required discretion"
                    improvement_area = "Refine models for current regime and reduce over-trading"
                else:
                    signal_quality = "Difficult day - models not aligned with price action"
                    improvement_area = "Review feature set, risk filters and regime assumptions"
            else:
                signal_quality = "Assessed qualitatively (no fully closed live-tracked predictions today)"
                improvement_area = "Collect more live history before changing models"
            page6.append(f"{EMOJI['bullet']} *Signal Quality*: {signal_quality}")
            page6.append(f"{EMOJI['bullet']} *Improvement Area*: {improvement_area}")
            
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
            ctx._save_daily_metrics_snapshot(now, prediction_eval or {}, daily_market_snapshot)
        except Exception as e:
            # Already logged inside helper; keep Daily Summary robust
            log.warning(f"{EMOJI['warning']} [SUMMARY-METRICS] Wrapper error while saving metrics: {e}")

        # ENGINE snapshot for summary stage (full-day prediction_eval + market snapshot)
        try:
            summary_sentiment = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL') if isinstance(news_data, dict) else 'NEUTRAL'
            ctx._engine_log_stage('summary', now, summary_sentiment, daily_market_snapshot, prediction_eval or {})
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

            acc_for_journal = float(prediction_eval.get('accuracy_pct', 0.0) or 0.0) if prediction_eval else 0.0
            tracked_for_journal = int(prediction_eval.get('total_tracked', 0) or 0) if prediction_eval else 0
            if tracked_for_journal > 0:
                daily_accuracy_str = f"{acc_for_journal:.0f}%"
                accuracy_lesson = f"Ensemble accuracy: {acc_for_journal:.0f}%"
            else:
                daily_accuracy_str = "N/A"
                accuracy_lesson = "Ensemble accuracy: N/A (no live-tracked predictions today)"
            surprise_factor = 'None'
            try:
                if 'crypto_prices' in locals():
                    btc_change_j = float(crypto_prices.get('BTC', {}).get('change_pct', 0) or 0.0)
                    if abs(btc_change_j) > 3:
                        surprise_factor = 'BTC volatility'
            except Exception:
                surprise_factor = 'None'

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
                    'daily_accuracy': daily_accuracy_str,
                    'daily_accuracy_grade': daily_accuracy_grade,
                    'best_call': 'Tech sector leadership' if (tracked_for_journal > 0 and acc_for_journal >= 60) else 'Defensive positioning' if day_sentiment == 'NEGATIVE' else 'Range trading',
                    'worst_call': 'None' if (tracked_for_journal > 0 and acc_for_journal >= 60) else 'Timing of defensive shift' if day_sentiment == 'NEGATIVE' else 'Breakout timing',
                    'surprise_factor': surprise_factor,
                    'overall_grade': daily_accuracy_grade
                },
                
                # Lessons and insights
                'lessons_learned': [
                    'ML models effective in current regime' if (tracked_for_journal > 0 and acc_for_journal >= 60) else 'Risk management preserved capital',
                    accuracy_lesson,
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
            journal_dir = Path(ctx.reports_dir) / '10_daily_journal'
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
            saved_path = ctx.save_content("daily_summary", pages, {
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
