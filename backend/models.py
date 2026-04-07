from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal
from datetime import datetime, timezone
import uuid

class Trade(BaseModel):
    """Trade execution record."""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str
    side: Literal["BUY", "SELL"]
    order_type: Literal["MARKET", "LIMIT"]
    quantity: float
    price: float
    total_value: float
    status: Literal["PENDING", "FILLED", "CANCELLED", "FAILED"]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    indicators: Optional[dict] = None
    strategy: Optional[str] = None
    pnl: Optional[float] = None
    
class Position(BaseModel):
    """Active trading position."""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str
    side: Literal["LONG", "SHORT"]
    entry_price: float
    current_price: float
    quantity: float
    stop_loss: float
    take_profit: Optional[float] = None
    trailing_stop: Optional[float] = None
    unrealized_pnl: float = 0.0
    opened_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
class Strategy(BaseModel):
    """Trading strategy configuration."""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    symbol: str
    timeframe: Literal["1m", "5m", "15m", "1h"]
    enabled: bool = True
    indicators: dict
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MarketData(BaseModel):
    """Market data snapshot."""
    symbol: str
    price: float
    volume: float
    high_24h: float
    low_24h: float
    change_24h: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Indicator(BaseModel):
    """Technical indicator values."""
    symbol: str
    timeframe: str
    ema_9: Optional[float] = None
    ema_21: Optional[float] = None
    ema_50: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    vwap: Optional[float] = None
    atr: Optional[float] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))