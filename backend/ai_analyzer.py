from emergentintegrations.llm.chat import LlmChat, UserMessage
import logging
from typing import Dict, List
import asyncio

logger = logging.getLogger(__name__)

class AIAnalyzer:
    """AI-powered trade analysis and sentiment detection."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def analyze_trade_pattern(self, trades: List[Dict]) -> Dict:
        """Analyze trade history for patterns and insights."""
        
        if not trades or len(trades) == 0:
            return {"analysis": "No trade history available", "recommendations": []}
        
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"pattern_analysis_{int(asyncio.get_event_loop().time())}",
                system_message="You are a professional trading analyst. Analyze trade patterns and provide concise insights."
            ).with_model("openai", "gpt-5.2")
            
            winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
            losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
            
            win_rate = len(winning_trades) / len(trades) * 100 if trades else 0
            total_pnl = sum(t.get('pnl', 0) for t in trades)
            
            prompt = f"""
            Analyze this trading performance:
            - Total trades: {len(trades)}
            - Win rate: {win_rate:.2f}%
            - Total PnL: ${total_pnl:.2f}
            - Winning trades: {len(winning_trades)}
            - Losing trades: {len(losing_trades)}
            
            Provide 3 key insights and 2 actionable recommendations in a concise format.
            """
            
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            return {
                "analysis": response,
                "win_rate": win_rate,
                "total_pnl": total_pnl
            }
        
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return {"analysis": "AI analysis unavailable", "error": str(e)}
    
    async def validate_trade_signal(self, signal: str, indicators: Dict) -> Dict:
        """Use AI to validate trading signal."""
        
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"signal_validation_{int(asyncio.get_event_loop().time())}",
                system_message="You are a trading signal validator. Assess signal quality based on technical indicators."
            ).with_model("openai", "gpt-5.2")
            
            prompt = f"""
            Validate this {signal} signal with indicators:
            - EMA 9: {indicators.get('ema_9')}
            - EMA 21: {indicators.get('ema_21')}
            - EMA 50: {indicators.get('ema_50')}
            - RSI: {indicators.get('rsi')}
            - MACD: {indicators.get('macd')}
            - VWAP: {indicators.get('vwap')}
            - Current Price: {indicators.get('current_price')}
            
            Provide: 1) Signal quality (Strong/Moderate/Weak), 2) Key concern if any. Keep response under 50 words.
            """
            
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            return {
                "validation": response,
                "ai_enabled": True
            }
        
        except Exception as e:
            logger.error(f"AI signal validation error: {e}")
            return {"validation": "AI validation unavailable", "ai_enabled": False}