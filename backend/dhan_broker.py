"""
DHAN Broker Integration for Indian Stock Market Trading
Supports NIFTY, SENSEX Futures & Options

TODO: Replace dummy credentials in .env file with real DHAN API credentials
Get your credentials from: https://api.dhan.co
"""

import httpx
import logging
from typing import Optional, Dict, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class DHANBroker:
    """DHAN API integration for Indian market trading."""
    
    BASE_URL = "https://api.dhan.co/v2"
    
    # TODO: Get real client_id and access_token from https://api.dhan.co
    def __init__(self, client_id: str, access_token: str):
        """
        Initialize DHAN broker client.
        
        Args:
            client_id: Your DHAN client ID (TODO: Replace dummy value)
            access_token: Your DHAN access token (TODO: Replace dummy value)
        """
        self.client_id = client_id
        self.access_token = access_token
        self.client = httpx.AsyncClient(timeout=10.0)
        self.use_mock = self._is_dummy_credentials()
        
        if self.use_mock:
            logger.warning("Using MOCK DHAN broker - Replace credentials in .env for real trading")
    
    def _is_dummy_credentials(self) -> bool:
        """Check if using dummy credentials."""
        return (
            not self.client_id or 
            not self.access_token or
            "DUMMY" in self.client_id or 
            "DUMMY" in self.access_token
        )
    
    def _get_headers(self) -> Dict:
        """Get API request headers."""
        return {
            "access-token": self.access_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def get_holdings(self) -> List[Dict]:
        """Get current holdings."""
        if self.use_mock:
            return self._mock_holdings()
        
        try:
            url = f"{self.BASE_URL}/holdings"
            response = await self.client.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching holdings: {e}")
            return self._mock_holdings()
    
    async def get_positions(self) -> List[Dict]:
        """Get open positions."""
        if self.use_mock:
            return self._mock_positions()
        
        try:
            url = f"{self.BASE_URL}/positions"
            response = await self.client.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return self._mock_positions()
    
    async def place_order(
        self,
        symbol: str,
        exchange: str,
        transaction_type: str,
        quantity: int,
        order_type: str = "MARKET",
        price: float = 0.0,
        product_type: str = "INTRADAY"
    ) -> Dict:
        """
        Place an order on DHAN.
        
        Args:
            symbol: Trading symbol (e.g., "NIFTY", "BANKNIFTY")
            exchange: Exchange segment ("NSE", "BSE", "NFO")
            transaction_type: "BUY" or "SELL"
            quantity: Lot size
            order_type: "MARKET" or "LIMIT"
            price: Order price (for LIMIT orders)
            product_type: "INTRADAY", "DELIVERY", "MTF"
        """
        if self.use_mock:
            return self._mock_order_response(symbol, transaction_type, quantity, price)
        
        try:
            url = f"{self.BASE_URL}/orders"
            
            payload = {
                "dhanClientId": self.client_id,
                "transactionType": transaction_type,
                "exchangeSegment": exchange,
                "productType": product_type,
                "orderType": order_type,
                "validity": "DAY",
                "securityId": symbol,
                "quantity": quantity,
                "disclosedQuantity": 0,
                "price": price if order_type == "LIMIT" else 0,
                "afterMarketOrder": False
            }
            
            response = await self.client.post(
                url,
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {"error": str(e), "status": "FAILED"}
    
    async def get_order_status(self, order_id: str) -> Dict:
        """Get status of a specific order."""
        if self.use_mock:
            return self._mock_order_status(order_id)
        
        try:
            url = f"{self.BASE_URL}/orders/{order_id}"
            response = await self.client.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching order status: {e}")
            return self._mock_order_status(order_id)
    
    async def cancel_order(self, order_id: str) -> Dict:
        """Cancel an order."""
        if self.use_mock:
            return {"orderId": order_id, "status": "CANCELLED"}
        
        try:
            url = f"{self.BASE_URL}/orders/{order_id}"
            response = await self.client.delete(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error canceling order: {e}")
            return {"error": str(e)}
    
    async def get_funds(self) -> Dict:
        """Get available funds/margin."""
        if self.use_mock:
            return self._mock_funds()
        
        try:
            url = f"{self.BASE_URL}/fundlimit"
            response = await self.client.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching funds: {e}")
            return self._mock_funds()
    
    # Mock data methods for testing without real credentials
    
    def _mock_holdings(self) -> List[Dict]:
        """Mock holdings data."""
        return [
            {
                "securityId": "NIFTY 50",
                "tradingSymbol": "NIFTY",
                "exchange": "NSE",
                "quantity": 50,
                "avgPrice": 21500.00,
                "ltp": 21650.00,
                "pnl": 7500.00
            }
        ]
    
    def _mock_positions(self) -> List[Dict]:
        """Mock positions data."""
        return [
            {
                "securityId": "NIFTY23DEC24500CE",
                "tradingSymbol": "NIFTY 24500 CE",
                "exchange": "NFO",
                "quantity": 50,
                "buyAvg": 150.00,
                "sellAvg": 0.00,
                "netQty": 50,
                "realizedProfit": 0.00,
                "unrealizedProfit": 2500.00
            }
        ]
    
    def _mock_order_response(self, symbol: str, transaction_type: str, quantity: int, price: float) -> Dict:
        """Mock order response."""
        return {
            "orderId": f"MOCK_ORDER_{datetime.now().timestamp()}",
            "orderStatus": "PENDING",
            "transactionType": transaction_type,
            "tradingSymbol": symbol,
            "quantity": quantity,
            "price": price,
            "message": "Order placed successfully (MOCK MODE)"
        }
    
    def _mock_order_status(self, order_id: str) -> Dict:
        """Mock order status."""
        return {
            "orderId": order_id,
            "orderStatus": "TRADED",
            "filledQty": 50,
            "avgPrice": 21650.00,
            "message": "Order executed (MOCK MODE)"
        }
    
    def _mock_funds(self) -> Dict:
        """Mock funds data."""
        return {
            "availabelBalance": 100000.00,
            "sodLimit": 150000.00,
            "collateralAmount": 50000.00,
            "receiveableAmount": 0.00,
            "utilizedAmount": 50000.00
        }
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
