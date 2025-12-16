#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SV Coherence Manager

Aggregates daily coherence and accuracy metrics across days.

Design goals (phase 1):
- Read structured daily journal JSON produced by DailyContentGenerator
  (reports/8_daily_content/10_daily_journal/journal_YYYY-MM-DD.json).
- Read prediction files (reports/1_daily/predictions_YYYY-MM-DD.json).
- Produce per-day JSON metrics files under:
    config/ml_analysis/coherence_YYYY-MM-DD.json
    config/daily_contexts/context_YYYY-MM-DD.json
- Produce a rolling history file with last N days:
    config/ml_analysis/coherence_history.json

This module does NOT generate messages; it only consolidates metrics
for Engine/Brain and offline analysis.
"""

from __future__ import annotations

import datetime as _dt
import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any

from config import sv_paths

log = logging.getLogger(__name__)


ITALY_TZ = _dt.timezone(_dt.timedelta(hours=1))  # simple CET; SV already uses Europe/Rome elsewhere


def _today_it() -> _dt.date:
    """Return today's date in Italian time (approx, non-DST-aware)."""
    return _dt.datetime.now(ITALY_TZ).date()


@dataclass
class DailyCoherenceMetrics:
    date: str
    coherence_score: float
    daily_accuracy: float
    messages_sent: int
    pages_generated: int
    sentiment_evolution: str
    news_volume: int
    predictions_count: int
    sources: Dict[str, str]


@dataclass
class DailyContextSnapshot:
    date: str
    market_story: str
    narrative_character: str
    key_turning_points: str
    lessons_learned: List[str]
    tomorrow_prep: Dict[str, Any]
    raw_sentiment: str


