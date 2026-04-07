import numpy as np
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class TechnicalIndicators:
    """Calculate technical indicators for trading analysis."""
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average."""
        if len(prices) < period:
            return None
        
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        
        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return round(ema, 8)
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index."""
        if len(prices) < period + 1:
            return None
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            diff = prices[i] - prices[i-1]
            if diff > 0:
                gains.append(diff)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(diff))
        
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        for i in range(period, len(gains)):
            avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
            avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 2)
    
    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """Calculate MACD indicator."""
        if len(prices) < slow:
            return {"macd": None, "signal": None, "histogram": None}
        
        ema_fast = TechnicalIndicators.calculate_ema(prices, fast)
        ema_slow = TechnicalIndicators.calculate_ema(prices, slow)
        
        if ema_fast is None or ema_slow is None:
            return {"macd": None, "signal": None, "histogram": None}
        
        macd_line = ema_fast - ema_slow
        
        macd_values = []
        for i in range(slow, len(prices)):
            fast_ema = TechnicalIndicators.calculate_ema(prices[:i+1], fast)
            slow_ema = TechnicalIndicators.calculate_ema(prices[:i+1], slow)
            if fast_ema and slow_ema:
                macd_values.append(fast_ema - slow_ema)
        
        signal_line = TechnicalIndicators.calculate_ema(macd_values, signal) if len(macd_values) >= signal else None
        histogram = (macd_line - signal_line) if signal_line else None
        
        return {
            "macd": round(macd_line, 8) if macd_line else None,
            "signal": round(signal_line, 8) if signal_line else None,
            "histogram": round(histogram, 8) if histogram else None
        }
    
    @staticmethod
    def calculate_vwap(prices: List[float], volumes: List[float]) -> float:
        """Calculate Volume Weighted Average Price."""
        if len(prices) != len(volumes) or len(prices) == 0:
            return None
        
        cumulative_pv = sum(p * v for p, v in zip(prices, volumes))
        cumulative_v = sum(volumes)
        
        if cumulative_v == 0:
            return None
        
        vwap = cumulative_pv / cumulative_v
        return round(vwap, 8)
    
    @staticmethod
    def calculate_atr(high: List[float], low: List[float], close: List[float], period: int = 14) -> float:
        """Calculate Average True Range for volatility."""
        if len(high) < period or len(low) < period or len(close) < period:
            return None
        
        true_ranges = []
        for i in range(1, len(close)):
            tr1 = high[i] - low[i]
            tr2 = abs(high[i] - close[i-1])
            tr3 = abs(low[i] - close[i-1])
            true_ranges.append(max(tr1, tr2, tr3))
        
        atr = sum(true_ranges[:period]) / period
        
        for tr in true_ranges[period:]:
            atr = ((atr * (period - 1)) + tr) / period
        
        return round(atr, 8)

class TradingEngine:
    """Core trading engine with multi-indicator analysis."""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
    
    def analyze_signal(self, klines: List, current_price: float) -> Dict:
        """Analyze trading signals based on indicators."""
        
        closes = [float(k[4]) for k in klines]
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]
        volumes = [float(k[5]) for k in klines]
        
        ema_9 = self.indicators.calculate_ema(closes, 9)
        ema_21 = self.indicators.calculate_ema(closes, 21)
        ema_50 = self.indicators.calculate_ema(closes, 50)
        rsi = self.indicators.calculate_rsi(closes, 14)
        macd_data = self.indicators.calculate_macd(closes)
        vwap = self.indicators.calculate_vwap(closes, volumes)
        atr = self.indicators.calculate_atr(highs, lows, closes, 14)
        
        indicators_data = {
            "ema_9": ema_9,
            "ema_21": ema_21,
            "ema_50": ema_50,
            "rsi": rsi,
            "macd": macd_data.get("macd"),
            "macd_signal": macd_data.get("signal"),
            "vwap": vwap,
            "atr": atr,
            "current_price": current_price
        }
        
        signal = self._evaluate_signal(indicators_data)
        
        return {
            "signal": signal,
            "indicators": indicators_data,
            "confidence": self._calculate_confidence(indicators_data, signal)
        }
    
    def _evaluate_signal(self, ind: Dict) -> str:
        """Evaluate buy/sell/hold signal."""
        
        if None in [ind.get("ema_9"), ind.get("ema_21"), ind.get("ema_50"), ind.get("rsi")]:
            return "HOLD"
        
        buy_conditions = 0
        sell_conditions = 0
        
        if ind["ema_9"] > ind["ema_21"] > ind["ema_50"]:
            buy_conditions += 1
        elif ind["ema_9"] < ind["ema_21"] < ind["ema_50"]:
            sell_conditions += 1
        
        if 55 <= ind["rsi"] <= 70:
            buy_conditions += 1
        elif 30 <= ind["rsi"] <= 45:
            sell_conditions += 1
        elif 45 < ind["rsi"] < 55:
            return "HOLD"
        
        if ind.get("macd") and ind.get("macd_signal"):
            if ind["macd"] > ind["macd_signal"]:
                buy_conditions += 1
            else:
                sell_conditions += 1
        
        if ind.get("vwap") and ind["current_price"] > ind["vwap"]:
            buy_conditions += 1
        elif ind.get("vwap") and ind["current_price"] < ind["vwap"]:
            sell_conditions += 1
        
        if buy_conditions >= 3:
            return "BUY"
        elif sell_conditions >= 3:
            return "SELL"
        else:
            return "HOLD"
    
    def _calculate_confidence(self, ind: Dict, signal: str) -> float:
        """Calculate confidence score for signal."""
        if signal == "HOLD":
            return 0.0
        
        score = 0
        total = 0
        
        if ind.get("ema_9") and ind.get("ema_21") and ind.get("ema_50"):
            total += 1
            if (signal == "BUY" and ind["ema_9"] > ind["ema_21"] > ind["ema_50"]) or \
               (signal == "SELL" and ind["ema_9"] < ind["ema_21"] < ind["ema_50"]):
                score += 1
        
        if ind.get("rsi"):
            total += 1
            if (signal == "BUY" and 55 <= ind["rsi"] <= 70) or \
               (signal == "SELL" and 30 <= ind["rsi"] <= 45):
                score += 1
        
        if ind.get("macd") and ind.get("macd_signal"):
            total += 1
            if (signal == "BUY" and ind["macd"] > ind["macd_signal"]) or \
               (signal == "SELL" and ind["macd"] < ind["macd_signal"]):
                score += 1
        
        if total > 0:
            return round((score / total) * 100, 2)
        return 0.0