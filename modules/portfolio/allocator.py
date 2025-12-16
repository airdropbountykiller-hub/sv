"""Portfolio allocation helper.

Calculates exposure by asset class and deviation against target weights.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class AllocationState:
    total_equity: float
    exposures: Dict[str, float]
    target_weights: Dict[str, float]
    actual_weights: Dict[str, float]
    deviations: Dict[str, Dict[str, float]]


class PortfolioAllocator:
    """Compute portfolio exposure vs. targets."""

    def __init__(self, target_allocations: Dict[str, float] | None = None):
        self.target_allocations = target_allocations or {
            "cash": 0.20,
            "equity": 0.40,  # includes indices/stocks/ETFs/Gold
            "bonds": 0.20,
            "crypto": 0.20,
        }

    def compute_allocation(self, portfolio_state: Dict, asset_clusters: Dict[str, str]) -> AllocationState:
        """Calculate current weights and deviation from targets.

        Args:
            portfolio_state: State from SVPortfolioManager (positions, cash, etc.).
            asset_clusters: Mapping of tickers to asset classes.
        """
        exposures = {key: 0.0 for key in self.target_allocations.keys()}
        exposures.setdefault("other", 0.0)

        cash = float(portfolio_state.get("available_cash", 0.0))
        exposures["cash"] = cash

        positions: List[Dict] = portfolio_state.get("active_positions", [])
        for position in positions:
            asset = position.get("asset")
            size = float(position.get("position_size", 0))
            asset_class = asset_clusters.get(asset, "other")
            exposures[asset_class] = exposures.get(asset_class, 0.0) + size

        total_equity = max(0.0, sum(exposures.values()))

        actual_weights: Dict[str, float] = {}
        deviations: Dict[str, Dict[str, float]] = {}

        for asset_class, target_weight in self.target_allocations.items():
            exposure_value = exposures.get(asset_class, 0.0)
            if total_equity > 0:
                weight = exposure_value / total_equity
            else:
                weight = 0.0
            actual_weights[asset_class] = weight
            deviations[asset_class] = {
                "difference_pct": weight - target_weight,
                "difference_value": (target_weight * total_equity) - exposure_value,
            }

        # Track how much "other" exposure is present even if not in targets
        if exposures.get("other", 0) > 0:
            actual_weights["other"] = exposures["other"] / total_equity if total_equity else 0.0
            deviations["other"] = {
                "difference_pct": actual_weights["other"],
                "difference_value": exposures["other"],
            }

        return AllocationState(
            total_equity=total_equity,
            exposures=exposures,
            target_weights=self.target_allocations,
            actual_weights=actual_weights,
            deviations=deviations,
        )