class CoherenceManager:
    """Coherence Manager: reads per-day artifacts and writes aggregate metrics.

    This class operates on *existing* outputs of the system (journal, predictions, etc.)
    and does not change message generation. It is safe to run after the Daily Summary
    has been produced.
    """

    def __init__(self, project_root: Optional[Path] = None) -> None:
        if project_root is None:
            # modules/coherence_manager.py -> project root
            project_root = Path(__file__).resolve().parent.parent
        self.project_root = project_root

        self.reports_dir = self.project_root / "reports" / "8_daily_content"
        self.journal_dir = self.reports_dir / "10_daily_journal"
        self.pred_dir = self.project_root / "reports" / "1_daily"

        self.analysis_dir = Path(sv_paths.ML_ANALYSIS_DIR)
        self.context_dir = Path(sv_paths.DAILY_CONTEXTS_DIR)
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        self.context_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Core per-day analysis
    # ------------------------------------------------------------------

    def analyze_day(self, date: Optional[_dt.date] = None) -> Optional[Dict[str, Any]]:
        """Analyze a single day and write per-day metrics/context files.

        Returns a dict with metrics, or None if no journal exists for that date.
        """
        if date is None:
            date = _today_it()
        date_str = date.strftime("%Y-%m-%d")

        journal_file = self.journal_dir / f"journal_{date_str}.json"
        if not journal_file.exists():
            log.warning(f"[COHERENCE] No journal file found for {date_str}: {journal_file}")
            return None

        try:
            with open(journal_file, "r", encoding="utf-8") as jf:
                journal = json.load(jf)
        except Exception as e:
            log.error(f"[COHERENCE] Error reading journal {journal_file}: {e}")
            return None

        # Optional predictions
        pred_file = self.pred_dir / f"predictions_{date_str}.json"
        preds: List[Dict[str, Any]] = []
        if pred_file.exists():
            try:
                with open(pred_file, "r", encoding="utf-8") as pf:
                    pred_data = json.load(pf)
                    preds = pred_data.get("predictions", []) or []
            except Exception as e:
                log.warning(f"[COHERENCE] Error reading predictions {pred_file}: {e}")

        md = journal.get("metadata", {})
        model_perf = journal.get("model_performance", {})
        narrative = journal.get("market_narrative", {})
        tomorrow_prep = journal.get("tomorrow_prep", {})

        # Parse numeric fields safely
        def _parse_pct(value: Any, default: float = 0.0) -> float:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                v = value.strip().replace("%", "")
                try:
                    return float(v)
                except ValueError:
                    return default
            return default

        daily_accuracy = _parse_pct(model_perf.get("daily_accuracy", "0"))
        coherence_score = float(md.get("coherence_score", 0.0))

        metrics = DailyCoherenceMetrics(
            date=date_str,
            coherence_score=coherence_score,
            daily_accuracy=daily_accuracy,
            messages_sent=int(md.get("messages_sent", 27)),
            pages_generated=int(md.get("pages_generated", 6)),
            sentiment_evolution=str(md.get("sentiment_evolution", "NEUTRAL")),
            news_volume=int(md.get("news_volume", 0)),
            predictions_count=len(preds),
            sources={
                "journal": str(journal_file),
                "predictions": str(pred_file) if pred_file.exists() else "",
            },
        )

        # Extract sentiment_intraday_evolution if available
        sentiment_intraday = md.get("sentiment_intraday_evolution", {})
        
        context = DailyContextSnapshot(
            date=date_str,
            market_story=str(narrative.get("story", "Market session completed")),
            narrative_character=str(narrative.get("character", "Standard trading day")),
            key_turning_points=str(narrative.get("key_turning_points", "")),
            lessons_learned=list(journal.get("lessons_learned", [])),
            tomorrow_prep=tomorrow_prep,
            raw_sentiment=str(md.get("sentiment_evolution", "NEUTRAL")),
        )

        # Write per-day files
        metrics_path = self.analysis_dir / f"coherence_{date_str}.json"
        context_path = self.context_dir / f"context_{date_str}.json"
        try:
            with open(metrics_path, "w", encoding="utf-8") as mf:
                json.dump(asdict(metrics), mf, indent=2, ensure_ascii=False)
            with open(context_path, "w", encoding="utf-8") as cf:
                json.dump(asdict(context), cf, indent=2, ensure_ascii=False)
            log.info(f"[COHERENCE] Saved metrics: {metrics_path}")
            log.info(f"[COHERENCE] Saved context: {context_path}")
        except Exception as e:
            log.error(f"[COHERENCE] Error writing analysis files for {date_str}: {e}")

        return {
            "metrics": asdict(metrics),
            "context": asdict(context),
        }

    # ------------------------------------------------------------------
    # Rolling history
    # ------------------------------------------------------------------

    def analyze_range(self, days_back: int = 7) -> Dict[str, Any]:
        """Analyze a rolling window of days and produce a history file.

        Only days for which a journal exists are included.
        """
        today = _today_it()
        results: List[Dict[str, Any]] = []

        for i in range(days_back):
            day = today - _dt.timedelta(days=i)
            res = self.analyze_day(day)
            if res is not None:
                results.append(res["metrics"])

        # Sort by date ascending
        results.sort(key=lambda r: r.get("date", ""))

        history = {
            "generated_at": _dt.datetime.now(ITALY_TZ).isoformat(),
            "days_back": days_back,
            "entries": results,
        }

        history_path = self.analysis_dir / "coherence_history.json"
        try:
            with open(history_path, "w", encoding="utf-8") as hf:
                json.dump(history, hf, indent=2, ensure_ascii=False)
            log.info(f"[COHERENCE] Saved history: {history_path}")
        except Exception as e:
            log.error(f"[COHERENCE] Error writing history file: {e}")

        return history


# Convenience function for CLI / schedulers

def run_daily_coherence_analysis(days_back: int = 7) -> Dict[str, Any]:
    """Run coherence analysis for the last N days and return the history dict."""
    mgr = CoherenceManager()
    return mgr.analyze_range(days_back=days_back)
