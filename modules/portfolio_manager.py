#!/usr/bin/env python3
"""
SV Portfolio Manager - $25K Initial Capital
Tracks ML signals and calculates real P&L for dashboard display
"""

from pathlib import Path
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

from config import sv_paths

logger = logging.getLogger(__name__)


class SVPortfolioManager:
    """Manages $25K simulated portfolio tracking ML signals"""

    def __init__(self, base_dir: str, portfolio_file: Optional[str] = None, history_dir: Optional[str] = None):
        self.base_dir = base_dir
        self.portfolio_file = portfolio_file or sv_paths.PORTFOLIO_STATE_FILE
        self.history_dir = history_dir or os.path.join(base_dir, 'reports', 'portfolio_history')

        self.asset_clusters = {
            'BTC': 'crypto', 'ETH': 'crypto', 'BNB': 'crypto', 'SOL': 'crypto',
            'ADA': 'crypto', 'XRP': 'crypto', 'DOT': 'crypto', 'LINK': 'crypto',
            'SPX': 'indices', '^GSPC': 'indices', 'SP500': 'indices',
            'SPY': 'equity', 'QQQ': 'equity', 'AAPL': 'equity', 'MSFT': 'equity',
            'EURUSD': 'fx', 'EURUSD=X': 'fx',
            'GOLD': 'commodities', 'XAUUSD=X': 'commodities',
        }

        self.broker_profiles = self._init_broker_profiles()

        # Portfolio configuration
        self.initial_capital = sum(profile['initial_capital'] for profile in self.broker_profiles.values())
        self.max_position_size = 0.20  # fallback max per trade
        self.risk_per_trade = 0.02     # fallback risk per trade

        # Ensure directories exist
        os.makedirs(os.path.dirname(self.portfolio_file), exist_ok=True)
        os.makedirs(self.history_dir, exist_ok=True)

        self.portfolio = self._load_portfolio()

    def _init_broker_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Define broker-specific sizing/limit rules."""
        return {
            'IG': {
                'initial_capital': 10000.0,
                'strategy': 'bot_trading',
                'risk_per_trade': 0.02,
                'max_position_size': 0.20,
                'max_open_trades': 6,
                'max_trades_per_asset': 2,
                'cluster_limits': {'indices': 0.6, 'fx': 0.25, 'commodities': 0.2},
                'auto_trading': True,
            },
            'BYBIT_BTC': {
                'initial_capital': 2500.0,
                'strategy': 'futures_inverse_btc_collateral',
                'risk_per_trade': 0.015,
                'max_position_size': 0.25,
                'max_open_trades': 3,
                'max_trades_per_asset': 2,
                'cluster_limits': {'crypto': 1.0},
                'auto_trading': True,
            },
            'BYBIT_USDT': {
                'initial_capital': 2500.0,
                'strategy': 'futures_usdt_collateral',
                'risk_per_trade': 0.015,
                'max_position_size': 0.25,
                'max_open_trades': 3,
                'max_trades_per_asset': 2,
                'cluster_limits': {'crypto': 1.0},
                'auto_trading': True,
            },
            'DIRECTA': {
                'initial_capital': 5000.0,
                'strategy': 'long_term_equity',
                'risk_per_trade': 0.01,
                'max_position_size': 0.15,
                'max_open_trades': 3,
                'max_trades_per_asset': 1,
                'cluster_limits': {'equity': 1.0},
                'auto_trading': False,  # solo segnali discrezionali
            },
            'TRADE_REPUBLIC': {
                'initial_capital': 5000.0,
                'strategy': 'long_term_equity',
                'risk_per_trade': 0.01,
                'max_position_size': 0.15,
                'max_open_trades': 3,
                'max_trades_per_asset': 1,
                'cluster_limits': {'equity': 1.0},
                'auto_trading': False,  # solo segnali discrezionali
            },
        }
    
    def _load_portfolio(self) -> Dict[str, Any]:
        """Load portfolio state from disk or create new one"""
        if os.path.exists(self.portfolio_file):
            try:
                with open(self.portfolio_file, 'r', encoding='utf-8') as f:
                    portfolio = json.load(f)
                    portfolio = self._ensure_broker_state(portfolio)
                    logger.info(f"Loaded portfolio: ${portfolio['current_balance']:.2f}")
                    return portfolio
            except Exception as e:
                logger.error(f"Error loading portfolio: {e}")
        
        # Create new portfolio
        portfolio = {
            "created_at": datetime.now().isoformat(),
            "initial_capital": self.initial_capital,
            "current_balance": self.initial_capital,
            "available_cash": self.initial_capital,
            "total_invested": 0.0,
            "total_pnl": 0.0,
            "total_pnl_pct": 0.0,
            "active_positions": [],
            "closed_positions": [],
            "daily_balances": [],
            "brokers": {
                name: {
                    'initial_capital': profile['initial_capital'],
                    'available_cash': profile['initial_capital'],
                    'total_invested': 0.0,
                    'current_balance': profile['initial_capital'],
                    'realized_pnl': 0.0,
                    'strategy': profile['strategy'],
                    'auto_trading': profile['auto_trading'],
                }
                for name, profile in self.broker_profiles.items()
            },
            "performance_metrics": {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "profit_factor": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": None
            }
        }

        self._save_portfolio(portfolio)
        logger.info(f"Created new portfolio: ${self.initial_capital}")
        return portfolio
    
    def _save_portfolio(self, portfolio: Dict[str, Any]):
        """Save portfolio state to disk"""
        try:
            with open(self.portfolio_file, 'w', encoding='utf-8') as f:
                json.dump(portfolio, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving portfolio: {e}")

    def _ensure_broker_state(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """Backfill broker-specific state for legacy portfolio files."""
        brokers = portfolio.get('brokers', {}) or {}
        for name, profile in self.broker_profiles.items():
            if name not in brokers:
                brokers[name] = {
                    'initial_capital': profile['initial_capital'],
                    'available_cash': profile['initial_capital'],
                    'total_invested': 0.0,
                    'current_balance': profile['initial_capital'],
                    'realized_pnl': 0.0,
                    'strategy': profile['strategy'],
                    'auto_trading': profile['auto_trading'],
                }
            else:
                brokers[name].setdefault('initial_capital', profile['initial_capital'])
                brokers[name].setdefault('available_cash', brokers[name]['initial_capital'])
                brokers[name].setdefault('total_invested', 0.0)
                brokers[name].setdefault('current_balance', brokers[name]['initial_capital'])
                brokers[name].setdefault('realized_pnl', 0.0)
                brokers[name].setdefault('strategy', profile['strategy'])
                brokers[name].setdefault('auto_trading', profile['auto_trading'])
        portfolio['brokers'] = brokers
        portfolio.setdefault('initial_capital', self.initial_capital)
        return portfolio
    
    def calculate_position_size(self, entry_price: float, stop_price: float,
                              confidence: int, broker: str) -> float:
        """Calculate position size based on risk management rules"""
        if entry_price <= 0 or stop_price <= 0 or confidence <= 0:
            return 0.0

        broker_profile = self.broker_profiles.get(broker, {})
        broker_state = self.portfolio['brokers'].get(broker, {})

        risk_per_trade = broker_profile.get('risk_per_trade', self.risk_per_trade)
        max_position_size = broker_profile.get('max_position_size', self.max_position_size)

        broker_balance = broker_state.get('current_balance', broker_profile.get('initial_capital', self.initial_capital))

        # Risk amount (configurable % of broker balance)
        risk_amount = broker_balance * risk_per_trade

        # Distance to stop loss
        risk_per_unit = abs(entry_price - stop_price)
        if risk_per_unit <= 0:
            return 0.0

        # Base position size
        base_size = risk_amount / risk_per_unit * entry_price

        # Confidence multiplier (50-100% confidence -> 0.5-1.0x)
        confidence_mult = max(0.5, min(1.0, confidence / 100.0))
        position_size = base_size * confidence_mult

        # Max position size limit (% of broker balance)
        max_size = broker_balance * max_position_size
        position_size = min(position_size, max_size)

        # Available cash limit
        available_cash = broker_state.get('available_cash', self.portfolio['available_cash'])
        position_size = min(position_size, available_cash)

        return round(position_size, 2)
    
    def open_position(self, prediction: Dict[str, Any], current_price: float = None) -> Optional[str]:
        """Open new position based on ML prediction"""
        try:
            asset = prediction.get('asset', '')
            direction = prediction.get('direction', 'LONG')
            entry_price = float(prediction.get('entry', 0))
            target_price = float(prediction.get('target', 0))
            stop_price = float(prediction.get('stop', 0))
            confidence = int(prediction.get('confidence', 50))
            broker = prediction.get('broker', 'IG')

            if not all([asset, entry_price, target_price, stop_price]):
                logger.warning("Invalid prediction data for position opening")
                return None

            broker_profile = self.broker_profiles.get(broker, {})
            broker_state = self.portfolio['brokers'].get(broker)

            if broker_state is None:
                logger.warning(f"Unknown broker '{broker}' in prediction; skipping trade")
                return None

            if not broker_profile.get('auto_trading', True):
                logger.info(f"Broker {broker} is configured for discretionary trading only; ignoring bot signal")
                return None

            broker_positions = [p for p in self.portfolio['active_positions'] if p.get('broker') == broker]

            max_open_trades = broker_profile.get('max_open_trades')
            if max_open_trades is not None and len(broker_positions) >= max_open_trades:
                logger.info(f"Broker {broker} at max open trades ({max_open_trades}); skipping {asset}")
                return None

            max_trades_per_asset = broker_profile.get('max_trades_per_asset')
            asset_trades = [p for p in broker_positions if p.get('asset') == asset]
            if max_trades_per_asset is not None and len(asset_trades) >= max_trades_per_asset:
                logger.info(f"Broker {broker} at max trades for {asset}; skipping")
                return None

            # Use current price if provided, otherwise use entry price
            live_price = current_price or entry_price

            # Calculate position size
            position_size = self.calculate_position_size(entry_price, stop_price, confidence, broker)

            # Enforce cluster exposure limits after sizing
            cluster = self.asset_clusters.get(asset, 'other')
            cluster_limit = broker_profile.get('cluster_limits', {}).get(cluster)
            if cluster_limit is not None:
                cluster_exposure = sum(p['position_size'] for p in broker_positions
                                       if self.asset_clusters.get(p.get('asset'), 'other') == cluster)
                projected_exposure = cluster_exposure + position_size
                limit_base = broker_state.get('current_balance') or broker_profile.get('initial_capital', 0)
                limit_amount = limit_base * cluster_limit
                if projected_exposure > limit_amount:
                    logger.info(f"Broker {broker} cluster limit reached for {cluster}; skipping {asset}")
                    return None

            if position_size < 100:  # Minimum $100 position
                logger.info(f"Position size too small: ${position_size:.2f}")
                return None

            # Calculate units
            units = position_size / entry_price

            # Create position ID
            position_id = f"{asset}_{direction}_{broker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Create position object
            position = {
                "id": position_id,
                "asset": asset,
                "direction": direction,
                "broker": broker,
                "entry_price": entry_price,
                "target_price": target_price,
                "stop_price": stop_price,
                "position_size": position_size,
                "units": round(units, 8),
                "confidence": confidence,
                "entry_time": datetime.now().isoformat(),
                "status": "ACTIVE",
                "current_price": live_price,
                "current_pnl": 0.0,
                "pnl_percentage": 0.0,
                "max_favorable": 0.0,
                "max_adverse": 0.0
            }

            # Update portfolio
            self.portfolio['active_positions'].append(position)
            broker_state['available_cash'] -= position_size
            broker_state['total_invested'] += position_size

            self._update_portfolio_metrics()
            self._save_portfolio(self.portfolio)

            logger.info(f"Opened {direction} position on {broker}: {asset} ${position_size:.2f} @ {entry_price}")
            return position_id

        except Exception as e:
            logger.error(f"Error opening position: {e}")
            return None
    
    def update_positions(self, live_prices: Dict[str, Dict[str, float]]):
        """Update all active positions with current market prices"""
        if not self.portfolio['active_positions']:
            return
        
        for position in self.portfolio['active_positions']:
            asset = position['asset']
            
            # Get current price
            current_price = None
            if asset in live_prices:
                current_price = live_prices[asset].get('price', 0)
            
            if not current_price or current_price <= 0:
                continue
            
            # Update position
            position['current_price'] = current_price
            
            # Calculate P&L
            entry_price = position['entry_price']
            units = position['units']
            direction = position['direction']
            
            if direction.upper() == 'LONG':
                pnl = (current_price - entry_price) * units
            else:  # SHORT
                pnl = (entry_price - current_price) * units
            
            position['current_pnl'] = round(pnl, 2)
            position['pnl_percentage'] = round((pnl / position['position_size']) * 100, 2)
            
            # Track max favorable/adverse
            if pnl > position['max_favorable']:
                position['max_favorable'] = round(pnl, 2)
            if pnl < position['max_adverse']:
                position['max_adverse'] = round(pnl, 2)
            
            # Check for stop/target hits
            if direction.upper() == 'LONG':
                if current_price >= position['target_price']:
                    self.close_position(position['id'], current_price, 'TARGET_HIT')
                elif current_price <= position['stop_price']:
                    self.close_position(position['id'], current_price, 'STOP_HIT')
            else:  # SHORT
                if current_price <= position['target_price']:
                    self.close_position(position['id'], current_price, 'TARGET_HIT')
                elif current_price >= position['stop_price']:
                    self.close_position(position['id'], current_price, 'STOP_HIT')
        
        # Update total P&L
        self._update_portfolio_metrics()
        self._save_portfolio(self.portfolio)
    
    def close_position(self, position_id: str, close_price: float, reason: str = 'MANUAL'):
        """Close position and update portfolio"""
        position = None
        for i, pos in enumerate(self.portfolio['active_positions']):
            if pos['id'] == position_id:
                position = self.portfolio['active_positions'].pop(i)
                break
        
        if not position:
            logger.warning(f"Position not found: {position_id}")
            return
        
        # Calculate final P&L
        entry_price = position['entry_price']
        units = position['units']
        direction = position['direction']
        
        if direction.upper() == 'LONG':
            pnl = (close_price - entry_price) * units
        else:  # SHORT
            pnl = (entry_price - close_price) * units
        
        # Update position for history
        position.update({
            'close_price': close_price,
            'close_time': datetime.now().isoformat(),
            'final_pnl': round(pnl, 2),
            'final_pnl_pct': round((pnl / position['position_size']) * 100, 2),
            'close_reason': reason,
            'status': 'CLOSED'
        })
        
        broker_name = position.get('broker', 'IG')
        broker_state = self.portfolio['brokers'].get(broker_name, {})

        # Update portfolio
        self.portfolio['closed_positions'].append(position)
        broker_state['available_cash'] = broker_state.get('available_cash', 0) + position['position_size'] + pnl
        broker_state['total_invested'] = max(0.0, broker_state.get('total_invested', 0) - position['position_size'])
        broker_state['realized_pnl'] = broker_state.get('realized_pnl', 0) + pnl
        
        # Update performance metrics
        self.portfolio['performance_metrics']['total_trades'] += 1
        if pnl > 0:
            self.portfolio['performance_metrics']['winning_trades'] += 1
        else:
            self.portfolio['performance_metrics']['losing_trades'] += 1
        
        self._update_portfolio_metrics()
        self._save_portfolio(self.portfolio)
        
        logger.info(f"Closed position: {position['asset']} {direction} P&L: ${pnl:.2f} ({reason})")
    
    def _update_portfolio_metrics(self):
        """Update portfolio performance metrics"""
        # Calculate current balance
        active_pnl = sum(pos.get('current_pnl', 0) for pos in self.portfolio['active_positions'])
        closed_pnl = sum(pos.get('final_pnl', 0) for pos in self.portfolio['closed_positions'])

        # Update per-broker exposures and balances
        for broker_name, broker_state in self.portfolio['brokers'].items():
            open_positions = [p for p in self.portfolio['active_positions'] if p.get('broker') == broker_name]
            broker_state['total_invested'] = sum(p.get('position_size', 0) for p in open_positions)
            open_pnl = sum(p.get('current_pnl', 0) for p in open_positions)
            closed_pnl_broker = sum(p.get('final_pnl', 0) for p in self.portfolio['closed_positions'] if p.get('broker') == broker_name)
            broker_state['realized_pnl'] = closed_pnl_broker
            broker_state['current_balance'] = broker_state.get('available_cash', 0) + broker_state['total_invested'] + open_pnl

        self.portfolio['available_cash'] = sum(b.get('available_cash', 0) for b in self.portfolio['brokers'].values())
        self.portfolio['total_invested'] = sum(b.get('total_invested', 0) for b in self.portfolio['brokers'].values())

        self.portfolio['current_balance'] = (
            self.portfolio['available_cash'] +
            self.portfolio['total_invested'] +
            active_pnl
        )

        self.portfolio['total_pnl'] = active_pnl + closed_pnl
        self.portfolio['total_pnl_pct'] = (self.portfolio['total_pnl'] / self.initial_capital) * 100

        # Update performance metrics
        metrics = self.portfolio['performance_metrics']
        total_trades = metrics['total_trades']

        if total_trades > 0:
            metrics['win_rate'] = (metrics['winning_trades'] / total_trades) * 100

            # Calculate avg win/loss from closed positions
            winning_trades = [p for p in self.portfolio['closed_positions'] if p.get('final_pnl', 0) > 0]
            losing_trades = [p for p in self.portfolio['closed_positions'] if p.get('final_pnl', 0) <= 0]

            if winning_trades:
                metrics['avg_win'] = sum(p['final_pnl'] for p in winning_trades) / len(winning_trades)
            if losing_trades:
                metrics['avg_loss'] = sum(p['final_pnl'] for p in losing_trades) / len(losing_trades)
            
            # Profit factor
            total_wins = sum(p.get('final_pnl', 0) for p in winning_trades)
            total_losses = abs(sum(p.get('final_pnl', 0) for p in losing_trades))
            if total_losses > 0:
                metrics['profit_factor'] = total_wins / total_losses
    
    def get_portfolio_snapshot(self) -> Dict[str, Any]:
        """Get current portfolio snapshot for dashboard"""
        broker_snapshots = {}
        for name, state in self.portfolio.get('brokers', {}).items():
            broker_snapshots[name] = {
                'balance': round(state.get('current_balance', 0), 2),
                'available_cash': round(state.get('available_cash', 0), 2),
                'invested': round(state.get('total_invested', 0), 2),
                'realized_pnl': round(state.get('realized_pnl', 0), 2),
                'strategy': state.get('strategy'),
                'auto_trading': state.get('auto_trading', True),
            }

        return {
            'current_balance': round(self.portfolio['current_balance'], 2),
            'available_cash': round(self.portfolio['available_cash'], 2),
            'total_invested': round(self.portfolio['total_invested'], 2),
            'total_pnl': round(self.portfolio['total_pnl'], 2),
            'total_pnl_pct': round(self.portfolio['total_pnl_pct'], 2),
            'active_positions': len(self.portfolio['active_positions']),
            'performance_metrics': self.portfolio['performance_metrics'],
            'positions': self.portfolio['active_positions'],
            'brokers': broker_snapshots,
        }

    def describe_configuration(self) -> Dict[str, Any]:
        """Describe broker limits, strategies and cluster mapping for quick review."""

        brokers = {}
        for name, profile in self.broker_profiles.items():
            brokers[name] = {
                'strategy': profile.get('strategy'),
                'auto_trading': profile.get('auto_trading', True),
                'risk_per_trade': profile.get('risk_per_trade', self.risk_per_trade),
                'max_position_size': profile.get('max_position_size', self.max_position_size),
                'max_open_trades': profile.get('max_open_trades'),
                'max_trades_per_asset': profile.get('max_trades_per_asset'),
                'cluster_limits': profile.get('cluster_limits', {}),
            }

        return {
            'initial_capital': self.initial_capital,
            'asset_clusters': self.asset_clusters,
            'brokers': brokers,
        }

    def integration_overview(self) -> Dict[str, Any]:
        """Describe how the portfolio manager plugs into the runtime pipeline.

        This is meant to be consumed by orchestration/reporting code so the
        integration stays declarative (what feeds/signals/outputs are expected).
        """

        return {
            'inputs': {
                'market_snapshot': 'modules.engine.market_data.get_market_snapshot(now) for BTC/SPX/EURUSD/Gold',
                'live_quotes': 'modules.engine.market_data.get_live_equity_fx_quotes for tickers referenced by signals',
                'signals': 'modules.brain prediction cards with asset/entry/stop/target/confidence/broker',
            },
            'routing': {
                'automated_brokers': ['IG', 'BYBIT_BTC', 'BYBIT_USDT'],
                'discretionary_brokers': ['DIRECTA', 'TRADE_REPUBLIC'],
                'gate': 'call open_position only when broker auto_trading=True; otherwise surface to UI/advisor queue',
            },
            'risk_checks': [
                'per-broker caps (max_open_trades, max_trades_per_asset, cluster_limits)',
                'sizing via calculate_position_size using broker risk_per_trade and max_position_size',
                'available_cash guardrails updated per broker account',
            ],
            'outputs': {
                'state': self.portfolio_file,
                'snapshot': 'get_portfolio_snapshot for dashboards/telemetry',
                'history': self.history_dir,
                'configuration': 'describe_configuration and integration_overview for UI/help panels',
            },
        }
    
    def save_daily_snapshot(self):
        """Save daily portfolio snapshot for historical tracking.

        Non è richiamato dal dashboard/intraday attuale; può essere usato da
        script schedulati esterni per costruire una cronologia P&L.
        """
        today = datetime.now().strftime('%Y-%m-%d')
        snapshot = {
            'date': today,
            'balance': self.portfolio['current_balance'],
            'pnl': self.portfolio['total_pnl'],
            'pnl_pct': self.portfolio['total_pnl_pct'],
            'active_positions': len(self.portfolio['active_positions']),
            'metrics': self.portfolio['performance_metrics'].copy()
        }
        
        # Add to daily balances
        daily_balances = self.portfolio.get('daily_balances', [])
        # Remove today's entry if exists
        daily_balances = [b for b in daily_balances if b['date'] != today]
        daily_balances.append(snapshot)
        
        # Keep last 90 days
        daily_balances = daily_balances[-90:]
        self.portfolio['daily_balances'] = daily_balances
        
        self._save_portfolio(self.portfolio)
        
        # Also save separate daily file
        daily_file = os.path.join(self.history_dir, f'portfolio_{today}.json')
        try:
            with open(daily_file, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving daily snapshot: {e}")


def get_portfolio_manager(base_dir: str = None) -> SVPortfolioManager:
    """Get portfolio manager instance"""
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent
    
    return SVPortfolioManager(base_dir)


if __name__ == "__main__":
    # Test the portfolio manager
    logging.basicConfig(level=logging.INFO)
    
    portfolio = get_portfolio_manager()
    
    # Test opening position
    test_prediction = {
        "asset": "BTC",
        "direction": "LONG", 
        "entry": 86000,
        "target": 88000,
        "stop": 84000,
        "confidence": 70
    }
    
    position_id = portfolio.open_position(test_prediction, 86500)
    print(f"Opened position: {position_id}")
    
    # Test portfolio snapshot
    snapshot = portfolio.get_portfolio_snapshot()
    print(f"Portfolio snapshot: ${snapshot['current_balance']:.2f}")
    print(f"Active positions: {snapshot['active_positions']}")
    print(f"Total P&L: ${snapshot['total_pnl']:.2f} ({snapshot['total_pnl_pct']:.2f}%)")