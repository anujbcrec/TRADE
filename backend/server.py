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
from dhan_broker import DHANBroker
from telegram_alerts import TelegramAlert
from auto_trader import AutoTrader
from tradingview_webhook import WebhookHandler, TradingViewSignal
from backtesting_engine import BacktestingEngine
from advanced_strategies import AdvancedStrategies

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
dhan_broker = None
telegram_alerts = None
auto_trader = None
webhook_handler = None
advanced_strategies = None
mongo_client = None
db = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global market_data_client, trading_engine, risk_manager, ai_analyzer, dhan_broker, telegram_alerts, auto_trader, webhook_handler, advanced_strategies, mongo_client, db
    
    market_data_client = BinanceMarketData(testnet=settings.binance_testnet_enabled)
    trading_engine = TradingEngine()
    risk_manager = RiskManager(
        max_risk_per_trade=settings.max_risk_per_trade,
        max_daily_loss=settings.max_daily_loss,
        max_consecutive_losses=settings.max_consecutive_losses
    )
    
    if settings.emergent_llm_key:
        ai_analyzer = AIAnalyzer(api_key=settings.emergent_llm_key)
    
    # Initialize DHAN broker (with dummy credentials by default)
    dhan_broker = DHANBroker(
        client_id=settings.dhan_client_id,
        access_token=settings.dhan_access_token
    )
    
    # Initialize Telegram alerts (with dummy token by default)
    telegram_alerts = TelegramAlert(
        bot_token=settings.telegram_bot_token,
        chat_id=settings.telegram_chat_id
    )
    
    # Initialize auto-trader
    auto_trader = AutoTrader(
        enabled=settings.auto_trade_enabled,
        min_confidence=settings.auto_trade_min_confidence,
        max_position_size=settings.auto_trade_max_position_size
    )
    
    # Initialize webhook handler
    webhook_handler = WebhookHandler(secret=settings.webhook_secret)
    
    # Initialize advanced strategies (with dummy news API key by default)
    advanced_strategies = AdvancedStrategies(news_api_key=settings.news_api_key)
    
    mongo_client = AsyncIOMotorClient(settings.mongo_url)
    db = mongo_client[settings.db_name]
    
    logger.info("Application startup complete")
    yield
    
    await market_data_client.close()
    await dhan_broker.close()
    await telegram_alerts.close()
    await advanced_strategies.close()
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


# ========== DHAN BROKER ENDPOINTS ==========

@api_router.get("/broker/dhan/holdings")
async def get_dhan_holdings():
    """Get DHAN holdings (Indian market positions)."""
    try:
        holdings = await dhan_broker.get_holdings()
        return {"holdings": holdings}
    except Exception as e:
        logger.error(f"Error fetching DHAN holdings: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/broker/dhan/positions")
async def get_dhan_positions():
    """Get DHAN positions."""
    try:
        positions = await dhan_broker.get_positions()
        return {"positions": positions}
    except Exception as e:
        logger.error(f"Error fetching DHAN positions: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/broker/dhan/funds")
