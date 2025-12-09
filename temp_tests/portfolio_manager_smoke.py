"""Quick smoke test for SVPortfolioManager.

Runs an end-to-end cycle using a temporary portfolio file so it doesn't touch
production state. Useful to verify that broker guardrails and sizing work
without manual wiring.
"""

import logging
import os
import sys
from tempfile import TemporaryDirectory

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from modules.portfolio_manager import SVPortfolioManager


logging.basicConfig(level=logging.INFO)


def run_smoke_test() -> None:
    """Execute a short scenario across brokers to validate basic flows."""
    with TemporaryDirectory() as tmp:
        pm = SVPortfolioManager(
            base_dir=tmp,
            portfolio_file=os.path.join(tmp, "portfolio_state.json"),
            history_dir=os.path.join(tmp, "history"),
        )

        # IG: automated, should open
        ig_trade = {
            "asset": "SPX",
            "direction": "LONG",
            "entry": 4500,
            "target": 4550,
            "stop": 4450,
            "confidence": 70,
            "broker": "IG",
        }
        ig_id = pm.open_position(ig_trade, current_price=4510)

        # Directa: discretionary only, should be ignored (auto_trading=False)
        directa_trade = {
            "asset": "AAPL",
            "direction": "LONG",
            "entry": 180,
            "target": 190,
            "stop": 170,
            "confidence": 80,
            "broker": "DIRECTA",
        }
        directa_id = pm.open_position(directa_trade, current_price=181)

        pm.update_positions({"SPX": {"price": 4530}})

        if ig_id:
            pm.close_position(ig_id, close_price=4545, reason="SMOKE_TEST")

        snapshot = pm.get_portfolio_snapshot()

        print("=== Smoke test output ===")
        print(f"IG opened? {'yes' if ig_id else 'no'}")
        print(f"Directa opened? {'yes' if directa_id else 'no (blocked as expected)'}")
        print(f"Closed trades: {len(pm.portfolio['closed_positions'])}")
        print(f"Available cash (IG): {snapshot['brokers']['IG']['available_cash']}")
        print(f"Total P&L: {snapshot['total_pnl']}")


if __name__ == "__main__":
    run_smoke_test()
