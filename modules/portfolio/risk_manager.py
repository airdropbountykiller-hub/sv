"""Risk management helpers for the portfolio decision layer."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class RiskMetrics:
    volatility: Optional[float]
    max_drawdown: Optional[float]
    asset_risks: Dict[str, Optional[float]]


class RiskManager:
    """Compute basic volatility and drawdown metrics."""

    def __init__(self, lookback: int = 30):
        self.lookback = lookback

    @staticmethod
    def _max_drawdown(curve: List[float]) -> float:
        peak = curve[0]
        max_dd = 0.0
        for value in curve:
            peak = max(peak, value)
            drawdown = (value - peak) / peak if peak else 0.0
            max_dd = min(max_dd, drawdown)
        return max_dd

    @staticmethod
    def _annualized_volatility(series: List[float]) -> float:
        returns = []
        for i in range(1, len(series)):
            prev = series[i - 1]
            curr = series[i]
            if prev:
                returns.append((curr / prev) - 1.0)
        if not returns:
            return 0.0
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        daily_vol = math.sqrt(variance)
        return daily_vol * math.sqrt(252)  # trading days

    def assess(self, price_history: Dict[str, List[float]] | None) -> RiskMetrics:
        """Calculate simple risk metrics from price history.

        Args:
            price_history: mapping of asset->price series or "equity_curve"->equity series.
        """
        price_history = price_history or {}
        equity_curve = price_history.get("equity_curve")

        volatility = None
        max_drawdown = None
        if equity_curve and len(equity_curve) > 1:
            volatility = round(self._annualized_volatility(equity_curve), 4)
            max_drawdown = round(self._max_drawdown(equity_curve), 4)

        asset_risks: Dict[str, Optional[float]] = {}
        for asset, series in price_history.items():
            if asset == "equity_curve":
                continue
            if series and len(series) > 1:
                asset_risks[asset] = round(self._annualized_volatility(series), 4)
            else:
                asset_risks[asset] = None

        return RiskMetrics(volatility=volatility, max_drawdown=max_drawdown, asset_risks=asset_risks)
