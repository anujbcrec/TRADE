"""
TradingView Webhook Handler
Receives and validates trading signals from TradingView alerts

TODO: Change WEBHOOK_SECRET in .env for security

TradingView Alert Message Format (JSON):
{
    "secret": "your_webhook_secret",
    "symbol": "BTCUSDT",
    "action": "BUY",
    "price": 50000.0,
    "time": "2024-01-01 12:00:00",
    "strategy": "EMA_CROSSOVER",
    "timeframe": "1h"
}
"""

import logging
from typing import Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class TradingViewSignal(BaseModel):
    """TradingView webhook signal model."""
    secret: str
    symbol: str
    action: str  # BUY, SELL, CLOSE
    price: Optional[float] = None
    time: Optional[str] = None
    strategy: Optional[str] = "TRADINGVIEW"
    timeframe: Optional[str] = "1h"
    quantity: Optional[float] = None

class WebhookHandler:
    """Handle TradingView webhook signals."""
    
    def __init__(self, secret: str):
        """
        Initialize webhook handler.
        
        Args:
            secret: Webhook authentication secret (TODO: Change in .env)
        """
        self.secret = secret
        self.signal_history = []
        self.max_history = 100
        
        if not secret or secret == "change_this_secret_key" or "DUMMY" in secret:
            logger.warning(
                "Using default/dummy webhook secret! "
                "Change WEBHOOK_SECRET in .env for production"
            )
    
    def validate_signal(self, signal: TradingViewSignal) -> Dict:
        """
        Validate incoming webhook signal.
        
        Returns:
            dict with 'valid' (bool) and 'reason' (str)
        """
        # Verify secret
        if signal.secret != self.secret:
            logger.warning("Invalid webhook secret received")
            return {
                "valid": False,
                "reason": "Invalid webhook secret - unauthorized request"
            }
        
        # Validate action
        if signal.action not in ["BUY", "SELL", "CLOSE"]:
            return {
                "valid": False,
                "reason": f"Invalid action: {signal.action}. Must be BUY, SELL, or CLOSE"
            }
        
        # Validate symbol
        if not signal.symbol or len(signal.symbol) < 3:
            return {
                "valid": False,
                "reason": "Invalid or missing symbol"
            }
        
        # Check for duplicate signals (within 10 seconds)
        if self._is_duplicate_signal(signal):
            return {
                "valid": False,
                "reason": "Duplicate signal detected - already processed recently"
            }
        
        # Validate price if provided
        if signal.price is not None and signal.price <= 0:
            return {
                "valid": False,
                "reason": "Invalid price value"
            }
        
        return {
            "valid": True,
            "reason": "Signal validation passed"
        }
    
    def _is_duplicate_signal(self, signal: TradingViewSignal) -> bool:
        """
        Check if signal is duplicate of recent signal.
        """
        current_time = datetime.now()
        
        for hist_signal in self.signal_history[-10:]:
            if (
                hist_signal["symbol"] == signal.symbol and
                hist_signal["action"] == signal.action and
                (current_time - hist_signal["timestamp"]).total_seconds() < 10
            ):
                return True
        
        return False
    
    def record_signal(self, signal: TradingViewSignal, status: str):
        """
        Record processed signal in history.
        """
        self.signal_history.append({
            "symbol": signal.symbol,
            "action": signal.action,
            "strategy": signal.strategy,
            "status": status,
            "timestamp": datetime.now()
        })
        
        # Keep only last N signals
        if len(self.signal_history) > self.max_history:
            self.signal_history = self.signal_history[-self.max_history:]
    
    def get_signal_history(self, limit: int = 50) -> list:
        """
        Get recent signal history.
        """
        return self.signal_history[-limit:]
    
    def process_signal(self, signal: TradingViewSignal) -> Dict:
        """
        Process and prepare signal for execution.
        
        Returns:
            dict with signal details ready for trading engine
        """
        return {
            "symbol": signal.symbol,
            "side": signal.action,
            "price": signal.price,
            "strategy": signal.strategy or "TRADINGVIEW",
            "timeframe": signal.timeframe or "1h",
            "quantity": signal.quantity,
            "source": "TRADINGVIEW_WEBHOOK",
            "timestamp": datetime.now().isoformat()
        }
