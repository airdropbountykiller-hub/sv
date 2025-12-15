"""High-level portfolio decision layer implementing allocator → risk → executor flow."""
from __future__ import annotations

from typing import Dict, List, Any, Optional

from config import sv_paths
from modules.portfolio import PortfolioAllocator, RiskManager, PortfolioExecutor, PortfolioStateBuilder


class PortfolioDecisionLayer:
    """Combines allocation, risk, and execution to produce portfolio outputs."""

    def __init__(self, portfolio_manager):
        self.portfolio_manager = portfolio_manager
        self.allocator = PortfolioAllocator()
        self.risk_manager = RiskManager()
        self.executor = PortfolioExecutor(portfolio_manager.broker_profiles, portfolio_manager.asset_clusters)
        self.builder = PortfolioStateBuilder()

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

        recommendations = self.executor.generate_recommendations(signals, allocation_state, portfolio_state)

        state_payload = self.builder.build_state(portfolio_state, allocation_state, risk_report, recommendations)
        signals_payload = self.builder.build_signals(recommendations, allocation_state, risk_report)

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
