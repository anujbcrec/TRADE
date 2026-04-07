"""
Telegram Alert System for Trading Notifications

TODO: Replace dummy TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env file
How to get your bot token:
1. Open Telegram and search for @BotFather
2. Send /newbot and follow instructions
3. Copy the bot token provided
4. Get your chat_id by messaging @userinfobot
"""

import httpx
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class TelegramAlert:
    """Send trading alerts via Telegram."""
    
    BASE_URL = "https://api.telegram.org/bot"
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize Telegram bot.
        
        Args:
            bot_token: Your Telegram bot token (TODO: Replace dummy in .env)
            chat_id: Your Telegram chat ID (TODO: Replace dummy in .env)
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.client = httpx.AsyncClient(timeout=10.0)
        self.use_mock = self._is_dummy_credentials()
        
        if self.use_mock:
            logger.warning("Using MOCK Telegram alerts - Add real bot token in .env for notifications")
    
    def _is_dummy_credentials(self) -> bool:
        """Check if using dummy credentials."""
        return (
            not self.bot_token or 
            not self.chat_id or
            "DUMMY" in self.bot_token or 
            "DUMMY" in self.chat_id
        )
    
    async def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """Send a text message."""
        if self.use_mock:
            logger.info(f"[MOCK TELEGRAM] {message}")
            return True
        
        try:
            url = f"{self.BASE_URL}{self.bot_token}/sendMessage"
            
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            return True
        
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    async def send_trade_alert(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        signal_type: str = "MANUAL"
    ) -> bool:
        """Send trade execution alert."""
        
        emoji = "🟢" if side == "BUY" else "🔴"
        
        message = f"""
{emoji} <b>TRADE EXECUTED</b> {emoji}

<b>Symbol:</b> {symbol}
<b>Side:</b> {side}
<b>Quantity:</b> {quantity}
<b>Price:</b> ${price:.2f}
<b>Type:</b> {signal_type}
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        return await self.send_message(message.strip())
    
    async def send_signal_alert(
        self,
        symbol: str,
        signal: str,
        confidence: float,
        indicators: dict
    ) -> bool:
        """Send trading signal alert."""
        
        emoji = "📈" if signal == "BUY" else "📉" if signal == "SELL" else "⏸️"
        
        message = f"""
{emoji} <b>SIGNAL DETECTED</b> {emoji}

<b>Symbol:</b> {symbol}
<b>Signal:</b> {signal}
<b>Confidence:</b> {confidence:.1f}%

<b>Indicators:</b>
• RSI: {indicators.get('rsi', 'N/A')}
• MACD: {indicators.get('macd', 'N/A')}
• EMA Trend: {"Bullish" if indicators.get('ema_9', 0) > indicators.get('ema_21', 0) else "Bearish"}

<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        return await self.send_message(message.strip())
    
    async def send_position_alert(
        self,
        symbol: str,
        action: str,
        entry_price: float,
        current_price: float,
        pnl: float,
        reason: str = ""
    ) -> bool:
        """Send position update alert."""
        
        emoji = "✅" if action == "CLOSED" else "⚠️"
        pnl_emoji = "💰" if pnl >= 0 else "📉"
        
        message = f"""
{emoji} <b>POSITION {action}</b>

<b>Symbol:</b> {symbol}
<b>Entry:</b> ${entry_price:.2f}
<b>Exit:</b> ${current_price:.2f}
<b>P&L:</b> ${pnl:.2f} {pnl_emoji}
{f'<b>Reason:</b> {reason}' if reason else ''}

<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        return await self.send_message(message.strip())
    
    async def send_risk_alert(self, message: str, alert_type: str = "WARNING") -> bool:
        """Send risk management alert."""
        
        emoji = "🚨" if alert_type == "CRITICAL" else "⚠️"
        
        alert_message = f"""
{emoji} <b>RISK ALERT</b> {emoji}

{message}

<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        return await self.send_message(alert_message.strip())
    
    async def send_daily_summary(
        self,
        total_trades: int,
        winning_trades: int,
        total_pnl: float,
        win_rate: float
    ) -> bool:
        """Send daily trading summary."""
        
        pnl_emoji = "💰" if total_pnl >= 0 else "📉"
        
        message = f"""
📊 <b>DAILY TRADING SUMMARY</b> 📊

<b>Total Trades:</b> {total_trades}
<b>Winning Trades:</b> {winning_trades}
<b>Win Rate:</b> {win_rate:.1f}%
<b>Total P&L:</b> ${total_pnl:.2f} {pnl_emoji}

<b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}
        """
        
        return await self.send_message(message.strip())
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
