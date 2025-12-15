# Intraday generator for the Late Night block.
#
# New in the 3-hour SV schedule (00/03/06/09/12/15/18/21).

from typing import Any, Dict, List

from modules import daily_generator as dg

EMOJI = dg.EMOJI
log = dg.log
_now_it = dg._now_it
get_enhanced_news = dg.get_enhanced_news
get_fallback_data = dg.get_fallback_data
get_live_crypto_prices = dg.get_live_crypto_prices

# Optional dependency flags
DEPENDENCIES_AVAILABLE = getattr(dg, "DEPENDENCIES_AVAILABLE", False)


def generate_late_night_report(ctx) -> List[str]:
    """LATE NIGHT UPDATE 03:00 - 1 message

    Asia session checkpoint + prepare Press Review.
    """
    try:
        log.info(f"{EMOJI['night']} [LATE_NIGHT] Generating late night update...")

        now = _now_it()
        news_data = get_enhanced_news(content_type="late_night", max_news=5)
        fallback_data = get_fallback_data()

        parts: List[str] = []
        parts.append(f"{EMOJI['night']} *SV - LATE NIGHT UPDATE* `{now.strftime('%H:%M')}`")
        parts.append(f"{EMOJI['calendar']} {now.strftime('%A %m/%d/%Y')}")
        parts.append(f"{EMOJI['bullet']} Asia session checkpoint + pre-Europe prep")
        parts.append(EMOJI['line'] * 40)
        parts.append("")

        market_status = fallback_data.get('market_status', 'CLOSED')
        parts.append(f"{EMOJI['world']} *ASIA SESSION FOCUS:*")
        parts.append(f"{EMOJI['bullet']} Market status: {market_status}")
        parts.append(f"{EMOJI['bullet']} Watch: risk sentiment shift + FX/commodities reaction")
        parts.append("")

        parts.append(f"{EMOJI['btc']} *CRYPTO CHECK (24/7):*")
        try:
            crypto = get_live_crypto_prices() or {}
        except Exception:
            crypto = {}

        def _fmt(sym: str, decimals: int = 0) -> str:
            d = crypto.get(sym, {}) if isinstance(crypto, dict) else {}
            p = float(d.get('price', 0) or 0.0)
            c = float(d.get('change_pct', 0) or 0.0)
            if p <= 0:
                return f"{EMOJI['bullet']} *{sym}*: live data unavailable"
            if decimals == 0:
                return f"{EMOJI['bullet']} *{sym}*: ${p:,.0f} ({c:+.1f}%)"
            return f"{EMOJI['bullet']} *{sym}*: ${p:,.{decimals}f} ({c:+.1f}%)"

        parts.append(_fmt('BTC', 0))
        parts.append(_fmt('ETH', 0))
        parts.append("")

        # News pulse
        try:
            news_list = news_data.get('news', []) if isinstance(news_data, dict) else []
            if news_list:
                parts.append(f"{EMOJI['news']} *OVERNIGHT NEWS (Top 2):*")
                for i, item in enumerate(news_list[:2], 1):
                    title = item.get('title', 'News update')
                    short = title if len(title) <= 90 else title[:90] + '...'
                    parts.append(f"{EMOJI['bullet']} {i}. {short}")
                parts.append("")
        except Exception as e:
            log.warning(f"{EMOJI['warn']} [LATE_NIGHT-NEWS] Error: {e}")

        parts.append(f"{EMOJI['clock']} *NEXT CHECKPOINTS (Italy time):*")
        parts.append(f"{EMOJI['bullet']} *06:00 Press Review*: Macro + news intelligence")
        parts.append(f"{EMOJI['bullet']} *09:00 Morning*: Setup + predictions")
        parts.append("")

        parts.append(EMOJI['line'] * 40)
        parts.append(f"{EMOJI['robot']} SV Enhanced {EMOJI['bullet']} Late Night")

        message = "\n".join(parts)
        messages = [message]

        # Save + engine stage
        try:
            saved_path = ctx.save_content(
                "late_night_report",
                messages,
                {
                    'total_messages': 1,
                    'enhanced_features': ['Asia Checkpoint', 'Crypto Snapshot'],
                    'news_count': len(news_data.get('news', [])) if isinstance(news_data, dict) else 0,
                    'sentiment': news_data.get('sentiment', {}) if isinstance(news_data, dict) else {},
                },
            )
            log.info(f"{EMOJI['file']} [LATE_NIGHT] Saved to: {saved_path}")
        except Exception as e:
            log.warning(f"{EMOJI['warn']} [LATE_NIGHT] Error saving content: {e}")

        try:
            sentiment = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL') if isinstance(news_data, dict) else 'NEUTRAL'
            assets: Dict[str, Any] = {}
            try:
                from modules.engine.market_data import get_market_snapshot

                snap = get_market_snapshot(now) or {}
                assets = snap.get('assets', {}) or {}
            except Exception:
                assets = {}
            ctx._engine_log_stage('late_night', now, sentiment, assets, None)
        except Exception as e:
            log.warning(f"{EMOJI['warn']} [ENGINE-LATE_NIGHT] Error logging stage: {e}")

        try:
            sentiment = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL') if isinstance(news_data, dict) else 'NEUTRAL'
            ctx._save_sentiment_for_stage('late_night', sentiment, now)
        except Exception as e:
            log.warning(f"[SENTIMENT-TRACKING] Error in late_night: {e}")

        return messages

    except Exception as e:
        log.error(f"{EMOJI['cross']} [LATE_NIGHT] General error: {e}")
        return [f"{EMOJI['night']} *SV - LATE NIGHT UPDATE*\n{EMOJI['calendar']} {_now_it().strftime('%H:%M')} {EMOJI['bullet']} System under maintenance"]
