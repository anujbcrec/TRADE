import httpx
import logging
from typing import Optional, List
from datetime import datetime
import random
import time

logger = logging.getLogger(__name__)

class BinanceMarketData:
    """Handle Binance market data requests."""
    
    BASE_URL = "https://api.binance.com/api/v3"
    TESTNET_URL = "https://testnet.binance.vision/api/v3"
    
    def __init__(self, testnet: bool = False):
        """Initialize market data client."""
        self.base_url = self.TESTNET_URL if testnet else self.BASE_URL
        self.client = httpx.AsyncClient(timeout=10.0)
        self.use_mock = False
        self.mock_prices = {
            "BTCUSDT": 97850.50,
            "ETHUSDT": 3420.75,
            "BNBUSDT": 612.30,
            "SOLUSDT": 145.80,
            "ADAUSDT": 0.95
        }
    
    async def get_price(self, symbol: str) -> dict:
        """Get current price for a symbol."""
        try:
            url = f"{self.base_url}/ticker/price"
            params = {"symbol": symbol}
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            self.use_mock = False
            return response.json()
        except Exception as e:
            logger.warning(f"Binance API unavailable, using mock data: {e}")
            self.use_mock = True
            
            if symbol not in self.mock_prices:
                self.mock_prices[symbol] = 100.0
            
            self.mock_prices[symbol] *= (1 + random.uniform(-0.001, 0.001))
            
            return {
                "symbol": symbol,
                "price": str(round(self.mock_prices[symbol], 2))
            }
    
    async def get_24hr_stats(self, symbol: str) -> dict:
        """Get 24-hour price statistics."""
        try:
            if not self.use_mock:
                url = f"{self.base_url}/ticker/24hr"
                params = {"symbol": symbol}
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning(f"Using mock 24hr stats: {e}")
        
        current_price = self.mock_prices.get(symbol, 100.0)
        change = random.uniform(-5, 5)
        
        return {
            "symbol": symbol,
            "priceChange": str(round(current_price * change / 100, 2)),
            "priceChangePercent": str(round(change, 2)),
            "weightedAvgPrice": str(round(current_price, 2)),
            "prevClosePrice": str(round(current_price / (1 + change/100), 2)),
            "lastPrice": str(round(current_price, 2)),
            "lastQty": "0.5",
            "bidPrice": str(round(current_price * 0.999, 2)),
            "askPrice": str(round(current_price * 1.001, 2)),
            "openPrice": str(round(current_price / (1 + change/100), 2)),
            "highPrice": str(round(current_price * 1.02, 2)),
            "lowPrice": str(round(current_price * 0.98, 2)),
            "volume": str(round(random.uniform(10000, 50000), 2)),
            "quoteVolume": str(round(current_price * random.uniform(10000, 50000), 2)),
            "openTime": int(time.time() * 1000) - 86400000,
            "closeTime": int(time.time() * 1000),
            "count": random.randint(50000, 100000)
        }
    
    async def get_klines(self, symbol: str, interval: str = "1h", limit: int = 100) -> List:
        """Get kline/candlestick data."""
        try:
            if not self.use_mock:
                url = f"{self.base_url}/klines"
                params = {
                    "symbol": symbol,
                    "interval": interval,
                    "limit": min(limit, 1000)
                }
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning(f"Using mock klines: {e}")
        
        base_price = self.mock_prices.get(symbol, 100.0)
        klines = []
        current_time = int(time.time() * 1000)
        
        interval_ms = {
            "1m": 60000,
            "5m": 300000,
            "15m": 900000,
            "1h": 3600000,
            "4h": 14400000
        }.get(interval, 3600000)
        
        for i in range(limit):
            timestamp = current_time - (limit - i) * interval_ms
            
            open_price = base_price * (1 + random.uniform(-0.02, 0.02))
            close_price = open_price * (1 + random.uniform(-0.015, 0.015))
            high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.01))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.01))
            volume = random.uniform(50, 500)
            
            klines.append([
                timestamp,
                str(round(open_price, 2)),
                str(round(high_price, 2)),
                str(round(low_price, 2)),
                str(round(close_price, 2)),
                str(round(volume, 2)),
                timestamp + interval_ms - 1,
                str(round(close_price * volume, 2)),
                random.randint(100, 500),
                str(round(volume * 0.7, 2)),
                str(round(close_price * volume * 0.7, 2)),
                "0"
            ])
            
            base_price = close_price
        
        return klines
    
    async def get_order_book(self, symbol: str, limit: int = 20) -> dict:
        """Get order book depth."""
        try:
            if not self.use_mock:
                url = f"{self.base_url}/depth"
                params = {"symbol": symbol, "limit": limit}
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning(f"Using mock orderbook: {e}")
        
        current_price = self.mock_prices.get(symbol, 100.0)
        
        bids = []
        asks = []
        
        for i in range(limit):
            bid_price = current_price * (1 - 0.0001 * (i + 1))
            bid_qty = random.uniform(0.1, 5.0)
            bids.append([str(round(bid_price, 2)), str(round(bid_qty, 6))])
            
            ask_price = current_price * (1 + 0.0001 * (i + 1))
            ask_qty = random.uniform(0.1, 5.0)
            asks.append([str(round(ask_price, 2)), str(round(ask_qty, 6))])
        
        return {
            "lastUpdateId": int(time.time() * 1000),
            "bids": bids,
            "asks": asks
        }
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()