from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""
    
    mongo_url: str = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name: str = os.environ.get('DB_NAME', 'test_database')
    cors_origins: str = os.environ.get('CORS_ORIGINS', '*')
    
    emergent_llm_key: str = os.environ.get('EMERGENT_LLM_KEY', '')
    binance_api_key: str = os.environ.get('BINANCE_API_KEY', '')
    binance_api_secret: str = os.environ.get('BINANCE_API_SECRET', '')
    binance_testnet_enabled: bool = os.environ.get('BINANCE_TESTNET_ENABLED', 'true').lower() == 'true'
    
    # TODO: Replace these dummy values with real credentials in .env file
    dhan_client_id: str = os.environ.get('DHAN_CLIENT_ID', '')
    dhan_access_token: str = os.environ.get('DHAN_ACCESS_TOKEN', '')
    
    telegram_bot_token: str = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    telegram_chat_id: str = os.environ.get('TELEGRAM_CHAT_ID', '')
    
    news_api_key: str = os.environ.get('NEWS_API_KEY', '')
    webhook_secret: str = os.environ.get('WEBHOOK_SECRET', 'change_this_secret_key')
    
    max_risk_per_trade: float = float(os.environ.get('MAX_RISK_PER_TRADE', '0.02'))
    max_daily_loss: float = float(os.environ.get('MAX_DAILY_LOSS', '0.05'))
    max_consecutive_losses: int = int(os.environ.get('MAX_CONSECUTIVE_LOSSES', '3'))
    
    auto_trade_enabled: bool = os.environ.get('AUTO_TRADE_ENABLED', 'false').lower() == 'true'
    auto_trade_min_confidence: int = int(os.environ.get('AUTO_TRADE_MIN_CONFIDENCE', '75'))
    auto_trade_max_position_size: float = float(os.environ.get('AUTO_TRADE_MAX_POSITION_SIZE', '10000'))
    
    class Config:
        case_sensitive = False

@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()