import React, { useState, useEffect } from 'react';
import axios from 'axios';
import DashboardHeader from './DashboardHeader';
import ChartPanel from './ChartPanel';
import OrderBookPanel from './OrderBookPanel';
import BottomPanel from './BottomPanel';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TradingDashboard = () => {
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h');
  const [paperTrading, setPaperTrading] = useState(true);
  const [autoTrade, setAutoTrade] = useState(false);
  const [marketPrice, setMarketPrice] = useState(null);
  const [stats, setStats] = useState(null);
  const [signal, setSignal] = useState(null);
  
  useEffect(() => {
    fetchMarketPrice();
    fetchStats();
    
    const priceInterval = setInterval(fetchMarketPrice, 3000);
    const statsInterval = setInterval(fetchStats, 10000);
    
    return () => {
      clearInterval(priceInterval);
      clearInterval(statsInterval);
    };
  }, [selectedSymbol]);
  
  const fetchMarketPrice = async () => {
    try {
      const response = await axios.get(`${API}/market/price/${selectedSymbol}`);
      setMarketPrice(response.data);
    } catch (error) {
      console.error('Error fetching price:', error);
    }
  };
  
  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };
  
  const fetchSignal = async () => {
    try {
      const response = await axios.get(`${API}/analysis/signal/${selectedSymbol}?interval=${selectedTimeframe}`);
      setSignal(response.data);
      
      const signalType = response.data.signal;
      if (signalType === 'BUY') {
        toast.success(`BUY signal detected for ${selectedSymbol}`, {
          description: `Confidence: ${response.data.confidence}%`
        });
      } else if (signalType === 'SELL') {
        toast.error(`SELL signal detected for ${selectedSymbol}`, {
          description: `Confidence: ${response.data.confidence}%`
        });
      } else {
        toast.info('No clear signal - HOLD position');
      }
    } catch (error) {
      console.error('Error fetching signal:', error);
      toast.error('Failed to analyze signal');
    }
  };
  
  const executeTrade = async (side, quantity) => {
    try {
      const response = await axios.post(`${API}/trade/execute`, {
        symbol: selectedSymbol,
        side: side,
        quantity: quantity,
        order_type: 'MARKET'
      });
      
      toast.success(`${side} order executed`, {
        description: `${quantity} ${selectedSymbol} at $${response.data.price}`
      });
      
      fetchStats();
    } catch (error) {
      toast.error('Trade execution failed', {
        description: error.response?.data?.detail || error.message
      });
    }
  };
  
  return (
    <div className="trading-dashboard" data-testid="trading-dashboard">
      <DashboardHeader 
        selectedSymbol={selectedSymbol}
        setSelectedSymbol={setSelectedSymbol}
        selectedTimeframe={selectedTimeframe}
        setSelectedTimeframe={setSelectedTimeframe}
        paperTrading={paperTrading}
        setPaperTrading={setPaperTrading}
        autoTrade={autoTrade}
        setAutoTrade={setAutoTrade}
        marketPrice={marketPrice}
        stats={stats}
      />
      
      <div className="dashboard-grid">
        <ChartPanel 
          symbol={selectedSymbol}
          timeframe={selectedTimeframe}
          signal={signal}
          onAnalyze={fetchSignal}
        />
        
        <OrderBookPanel 
          symbol={selectedSymbol}
          marketPrice={marketPrice}
          onExecuteTrade={executeTrade}
          paperTrading={paperTrading}
        />
        
        <BottomPanel 
          symbol={selectedSymbol}
        />
      </div>
    </div>
  );
};

export default TradingDashboard;