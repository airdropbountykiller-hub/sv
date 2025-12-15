"""Builds portfolio JSON payloads for state and operational signals."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Any


class PortfolioStateBuilder:
    """Compose state and signal JSON outputs."""

    def build_state(
        self,
        portfolio_state: Dict[str, Any],
        allocation_state,
        risk_report,
        recommended_trades: List[Dict[str, Any]],
        rebalance_flags: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "initial_capital": portfolio_state.get("initial_capital"),
            "total_equity": allocation_state.total_equity,
            "available_cash": portfolio_state.get("available_cash"),
            "allocations": {
                "target_weights": allocation_state.target_weights,
                "actual_weights": allocation_state.actual_weights,
                "exposures": allocation_state.exposures,
                "deviations": allocation_state.deviations,
            },
            "costs": {
                "fees_paid": portfolio_state.get("total_fees_paid", 0.0),
                "estimated_taxes": portfolio_state.get("total_estimated_taxes", 0.0),
            },
            "backtesting": {
                "manual_brokers_included": portfolio_state.get("backtest_manual_trading", False),
            },
            "risk": {
                "volatility": risk_report.volatility,
                "max_drawdown": risk_report.max_drawdown,
                "asset_risks": risk_report.asset_risks,
            },
            "rebalancing": rebalance_flags,
            "active_positions": portfolio_state.get("active_positions", []),
            "closed_positions": portfolio_state.get("closed_positions", []),
            "brokers": portfolio_state.get("brokers", {}),
            "performance_metrics": portfolio_state.get("performance_metrics", {}),
            "recommended_trades": recommended_trades,
        }

    def build_signals(
        self,
        recommended_trades: List[Dict[str, Any]],
        allocation_state,
        risk_report,
        rebalance_flags: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "underweight_classes": [
                    a for a, d in allocation_state.deviations.items() if d.get("difference_pct", 0) < -0.1
                ],
                "overweight_classes": [
                    a for a, d in allocation_state.deviations.items() if d.get("difference_pct", 0) > 0.1
                ],
            },
            "risk": {
                "volatility": risk_report.volatility,
                "max_drawdown": risk_report.max_drawdown,
            },
            "rebalancing": rebalance_flags,
            "recommended_trades": recommended_trades,
        }

    def write_outputs(
        self,
        state_payload: Dict[str, Any],
        signals_payload: Dict[str, Any],
        state_path: str,
        signals_path: str,
    ) -> None:
        import json
        import os

        os.makedirs(os.path.dirname(state_path), exist_ok=True)
        os.makedirs(os.path.dirname(signals_path), exist_ok=True)

        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state_payload, f, indent=2, ensure_ascii=False)

        with open(signals_path, "w", encoding="utf-8") as f:
            json.dump(signals_payload, f, indent=2, ensure_ascii=False)
