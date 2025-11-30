#!/usr/bin/env python3
"""
SV Portfolio Manager - $25K Initial Capital
Tracks ML signals and calculates real P&L for dashboard display
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SVPortfolioManager:
    """Manages $25K simulated portfolio tracking ML signals"""
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.portfolio_file = os.path.join(base_dir, 'backups', 'portfolio_state.json')
        self.history_dir = os.path.join(base_dir, 'reports', 'portfolio_history')
        
        # Portfolio configuration
        self.initial_capital = 25000.0
        self.max_position_size = 0.20  # 20% max per trade
        self.risk_per_trade = 0.02     # 2% risk per trade
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.portfolio_file), exist_ok=True)
        os.makedirs(self.history_dir, exist_ok=True)
        
        self.portfolio = self._load_portfolio()
    
    def _load_portfolio(self) -> Dict[str, Any]:
        """Load portfolio state from disk or create new one"""
        if os.path.exists(self.portfolio_file):
            try:
                with open(self.portfolio_file, 'r', encoding='utf-8') as f:
                    portfolio = json.load(f)
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
    
    def calculate_position_size(self, entry_price: float, stop_price: float, 
                              confidence: int) -> float:
        """Calculate position size based on risk management rules"""
        if entry_price <= 0 or stop_price <= 0 or confidence <= 0:
            return 0.0
        
        # Risk amount (2% of current balance)
        risk_amount = self.portfolio['current_balance'] * self.risk_per_trade
        
        # Distance to stop loss
        risk_per_unit = abs(entry_price - stop_price)
        if risk_per_unit <= 0:
            return 0.0
        
        # Base position size
        base_size = risk_amount / risk_per_unit * entry_price
        
        # Confidence multiplier (50-100% confidence -> 0.5-1.0x)
        confidence_mult = max(0.5, min(1.0, confidence / 100.0))
        position_size = base_size * confidence_mult
        
        # Max position size limit (20% of portfolio)
        max_size = self.portfolio['current_balance'] * self.max_position_size
        position_size = min(position_size, max_size)
        
        # Available cash limit
        available_cash = self.portfolio['available_cash']
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
            
            if not all([asset, entry_price, target_price, stop_price]):
                logger.warning("Invalid prediction data for position opening")
                return None
            
            # Use current price if provided, otherwise use entry price
            live_price = current_price or entry_price
            
            # Calculate position size
            position_size = self.calculate_position_size(entry_price, stop_price, confidence)
            
            if position_size < 100:  # Minimum $100 position
                logger.info(f"Position size too small: ${position_size:.2f}")
                return None
            
            # Calculate units
            units = position_size / entry_price
            
            # Create position ID
            position_id = f"{asset}_{direction}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create position object
            position = {
                "id": position_id,
                "asset": asset,
                "direction": direction,
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
            self.portfolio['available_cash'] -= position_size
            self.portfolio['total_invested'] += position_size
            
            self._save_portfolio(self.portfolio)
            
            logger.info(f"Opened {direction} position: {asset} ${position_size:.2f} @ {entry_price}")
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
        
        # Update portfolio
        self.portfolio['closed_positions'].append(position)
        self.portfolio['available_cash'] += position['position_size'] + pnl
        self.portfolio['total_invested'] -= position['position_size']
        
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
        return {
            'current_balance': round(self.portfolio['current_balance'], 2),
            'available_cash': round(self.portfolio['available_cash'], 2),
            'total_invested': round(self.portfolio['total_invested'], 2),
            'total_pnl': round(self.portfolio['total_pnl'], 2),
            'total_pnl_pct': round(self.portfolio['total_pnl_pct'], 2),
            'active_positions': len(self.portfolio['active_positions']),
            'performance_metrics': self.portfolio['performance_metrics'],
            'positions': self.portfolio['active_positions']
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
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
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