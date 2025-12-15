# Intraday generator for the Night block.
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


def generate_night_report(ctx) -> List[str]:
    """NIGHT REPORT 00:00 - 1 message

    After-hours / crypto-focused handoff into Asia session.
    """
    try:
        log.info(f"{EMOJI['night']} [NIGHT] Generating night report...")

        now = _now_it()
        news_data = get_enhanced_news(content_type="night", max_news=5)
        fallback_data = get_fallback_data()

        parts: List[str] = []
        parts.append(f"{EMOJI['night']} *SV - NIGHT REPORT* `{now.strftime('%H:%M')}`")
        parts.append(f"{EMOJI['calendar']} {now.strftime('%A %m/%d/%Y')}")
        parts.append(f"{EMOJI['bullet']} Start of the 24/7 cycle (Asia session focus)")
        parts.append(EMOJI['line'] * 40)
        parts.append("")

        # High-level context
        market_status = fallback_data.get('market_status', 'CLOSED')
        parts.append(f"{EMOJI['world']} *GLOBAL CONTEXT:*")
        parts.append(f"{EMOJI['bullet']} Market status: {market_status}")
        parts.append(f"{EMOJI['bullet']} Focus: Asia liquidity + crypto momentum")
        parts.append("")

        # Crypto snapshot
        parts.append(f"{EMOJI['btc']} *CRYPTO SNAPSHOT (24/7):*")
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
        parts.append(_fmt('SOL', 2))
        parts.append("")

        # News pulse (compact)
        try:
            news_list = news_data.get('news', []) if isinstance(news_data, dict) else []
            if news_list:
                parts.append(f"{EMOJI['news']} *NEWS PULSE (Top 2):*")
                for i, item in enumerate(news_list[:2], 1):
                    title = item.get('title', 'News update')
                    short = title if len(title) <= 90 else title[:90] + '...'
                    parts.append(f"{EMOJI['bullet']} {i}. {short}")
                parts.append("")
        except Exception as e:
            log.warning(f"{EMOJI['warn']} [NIGHT-NEWS] Error: {e}")

        # Next checkpoints
        parts.append(f"{EMOJI['clock']} *NEXT CHECKPOINTS (Italy time):*")
        parts.append(f"{EMOJI['bullet']} *03:00 Late Night*: Asia session check")
        parts.append(f"{EMOJI['bullet']} *06:00 Press Review*: Macro + news intelligence")
        parts.append(f"{EMOJI['bullet']} *09:00 Morning*: Setup + predictions")
        parts.append("")

        parts.append(EMOJI['line'] * 40)
        parts.append(f"{EMOJI['robot']} SV Enhanced {EMOJI['bullet']} Night Report")

        message = "\n".join(parts)
        messages = [message]

        # Save + engine stage
        try:
            saved_path = ctx.save_content(
                "night_report",
                messages,
                {
                    'total_messages': 1,
                    'enhanced_features': ['Crypto Snapshot', 'Asia Handoff'],
                    'news_count': len(news_data.get('news', [])) if isinstance(news_data, dict) else 0,
                    'sentiment': news_data.get('sentiment', {}) if isinstance(news_data, dict) else {},
                },
            )
            log.info(f"{EMOJI['file']} [NIGHT] Saved to: {saved_path}")
        except Exception as e:
            log.warning(f"{EMOJI['warn']} [NIGHT] Error saving content: {e}")

        try:
            sentiment = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL') if isinstance(news_data, dict) else 'NEUTRAL'
            assets: Dict[str, Any] = {}
            try:
                from modules.engine.market_data import get_market_snapshot

                snap = get_market_snapshot(now) or {}
                assets = snap.get('assets', {}) or {}
            except Exception:
                assets = {}
            ctx._engine_log_stage('night', now, sentiment, assets, None)
        except Exception as e:
            log.warning(f"{EMOJI['warn']} [ENGINE-NIGHT] Error logging stage: {e}")

        try:
            sentiment = news_data.get('sentiment', {}).get('sentiment', 'NEUTRAL') if isinstance(news_data, dict) else 'NEUTRAL'
            ctx._save_sentiment_for_stage('night', sentiment, now)
        except Exception as e:
            log.warning(f"[SENTIMENT-TRACKING] Error in night: {e}")

        return messages

    except Exception as e:
        log.error(f"{EMOJI['cross']} [NIGHT] General error: {e}")
        return [f"{EMOJI['night']} *SV - NIGHT REPORT*\n{EMOJI['calendar']} {_now_it().strftime('%H:%M')} {EMOJI['bullet']} System under maintenance"]
