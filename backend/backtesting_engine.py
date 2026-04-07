"""
Backtest Engine for Strategy Performance Testing
Test trading strategies on historical data before live deployment
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import statistics

logger = logging.getLogger(__name__)

class BacktestResult:
    """Backtesting result container."""
    
    def __init__(self):
        self.trades = []
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0
        self.max_drawdown = 0.0
        self.win_rate = 0.0
        self.profit_factor = 0.0
        self.sharpe_ratio = 0.0
        self.max_consecutive_wins = 0
        self.max_consecutive_losses = 0
        self.avg_win = 0.0
        self.avg_loss = 0.0
        self.largest_win = 0.0
        self.largest_loss = 0.0

class BacktestingEngine:
    """Backtest trading strategies on historical data."""
    
    def __init__(self, initial_capital: float = 10000.0):
        """
        Initialize backtesting engine.
        
        Args:
            initial_capital: Starting capital for backtest
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.trades = []
        self.equity_curve = []
    
    async def run_backtest(
        self,
        klines: List,
        trading_engine,
        risk_manager,
        timeframe: str = "1h"
    ) -> BacktestResult:
        """
        Run backtest on historical kline data.
        
        Args:
            klines: Historical candlestick data
            trading_engine: Trading engine instance
            risk_manager: Risk manager instance
            timeframe: Chart timeframe
        
        Returns:
            BacktestResult with performance metrics
        """
        logger.info(f"Starting backtest with {len(klines)} candles, capital: ${self.initial_capital}")
        
        self.current_capital = self.initial_capital
        self.trades = []
        self.equity_curve = [self.initial_capital]
        
        position = None
        consecutive_losses = 0
        
        # Use sliding window for indicator calculation
        window_size = 100
        
        for i in range(window_size, len(klines)):
            window_klines = klines[i-window_size:i]
            current_kline = klines[i]
            
            current_price = float(current_kline[4])  # Close price
            timestamp = current_kline[0]
            
            # Get signal from trading engine
            analysis = trading_engine.analyze_signal(window_klines, current_price)
            signal = analysis["signal"]
            confidence = analysis["confidence"]
            indicators = analysis["indicators"]
            
            # Check if we have open position
            if position:
                # Check stop loss
                if position["side"] == "LONG":
                    if current_price <= position["stop_loss"]:
                        pnl = (current_price - position["entry_price"]) * position["quantity"]
                        self._close_position(position, current_price, pnl, "STOP_LOSS", timestamp)
                        position = None
                        if pnl < 0:
                            consecutive_losses += 1
                        else:
                            consecutive_losses = 0
                        continue
                    
                    # Check take profit
                    if position.get("take_profit") and current_price >= position["take_profit"]:
                        pnl = (current_price - position["entry_price"]) * position["quantity"]
                        self._close_position(position, current_price, pnl, "TAKE_PROFIT", timestamp)
                        position = None
                        consecutive_losses = 0
                        continue
            
            # Entry signals
            if not position:
                daily_pnl = sum(t["pnl"] for t in self.trades[-10:] if "pnl" in t)
                
                risk_check = risk_manager.should_trade(daily_pnl, consecutive_losses)
                
                if risk_check["allowed"] and signal in ["BUY", "SELL"] and confidence >= 60:
                    # Calculate position size
                    atr = indicators.get("atr", current_price * 0.02)
                    stop_loss = risk_manager.calculate_stop_loss(current_price, signal, atr)
                    
                    quantity = risk_manager.calculate_position_size(
                        self.current_capital,
                        current_price,
                        stop_loss,
                        atr
                    )
                    
                    if quantity > 0:
                        take_profit = risk_manager.calculate_take_profit(
                            current_price, stop_loss, signal
                        )
                        
                        position = {
                            "side": "LONG" if signal == "BUY" else "SHORT",
                            "entry_price": current_price,
                            "quantity": quantity,
                            "stop_loss": stop_loss,
                            "take_profit": take_profit,
                            "entry_time": timestamp,
                            "indicators": indicators
                        }
                        
                        logger.debug(f"Opened {position['side']} position at ${current_price}")
            
            self.equity_curve.append(self.current_capital)
        
        # Close any remaining position
        if position:
            current_price = float(klines[-1][4])
            pnl = (current_price - position["entry_price"]) * position["quantity"]
            self._close_position(position, current_price, pnl, "BACKTEST_END", klines[-1][0])
        
        return self._calculate_results()
    
    def _close_position(
        self,
        position: Dict,
        exit_price: float,
        pnl: float,
        reason: str,
        timestamp: int
    ):
        """Close position and record trade."""
        self.current_capital += pnl
        
        self.trades.append({
            "side": position["side"],
            "entry_price": position["entry_price"],
            "exit_price": exit_price,
            "quantity": position["quantity"],
            "pnl": pnl,
            "pnl_percent": (pnl / (position["entry_price"] * position["quantity"])) * 100,
            "reason": reason,
            "entry_time": position["entry_time"],
            "exit_time": timestamp,
            "hold_duration": timestamp - position["entry_time"]
        })
        
        logger.debug(f"Closed position - P&L: ${pnl:.2f}, Reason: {reason}")
    
    def _calculate_results(self) -> BacktestResult:
        """Calculate backtest performance metrics."""
        result = BacktestResult()
        
        if not self.trades:
            logger.warning("No trades executed in backtest")
            return result
        
        result.trades = self.trades
        result.total_trades = len(self.trades)
        
        winning_trades = [t for t in self.trades if t["pnl"] > 0]
        losing_trades = [t for t in self.trades if t["pnl"] < 0]
        
        result.winning_trades = len(winning_trades)
        result.losing_trades = len(losing_trades)
        result.total_pnl = sum(t["pnl"] for t in self.trades)
        
        # Win rate
        result.win_rate = (result.winning_trades / result.total_trades * 100) if result.total_trades > 0 else 0
        
        # Average win/loss
        result.avg_win = statistics.mean([t["pnl"] for t in winning_trades]) if winning_trades else 0
        result.avg_loss = statistics.mean([t["pnl"] for t in losing_trades]) if losing_trades else 0
        
        # Largest win/loss
        result.largest_win = max([t["pnl"] for t in winning_trades]) if winning_trades else 0
        result.largest_loss = min([t["pnl"] for t in losing_trades]) if losing_trades else 0
        
        # Profit factor
        total_wins = sum(t["pnl"] for t in winning_trades)
        total_losses = abs(sum(t["pnl"] for t in losing_trades))
        result.profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        # Max drawdown
        result.max_drawdown = self._calculate_max_drawdown()
        
        # Consecutive wins/losses
        result.max_consecutive_wins = self._max_consecutive(self.trades, True)
        result.max_consecutive_losses = self._max_consecutive(self.trades, False)
        
        # Sharpe ratio (simplified)
        if len(self.trades) > 1:
            returns = [t["pnl_percent"] for t in self.trades]
            avg_return = statistics.mean(returns)
            std_return = statistics.stdev(returns)
            result.sharpe_ratio = (avg_return / std_return) if std_return > 0 else 0
        
        logger.info(
            f"Backtest complete - Trades: {result.total_trades}, "
            f"Win Rate: {result.win_rate:.2f}%, Total P&L: ${result.total_pnl:.2f}"
        )
        
        return result
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown."""
        if not self.equity_curve:
            return 0.0
        
        peak = self.equity_curve[0]
        max_dd = 0.0
        
        for equity in self.equity_curve:
            if equity > peak:
                peak = equity
            
            drawdown = (peak - equity) / peak * 100
            max_dd = max(max_dd, drawdown)
        
        return max_dd
    
    def _max_consecutive(self, trades: List[Dict], wins: bool) -> int:
        """Calculate max consecutive wins or losses."""
        max_consecutive = 0
        current_consecutive = 0
        
        for trade in trades:
            if (wins and trade["pnl"] > 0) or (not wins and trade["pnl"] < 0):
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
