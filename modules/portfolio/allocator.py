"""Allocation and deviation planner for the portfolio decision layer."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


@dataclass
class AllocationResult:
    exposure_by_class: Dict[str, float]
    exposure_pct: Dict[str, float]
    target_allocation: Dict[str, float]
    deviations: Dict[str, float]
    recommended_trades: List[Dict[str, object]]


class AllocationPlanner:
    """Calculates asset-class exposure and proposes balancing trades."""

    DEFAULT_TARGETS: Dict[str, float] = {
        "cash": 0.20,
        "indices": 0.40,
        "bonds": 0.20,
        "crypto": 0.20,
    }

    def __init__(self, target_allocation: Dict[str, float] | None = None, deviation_threshold: float = 0.10):
        self.target_allocation = target_allocation or self.DEFAULT_TARGETS
        self.deviation_threshold = deviation_threshold

    def _infer_asset_class(self, position: Dict[str, object], cluster_map: Dict[str, str]) -> str:
        symbol = str(position.get("symbol") or position.get("ticker") or "").upper()
        if not symbol:
            return position.get("asset_class") or "unclassified"
        return position.get("asset_class") or cluster_map.get(symbol, "unclassified")

    def _position_value(self, position: Dict[str, object]) -> float:
        current_value = position.get("current_value")
        if current_value is not None:
            return float(current_value)
        invested = float(position.get("invested", 0.0))
        pnl = float(position.get("current_pnl", 0.0))
        return invested + pnl

    def calculate_allocation(
        self,
        positions: Iterable[Dict[str, object]],
        cash_available: float,
        portfolio_balance: float,
        cluster_map: Dict[str, str],
    ) -> AllocationResult:
        exposure_by_class: Dict[str, float] = {k: 0.0 for k in self.target_allocation.keys()}
        exposure_by_class.setdefault("unclassified", 0.0)

        for pos in positions:
            asset_class = self._infer_asset_class(pos, cluster_map)
            value = self._position_value(pos)
            exposure_by_class[asset_class] = exposure_by_class.get(asset_class, 0.0) + value

        exposure_by_class["cash"] = cash_available

        exposure_pct: Dict[str, float] = {}
        for asset_class, value in exposure_by_class.items():
            exposure_pct[asset_class] = (value / portfolio_balance * 100) if portfolio_balance else 0.0

        deviations: Dict[str, float] = {}
        recommended_trades: List[Dict[str, object]] = []

        for asset_class, target in self.target_allocation.items():
            current_value = exposure_by_class.get(asset_class, 0.0)
            target_value = portfolio_balance * target
            gap = target_value - current_value
            deviations[asset_class] = gap

            if portfolio_balance <= 0:
                continue
            gap_pct_of_total = abs(gap) / portfolio_balance
            if gap_pct_of_total >= self.deviation_threshold:
                action = "BUY" if gap > 0 else "SELL"
                recommended_trades.append(
                    {
                        "asset_class": asset_class,
                        "action": action,
                        "amount": round(abs(gap), 2),
                        "gap_pct_of_total": round(gap_pct_of_total * 100, 2),
                        "target_pct": target * 100,
                    }
                )

        return AllocationResult(
            exposure_by_class=exposure_by_class,
            exposure_pct=exposure_pct,
            target_allocation={k: v * 100 for k, v in self.target_allocation.items()},
            deviations=deviations,
            recommended_trades=recommended_trades,
        )
