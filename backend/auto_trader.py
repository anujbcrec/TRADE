"""
Automated Trading System
Executes trades based on signals when AUTO_TRADE_ENABLED=true
"""

import logging
from typing import Dict, Optional
from datetime import datetime, timezone
from models import Trade
from risk_manager import RiskManager

logger = logging.getLogger(__name__)

class AutoTrader:
    """Automated trading execution system."""
    
    def __init__(
        self,
        enabled: bool = False,
        min_confidence: int = 75,
        max_position_size: float = 10000
    ):
        """
        Initialize auto-trader.
        
        Args:
            enabled: Enable/disable auto-trading
            min_confidence: Minimum signal confidence to trade (0-100)
            max_position_size: Maximum position size in USD
        """
        self.enabled = enabled
        self.min_confidence = min_confidence
        self.max_position_size = max_position_size
        self.risk_manager = RiskManager()
        
        logger.info(
            f"AutoTrader initialized - Enabled: {enabled}, "
            f"Min Confidence: {min_confidence}%, Max Size: ${max_position_size}"
        )
    
    def should_execute_trade(
        self,
        signal: str,
        confidence: float,
        indicators: Dict,
        daily_pnl: float,
        consecutive_losses: int
    ) -> Dict:
        """
        Determine if auto-trade should execute.
        
        Returns:
            dict with 'should_trade' (bool) and 'reason' (str)
        """
        if not self.enabled:
            return {
                "should_trade": False,
                "reason": "Auto-trading is disabled. Enable in settings or .env (AUTO_TRADE_ENABLED=true)"
            }
        
        if signal == "HOLD":
            return {
                "should_trade": False,
                "reason": "Signal is HOLD - no clear trading opportunity"
            }
        
        if confidence < self.min_confidence:
            return {
                "should_trade": False,
                "reason": f"Confidence {confidence}% below minimum threshold {self.min_confidence}%"
            }
        
        risk_check = self.risk_manager.should_trade(daily_pnl, consecutive_losses)
        if not risk_check["allowed"]:
            return {
                "should_trade": False,
                "reason": f"Risk check failed: {risk_check['reason']}"
            }
        
        if not self._validate_indicators(indicators, signal):
            return {
                "should_trade": False,
                "reason": "Indicator validation failed - conflicting signals"
            }
        
        return {
            "should_trade": True,
            "reason": f"{signal} signal with {confidence}% confidence - All checks passed"
        }
    
    def _validate_indicators(self, indicators: Dict, signal: str) -> bool:
        """Additional indicator validation for safety."""
        
        rsi = indicators.get('rsi')
        if rsi is None:
            return False
        
        if signal == "BUY":
            if rsi > 80:
                logger.warning(f"RSI too high ({rsi}) for BUY signal - potential overbought")
                return False
            
            if not (indicators.get('ema_9', 0) > indicators.get('ema_21', 0)):
                logger.warning("EMA trend not aligned with BUY signal")
                return False
        
        elif signal == "SELL":
            if rsi < 20:
                logger.warning(f"RSI too low ({rsi}) for SELL signal - potential oversold")
                return False
            
            if not (indicators.get('ema_9', 0) < indicators.get('ema_21', 0)):
                logger.warning("EMA trend not aligned with SELL signal")
                return False
        
        return True
    
    def calculate_position_size(
        self,
        capital: float,
        current_price: float,
        indicators: Dict
    ) -> float:
        """
        Calculate optimal position size.
        
        Args:
            capital: Available capital
            current_price: Current market price
            indicators: Technical indicators (includes ATR)
        """
        atr = indicators.get('atr')
        
        entry_price = current_price
        side = "BUY"
        
        stop_loss = self.risk_manager.calculate_stop_loss(entry_price, side, atr)
        
        position_size = self.risk_manager.calculate_position_size(
            capital, entry_price, stop_loss, atr
        )
        
        max_quantity = self.max_position_size / current_price
        
        final_quantity = min(position_size, max_quantity)
        
        logger.info(
            f"Position sizing - Capital: ${capital}, Price: ${current_price}, "
            f"ATR: {atr}, Calculated: {position_size}, Final: {final_quantity}"
        )
        
        return round(final_quantity, 8)
    
    def create_auto_trade_record(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        indicators: Dict,
        confidence: float
    ) -> Trade:
        """Create trade record for auto-executed trade."""
        
        return Trade(
            symbol=symbol,
            side=side,
            order_type="MARKET",
            quantity=quantity,
            price=price,
            total_value=quantity * price,
            status="FILLED",
            indicators=indicators,
            strategy=f"AUTO_TRADE_{confidence:.1f}%_CONFIDENCE",
            timestamp=datetime.now(timezone.utc)
        )
    
    def get_status(self) -> Dict:
        """Get auto-trader status."""
        return {
            "enabled": self.enabled,
            "min_confidence": self.min_confidence,
            "max_position_size": self.max_position_size,
            "risk_per_trade": self.risk_manager.max_risk_per_trade,
            "max_daily_loss": self.risk_manager.max_daily_loss,
            "max_consecutive_losses": self.risk_manager.max_consecutive_losses
        }
