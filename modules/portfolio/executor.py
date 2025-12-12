"""Trade routing helper for the portfolio decision layer."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class BrokerPolicy:
    name: str
    mode: str  # "bot" or "notify"
    allowed_classes: List[str]
    notes: str


class TradeExecutor:
    """Assigns recommended trades to brokers according to the policy."""

    def __init__(self):
        self.broker_policies: Dict[str, BrokerPolicy] = {
            "BYBIT": BrokerPolicy(
                name="Bybit",
                mode="bot",
                allowed_classes=["crypto"],
                notes="Bot trading on crypto spot/derivatives (50% capital)",
            ),
            "IG": BrokerPolicy(
                name="IG Italia",
                mode="bot",
                allowed_classes=["indices", "equity"],
                notes="Bot trading for indices, ETFs, stocks (50% margin)",
            ),
            "DIRECTA": BrokerPolicy(
                name="Directa",
                mode="notify",
                allowed_classes=["equity", "bonds"],
                notes="Medium/long-term manual execution only",
            ),
            "TRADE_REPUBLIC": BrokerPolicy(
                name="Trade Republic",
                mode="notify",
                allowed_classes=["equity", "bonds"],
                notes="Medium/long-term manual execution only",
            ),
        }

    def assign(self, recommended_trades: List[Dict[str, object]]) -> List[Dict[str, object]]:
        routed: List[Dict[str, object]] = []
        for trade in recommended_trades:
            asset_class = trade.get("asset_class")
            target_policy = self._select_policy(asset_class)
            if not target_policy:
                continue
            routed.append(
                {
                    **trade,
                    "broker": target_policy.name,
                    "mode": target_policy.mode,
                    "notes": target_policy.notes,
                }
            )
        return routed

    def _select_policy(self, asset_class: str) -> BrokerPolicy | None:
        asset_class = (asset_class or "").lower()
        for policy in self.broker_policies.values():
            if asset_class in [cls.lower() for cls in policy.allowed_classes]:
                return policy
        return None
