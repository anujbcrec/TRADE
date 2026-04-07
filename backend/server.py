from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
import os
import logging
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel

from config import get_settings
from models import Trade, Position, Strategy, MarketData, Indicator
from binance_client import BinanceMarketData
from trading_engine import TradingEngine
from risk_manager import RiskManager
from ai_analyzer import AIAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

market_data_client = None
trading_engine = None
risk_manager = None
ai_analyzer = None
mongo_client = None
db = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global market_data_client, trading_engine, risk_manager, ai_analyzer, mongo_client, db
    
    market_data_client = BinanceMarketData(testnet=settings.binance_testnet_enabled)
    trading_engine = TradingEngine()
    risk_manager = RiskManager(
        max_risk_per_trade=settings.max_risk_per_trade,
        max_daily_loss=settings.max_daily_loss,
        max_consecutive_losses=settings.max_consecutive_losses
    )
    
    if settings.emergent_llm_key:
        ai_analyzer = AIAnalyzer(api_key=settings.emergent_llm_key)
    
    mongo_client = AsyncIOMotorClient(settings.mongo_url)
    db = mongo_client[settings.db_name]
    
    logger.info("Application startup complete")
    yield
    
    await market_data_client.close()
    mongo_client.close()
    logger.info("Application shutdown complete")

app = FastAPI(title="AI Trading Platform", lifespan=lifespan)
api_router = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TradeRequest(BaseModel):
    symbol: str
    side: str
    quantity: float
    order_type: str = "MARKET"
    price: Optional[float] = None

class PositionRequest(BaseModel):
    symbol: str
    side: str
    quantity: float
    entry_price: float


@api_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@api_router.get("/market/price/{symbol}")
async def get_price(symbol: str):
    """Get current price for a symbol."""
    try:
        price_data = await market_data_client.get_price(symbol)
        stats = await market_data_client.get_24hr_stats(symbol)
        
        return {
            "symbol": price_data["symbol"],
            "price": float(price_data["price"]),
            "volume": float(stats.get("volume", 0)),
            "high_24h": float(stats.get("highPrice", 0)),
            "low_24h": float(stats.get("lowPrice", 0)),
            "change_24h": float(stats.get("priceChangePercent", 0))
        }
    except Exception as e:
        logger.error(f"Error fetching price: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/market/klines/{symbol}")
async def get_klines(symbol: str, interval: str = "1h", limit: int = 100):
    """Get kline/candlestick data."""
    try:
        klines = await market_data_client.get_klines(symbol, interval, limit)
        
        formatted_klines = []
        for k in klines:
            formatted_klines.append({
                "time": int(k[0]),
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5])
            })
        
        return {"symbol": symbol, "interval": interval, "klines": formatted_klines}
    except Exception as e:
        logger.error(f"Error fetching klines: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/market/orderbook/{symbol}")
async def get_orderbook(symbol: str, limit: int = 20):
    """Get order book."""
    try:
        orderbook = await market_data_client.get_order_book(symbol, limit)
        
        bids = [[float(b[0]), float(b[1])] for b in orderbook["bids"][:limit]]
        asks = [[float(a[0]), float(a[1])] for a in orderbook["asks"][:limit]]
        
        return {"symbol": symbol, "bids": bids, "asks": asks}
    except Exception as e:
        logger.error(f"Error fetching orderbook: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/analysis/signal/{symbol}")
