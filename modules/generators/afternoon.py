# Intraday generator for the Afternoon block.
#
# New in the 3-hour SV schedule (00/03/06/09/12/15/18/21).

from typing import Any, Dict, List
import datetime

from modules import daily_generator as dg

EMOJI = dg.EMOJI
log = dg.log
_now_it = dg._now_it
get_enhanced_news = dg.get_enhanced_news
get_fallback_data = dg.get_fallback_data
get_live_crypto_prices = dg.get_live_crypto_prices
GOLD_GRAMS_PER_TROY_OUNCE = dg.GOLD_GRAMS_PER_TROY_OUNCE

# Optional dependency flags (mirrors modules.daily_generator)
DEPENDENCIES_AVAILABLE = getattr(dg, "DEPENDENCIES_AVAILABLE", False)
REGIME_MANAGER_AVAILABLE = getattr(dg, "REGIME_MANAGER_AVAILABLE", False)


def generate_afternoon_update(ctx) -> List[str]:
    """AFTERNOON UPDATE 15:00 - 3 messages

    Mid-session checkpoint to bridge Noon -> Evening.
    """
    try:
        log.info(f"{EMOJI['sun']} [AFTERNOON] Generating afternoon update (3 messages)...")

        messages: List[str] = []
        now = _now_it()

        news_data = get_enhanced_news(content_type="afternoon", max_news=6)
        fallback_data = get_fallback_data()

        # === MESSAGE 1: MARKET SNAPSHOT ===
        try:
            msg1: List[str] = []
            msg1.append(f"{EMOJI['sun']} *SV - AFTERNOON UPDATE* `{now.strftime('%H:%M')}`")
            msg1.append(f"{EMOJI['calendar']} {now.strftime('%A %m/%d/%Y')} {EMOJI['bullet']} Message 1/3")
            msg1.append(f"{EMOJI['bullet']} Noon follow-up + US session prep")
            msg1.append(EMOJI['line'] * 40)
            msg1.append("")

            # Continuity from Noon
            msg1.append(f"{EMOJI['chart']} *NOON FOLLOW-UP (from 12:00):*")
            try:
                if DEPENDENCIES_AVAILABLE:
                    from narrative_continuity import get_narrative_continuity

                    continuity = get_narrative_continuity()
                    fn = getattr(continuity, "get_afternoon_noon_connection", None)
                    noon_connection = fn() if callable(fn) else {}

                    default_followup = f"{EMOJI['bullet']} Intraday bias validation: monitoring post-noon follow-through"
                    default_focus = f"{EMOJI['bullet']} Focus: US cash open (15:30 CET) + volatility response"

                    msg1.append(noon_connection.get('noon_followup', default_followup))
                    msg1.append(noon_connection.get('focus_areas_update', default_focus))
                else:
                    msg1.append(f"{EMOJI['bullet']} Intraday bias validation: monitoring post-noon follow-through")
                    msg1.append(f"{EMOJI['bullet']} Focus: US cash open (15:30 CET) + volatility response")
            except Exception as e:
                log.warning(f"{EMOJI['warn']} [AFTERNOON-CONTINUITY] Error: {e}")
                msg1.append(f"{EMOJI['bullet']} Noon follow-up: intraday tracking active")

            msg1.append("")

            # Live snapshot (BTC always; SPX/EURUSD/GOLD when available)
            msg1.append(f"{EMOJI['chart_up']} *LIVE SNAPSHOT:*")
            assets_snapshot: Dict[str, Any] = {}
            try:
                from modules.engine.market_data import get_market_snapshot

                snap = get_market_snapshot(now) or {}
                assets_snapshot = snap.get('assets', {}) or {}
            except Exception as qe:
                log.warning(f"{EMOJI['warn']} [AFTERNOON-SNAPSHOT] Market snapshot unavailable: {qe}")
                assets_snapshot = {}

            # BTC
            try:
                crypto = get_live_crypto_prices() or {}
            except Exception:
                crypto = {}
            btc = crypto.get('BTC', {}) if isinstance(crypto, dict) else {}
            btc_price = float(btc.get('price', 0) or 0.0)
            btc_chg = float(btc.get('change_pct', 0) or 0.0)
            if btc_price > 0:
                msg1.append(f"{EMOJI['bullet']} {EMOJI['btc']} *BTC*: ${btc_price:,.0f} ({btc_chg:+.1f}%)")
            else:
                msg1.append(f"{EMOJI['bullet']} {EMOJI['btc']} *BTC*: Live data unavailable")

            # SPX
            spx = assets_snapshot.get('SPX', {}) if isinstance(assets_snapshot, dict) else {}
            spx_price = float(spx.get('price', 0) or 0.0)
            spx_chg = spx.get('change_pct', None)
            if spx_price > 0 and spx_chg is not None:
                msg1.append(f"{EMOJI['bullet']} {EMOJI['us_flag']} *S&P 500*: {int(spx_price)} ({float(spx_chg):+.1f}%)")
            elif spx_price > 0:
                msg1.append(f"{EMOJI['bullet']} {EMOJI['us_flag']} *S&P 500*: {int(spx_price)} (snapshot)")
            else:
                msg1.append(f"{EMOJI['bullet']} {EMOJI['us_flag']} *S&P 500*: Live tracking")

            # EURUSD
            eur = assets_snapshot.get('EURUSD', {}) if isinstance(assets_snapshot, dict) else {}
            eur_price = float(eur.get('price', 0) or 0.0)
            eur_chg = eur.get('change_pct', None)
            if eur_price > 0 and eur_chg is not None:
                msg1.append(f"{EMOJI['bullet']} {EMOJI['eu_flag']} *EUR/USD*: {eur_price:.3f} ({float(eur_chg):+.1f}%)")
            elif eur_price > 0:
                msg1.append(f"{EMOJI['bullet']} {EMOJI['eu_flag']} *EUR/USD*: {eur_price:.3f} (snapshot)")
            else:
                msg1.append(f"{EMOJI['bullet']} {EMOJI['eu_flag']} *EUR/USD*: Live tracking")

            # GOLD (USD/gram)
            gold = assets_snapshot.get('GOLD', {}) if isinstance(assets_snapshot, dict) else {}
            gold_g = float(gold.get('price', 0) or 0.0)
            gold_chg = gold.get('change_pct', None)
            if gold_g > 0 and gold_chg is not None:
                gold_str = f"${gold_g:,.2f}/g" if gold_g >= 1 else f"${gold_g:.3f}/g"
                msg1.append(f"{EMOJI['bullet']} *Gold*: {gold_str} ({float(gold_chg):+.1f}%)")
            elif gold_g > 0:
                gold_str = f"${gold_g:,.2f}/g" if gold_g >= 1 else f"${gold_g:.3f}/g"
                msg1.append(f"{EMOJI['bullet']} *Gold*: {gold_str} (snapshot)")
            else:
                msg1.append(f"{EMOJI['bullet']} *Gold*: Live tracking")

            msg1.append("")

            # News impact (Top 3)
            try:
                news_list = news_data.get('news', []) if isinstance(news_data, dict) else []
                if news_list:
                    # optional filtering
                    filtered = []
                    for it in news_list:
                        title = (it.get('title') or '')
                        try:
                            if hasattr(ctx, '_is_personal_finance') and ctx._is_personal_finance(title):
                                continue
                            if hasattr(ctx, '_is_low_impact_gadget_or_lifestyle') and ctx._is_low_impact_gadget_or_lifestyle(title):
                                continue
                        except Exception:
                            pass
                        filtered.append(it)
                    if filtered:
                        news_list = filtered

                    msg1.append(f"{EMOJI['news']} *NEWS IMPACT SINCE NOON (Top 3):*")
                    enriched = []
                    for item in news_list:
                        title = item.get('title', 'News update')
                        hours_ago = item.get('hours_ago', item.get('published_hours_ago', 2))
                        try:
                            hours_ago = int(hours_ago)
                        except Exception:
                            hours_ago = 2
                        impact = ctx._analyze_news_impact_detailed(title, published_ago_hours=hours_ago) if hasattr(ctx, '_analyze_news_impact_detailed') else {'impact_score': 0, 'catalyst_type': 'News', 'time_relevance': 'Recent', 'sectors': []}
                        enriched.append((impact.get('impact_score', 0), title, item, impact))
                    enriched.sort(key=lambda x: x[0], reverse=True)
                    for i, (_, title, item, impact) in enumerate(enriched[:3], 1):
                        short = title if len(title) <= 80 else title[:80] + '...'
                        source = item.get('source', 'News')
                        link = item.get('link', '')
                        sectors = ', '.join((impact.get('sectors') or [])[:2]) or 'Broad Market'
                        msg1.append(f"{EMOJI['bullet']} {i}. {short}")
                        msg1.append(f"   {EMOJI['chart']} Impact: {impact.get('impact_score', 0):.1f}/10 ({impact.get('catalyst_type', 'News')}) {EMOJI['folder']} {source}")
                        if link:
                            msg1.append(f"   {EMOJI['link']} {link}")
                        msg1.append(f"   {EMOJI['clock']} {impact.get('time_relevance', 'Recent')} {EMOJI['target']} Sectors: {sectors}")
                        try:
                            if hasattr(ctx, '_mark_news_used'):
                                ctx._mark_news_used(item, now)
                        except Exception:
                            pass
                    msg1.append("")
            except Exception as e:
                log.warning(f"{EMOJI['warn']} [AFTERNOON-NEWS] Error: {e}")

            market_status = fallback_data.get('market_status', 'ACTIVE')
            msg1.append(f"{EMOJI['bank']} *Market Status*: {market_status}")
            msg1.append("")

            msg1.append(EMOJI['line'] * 40)
            msg1.append(f"{EMOJI['robot']} SV Enhanced {EMOJI['bullet']} Afternoon 1/3")

            messages.append("\n".join(msg1))
            log.info(f"{EMOJI['check']} [AFTERNOON] Message 1 generated")
        except Exception as e:
            log.error(f"{EMOJI['cross']} [AFTERNOON] Message 1 error: {e}")
            messages.append(f"{EMOJI['sun']} *SV - AFTERNOON UPDATE*\n{EMOJI['calendar']} {now.strftime('%H:%M')} {EMOJI['bullet']} System loading")

        # === MESSAGE 2: ML CHECKPOINT ===
        afternoon_prediction_eval: Dict[str, Any] = {}
        try:
            msg2: List[str] = []
            msg2.append(f"{EMOJI['brain']} *SV - ML CHECKPOINT* `{now.strftime('%H:%M')}`")
            msg2.append(f"{EMOJI['calendar']} {now.strftime('%A %m/%d/%Y')} {EMOJI['bullet']} Message 2/3")
            msg2.append(f"{EMOJI['bullet']} Live prediction evaluation + regime update")
            msg2.append(EMOJI['line'] * 40)
            msg2.append("")

            # Live evaluation
            try:
                afternoon_prediction_eval = ctx._evaluate_predictions_with_live_data(now) if hasattr(ctx, '_evaluate_predictions_with_live_data') else {}
                afternoon_prediction_eval = afternoon_prediction_eval or {}
            except Exception as eval_e:
                log.warning(f"{EMOJI['warn']} [AFTERNOON-ML] Live eval error: {eval_e}")
                afternoon_prediction_eval = {}

            total_tracked = int(afternoon_prediction_eval.get('total_tracked', 0) or 0)
            hits = int(afternoon_prediction_eval.get('hits', 0) or 0)
            acc = float(afternoon_prediction_eval.get('accuracy_pct', 0.0) or 0.0)

            if total_tracked > 0:
                msg2.append(f"{EMOJI['bullet']} *Live-tracked predictions*: {hits}/{total_tracked} hits ({acc:.0f}% accuracy)")
            else:
                msg2.append(f"{EMOJI['bullet']} *Live-tracked predictions*: n/a (insufficient closed predictions yet)")

            # Regime summary via BRAIN helper (consistent with Noon/Evening/Summary)
            try:
                from modules.brain.regime_detection import get_regime_summary

                tracking = ctx._load_sentiment_tracking(now) if hasattr(ctx, '_load_sentiment_tracking') else {}
                afternoon_sentiment = (
                    news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL')
                    if isinstance(news_data, dict)
                    else 'NEUTRAL'
                )
                sentiment_payload: Any = tracking if isinstance(tracking, dict) and tracking else {'afternoon': afternoon_sentiment}

                regime_summary = get_regime_summary(afternoon_prediction_eval, sentiment_payload)
                regime_label = regime_summary.get('regime_label', 'NEUTRAL')
                conf_pct = int(regime_summary.get('confidence_pct', 60) or 60)
                tone = str(regime_summary.get('tone', 'limited live history') or 'limited live history')

                msg2.append(f"{EMOJI['bullet']} *Regime*: {regime_label} ({conf_pct}% confidence, {tone})")
                msg2.append(f"{EMOJI['bullet']} *Position sizing*: {regime_summary.get('position_sizing', 'Standard allocation')}")
                msg2.append(f"{EMOJI['bullet']} *Risk management*: {regime_summary.get('risk_management', 'Balanced tactical approach')}")
            except Exception as re:
                log.warning(f"{EMOJI['warn']} [AFTERNOON-REGIME] Error: {re}")
                msg2.append(f"{EMOJI['bullet']} *Regime*: Update unavailable - monitoring")

            msg2.append("")
            msg2.append(EMOJI['line'] * 40)
            msg2.append(f"{EMOJI['robot']} SV Enhanced {EMOJI['bullet']} ML Checkpoint 2/3")

            messages.append("\n".join(msg2))
            log.info(f"{EMOJI['check']} [AFTERNOON] Message 2 generated")
        except Exception as e:
            log.error(f"{EMOJI['cross']} [AFTERNOON] Message 2 error: {e}")
            messages.append(f"{EMOJI['brain']} *SV - ML CHECKPOINT*\n{EMOJI['calendar']} {now.strftime('%H:%M')} {EMOJI['bullet']} System loading")

        # === MESSAGE 3: NEXT STEPS ===
        try:
            msg3: List[str] = []
            msg3.append(f"{EMOJI['target']} *SV - ACTION PLAN* `{now.strftime('%H:%M')}`")
            msg3.append(f"{EMOJI['calendar']} {now.strftime('%A %m/%d/%Y')} {EMOJI['bullet']} Message 3/3")
            msg3.append(f"{EMOJI['bullet']} Risk controls + upcoming checkpoints")
            msg3.append(EMOJI['line'] * 40)
            msg3.append("")

            # Key reminders
            msg3.append(f"{EMOJI['shield']} *RISK CONTROLS:*")
            msg3.append(f"{EMOJI['bullet']} Avoid overtrading into US open volatility")
            msg3.append(f"{EMOJI['bullet']} Respect stops and position sizing")
            msg3.append(f"{EMOJI['bullet']} Prioritize high-impact catalysts only")
            msg3.append("")

            msg3.append(f"{EMOJI['clock']} *NEXT CHECKPOINTS (Italy time):*")
            msg3.append(f"{EMOJI['bullet']} *18:00 Evening Analysis*: Session wrap + performance review")
            msg3.append(f"{EMOJI['bullet']} *21:00 Daily Summary*: Complete day analysis (6 pages)")
            msg3.append(f"{EMOJI['bullet']} *00:00 Night Report*: After-hours + Asia handoff")
            msg3.append(f"{EMOJI['bullet']} *03:00 Late Night*: Asia session check")
            msg3.append(f"{EMOJI['bullet']} *06:00 Press Review*: Macro + news intelligence")
            msg3.append("")

            msg3.append(EMOJI['line'] * 40)
            msg3.append(f"{EMOJI['robot']} SV Enhanced {EMOJI['bullet']} Afternoon Complete 3/3")

            messages.append("\n".join(msg3))
            log.info(f"{EMOJI['check']} [AFTERNOON] Message 3 generated")
        except Exception as e:
            log.error(f"{EMOJI['cross']} [AFTERNOON] Message 3 error: {e}")
            messages.append(f"{EMOJI['target']} *SV - ACTION PLAN*\n{EMOJI['calendar']} {now.strftime('%H:%M')} {EMOJI['bullet']} System loading")

        # Save content + engine stage
        if messages:
            saved_path = ctx.save_content(
                "afternoon_update",
                messages,
                {
                    'total_messages': len(messages),
                    'enhanced_features': ['Market Snapshot', 'ML Checkpoint', 'Action Plan'],
                    'news_count': len(news_data.get('news', [])) if isinstance(news_data, dict) else 0,
                    'sentiment': news_data.get('sentiment', {}) if isinstance(news_data, dict) else {},
                    'continuity_with_noon': True,
                },
            )
            log.info(f"{EMOJI['file']} [AFTERNOON] Saved to: {saved_path}")

            try:
                afternoon_sent = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL') if isinstance(news_data, dict) else 'NEUTRAL'
                assets_for_engine: Dict[str, Any] = {}
                try:
                    from modules.engine.market_data import get_market_snapshot

                    snap2 = get_market_snapshot(now) or {}
                    assets_for_engine = snap2.get('assets', {}) or {}
                except Exception as md_e:
                    log.warning(f"{EMOJI['warning']} [ENGINE-AFTERNOON] Snapshot error: {md_e}")
                ctx._engine_log_stage('afternoon', now, afternoon_sent, assets_for_engine, afternoon_prediction_eval or {})
            except Exception as e:
                log.warning(f"{EMOJI['warning']} [ENGINE-AFTERNOON] Error logging stage: {e}")

        # Save sentiment
        try:
            afternoon_sent = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL') if isinstance(news_data, dict) else 'NEUTRAL'
            ctx._save_sentiment_for_stage('afternoon', afternoon_sent, now)
        except Exception as e:
            log.warning(f"[SENTIMENT-TRACKING] Error in afternoon: {e}")

        log.info(f"{EMOJI['check']} [AFTERNOON] Completed generation of {len(messages)} afternoon messages")
        return messages

    except Exception as e:
        log.error(f"{EMOJI['cross']} [AFTERNOON] General error: {e}")
        return [f"{EMOJI['sun']} *SV - AFTERNOON UPDATE*\n{EMOJI['calendar']} {_now_it().strftime('%H:%M')} {EMOJI['bullet']} System under maintenance"]
