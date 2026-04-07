import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ArrowUp, ArrowDown } from '@phosphor-icons/react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const OrderBookPanel = ({ symbol, marketPrice, onExecuteTrade, paperTrading }) => {
  const [orderbook, setOrderbook] = useState({ bids: [], asks: [] });
  const [quantity, setQuantity] = useState(0.01);
  
  useEffect(() => {
    fetchOrderBook();
    const interval = setInterval(fetchOrderBook, 2000);
    return () => clearInterval(interval);
  }, [symbol]);
  
  const fetchOrderBook = async () => {
    try {
      const response = await axios.get(`${API}/market/orderbook/${symbol}?limit=15`);
      setOrderbook(response.data);
    } catch (error) {
      console.error('Error fetching orderbook:', error);
    }
  };
  
  const handleBuy = () => {
    if (quantity > 0) {
      onExecuteTrade('BUY', quantity);
    }
  };
  
  const handleSell = () => {
    if (quantity > 0) {
      onExecuteTrade('SELL', quantity);
    }
  };
  
  return (
    <div className="orderbook-panel p-4 flex flex-col scrollbar-thin" data-testid="orderbook-panel">
      <h2 className="text-lg font-medium tracking-tight mb-4">ORDER BOOK</h2>
      
      <div className="mb-4">
        <div className="flex items-center justify-between text-xs text-[#888888] uppercase tracking-wider mb-2 px-2">
          <span>Price (USDT)</span>
          <span>Amount</span>
        </div>
        
        <div className="space-y-px">
          {orderbook.asks.slice(0, 10).reverse().map((ask, idx) => (
            <div key={`ask-${idx}`} className="flex items-center justify-between px-2 py-1 hover:bg-[#1A1A1A] relative">
              <div 
                className="absolute left-0 top-0 bottom-0 loss-bg" 
                style={{ width: `${(ask[1] / Math.max(...orderbook.asks.map(a => a[1]))) * 100}%` }}
              ></div>
              <span className="font-mono text-sm loss relative z-10">{ask[0].toFixed(2)}</span>
              <span className="font-mono text-xs text-[#888888] relative z-10">{ask[1].toFixed(6)}</span>
            </div>
          ))}
        </div>
        
        {marketPrice && (
          <div className="border-y border-[#222222] py-2 my-2">
            <div className="flex items-center justify-center gap-2">
              <span className="font-mono text-lg font-semibold tracking-tighter">
                ${parseFloat(marketPrice.price).toFixed(2)}
              </span>
              <span className={`text-xs font-mono ${marketPrice.change_24h >= 0 ? 'profit' : 'loss'}`}>
                {marketPrice.change_24h >= 0 ? '▲' : '▼'} {Math.abs(marketPrice.change_24h).toFixed(2)}%
              </span>
            </div>
          </div>
        )}
        
        <div className="space-y-px">
          {orderbook.bids.slice(0, 10).map((bid, idx) => (
            <div key={`bid-${idx}`} className="flex items-center justify-between px-2 py-1 hover:bg-[#1A1A1A] relative">
              <div 
                className="absolute left-0 top-0 bottom-0 profit-bg" 
                style={{ width: `${(bid[1] / Math.max(...orderbook.bids.map(b => b[1]))) * 100}%` }}
              ></div>
              <span className="font-mono text-sm profit relative z-10">{bid[0].toFixed(2)}</span>
              <span className="font-mono text-xs text-[#888888] relative z-10">{bid[1].toFixed(6)}</span>
            </div>
          ))}
        </div>
      </div>
      
      <div className="mt-auto pt-4 border-t border-[#222222]">
        <h3 className="text-sm font-medium mb-3 uppercase tracking-wider">Quick Trade</h3>
        
        <div className="mb-3">
          <label className="text-xs text-[#888888] uppercase tracking-wider block mb-2">Quantity</label>
          <Input 
            type="number" 
            value={quantity}
            onChange={(e) => setQuantity(parseFloat(e.target.value) || 0)}
            step="0.001"
            className="bg-black border-[#222222] text-white font-mono rounded-none h-9"
            data-testid="quantity-input"
          />
        </div>
        
        <div className="grid grid-cols-2 gap-2">
          <Button 
            onClick={handleBuy}
            className="bg-[#00E676] hover:bg-[#00C864] text-black rounded-none h-10 font-medium"
            data-testid="buy-button"
          >
            <ArrowUp size={16} weight="bold" className="mr-1" />
            BUY
          </Button>
          
          <Button 
            onClick={handleSell}
            className="bg-[#FF3344] hover:bg-[#E02030] text-white rounded-none h-10 font-medium"
            data-testid="sell-button"
          >
            <ArrowDown size={16} weight="bold" className="mr-1" />
            SELL
          </Button>
        </div>
        
        {paperTrading && (
          <div className="mt-2 px-2 py-1 bg-[#FFB800] bg-opacity-10 border border-[#FFB800] text-[#FFB800] text-xs text-center">
            PAPER TRADING MODE
          </div>
        )}
      </div>
    </div>
  );
};

export default OrderBookPanel;