import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { TrendUp, TrendDown, ChartLine } from '@phosphor-icons/react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ChartPanel = ({ symbol, timeframe, signal, onAnalyze }) => {
  const [chartData, setChartData] = useState([]);
  const [indicators, setIndicators] = useState(null);
  
  useEffect(() => {
    fetchChartData();
    const interval = setInterval(fetchChartData, 5000);
    return () => clearInterval(interval);
  }, [symbol, timeframe]);
  
  const fetchChartData = async () => {
    try {
      const response = await axios.get(`${API}/market/klines/${symbol}?interval=${timeframe}&limit=100`);
      const klines = response.data.klines;
      
      const formatted = klines.map(k => ({
        time: new Date(k.time).toLocaleTimeString(),
        price: k.close,
        high: k.high,
        low: k.low,
        volume: k.volume
      }));
      
      setChartData(formatted);
    } catch (error) {
      console.error('Error fetching chart data:', error);
    }
  };
  
  useEffect(() => {
    if (signal) {
      setIndicators(signal.indicators);
    }
  }, [signal]);
  
  return (
    <div className="chart-panel p-4 flex flex-col" data-testid="chart-panel">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-medium tracking-tight">PRICE CHART</h2>
          <span className="text-xs text-[#888888] font-mono uppercase tracking-wider">
            {symbol} • {timeframe}
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          {signal && (
            <div className={`flex items-center gap-2 px-3 py-1.5 border border-[#222222] ${
              signal.signal === 'BUY' ? 'profit-bg' : signal.signal === 'SELL' ? 'loss-bg' : 'bg-[#0C0C0C]'
            }`}>
              {signal.signal === 'BUY' ? (
                <TrendUp size={16} weight="bold" className="profit" />
              ) : signal.signal === 'SELL' ? (
                <TrendDown size={16} weight="bold" className="loss" />
              ) : (
                <ChartLine size={16} weight="bold" />
              )}
              <span className={`text-sm font-mono font-medium ${
                signal.signal === 'BUY' ? 'profit' : signal.signal === 'SELL' ? 'loss' : ''
              }`}>
                {signal.signal}
              </span>
              {signal.confidence > 0 && (
                <span className="text-xs text-[#888888]">({signal.confidence}%)</span>
              )}
            </div>
          )}
          
          <Button 
            onClick={onAnalyze}
            className="bg-white text-black hover:bg-[#CCCCCC] rounded-none h-9"
            data-testid="analyze-signal-btn"
          >
            ANALYZE SIGNAL
          </Button>
        </div>
      </div>
      
      {indicators && (
        <div className="grid grid-cols-4 gap-4 mb-4 pb-4 border-b border-[#222222]">
          <div>
            <div className="text-xs text-[#888888] uppercase tracking-wider mb-1">RSI (14)</div>
            <div className={`font-mono text-base font-medium ${
              indicators.rsi >= 70 ? 'loss' : indicators.rsi <= 30 ? 'profit' : ''
            }`}>
              {indicators.rsi?.toFixed(2) || 'N/A'}
            </div>
          </div>
          
          <div>
            <div className="text-xs text-[#888888] uppercase tracking-wider mb-1">MACD</div>
            <div className={`font-mono text-base font-medium ${
              indicators.macd > indicators.macd_signal ? 'profit' : 'loss'
            }`}>
              {indicators.macd?.toFixed(4) || 'N/A'}
            </div>
          </div>
          
          <div>
            <div className="text-xs text-[#888888] uppercase tracking-wider mb-1">VWAP</div>
            <div className="font-mono text-base font-medium">
              ${indicators.vwap?.toFixed(2) || 'N/A'}
            </div>
          </div>
          
          <div>
            <div className="text-xs text-[#888888] uppercase tracking-wider mb-1">ATR (14)</div>
            <div className="font-mono text-base font-medium">
              {indicators.atr?.toFixed(4) || 'N/A'}
            </div>
          </div>
        </div>
      )}
      
      <div className="flex-1" style={{ minHeight: 0 }}>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <XAxis 
                dataKey="time" 
                stroke="#888888" 
                style={{ fontSize: '10px', fontFamily: 'JetBrains Mono' }}
                tick={{ fill: '#888888' }}
              />
              <YAxis 
                domain={['dataMin - 50', 'dataMax + 50']}
                stroke="#888888" 
                style={{ fontSize: '10px', fontFamily: 'JetBrains Mono' }}
                tick={{ fill: '#888888' }}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#0C0C0C',
                  border: '1px solid #222222',
                  borderRadius: 0,
                  fontFamily: 'JetBrains Mono',
                  fontSize: '12px'
                }}
                labelStyle={{ color: '#888888' }}
              />
              {indicators?.vwap && (
                <ReferenceLine y={indicators.vwap} stroke="#FFB800" strokeDasharray="3 3" />
              )}
              <Line 
                type="monotone" 
                dataKey="price" 
                stroke="#FFFFFF" 
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex items-center justify-center text-[#888888]">
            Loading chart data...
          </div>
        )}
      </div>
    </div>
  );
};

export default ChartPanel;