async def get_dhan_funds():
    """Get DHAN account funds."""
    try:
        funds = await dhan_broker.get_funds()
        return funds
    except Exception as e:
        logger.error(f"Error fetching DHAN funds: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ========== AUTO-TRADING ENDPOINTS ==========

@api_router.get("/auto-trade/status")
async def get_auto_trade_status():
    """Get auto-trading status and configuration."""
    return auto_trader.get_status()


@api_router.post("/auto-trade/toggle")
async def toggle_auto_trade(enabled: bool):
    """Enable/disable auto-trading."""
    auto_trader.enabled = enabled
    status = "enabled" if enabled else "disabled"
    
    await telegram_alerts.send_message(
        f"🤖 Auto-trading has been {status.upper()}"
    )
    
    return {"auto_trade_enabled": enabled, "message": f"Auto-trading {status}"}


# ========== TRADINGVIEW WEBHOOK ENDPOINT ==========

@api_router.post("/webhook/tradingview")
async def tradingview_webhook(signal: TradingViewSignal):
    """
    Receive trading signals from TradingView webhooks.
    
    Webhook URL: https://your-app.emergent.host/api/webhook/tradingview
    """
    try:
        # Validate signal
        validation = webhook_handler.validate_signal(signal)
        
        if not validation["valid"]:
            webhook_handler.record_signal(signal, "REJECTED")
            raise HTTPException(status_code=400, detail=validation["reason"])
        
        # Process signal
        processed_signal = webhook_handler.process_signal(signal)
        
        # Send Telegram alert
        await telegram_alerts.send_signal_alert(
            symbol=signal.symbol,
            signal=signal.action,
            confidence=100,
            indicators={"source": "TradingView", "strategy": signal.strategy}
        )
        
        # Record signal
        webhook_handler.record_signal(signal, "RECEIVED")
        
        logger.info(f"TradingView signal received: {signal.action} {signal.symbol}")
        
        return {
            "status": "success",
            "message": "Signal received and processed",
            "signal": processed_signal
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/webhook/history")
async def get_webhook_history(limit: int = 50):
    """Get webhook signal history."""
    history = webhook_handler.get_signal_history(limit)
    return {"signals": history, "count": len(history)}


# ========== BACKTESTING ENDPOINTS ==========

@api_router.post("/backtest/run")
async def run_backtest(
    symbol: str,
    interval: str = "1h",
    limit: int = 500,
    initial_capital: float = 10000.0
):
    """
    Run backtest on historical data.
    """
    try:
        # Fetch historical data
        klines = await market_data_client.get_klines(symbol, interval, limit)
        
        if len(klines) < 100:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data. Need at least 100 candles, got {len(klines)}"
            )
        
        # Initialize backtest engine
        backtest_engine = BacktestingEngine(initial_capital=initial_capital)
        
        # Run backtest
        result = await backtest_engine.run_backtest(
            klines, trading_engine, risk_manager, interval
        )
        
        # Return results
        return {
            "symbol": symbol,
            "interval": interval,
            "initial_capital": initial_capital,
            "final_capital": backtest_engine.current_capital,
            "total_trades": result.total_trades,
            "winning_trades": result.winning_trades,
            "losing_trades": result.losing_trades,
            "win_rate": round(result.win_rate, 2),
            "total_pnl": round(result.total_pnl, 2),
            "profit_factor": round(result.profit_factor, 2),
            "max_drawdown": round(result.max_drawdown, 2),
            "sharpe_ratio": round(result.sharpe_ratio, 2),
            "max_consecutive_wins": result.max_consecutive_wins,
            "max_consecutive_losses": result.max_consecutive_losses,
            "avg_win": round(result.avg_win, 2),
            "avg_loss": round(result.avg_loss, 2),
            "largest_win": round(result.largest_win, 2),
            "largest_loss": round(result.largest_loss, 2),
            "trades": result.trades[:20]  # Return first 20 trades
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== ADVANCED STRATEGIES ENDPOINTS ==========

@api_router.get("/strategies/breakout/{symbol}")
async def detect_breakout(symbol: str, interval: str = "1h", lookback: int = 20):
    """Detect price breakout patterns."""
    try:
        klines = await market_data_client.get_klines(symbol, interval, lookback + 1)
        price_data = await market_data_client.get_price(symbol)
        current_price = float(price_data["price"])
        
        breakout = advanced_strategies.detect_breakout(klines, current_price, lookback)
        
        return {"symbol": symbol, "breakout_analysis": breakout}
    except Exception as e:
        logger.error(f"Breakout detection error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/strategies/volume/{symbol}")
async def analyze_volume(symbol: str, interval: str = "1h", lookback: int = 20):
    """Analyze volume patterns."""
    try:
        klines = await market_data_client.get_klines(symbol, interval, lookback)
        
        volume_analysis = advanced_strategies.analyze_volume(klines, lookback)
        
        return {"symbol": symbol, "volume_analysis": volume_analysis}
    except Exception as e:
        logger.error(f"Volume analysis error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/strategies/news/{symbol}")
async def check_news_events(symbol: str):
    """Check for major news events."""
    try:
        news_check = await advanced_strategies.check_news_events(symbol)
        
        return {"symbol": symbol, "news_analysis": news_check}
    except Exception as e:
        logger.error(f"News check error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/strategies/consolidation/{symbol}")
async def detect_consolidation(symbol: str, interval: str = "1h", lookback: int = 20):
    """Detect price consolidation."""
    try:
        klines = await market_data_client.get_klines(symbol, interval, lookback)
        
        consolidation = advanced_strategies.detect_consolidation(klines, lookback)
        
        return {"symbol": symbol, "consolidation_analysis": consolidation}
    except Exception as e:
        logger.error(f"Consolidation detection error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


app.include_router(api_router)


@app.on_event("shutdown")
async def shutdown():
    """Shutdown handler."""
    if mongo_client:
        mongo_client.close()
