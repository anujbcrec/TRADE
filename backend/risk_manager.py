from typing import Dict, Optional
import logging
from models import Position
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class RiskManager:
    """Risk management system for trading."""
    
    def __init__(self, max_risk_per_trade: float = 0.02, max_daily_loss: float = 0.05, max_consecutive_losses: int = 3):
        self.max_risk_per_trade = max_risk_per_trade
        self.max_daily_loss = max_daily_loss
        self.max_consecutive_losses = max_consecutive_losses
        self.consecutive_losses = 0
        self.daily_pnl = 0.0
    
    def calculate_position_size(self, capital: float, entry_price: float, stop_loss: float, atr: Optional[float] = None) -> float:
        """Calculate position size based on risk per trade."""
        
        risk_amount = capital * self.max_risk_per_trade
        
        price_risk = abs(entry_price - stop_loss)
        
        if atr and atr > 0:
            price_risk = max(price_risk, atr * 2)
        
        if price_risk <= 0:
            logger.warning("Invalid price risk calculation")
            return 0.0
        
        position_size = risk_amount / price_risk
        
        return round(position_size, 8)
    
    def calculate_stop_loss(self, entry_price: float, side: str, atr: Optional[float] = None) -> float:
        """Calculate dynamic stop loss based on ATR."""
        
        if atr and atr > 0:
            atr_multiplier = 2.0
            stop_distance = atr * atr_multiplier
        else:
            stop_distance = entry_price * 0.02
        
        if side == "BUY" or side == "LONG":
            stop_loss = entry_price - stop_distance
        else:
            stop_loss = entry_price + stop_distance
        
        return round(stop_loss, 8)
    
    def calculate_take_profit(self, entry_price: float, stop_loss: float, side: str, risk_reward: float = 2.0) -> float:
        """Calculate take profit based on risk-reward ratio."""
        
        risk = abs(entry_price - stop_loss)
        reward = risk * risk_reward
        
        if side == "BUY" or side == "LONG":
            take_profit = entry_price + reward
        else:
            take_profit = entry_price - reward
        
        return round(take_profit, 8)
    
    def should_trade(self, daily_pnl: float, consecutive_losses: int) -> Dict:
        """Check if trading should be allowed based on risk rules."""
        
        if consecutive_losses >= self.max_consecutive_losses:
            return {
                "allowed": False,
                "reason": f"Max consecutive losses ({self.max_consecutive_losses}) reached"
            }
        
        if daily_pnl <= -self.max_daily_loss:
            return {
                "allowed": False,
                "reason": f"Daily loss limit ({self.max_daily_loss * 100}%) exceeded"
            }
        
        return {"allowed": True, "reason": "All risk checks passed"}
    
    def update_trailing_stop(self, position: Position, current_price: float, trailing_percent: float = 0.02) -> Optional[float]:
        """Update trailing stop loss."""
        
        if position.side == "LONG":
            if current_price > position.entry_price:
                profit = current_price - position.entry_price
                new_trailing_stop = current_price - (current_price * trailing_percent)
                
                if position.trailing_stop is None or new_trailing_stop > position.trailing_stop:
                    return round(new_trailing_stop, 8)
        else:
            if current_price < position.entry_price:
                profit = position.entry_price - current_price
                new_trailing_stop = current_price + (current_price * trailing_percent)
                
                if position.trailing_stop is None or new_trailing_stop < position.trailing_stop:
                    return round(new_trailing_stop, 8)
        
        return position.trailing_stop