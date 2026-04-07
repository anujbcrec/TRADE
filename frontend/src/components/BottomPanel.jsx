import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { X } from '@phosphor-icons/react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const BottomPanel = ({ symbol }) => {
  const [positions, setPositions] = useState([]);
  const [trades, setTrades] = useState([]);
  const [activeTab, setActiveTab] = useState('positions');
  
  useEffect(() => {
    fetchPositions();
    fetchTrades();
    
    const interval = setInterval(() => {
      fetchPositions();
      fetchTrades();
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);
  
  const fetchPositions = async () => {
    try {
      const response = await axios.get(`${API}/positions`);
      setPositions(response.data.positions || []);
    } catch (error) {
      console.error('Error fetching positions:', error);
    }
  };
  
  const fetchTrades = async () => {
    try {
      const response = await axios.get(`${API}/trades?limit=50`);
      setTrades(response.data.trades || []);
    } catch (error) {
      console.error('Error fetching trades:', error);
    }
  };
  
  const closePosition = async (positionId) => {
    try {
      await axios.delete(`${API}/positions/${positionId}`);
      fetchPositions();
    } catch (error) {
      console.error('Error closing position:', error);
    }
  };
  
  return (
    <div className="bottom-panel" data-testid="bottom-panel">
      <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
        <div className="border-b border-[#222222] px-4">
          <TabsList className="bg-transparent border-0 h-12 gap-0 p-0">
            <TabsTrigger 
              value="positions" 
              className="data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-white rounded-none px-6 h-full uppercase tracking-wider text-xs"
              data-testid="positions-tab"
            >
              Positions ({positions.length})
            </TabsTrigger>
            <TabsTrigger 
              value="trades" 
              className="data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-white rounded-none px-6 h-full uppercase tracking-wider text-xs"
              data-testid="trades-tab"
            >
              Trade History ({trades.length})
            </TabsTrigger>
          </TabsList>
        </div>
        
        <TabsContent value="positions" className="flex-1 m-0 overflow-hidden">
          <ScrollArea className="h-full">
            <div className="px-4 py-2">
              {positions.length > 0 ? (
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-[#222222] text-xs text-[#888888] uppercase tracking-wider">
                      <th className="text-left py-2 px-3 font-medium">Symbol</th>
                      <th className="text-left py-2 px-3 font-medium">Side</th>
                      <th className="text-right py-2 px-3 font-medium">Quantity</th>
                      <th className="text-right py-2 px-3 font-medium">Entry</th>
                      <th className="text-right py-2 px-3 font-medium">Current</th>
                      <th className="text-right py-2 px-3 font-medium">Stop Loss</th>
                      <th className="text-right py-2 px-3 font-medium">Take Profit</th>
                      <th className="text-right py-2 px-3 font-medium">Unrealized P&L</th>
                      <th className="text-center py-2 px-3 font-medium">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {positions.map((pos, idx) => (
                      <tr key={idx} className="border-b border-[#222222] hover:bg-[#1A1A1A]">
                        <td className="py-2 px-3 font-mono text-sm">{pos.symbol}</td>
                        <td className="py-2 px-3">
                          <span className={`text-xs px-2 py-1 ${pos.side === 'LONG' ? 'profit-bg profit' : 'loss-bg loss'}`}>
                            {pos.side}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-right font-mono text-sm">{pos.quantity}</td>
                        <td className="py-2 px-3 text-right font-mono text-sm">${pos.entry_price?.toFixed(2)}</td>
                        <td className="py-2 px-3 text-right font-mono text-sm">${pos.current_price?.toFixed(2)}</td>
                        <td className="py-2 px-3 text-right font-mono text-sm">${pos.stop_loss?.toFixed(2)}</td>
                        <td className="py-2 px-3 text-right font-mono text-sm">${pos.take_profit?.toFixed(2) || 'N/A'}</td>
                        <td className={`py-2 px-3 text-right font-mono text-sm font-medium ${pos.unrealized_pnl >= 0 ? 'profit' : 'loss'}`}>
                          ${pos.unrealized_pnl?.toFixed(2)}
                        </td>
                        <td className="py-2 px-3 text-center">
                          <Button 
                            size="sm"
                            onClick={() => closePosition(pos.id)}
                            className="bg-transparent hover:bg-[#FF3344] border border-[#222222] rounded-none h-7 px-2"
                            data-testid={`close-position-${idx}`}
                          >
                            <X size={14} />
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="text-center py-8 text-[#888888]">
                  No open positions
                </div>
              )}
            </div>
          </ScrollArea>
        </TabsContent>
        
        <TabsContent value="trades" className="flex-1 m-0 overflow-hidden">
          <ScrollArea className="h-full">
            <div className="px-4 py-2">
              {trades.length > 0 ? (
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-[#222222] text-xs text-[#888888] uppercase tracking-wider">
                      <th className="text-left py-2 px-3 font-medium">Time</th>
                      <th className="text-left py-2 px-3 font-medium">Symbol</th>
                      <th className="text-left py-2 px-3 font-medium">Side</th>
                      <th className="text-left py-2 px-3 font-medium">Type</th>
                      <th className="text-right py-2 px-3 font-medium">Quantity</th>
                      <th className="text-right py-2 px-3 font-medium">Price</th>
                      <th className="text-right py-2 px-3 font-medium">Total</th>
                      <th className="text-left py-2 px-3 font-medium">Status</th>
                      <th className="text-right py-2 px-3 font-medium">P&L</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trades.map((trade, idx) => (
                      <tr key={idx} className="border-b border-[#222222] hover:bg-[#1A1A1A]">
                        <td className="py-2 px-3 font-mono text-xs text-[#888888]">
                          {new Date(trade.timestamp).toLocaleTimeString()}
                        </td>
                        <td className="py-2 px-3 font-mono text-sm">{trade.symbol}</td>
                        <td className="py-2 px-3">
                          <span className={`text-xs px-2 py-1 ${trade.side === 'BUY' ? 'profit-bg profit' : 'loss-bg loss'}`}>
                            {trade.side}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-xs text-[#888888]">{trade.order_type}</td>
                        <td className="py-2 px-3 text-right font-mono text-sm">{trade.quantity}</td>
                        <td className="py-2 px-3 text-right font-mono text-sm">${trade.price?.toFixed(2)}</td>
                        <td className="py-2 px-3 text-right font-mono text-sm">${trade.total_value?.toFixed(2)}</td>
                        <td className="py-2 px-3 text-xs">{trade.status}</td>
                        <td className={`py-2 px-3 text-right font-mono text-sm ${trade.pnl ? (trade.pnl >= 0 ? 'profit' : 'loss') : ''}`}>
                          {trade.pnl ? `$${trade.pnl.toFixed(2)}` : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="text-center py-8 text-[#888888]">
                  No trade history
                </div>
              )}
            </div>
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default BottomPanel;