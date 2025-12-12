"""JSON builders for portfolio state and operational signals."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from config import sv_paths


class PortfolioStateBuilder:
    """Aggregates allocation, risk, and trade routing into JSON outputs."""

    def __init__(self, state_file: str | None = None, signals_file: str | None = None):
        self.state_file = state_file or sv_paths.PORTFOLIO_STATE_FILE
        self.signals_file = signals_file or sv_paths.PORTFOLIO_SIGNALS_FILE

    def build_state(
        self,
        base_portfolio: Dict[str, object],
        allocation: Dict[str, object],
        risk: Dict[str, object],
        trades: List[Dict[str, object]],
    ) -> Dict[str, object]:
        """Append decision-layer data onto the base portfolio state."""

        timestamp = datetime.utcnow().isoformat()
        state = dict(base_portfolio)
        state["decision_layer"] = {
            "generated_at": timestamp,
            "allocation": allocation,
            "risk": risk,
            "routed_trades": trades,
        }

        self._write_json(self.state_file, state)
        return state

    def build_signals(self, trades: List[Dict[str, object]]) -> Dict[str, object]:
        timestamp = datetime.utcnow().isoformat()
        payload = {
            "generated_at": timestamp,
            "signals": trades,
        }
        self._write_json(self.signals_file, payload)
        return payload

    def _write_json(self, path: str, data: Dict[str, object]):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
