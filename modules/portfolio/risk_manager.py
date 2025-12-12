"""Risk metrics for the portfolio decision layer."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


def _compute_drawdown(balances: List[float]) -> float:
    if not balances:
        return 0.0
    peak = balances[0]
    max_dd = 0.0
    for value in balances:
        peak = max(peak, value)
        drawdown = (peak - value) / peak if peak else 0.0
        max_dd = max(max_dd, drawdown)
    return round(max_dd * 100, 2)


def _compute_volatility(balances: List[float]) -> float:
    if len(balances) < 2:
        return 0.0
    returns = []
    for prev, curr in zip(balances, balances[1:]):
        returns.append(((curr - prev) / prev) if prev else 0.0)
    if not returns:
        return 0.0
    avg = sum(returns) / len(returns)
    variance = sum((r - avg) ** 2 for r in returns) / len(returns)
    return round((variance ** 0.5) * 100, 2)


@dataclass
class RiskSnapshot:
    total_exposure_pct: float
    cash_pct: float
    volatility_pct: float
    max_drawdown_pct: float
    risk_flags: List[str]


class RiskManager:
    """Evaluates high-level portfolio risk from balance history and allocations."""

    def __init__(self, min_cash_buffer: float = 0.15, max_exposure: float = 0.90):
        self.min_cash_buffer = min_cash_buffer
        self.max_exposure = max_exposure

    def evaluate(
        self,
        portfolio_balance: float,
        invested: float,
        cash_available: float,
        daily_balances: List[Dict[str, float]],
    ) -> RiskSnapshot:
        cash_pct = (cash_available / portfolio_balance) if portfolio_balance else 0.0
        exposure_pct = (invested / portfolio_balance) if portfolio_balance else 0.0

        balances_only = [entry.get("balance", 0.0) for entry in daily_balances or []]
        max_drawdown_pct = _compute_drawdown(balances_only)
        volatility_pct = _compute_volatility(balances_only)

        risk_flags: List[str] = []
        if cash_pct < self.min_cash_buffer:
            risk_flags.append("Cash buffer below target")
        if exposure_pct > self.max_exposure:
            risk_flags.append("Exposure above policy limit")
        if max_drawdown_pct > 20:
            risk_flags.append("Drawdown > 20%")

        return RiskSnapshot(
            total_exposure_pct=round(exposure_pct * 100, 2),
            cash_pct=round(cash_pct * 100, 2),
            volatility_pct=volatility_pct,
            max_drawdown_pct=max_drawdown_pct,
            risk_flags=risk_flags,
        )
