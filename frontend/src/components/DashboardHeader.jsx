import React from 'react';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ChartLine, Lightning, TestTube, Robot } from '@phosphor-icons/react';

const DashboardHeader = ({
  selectedSymbol,
  setSelectedSymbol,
  selectedTimeframe,
  setSelectedTimeframe,
  paperTrading,
  setPaperTrading,
  autoTrade,
  setAutoTrade,
  marketPrice,
  stats
}) => {
  const symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT'];
  const timeframes = ['1m', '5m', '15m', '1h', '4h'];
  
  return (
    <div className="dashboard-header px-4 py-3" data-testid="dashboard-header">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white flex items-center justify-center">
              <ChartLine size={24} weight="bold" color="#000" />
            </div>
            <h1 className="text-xl font-semibold tracking-tight">QUANT TRADER PRO</h1>
          </div>
          
          <div className="h-8 w-px bg-[#222222]"></div>
          
          <div className="flex items-center gap-3">
            <span className="text-xs text-[#888888] uppercase tracking-wider">Symbol</span>
            <Select value={selectedSymbol} onValueChange={setSelectedSymbol}>
              <SelectTrigger className="w-32 bg-black border-[#222222] text-white font-mono" data-testid="symbol-selector">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-black border-[#222222]">
                {symbols.map(sym => (
                  <SelectItem key={sym} value={sym} className="text-white font-mono hover:bg-[#1A1A1A]">
                    {sym}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          <div className="flex items-center gap-3">
            <span className="text-xs text-[#888888] uppercase tracking-wider">Timeframe</span>
            <Select value={selectedTimeframe} onValueChange={setSelectedTimeframe}>
              <SelectTrigger className="w-24 bg-black border-[#222222] text-white font-mono" data-testid="timeframe-selector">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-black border-[#222222]">
                {timeframes.map(tf => (
                  <SelectItem key={tf} value={tf} className="text-white font-mono hover:bg-[#1A1A1A]">
                    {tf}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          {marketPrice && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-[#888888]">PRICE</span>
              <span className="font-mono text-2xl font-semibold tracking-tighter">
                ${parseFloat(marketPrice.price).toFixed(2)}
              </span>
              <span className={`text-sm font-mono ${marketPrice.change_24h >= 0 ? 'profit' : 'loss'}`}>
                {marketPrice.change_24h >= 0 ? '+' : ''}{marketPrice.change_24h?.toFixed(2)}%
              </span>
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-6">
          {stats && (
            <div className="flex items-center gap-6">
              <div className="text-right">
                <div className="text-xs text-[#888888] uppercase tracking-wider">Total PnL</div>
                <div className={`font-mono text-lg font-medium ${stats.total_pnl >= 0 ? 'profit' : 'loss'}`}>
                  ${stats.total_pnl?.toFixed(2)}
                </div>
              </div>
              
              <div className="text-right">
                <div className="text-xs text-[#888888] uppercase tracking-wider">Win Rate</div>
                <div className="font-mono text-lg font-medium">
                  {stats.win_rate?.toFixed(1)}%
                </div>
              </div>
              
              <div className="text-right">
                <div className="text-xs text-[#888888] uppercase tracking-wider">Positions</div>
                <div className="font-mono text-lg font-medium">
                  {stats.open_positions}
                </div>
              </div>
            </div>
          )}
          
          <div className="h-8 w-px bg-[#222222]"></div>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Switch 
                checked={paperTrading} 
                onCheckedChange={setPaperTrading}
                data-testid="paper-trading-toggle"
              />
              <div className="flex items-center gap-1.5">
                <TestTube size={16} weight="bold" />
                <span className="text-sm">Paper</span>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Switch 
                checked={autoTrade} 
                onCheckedChange={setAutoTrade}
                data-testid="auto-trade-toggle"
              />
              <div className="flex items-center gap-1.5">
                <Robot size={16} weight="bold" />
                <span className="text-sm">Auto</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardHeader;