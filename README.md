# AI-Powered Automated Trading Platform 🚀

Production-grade institutional trading platform with AI analysis, auto-trading, and multi-market support.

## 🎯 Core Features

### Trading Engine
- **Multi-Timeframe Analysis**: 1m, 5m, 15m, 1h, 4h support
- **Technical Indicators**: EMA (9, 21, 50), RSI, MACD, VWAP, ATR
- **Signal Generation**: Buy/Sell signals with confidence scoring
- **Risk Management**: Dynamic stop-loss, take-profit, position sizing

### Advanced Features
✅ **DHAN Broker Integration** - Indian market trading (NIFTY, SENSEX F&O)
✅ **Auto-Trading System** - Automated signal execution
✅ **TradingView Webhooks** - External signal integration
✅ **Telegram Alerts** - Real-time trade notifications
✅ **Backtesting Engine** - Strategy performance testing
✅ **Advanced Strategies** - Breakout, volume, news filtering
✅ **AI Analysis** - GPT-5.2 powered insights

---

## 🔑 API Keys Configuration

### Currently Using DUMMY/MOCK Credentials
All integrations are functional with mock implementations. Replace with real credentials for production:

### 1. DHAN Broker API (Indian Markets)
**File**: `/app/backend/.env`

```bash
# TODO: Get credentials from https://api.dhan.co
DHAN_CLIENT_ID=your_actual_client_id_here
DHAN_ACCESS_TOKEN=your_actual_access_token_here
```

**How to get**:
1. Sign up at https://dhan.co
2. Go to API Settings → Generate API credentials
3. Copy Client ID and Access Token
4. Replace in .env file

---

### 2. Telegram Bot (Alerts & Notifications)
**File**: `/app/backend/.env`

```bash
# TODO: Get from @BotFather on Telegram
TELEGRAM_BOT_TOKEN=123456789:your_actual_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

**How to get**:
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow instructions
3. Copy the bot token provided
4. Send a message to your bot
5. Get your chat ID from `@userinfobot`
6. Replace both values in .env file

---

### 3. NewsAPI (News Filtering)
**File**: `/app/backend/.env`

```bash
# TODO: Get free API key from https://newsapi.org
NEWS_API_KEY=your_newsapi_key_here
```

**How to get**:
1. Go to https://newsapi.org
2. Sign up for free account (500 requests/day)
3. Copy API key from dashboard
4. Replace in .env file

---

### 4. TradingView Webhook Secret
**File**: `/app/backend/.env`

```bash
# Change this to a secure random string
WEBHOOK_SECRET=change_this_to_secure_random_string_12345
```

**TradingView Alert Setup**:
1. Create alert in TradingView
2. Set webhook URL: `https://your-app.emergent.host/api/webhook/tradingview`
3. Use this JSON format:
```json
{
  "secret": "your_webhook_secret_from_env",
  "symbol": "{{ticker}}",
  "action": "{{strategy.order.action}}",
  "price": {{close}},
  "strategy": "YOUR_STRATEGY_NAME",
  "timeframe": "{{interval}}"
}
```

---

## 🚀 API Endpoints

See `/app/API_DOCUMENTATION.md` for complete API reference.

Key endpoints:
- Trading: `/api/trade/execute`, `/api/positions`
- Analysis: `/api/analysis/signal/{symbol}`, `/api/ai/analyze-performance`
- Auto-Trading: `/api/auto-trade/status`, `/api/auto-trade/toggle`
- Webhooks: `/api/webhook/tradingview`
- Backtesting: `/api/backtest/run`
- DHAN Broker: `/api/broker/dhan/holdings`, `/api/broker/dhan/positions`
- Advanced: `/api/strategies/breakout/{symbol}`, `/api/strategies/volume/{symbol}`

---

## 🚀 Deployment

**Current Status**: ✅ DEPLOYMENT READY

```bash
# All checks passed
✓ Environment variables configured
✓ Database queries optimized
✓ ESLint configured
✓ No hardcoded secrets
✓ CORS properly set
✓ Supervisor config valid
```

**Deploy to Emergent**: Ready for Kubernetes deployment

Built with ❤️ using FastAPI, React, MongoDB, and Emergent AI
