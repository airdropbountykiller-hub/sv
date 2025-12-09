#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Legacy helpers extracted from modules.daily_generator.DailyContentGenerator.

These functions are no longer used by the current ENGINE/BRAIN + intraday
pipeline but are kept here for reference and potential future reuse.

Moved on 2025-11-23 during dead-code cleanup.
"""

import datetime
import json
import logging
from typing import Dict, List, Any

# Basic logger for this legacy module
log = logging.getLogger(__name__)

# Timezone helper (mirrors daily_generator behaviour as closely as needed here)
try:  # pragma: no cover - tiny fallback logic
    import pytz
    ITALY_TZ = pytz.timezone("Europe/Rome")
except Exception:  # pragma: no cover
    ITALY_TZ = datetime.timezone.utc


def _now_it() -> datetime.datetime:
    """Get current time in Italian timezone (legacy copy)."""
    return datetime.datetime.now(ITALY_TZ)


# --- Top-level helpers originally defined in daily_generator.py ---

try:  # pragma: no cover - legacy dependency
    from modules.sv_emoji import EMOJI
except Exception:  # pragma: no cover
    EMOJI = {}  # type: ignore


def ensure_emoji_visible(text):
    """Ensure emoji are visible in logs and files, especially on Windows.
    This doesn't alter the emoji for Telegram, only makes them visible in logs.
    """
    if not text:
        return text

    # Use our clean emoji module for safe log display
    try:
        # Replace any EMOJI references with clean text for logs
        safe_text = text
        for emoji_name, emoji_char in EMOJI.items():
            if emoji_char in safe_text:
                safe_text = safe_text.replace(emoji_char, f":{emoji_name}:")
        return safe_text
    except Exception:
        # Fallback: remove any problematic characters
        try:
            # Keep only ASCII + basic Unicode for safe logging
            return text.encode("ascii", "ignore").decode("ascii")
        except Exception:
            return "[LOG_SAFE_TEXT]"


def _get_ml_coherence_context(content_type: str) -> Dict:
    """Get ML coherence context for improving message precision and coherence.

    Legacy copy of the helper that talked to ml_coherence_analyzer.
    """
    try:
        from ml_coherence_analyzer import get_message_context
        return get_message_context(content_type, 24)
    except ImportError:
        log.warning("[ML-COHERENCE] ML coherence analyzer not available")
        return {"coherence_suggestions": []}
    except Exception as e:
        log.warning(f"[ML-COHERENCE] Error getting context: {e}")
        return {"coherence_suggestions": []}


# --- Legacy DailyContentGenerator-style helpers (now as free functions) ---


def analyze_previous_content(self, content_type: str, days_back: int = 7) -> Dict:
    """Legacy copy of DailyContentGenerator.analyze_previous_content.

    It expects an object ``self`` with a ``reports_dir`` attribute compatible
    with the original DailyContentGenerator.
    """
    try:
        log.info(f"[ANALYSIS] Analyzing previous {content_type} content ({days_back} days)")

        # Get files from last N days
        now = _now_it()
        files_to_analyze = []

        for i in range(days_back):
            check_date = now - datetime.timedelta(days=i)
            date_pattern = check_date.strftime("%Y-%m-%d")

            # Find files matching pattern
            pattern_files = list(self.reports_dir.glob(f"{date_pattern}_*_{content_type}.json"))
            files_to_analyze.extend(pattern_files)

        if not files_to_analyze:
            log.warning(f"[ANALYSIS] No previous {content_type} files found")
            return {"status": "no_data", "files_analyzed": 0}

        # Analyze content patterns
        analysis: Dict[str, Any] = {
            "status": "success",
            "files_analyzed": len(files_to_analyze),
            "content_patterns": {},
            "performance_metrics": {},
            "improvement_suggestions": [],
        }

        total_messages = 0
        total_chars = 0
        avg_lengths: List[float] = []
        common_themes: Dict[str, int] = {}

        for filepath in files_to_analyze:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)

                total_messages += data.get("messages_count", 0)
                total_chars += data.get("total_chars", 0)
                avg_lengths.append(data.get("avg_msg_length", 0))

                # Extract themes from messages
                for message in data.get("messages", []):
                    # Simple keyword extraction (can be enhanced with NLP)
                    words = str(message).lower().split()
                    for word in words:
                        if len(word) > 5:  # Only meaningful words
                            common_themes[word] = common_themes.get(word, 0) + 1

            except Exception as e:  # pragma: no cover - legacy diagnostics
                log.warning(f"[ANALYSIS] Error reading {filepath}: {e}")

        # Compile analysis results
        analysis["performance_metrics"] = {
            "avg_messages_per_content": total_messages / len(files_to_analyze),
            "avg_chars_per_content": total_chars / len(files_to_analyze),
            "avg_message_length": sum(avg_lengths) / len(avg_lengths) if avg_lengths else 0,
            "consistency_score": _calculate_consistency_score(self, avg_lengths),
        }

        # Top themes
        top_themes = sorted(common_themes.items(), key=lambda x: x[1], reverse=True)[:10]
        analysis["content_patterns"]["top_themes"] = top_themes

        # Generate improvement suggestions
        analysis["improvement_suggestions"] = _generate_improvement_suggestions(self, analysis)

        log.info(f"[ANALYSIS] Completed analysis of {len(files_to_analyze)} files")
        return analysis

    except Exception as e:  # pragma: no cover - legacy diagnostics
        log.error(f"[ANALYSIS] Error analyzing content: {e}")
        return {"status": "error", "error": str(e)}


def _calculate_consistency_score(self, lengths: List[float]) -> float:
    """Calculate consistency score based on message length variation (legacy)."""
    if not lengths or len(lengths) < 2:
        return 1.0

    import statistics

    mean_length = statistics.mean(lengths)
    std_dev = statistics.stdev(lengths)

    # Lower std deviation = higher consistency
    consistency = max(0.0, 1.0 - (std_dev / mean_length) if mean_length > 0 else 0.0)
    return min(1.0, consistency)


def _generate_improvement_suggestions(self, analysis: Dict) -> List[str]:
    """Generate improvement suggestions based on content analysis (legacy)."""
    suggestions: List[str] = []

    metrics = analysis.get("performance_metrics", {})
    avg_length = metrics.get("avg_message_length", 0)
    consistency = metrics.get("consistency_score", 1.0)

    # Length-based suggestions
    if avg_length < 200:
        suggestions.append("Consider adding more detailed analysis to messages")
    elif avg_length > 800:
        suggestions.append("Consider breaking down longer messages for better readability")

    # Consistency-based suggestions
    if consistency < 0.7:
        suggestions.append("Improve consistency in message structure and length")

    # Theme-based suggestions
    themes = analysis.get("content_patterns", {}).get("top_themes", [])
    if themes:
        top_theme = themes[0][0]
        suggestions.append(f"Consider varying content focus - '{top_theme}' appears frequently")

    # Default suggestions if none generated
    if not suggestions:
        suggestions.append("Content quality is good - maintain current standards")

    return suggestions


def _load_press_review_predictions(self, now):
    """Load ML predictions from Press Review at 07:00 of the same day (legacy)."""
    try:
        date_str = now.strftime("%Y-%m-%d")
        press_review_file = self.reports_dir / f"press_review_{date_str}.json"

        if press_review_file.exists():
            log.info(f"[ML-VERIFY] Loading ML predictions from: {press_review_file.name}")
            with open(press_review_file, "r", encoding="utf-8") as f:
                press_review_data = json.load(f)

            # Extract ML predictions from first message (ML Analysis)
            ml_predictions = press_review_data.get("metadata", {}).get("ml_predictions", {})
            if not ml_predictions and press_review_data.get("content"):
                # Fallback: analyze content to extract predictions
                ml_predictions = _extract_predictions_from_content(self, press_review_data["content"])

            log.info(f"[ML-VERIFY] Found {len(ml_predictions)} ML predictions from morning press review")
            return ml_predictions
        else:
            log.warning(f"[ML-VERIFY] Press review file not found: {press_review_file}")
            return {}

    except Exception as e:  # pragma: no cover - legacy diagnostics
        log.error(f"[ML-VERIFY] Error loading press review: {e}")
        return {}


def _extract_predictions_from_content(self, content):
    """Extract ML predictions from press review text content (legacy)."""
    predictions: Dict[str, Any] = {}
    try:
        # Search for prediction patterns in content
        if isinstance(content, list) and len(content) > 0:
            ml_content = content[0]  # First message = ML Analysis

            # Pattern comuni per BTC
            if "BTC" in ml_content or "Bitcoin" in ml_content:
                predictions["BTC"] = {"predicted": "NEUTRAL", "confidence": 65}

            # Pattern per S&P 500
            if "S&P" in ml_content or "SPX" in ml_content:
                predictions["SP500"] = {"predicted": "BULLISH", "confidence": 70}

            # Pattern per EUR/USD
            if "EUR" in ml_content or "EURUSD" in ml_content:
                predictions["EURUSD"] = {"predicted": "BEARISH", "confidence": 72}

    except Exception as e:  # pragma: no cover - legacy diagnostics
        log.warning(f"[EXTRACT-PREDICTIONS] Error: {e}")

    return predictions


def generate_weekly_verification(self) -> Dict:
    """Legacy copy of DailyContentGenerator.generate_weekly_verification."""
    try:
        log.info("[WEEKLY-VERIFICATION] Inizio verifica gerarchica weekly...")

        now = _now_it()
        week_start = now - datetime.timedelta(days=now.weekday())  # Monday

        weekly_results: Dict[str, Any] = {
            "week_period": f"{week_start.strftime('%Y-%m-%d')} to "
                           f"{(week_start + datetime.timedelta(days=6)).strftime('%Y-%m-%d')}",
            "total_content_analyzed": 0,
            "daily_accuracy_scores": {},
            "prediction_verification": {},
            "coherence_analysis": {},
            "weekly_summary": {},
            "improvement_areas": [],
        }

        # Analyze each day of the week
        for day_offset in range(7):
            current_day = week_start + datetime.timedelta(days=day_offset)
            date_str = current_day.strftime("%Y-%m-%d")
            day_name = current_day.strftime("%A")

            log.info(f"[WEEKLY] Analyzing {day_name} ({date_str})...")

            # Load all 5 contents of the day
            daily_files = [
                f"press_review_{date_str}.json",
                f"morning_report_{date_str}.json",
                f"noon_update_{date_str}.json",
                f"evening_analysis_{date_str}.json",
                f"daily_summary_{date_str}.json",
            ]

            daily_content_count = 0
            daily_predictions: List[Any] = []
            daily_coherence: List[float] = []

            for filename in daily_files:
                file_path = self.reports_dir / filename
                if file_path.exists():
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content_data = json.load(f)

                        daily_content_count += 1

                        # Extract ML predictions if present
                        metadata = content_data.get("metadata", {})
                        if "ml_predictions" in metadata:
                            daily_predictions.extend(metadata["ml_predictions"])

                        # Evaluate content coherence
                        if "content" in content_data:
                            coherence_score = _evaluate_content_quality(self, content_data["content"])
                            daily_coherence.append(coherence_score)

                    except Exception as e:  # pragma: no cover - legacy diagnostics
                        log.warning(f"[WEEKLY] Error loading {filename}: {e}")

            # Save daily results
            weekly_results["daily_accuracy_scores"][day_name] = {
                "content_count": daily_content_count,
                "expected_count": 5,
                "completion_rate": (daily_content_count / 5) * 100,
                "avg_coherence": sum(daily_coherence) / len(daily_coherence) if daily_coherence else 0.0,
                "prediction_count": len(daily_predictions),
            }

            weekly_results["total_content_analyzed"] += daily_content_count

        # Aggregate weekly metrics
        total_expected = 7 * 5  # 35 total contents
        completion_rate = (weekly_results["total_content_analyzed"] / total_expected) * 100

        daily_scores = [
            score["avg_coherence"]
            for score in weekly_results["daily_accuracy_scores"].values()
            if score["avg_coherence"] > 0
        ]
        weekly_avg_accuracy = sum(daily_scores) / len(daily_scores) if daily_scores else 0.0

        weekly_results["weekly_summary"] = {
            "completion_rate": completion_rate,
            "average_accuracy": weekly_avg_accuracy,
            "best_day": max(
                weekly_results["daily_accuracy_scores"].items(),
                key=lambda x: x[1]["avg_coherence"],
                default=("N/A", {"avg_coherence": 0}),
            )[0],
            "worst_day": min(
                weekly_results["daily_accuracy_scores"].items(),
                key=lambda x: x[1]["avg_coherence"],
                default=("N/A", {"avg_coherence": 0}),
            )[0],
            "total_predictions": sum(
                score["prediction_count"] for score in weekly_results["daily_accuracy_scores"].values()
            ),
        }

        # Improvement areas
        if completion_rate < 90:
            weekly_results["improvement_areas"].append(
                f"Completamento contenuti: {completion_rate:.1f}% < 90%"
            )
        if weekly_avg_accuracy < 0.8:
            weekly_results["improvement_areas"].append(
                f"Accuracy media: {weekly_avg_accuracy:.1%} < 80%"
            )

        week_file = self.reports_dir / f"weekly_verification_{week_start.strftime('%Y-W%W')}.json"
        with open(week_file, "w", encoding="utf-8") as f:
            json.dump(weekly_results, f, indent=2, ensure_ascii=False)

        log.info(
            f"[WEEKLY-VERIFICATION] Completed: "
            f"{weekly_results['total_content_analyzed']}/35 contents, {weekly_avg_accuracy:.1%} accuracy"
        )
        log.info(f"[WEEKLY-VERIFICATION] Saved to: {week_file}")

        return weekly_results

    except Exception as e:  # pragma: no cover - legacy diagnostics
        log.error(f"[WEEKLY-VERIFICATION] Error: {e}")
        return {"error": str(e)}


def _evaluate_content_quality(self, content):
    """Valuta qualità del content per scoring di coerenza (legacy)."""
    try:
        if isinstance(content, list):
            content_text = " ".join(str(item) for item in content)
        else:
            content_text = str(content)

        # Metriche base qualità
        word_count = len(content_text.split())

        # Penalità per contenuti troppo corti
        if word_count < 50:
            return 0.3
        elif word_count < 100:
            return 0.6

        # Bonus per termini finanziari
        financial_terms = ["market", "trading", "analysis", "btc", "bitcoin", "eur", "usd", "prediction"]
        financial_count = sum(1 for term in financial_terms if term.lower() in content_text.lower())
        financial_bonus = min(0.3, financial_count * 0.05)

        # Score base + bonus
        base_score = 0.7  # Score base per contenuti normali
        return min(1.0, base_score + financial_bonus)

    except Exception:  # pragma: no cover - legacy diagnostics
        return 0.5  # Neutral score in case of error


def generate_monthly_verification(self) -> Dict:
    """Legacy copy of DailyContentGenerator.generate_monthly_verification."""
    try:
        log.info("[MONTHLY-VERIFICATION] Inizio verifica gerarchica monthly...")

        now = _now_it()
        month_start = now.replace(day=1)
        if now.month == 12:
            month_end = now.replace(year=now.year + 1, month=1, day=1) - datetime.timedelta(days=1)
        else:
            month_end = now.replace(month=now.month + 1, day=1) - datetime.timedelta(days=1)

        monthly_results: Dict[str, Any] = {
            "month_period": f"{month_start.strftime('%Y-%m-%d')} to {month_end.strftime('%Y-%m-%d')}",
            "total_content_analyzed": 0,
            "weekly_summaries": {},
            "monthly_trends": {},
            "prediction_accuracy_evolution": {},
            "coherence_progression": {},
            "monthly_summary": {},
            "strategic_insights": [],
        }

        current_week_start = month_start - datetime.timedelta(days=month_start.weekday())
        weeks_analyzed = 0
        total_weekly_accuracy = 0.0
        total_weekly_content = 0

        while current_week_start <= month_end:
            week_id = current_week_start.strftime("%Y-W%W")
            week_file = self.reports_dir / f"weekly_verification_{week_id}.json"

            if week_file.exists():
                try:
                    with open(week_file, "r", encoding="utf-8") as f:
                        weekly_data = json.load(f)

                    week_name = f"Week {weeks_analyzed + 1}"
                    monthly_results["weekly_summaries"][week_name] = {
                        "period": weekly_data.get("week_period", "N/A"),
                        "completion_rate": weekly_data.get("weekly_summary", {}).get("completion_rate", 0),
                        "average_accuracy": weekly_data.get("weekly_summary", {}).get("average_accuracy", 0),
                        "total_content": weekly_data.get("total_content_analyzed", 0),
                        "best_day": weekly_data.get("weekly_summary", {}).get("best_day", "N/A"),
                        "worst_day": weekly_data.get("weekly_summary", {}).get("worst_day", "N/A"),
                        "improvement_areas": weekly_data.get("improvement_areas", []),
                    }

                    weeks_analyzed += 1
                    week_accuracy = weekly_data.get("weekly_summary", {}).get("average_accuracy", 0)
                    week_content = weekly_data.get("total_content_analyzed", 0)

                    total_weekly_accuracy += week_accuracy
                    total_weekly_content += week_content
                    monthly_results["total_content_analyzed"] += week_content

                    log.info(
                        f"[MONTHLY] Processed {week_name}: {week_content} contents, {week_accuracy:.1%} accuracy"
                    )

                except Exception as e:  # pragma: no cover - legacy diagnostics
                    log.warning(f"[MONTHLY] Error loading weekly file {week_file}: {e}")

            current_week_start += datetime.timedelta(days=7)

            # Safety limit to avoid infinite loops
            if weeks_analyzed >= 6:  # Max 6 weeks per month
                break

        if weeks_analyzed > 0:
            monthly_avg_accuracy = total_weekly_accuracy / weeks_analyzed
            expected_content = weeks_analyzed * 35  # 35 contents per week
            monthly_completion_rate = (
                (total_weekly_content / expected_content * 100) if expected_content > 0 else 0
            )

            weekly_accuracies = [
                summary["average_accuracy"]
                for summary in monthly_results["weekly_summaries"].values()
                if summary["average_accuracy"] > 0
            ]
            if len(weekly_accuracies) >= 2:
                trend_direction = (
                    "IMPROVING"
                    if weekly_accuracies[-1] > weekly_accuracies[0]
                    else "DECLINING"
                    if weekly_accuracies[-1] < weekly_accuracies[0]
                    else "STABLE"
                )
                trend_magnitude = abs(weekly_accuracies[-1] - weekly_accuracies[0])
            else:
                trend_direction = "INSUFFICIENT_DATA"
                trend_magnitude = 0.0

            monthly_results["monthly_trends"] = {
                "accuracy_trend": trend_direction,
                "trend_magnitude": trend_magnitude,
                "consistency_score": 1.0 - (max(weekly_accuracies) - min(weekly_accuracies))
                if weekly_accuracies
                else 0.0,
                "performance_volatility": "LOW"
                if trend_magnitude < 0.1
                else "MEDIUM"
                if trend_magnitude < 0.2
                else "HIGH",
            }

            monthly_results["monthly_summary"] = {
                "weeks_analyzed": weeks_analyzed,
                "total_content_expected": expected_content,
                "total_content_actual": total_weekly_content,
                "completion_rate": monthly_completion_rate,
                "average_accuracy": monthly_avg_accuracy,
                "best_week": max(
                    monthly_results["weekly_summaries"].items(),
                    key=lambda x: x[1]["average_accuracy"],
                    default=("N/A", {"average_accuracy": 0}),
                )[0],
                "worst_week": min(
                    monthly_results["weekly_summaries"].items(),
                    key=lambda x: x[1]["average_accuracy"],
                    default=("N/A", {"average_accuracy": 0}),
                )[0],
                "trend_direction": trend_direction,
            }

            if monthly_completion_rate >= 95:
                monthly_results["strategic_insights"].append(
                    "Excellent content completion rate - maintain standards"
                )
            elif monthly_completion_rate >= 85:
                monthly_results["strategic_insights"].append(
                    "Good completion rate - minor optimization needed"
                )
            else:
                monthly_results["strategic_insights"].append(
                    f"Low completion rate ({monthly_completion_rate:.1f}%) - review content pipeline"
                )

            if monthly_avg_accuracy >= 0.9:
                monthly_results["strategic_insights"].append(
                    "Outstanding accuracy - quality leadership achieved"
                )
            elif monthly_avg_accuracy >= 0.8:
                monthly_results["strategic_insights"].append(
                    "Strong accuracy performance - continue current approach"
                )
            else:
                monthly_results["strategic_insights"].append(
                    f"Accuracy needs improvement ({monthly_avg_accuracy:.1%}) - review ML models"
                )

            if trend_direction == "IMPROVING":
                monthly_results["strategic_insights"].append(
                    "Positive trend detected - scaling successful strategies"
                )
            elif trend_direction == "DECLINING":
                monthly_results["strategic_insights"].append(
                    "Declining trend - investigate root causes"
                )

        else:
            monthly_results["monthly_summary"] = {
                "weeks_analyzed": 0,
                "message": "No weekly verification files found for this month",
            }
            monthly_results["strategic_insights"].append(
                "No weekly data available - ensure weekly verification is running"
            )

        month_file = self.reports_dir / f"monthly_verification_{now.strftime('%Y-%m')}.json"
        with open(month_file, "w", encoding="utf-8") as f:
            json.dump(monthly_results, f, indent=2, ensure_ascii=False)

        if weeks_analyzed > 0:
            log.info(
                f"[MONTHLY-VERIFICATION] Completed: {weeks_analyzed} weeks, "
                f"{total_weekly_content} contents, {monthly_avg_accuracy:.1%} accuracy"
            )
        else:
            log.warning(
                f"[MONTHLY-VERIFICATION] No weekly data found for month {now.strftime('%Y-%m')}"
            )

        log.info(f"[MONTHLY-VERIFICATION] Saved to: {month_file}")
        return monthly_results

    except Exception as e:  # pragma: no cover - legacy diagnostics
        log.error(f"[MONTHLY-VERIFICATION] Error: {e}")
        return {"error": str(e)}