async def analyze_signal(symbol: str, interval: str = "1h"):
    """Analyze trading signal for a symbol."""
    try:
        klines = await market_data_client.get_klines(symbol, interval, 100)
        price_data = await market_data_client.get_price(symbol)
        current_price = float(price_data["price"])
        
        analysis = trading_engine.analyze_signal(klines, current_price)
        
        if ai_analyzer:
            ai_validation = await ai_analyzer.validate_trade_signal(
                analysis["signal"],
                analysis["indicators"]
            )
            analysis["ai_validation"] = ai_validation
        
        return analysis
    except Exception as e:
        logger.error(f"Error analyzing signal: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@api_router.post("/trade/execute")
async def execute_trade(trade_req: TradeRequest):
    """Execute a manual trade."""
    try:
        from datetime import timedelta
        start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        daily_trades = await db.trades.find(
            {"timestamp": {"$gte": start_of_day.isoformat()}},
            {"_id": 0, "pnl": 1, "timestamp": 1}
        ).limit(1000).to_list(1000)
        
        daily_pnl = sum(t.get("pnl", 0) for t in daily_trades if t.get("pnl"))
        
        recent_trades = await db.trades.find(
            {},
            {"_id": 0, "pnl": 1}
        ).sort("timestamp", -1).limit(10).to_list(10)
        
        consecutive_losses = 0
        for t in recent_trades:
            if t.get("pnl", 0) < 0:
                consecutive_losses += 1
            else:
                break
        
        risk_check = risk_manager.should_trade(daily_pnl, consecutive_losses)
        if not risk_check["allowed"]:
            raise HTTPException(status_code=403, detail=risk_check["reason"])
        
        price_data = await market_data_client.get_price(trade_req.symbol)
        current_price = float(price_data["price"])
        
        trade = Trade(
            symbol=trade_req.symbol,
            side=trade_req.side,
            order_type=trade_req.order_type,
            quantity=trade_req.quantity,
            price=trade_req.price or current_price,
            total_value=trade_req.quantity * (trade_req.price or current_price),
            status="FILLED",
            strategy="MANUAL"
        )
        
        trade_dict = trade.model_dump()
        trade_dict["timestamp"] = trade_dict["timestamp"].isoformat()
        
        await db.trades.insert_one(trade_dict)
        
        return trade.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/trades")
async def get_trades(limit: int = 100):
    """Get trade history."""
    try:
        trades = await db.trades.find(
            {},
            {"_id": 0, "symbol": 1, "side": 1, "order_type": 1, "quantity": 1, "price": 1, "total_value": 1, "status": 1, "timestamp": 1, "pnl": 1, "strategy": 1}
        ).sort("timestamp", -1).limit(min(limit, 100)).to_list(min(limit, 100))
        
        for trade in trades:
            if isinstance(trade.get("timestamp"), str):
                trade["timestamp"] = datetime.fromisoformat(trade["timestamp"])
        
        return {"trades": trades, "count": len(trades)}
    except Exception as e:
        logger.error(f"Error fetching trades: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@api_router.post("/positions")
async def create_position(pos_req: PositionRequest):
    """Create a new position."""
    try:
        klines = await market_data_client.get_klines(pos_req.symbol, "1h", 50)
        closes = [float(k[4]) for k in klines]
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]
        
        from trading_engine import TechnicalIndicators
        atr = TechnicalIndicators.calculate_atr(highs, lows, closes, 14)
        
        stop_loss = risk_manager.calculate_stop_loss(pos_req.entry_price, pos_req.side, atr)
        take_profit = risk_manager.calculate_take_profit(pos_req.entry_price, stop_loss, pos_req.side)
        
        position = Position(
            symbol=pos_req.symbol,
            side=pos_req.side,
            entry_price=pos_req.entry_price,
            current_price=pos_req.entry_price,
            quantity=pos_req.quantity,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        pos_dict = position.model_dump()
        pos_dict["opened_at"] = pos_dict["opened_at"].isoformat()
        pos_dict["updated_at"] = pos_dict["updated_at"].isoformat()
        
        await db.positions.insert_one(pos_dict)
        
        return position.model_dump()
    except Exception as e:
        logger.error(f"Error creating position: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/positions")
async def get_positions():
    """Get all open positions."""
    try:
        import asyncio
        
        positions = await db.positions.find(
            {},
            {"_id": 0, "id": 1, "symbol": 1, "side": 1, "entry_price": 1, "quantity": 1, "stop_loss": 1, "take_profit": 1, "opened_at": 1, "updated_at": 1, "current_price": 1, "unrealized_pnl": 1}
        ).limit(100).to_list(100)
        
        unique_symbols = list(set(pos["symbol"] for pos in positions))
        
        async def fetch_price(symbol):
            try:
                price_data = await market_data_client.get_price(symbol)
                return symbol, float(price_data["price"])
            except:
                return symbol, None
        
        price_results = await asyncio.gather(*[fetch_price(sym) for sym in unique_symbols])
        price_map = dict(price_results)
        
        updated_positions = []
        for pos in positions:
            if isinstance(pos.get("opened_at"), str):
                pos["opened_at"] = datetime.fromisoformat(pos["opened_at"])
            if isinstance(pos.get("updated_at"), str):
                pos["updated_at"] = datetime.fromisoformat(pos["updated_at"])
            
            current_price = price_map.get(pos["symbol"])
            if current_price:
                if pos["side"] == "LONG":
                    unrealized_pnl = (current_price - pos["entry_price"]) * pos["quantity"]
                else:
                    unrealized_pnl = (pos["entry_price"] - current_price) * pos["quantity"]
                
                pos["current_price"] = current_price
                pos["unrealized_pnl"] = round(unrealized_pnl, 2)
            
            updated_positions.append(pos)
        
        return {"positions": updated_positions, "count": len(updated_positions)}
    except Exception as e:
        logger.error(f"Error fetching positions: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@api_router.delete("/positions/{position_id}")
async def close_position(position_id: str):
    """Close a position."""
    try:
        result = await db.positions.delete_one({"id": position_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Position not found")
        
        return {"message": "Position closed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing position: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics."""
    try:
        trade_stats = await db.trades.aggregate([
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": 1},
                    "winning": {
                        "$sum": {
                            "$cond": [{"$gt": ["$pnl", 0]}, 1, 0]
                        }
                    },
                    "total_pnl": {"$sum": "$pnl"}
                }
            }
        ]).to_list(1)
        
        position_stats = await db.positions.aggregate([
            {
                "$group": {
                    "_id": None,
                    "count": {"$sum": 1},
                    "total_unrealized_pnl": {"$sum": "$unrealized_pnl"}
                }
            }
        ]).to_list(1)
        
        trade_data = trade_stats[0] if trade_stats else {"total": 0, "winning": 0, "total_pnl": 0}
        position_data = position_stats[0] if position_stats else {"count": 0, "total_unrealized_pnl": 0}
        
        total_trades = trade_data.get("total", 0)
        winning_trades = trade_data.get("winning", 0)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        return {
            "total_trades": total_trades,
            "win_rate": round(win_rate, 2),
            "total_pnl": round(trade_data.get("total_pnl", 0), 2),
            "open_positions": position_data.get("count", 0),
            "unrealized_pnl": round(position_data.get("total_unrealized_pnl", 0), 2)
        }
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/ai/analyze-performance")
async def analyze_performance():
    """Get AI analysis of trading performance."""
    try:
        if not ai_analyzer:
            return {"analysis": "AI analysis not enabled", "ai_enabled": False}
        
        trades = await db.trades.find(
            {},
            {"_id": 0, "pnl": 1, "symbol": 1, "side": 1, "timestamp": 1}
        ).sort("timestamp", -1).limit(100).to_list(100)
        
        analysis = await ai_analyzer.analyze_trade_pattern(trades)
        
        return analysis
    except Exception as e:
        logger.error(f"Error in AI analysis: {e}")
        return {"analysis": "AI analysis failed", "error": str(e), "ai_enabled": False}


app.include_router(api_router)


@app.on_event("shutdown")
async def shutdown():
    """Shutdown handler."""
    if mongo_client:
        mongo_client.close()
