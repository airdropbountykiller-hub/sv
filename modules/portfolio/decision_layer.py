"""High-level portfolio decision layer implementing allocator → risk → executor flow."""
from __future__ import annotations

from typing import Dict, List, Any, Optional

import json
from datetime import datetime
from pathlib import Path

from config import sv_paths
from modules.portfolio import PortfolioAllocator, RiskManager, PortfolioExecutor, PortfolioStateBuilder


class PortfolioDecisionLayer:
    """Combines allocation, risk, and execution to produce portfolio outputs."""

    def __init__(self, portfolio_manager):
        self.portfolio_manager = portfolio_manager
        self.config = self._load_config()
        target_allocations = self.config.get("target_allocations")
        rebalance_cfg = self.config.get("rebalance", {})
        trade_thresholds = self.config.get("trade_thresholds", {})

        self.allocator = PortfolioAllocator(target_allocations)
        self.risk_manager = RiskManager()
        self.executor = PortfolioExecutor(
            portfolio_manager.broker_profiles,
            portfolio_manager.asset_clusters,
            deviation_threshold=rebalance_cfg.get("deviation_threshold", 0.10),
            min_score=trade_thresholds.get("min_score", 0.6),
            min_notional=trade_thresholds.get("min_notional", 100.0),
        )
        self.builder = PortfolioStateBuilder()
        self.rebalance_cfg = rebalance_cfg

    def run(
        self,
        signals: Optional[List[Dict[str, Any]]] = None,
        market_snapshot: Optional[Dict[str, Any]] = None,
        price_history: Optional[Dict[str, List[float]]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Produce portfolio_state.json and portfolio_signals.json.

        Args:
            signals: ENGINE/BRAIN combined signals with ai_score/technical_score fields.
            market_snapshot: currently unused placeholder for future conditioning.
            price_history: optional price/equity series for risk metrics.
        """
        signals = signals or []

        portfolio_state = self.portfolio_manager.portfolio
        allocation_state = self.allocator.compute_allocation(portfolio_state, self.portfolio_manager.asset_clusters)
        risk_report = self.risk_manager.assess(price_history)

        rebalance_flags = self._rebalance_flags(allocation_state)

        recommendations = self.executor.generate_recommendations(
            signals, allocation_state, portfolio_state, rebalance_flags
        )

        state_payload = self.builder.build_state(
            portfolio_state, allocation_state, risk_report, recommendations, rebalance_flags
        )
        signals_payload = self.builder.build_signals(
            recommendations, allocation_state, risk_report, rebalance_flags
        )

        self.builder.write_outputs(
            state_payload=state_payload,
            signals_payload=signals_payload,
            state_path=sv_paths.PORTFOLIO_STATE_FILE,
            signals_path=sv_paths.PORTFOLIO_SIGNALS_FILE,
        )

        return {
            "state": state_payload,
            "signals": signals_payload,
        }

    def _rebalance_flags(self, allocation_state):
        deviation_triggered = any(
            abs(deviation.get("difference_pct", 0.0)) >= self.rebalance_cfg.get("deviation_threshold", 0.10)
            for deviation in allocation_state.deviations.values()
        )

        monthly_day = self.rebalance_cfg.get("monthly_day")
        today = datetime.utcnow().day
        monthly_due = monthly_day is not None and today == int(monthly_day)

        return {
            "monthly_due": monthly_due,
            "extraordinary_due": deviation_triggered,
        }

    def _load_config(self) -> Dict[str, Any]:
        config_path = Path(sv_paths.CONFIG_DIR) / "portfolio_config.json"
        if config_path.exists():
            try:
                with config_path.open("r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "target_allocations": {
                "cash": 0.2,
                "equity": 0.4,
                "bonds": 0.2,
                "crypto": 0.2,
            },
            "rebalance": {"monthly_day": 1, "deviation_threshold": 0.10},
            "trade_thresholds": {"min_notional": 100, "min_score": 0.6},
        }
