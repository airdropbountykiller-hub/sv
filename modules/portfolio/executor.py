"""Trade recommendation engine for the portfolio decision layer."""
from __future__ import annotations

from typing import Dict, List, Any


class PortfolioExecutor:
    """Generate recommended trades respecting broker policies and allocation drift."""

    def __init__(
        self,
        broker_profiles: Dict[str, Dict[str, Any]],
        asset_clusters: Dict[str, str],
        *,
        deviation_threshold: float = 0.10,
        min_score: float = 0.6,
        min_notional: float = 100.0,
    ):
        self.broker_profiles = broker_profiles
        self.asset_clusters = asset_clusters
        self.deviation_threshold = deviation_threshold
        self.min_score = min_score
        self.min_notional = min_notional

    def _pick_broker(self, asset_class: str) -> str | None:
        """Choose a broker for an asset class honoring auto_trading flag."""
        broker_priority: List[str]
        if asset_class == "crypto":
            broker_priority = ["BYBIT_BTC", "BYBIT_USDT", "IG"]
        elif asset_class in {"indices", "equity", "commodities", "fx"}:
            broker_priority = ["IG", "IG_ITALIA"] if "IG_ITALIA" in self.broker_profiles else ["IG"]
        else:
            broker_priority = ["IG"]

        for broker in broker_priority:
            profile = self.broker_profiles.get(broker)
            if profile and profile.get("auto_trading", False):
                return broker
        return None

    def generate_recommendations(
        self,
        signals: List[Dict[str, Any]],
        allocation_state,
        portfolio_state: Dict[str, Any],
        rebalance_flags: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        recommendations: List[Dict[str, Any]] = []

        broker_states = portfolio_state.get("brokers", {})
        rebalance_flags = rebalance_flags or {}

        for asset_class, deviation in allocation_state.deviations.items():
            difference_pct = deviation.get("difference_pct", 0.0)
            difference_value = deviation.get("difference_value", 0.0)

            # Require > configured drift from target
            if abs(difference_pct) < self.deviation_threshold:
                continue

            # When under target we look to buy; when over target we suggest trimming
            action = "BUY" if difference_value > 0 else "SELL"

            candidate_signals = [
                s for s in signals if self.asset_clusters.get(s.get("asset"), "other") == asset_class
            ]
            if not candidate_signals:
                continue

            candidate_signals.sort(
                key=lambda s: (float(s.get("ai_score", 0)) + float(s.get("technical_score", 0))) / 2,
                reverse=True,
            )

            best_signal = candidate_signals[0]
            combined_score = (float(best_signal.get("ai_score", 0)) + float(best_signal.get("technical_score", 0))) / 2

            # Favorable condition threshold
            if combined_score < self.min_score:
                continue

            broker = self._pick_broker(asset_class)
            if broker is None:
                continue

            broker_state = broker_states.get(broker, {})
            available_cash = float(broker_state.get("available_cash", 0))
            exposure = allocation_state.exposures.get(asset_class, 0)

            if action == "BUY":
                notional = min(difference_value, available_cash)
            else:
                notional = min(abs(difference_value), exposure)

            if notional < self.min_notional:  # keep recommendations meaningful
                continue

            reason = "allocation_drift"
            if rebalance_flags.get("monthly_due"):
                reason = "rebalance_monthly"
            elif rebalance_flags.get("extraordinary_due"):
                reason = "rebalance_extraordinary"

            recommendations.append(
                {
                    "asset": best_signal.get("asset"),
                    "asset_class": asset_class,
                    "broker": broker,
                    "action": action,
                    "notional": round(notional, 2),
                    "reason": reason,
                    "scores": {
                        "ai": best_signal.get("ai_score"),
                        "technical": best_signal.get("technical_score"),
                        "combined": round(combined_score, 3),
                    },
                }
            )

        return recommendations
