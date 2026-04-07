"""
Advanced Trading Strategies
Includes breakout detection, volume analysis, and news filtering

TODO: Replace NEWS_API_KEY in .env with your key from https://newsapi.org
"""

import httpx
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AdvancedStrategies:
    """Advanced trading strategy analysis."""
    
    def __init__(self, news_api_key: Optional[str] = None):
        """
        Initialize advanced strategies.
        
        Args:
            news_api_key: NewsAPI key (TODO: Get from https://newsapi.org)
        """
        self.news_api_key = news_api_key
        self.client = httpx.AsyncClient(timeout=10.0)
        self.use_mock_news = self._is_dummy_key()
        
        if self.use_mock_news:
            logger.warning("Using MOCK news data - Add NEWS_API_KEY in .env for real news filtering")
    
    def _is_dummy_key(self) -> bool:
        """Check if using dummy API key."""
        return not self.news_api_key or "DUMMY" in self.news_api_key
    
    def detect_breakout(
        self,
        klines: List,
        current_price: float,
        lookback_period: int = 20
    ) -> Dict:
        """
        Detect price breakout from recent range.
        
        Args:
            klines: Historical candlestick data
            current_price: Current market price
            lookback_period: Number of candles to analyze
        
        Returns:
            dict with breakout details
        """
        if len(klines) < lookback_period:
            return {"breakout": False, "type": None}
        
        recent_klines = klines[-lookback_period:]
        
        # Calculate resistance (highest high)
        highs = [float(k[2]) for k in recent_klines]
        resistance = max(highs)
        
        # Calculate support (lowest low)
        lows = [float(k[3]) for k in recent_klines]
        support = min(lows)
        
        # Calculate range
        price_range = resistance - support
        range_percent = (price_range / support) * 100
        
        # Breakout detection
        breakout_threshold = 0.002  # 0.2% beyond range
        
        if current_price > resistance * (1 + breakout_threshold):
            return {
                "breakout": True,
                "type": "RESISTANCE_BREAKOUT",
                "level": resistance,
                "strength": ((current_price - resistance) / resistance) * 100,
                "range_percent": range_percent,
                "support": support,
                "resistance": resistance
            }
        
        elif current_price < support * (1 - breakout_threshold):
            return {
                "breakout": True,
                "type": "SUPPORT_BREAKDOWN",
                "level": support,
                "strength": ((support - current_price) / support) * 100,
                "range_percent": range_percent,
                "support": support,
                "resistance": resistance
            }
        
        else:
            return {
                "breakout": False,
                "type": "RANGE_BOUND",
                "range_percent": range_percent,
                "support": support,
                "resistance": resistance
            }
    
    def analyze_volume(
        self,
        klines: List,
        lookback_period: int = 20
    ) -> Dict:
        """
        Analyze volume patterns for confirmation.
        
        Args:
            klines: Historical candlestick data
            lookback_period: Number of candles to analyze
        
        Returns:
            dict with volume analysis
        """
        if len(klines) < lookback_period:
            return {"volume_spike": False}
        
        recent_klines = klines[-lookback_period:]
        current_volume = float(klines[-1][5])
        
        # Calculate average volume
        volumes = [float(k[5]) for k in recent_klines[:-1]]
        avg_volume = sum(volumes) / len(volumes)
        
        # Volume spike detection
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        is_spike = volume_ratio > 1.5  # 50% above average
        
        # Price-volume correlation
        price_change = (float(klines[-1][4]) - float(klines[-2][4])) / float(klines[-2][4])
        
        return {
            "volume_spike": is_spike,
            "volume_ratio": round(volume_ratio, 2),
            "avg_volume": avg_volume,
            "current_volume": current_volume,
            "price_change_percent": round(price_change * 100, 2),
            "volume_confirmation": is_spike and abs(price_change) > 0.01,
            "buying_pressure": is_spike and price_change > 0,
            "selling_pressure": is_spike and price_change < 0
        }
    
    async def check_news_events(
        self,
        symbol: str,
        hours_lookback: int = 24
    ) -> Dict:
        """
        Check for major news events that could affect trading.
        
        Args:
            symbol: Trading symbol (e.g., "BTC", "ETH")
            hours_lookback: Hours to look back for news
        
        Returns:
            dict with news event details
        """
        if self.use_mock_news:
            return self._mock_news_check()
        
        try:
            # Extract cryptocurrency name from symbol
            crypto_name = symbol.replace("USDT", "").replace("USD", "")
            
            from_date = (datetime.now() - timedelta(hours=hours_lookback)).strftime('%Y-%m-%d')
            
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": f"{crypto_name} OR Bitcoin OR cryptocurrency",
                "from": from_date,
                "sortBy": "publishedAt",
                "language": "en",
                "apiKey": self.news_api_key
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get("articles", [])
            
            # Filter for high-impact keywords
            high_impact_keywords = [
                "crash", "surge", "breakthrough", "regulation", "ban",
                "sec", "fed", "central bank", "hack", "exploit"
            ]
            
            high_impact_news = []
            for article in articles[:10]:
                title = article.get("title", "").lower()
                description = article.get("description", "").lower()
                
                if any(keyword in title or keyword in description for keyword in high_impact_keywords):
                    high_impact_news.append({
                        "title": article.get("title"),
                        "source": article.get("source", {}).get("name"),
                        "published_at": article.get("publishedAt"),
                        "url": article.get("url")
                    })
            
            return {
                "has_major_news": len(high_impact_news) > 0,
                "news_count": len(articles),
                "high_impact_count": len(high_impact_news),
                "high_impact_news": high_impact_news[:3],
                "trading_recommendation": "AVOID" if len(high_impact_news) > 2 else "PROCEED_WITH_CAUTION" if len(high_impact_news) > 0 else "NORMAL"
            }
        
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            return self._mock_news_check()
    
    def _mock_news_check(self) -> Dict:
        """Mock news check for testing."""
        return {
            "has_major_news": False,
            "news_count": 5,
            "high_impact_count": 0,
            "high_impact_news": [],
            "trading_recommendation": "NORMAL",
            "note": "MOCK MODE - Replace NEWS_API_KEY in .env for real news"
        }
    
    def detect_consolidation(
        self,
        klines: List,
        lookback_period: int = 20,
        consolidation_threshold: float = 0.02
    ) -> Dict:
        """
        Detect price consolidation (tight range).
        
        Args:
            klines: Historical candlestick data
            lookback_period: Number of candles to analyze
            consolidation_threshold: Max range as % for consolidation (2% default)
        
        Returns:
            dict with consolidation details
        """
        if len(klines) < lookback_period:
            return {"consolidating": False}
        
        recent_klines = klines[-lookback_period:]
        
        highs = [float(k[2]) for k in recent_klines]
        lows = [float(k[3]) for k in recent_klines]
        
        highest = max(highs)
        lowest = min(lows)
        
        price_range = highest - lowest
        range_percent = (price_range / lowest) * 100
        
        is_consolidating = range_percent < (consolidation_threshold * 100)
        
        return {
            "consolidating": is_consolidating,
            "range_percent": round(range_percent, 2),
            "highest": highest,
            "lowest": lowest,
            "mid_point": (highest + lowest) / 2,
            "duration_candles": lookback_period,
            "breakout_potential": "HIGH" if is_consolidating and lookback_period > 15 else "LOW"
        }
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
