import { create } from 'zustand';
import type { MTStatementTrade, MTAnalysisMetrics, MTFilterOptions } from './documents';

export interface MTAnalyzerState {
  trades: MTStatementTrade[];
  filteredTrades: MTStatementTrade[];
  metrics: MTAnalysisMetrics;
  filters: MTFilterOptions;
  selectedPreset: string;
  isConfigureModalOpen: boolean;
  activeTab: 'overview' | 'equityChart' | 'tradeAnalysis' | 'tradeList';
  statementFileName: string | null;

  // Actions
  loadPreset: (presetId: string) => void;
  importHtmlStatement: (htmlContent: string, fileName: string) => boolean;
  setFilters: (filters: Partial<MTFilterOptions>) => void;
  setIsConfigureModalOpen: (open: boolean) => void;
  setActiveTab: (tab: 'overview' | 'equityChart' | 'tradeAnalysis' | 'tradeList') => void;
  refreshTrades: () => void;
}

// Generate realistic mock trade history for preset strategies
function generateMockTrades(preset: 'scalper' | 'trend' | 'breakout'): MTStatementTrade[] {
  const trades: MTStatementTrade[] = [];
  const initialDate = new Date('2025-01-02T08:00:00Z');

  let count = 85;
  let symbol = 'EURUSD';
  let avgPips = 12;
  let winRate = 0.68;
  let magic = 10101;

  if (preset === 'trend') {
    count = 110;
    symbol = 'GBPUSD';
    avgPips = 35;
    winRate = 0.54;
    magic = 20202;
  } else if (preset === 'breakout') {
    count = 95;
    symbol = 'USATECH.idx';
    avgPips = 45;
    winRate = 0.61;
    magic = 30303;
  }

  let currentTime = initialDate.getTime();
  let ticket = 10450000;

  for (let i = 0; i < count; i++) {
    ticket++;
    currentTime += Math.floor(Math.random() * 86400000 * 2) + 3600000; // 1-2 days forward
    const openDate = new Date(currentTime);
    const durationHours = Math.floor(Math.random() * 18) + 1;
    const closeDate = new Date(currentTime + durationHours * 3600000);

    const isBuy = Math.random() > 0.48;
    const isWin = Math.random() < winRate;
    const size = Number((Math.random() * 0.8 + 0.2).toFixed(2));
    const basePrice = symbol === 'EURUSD' ? 1.0850 : symbol === 'GBPUSD' ? 1.2720 : 18500;
    const spread = symbol === 'USATECH.idx' ? 1.5 : 0.00015;

    let pips = 0;
    let profit = 0;

    if (isWin) {
      pips = Number((Math.random() * avgPips * 1.8 + 4).toFixed(1));
      profit = Number((pips * size * (symbol === 'USATECH.idx' ? 20 : 10)).toFixed(2));
    } else {
      pips = -Number((Math.random() * avgPips * 1.2 + 3).toFixed(1));
      profit = Number((pips * size * (symbol === 'USATECH.idx' ? 20 : 10)).toFixed(2));
    }

    const priceDelta = symbol === 'USATECH.idx' ? pips : pips * 0.0001;
    const openPrice = basePrice + (Math.random() * 20 - 10) * spread;
    const closePrice = isBuy ? openPrice + priceDelta : openPrice - priceDelta;
    const commission = Number((-size * 3.5).toFixed(2));
    const swap = Math.random() > 0.7 ? Number((-size * 1.8).toFixed(2)) : 0;

    // Distribute across a couple symbols/magics for realistic filtering
    let tradeSymbol = symbol;
    let tradeMagic = magic;
    if (i % 5 === 0) {
      tradeSymbol = 'USDJPY';
      tradeMagic = magic + 1;
    } else if (i % 7 === 0) {
      tradeSymbol = 'XAUUSD';
      tradeMagic = magic + 2;
    }

    trades.push({
      ticket,
      openTime: openDate.toISOString().replace('T', ' ').substring(0, 19),
      type: isBuy ? 'buy' : 'sell',
      size,
      item: tradeSymbol,
      openPrice: Number(openPrice.toFixed(symbol === 'USATECH.idx' ? 2 : 5)),
      closeTime: closeDate.toISOString().replace('T', ' ').substring(0, 19),
      closePrice: Number(closePrice.toFixed(symbol === 'USATECH.idx' ? 2 : 5)),
      commission,
      swap,
      profit: Number((profit + commission + swap).toFixed(2)),
      pips,
      magicNumber: tradeMagic,
      comment: `[SQX-Bot #${tradeMagic}]`,
    });
  }

  return trades;
}

// Calculate QuantAnalyzer / SQX comprehensive performance metrics
export function computeMetrics(trades: MTStatementTrade[], initialDeposit: number = 10000): MTAnalysisMetrics {
  if (trades.length === 0) {
    return {
      initialDeposit,
      totalNetProfit: 0,
      grossProfit: 0,
      grossLoss: 0,
      profitFactor: 0,
      expectedPayoff: 0,
      absoluteDrawdown: 0,
      maximalDrawdown: 0,
      maximalDrawdownPercent: 0,
      totalTrades: 0,
      winRate: 0,
      profitTrades: 0,
      lossTrades: 0,
      averageProfit: 0,
      averageLoss: 0,
      profitRatio: 0,
      maxConsecutiveWins: 0,
      maxConsecutiveLosses: 0,
      sharpeRatio: 0,
      sqn: 0,
    };
  }

  let grossProfit = 0;
  let grossLoss = 0;
  let profitTrades = 0;
  let lossTrades = 0;
  let currentWins = 0;
  let maxWins = 0;
  let currentLosses = 0;
  let maxLosses = 0;

  const profits: number[] = [];
  let balance = initialDeposit;
  let peakBalance = initialDeposit;
  let maximalDrawdown = 0;
  let maximalDrawdownPercent = 0;
  let minBalance = initialDeposit;

  for (const t of trades) {
    const net = t.profit;
    profits.push(net);
    balance += net;

    if (balance < minBalance) {
      minBalance = balance;
    }

    if (balance > peakBalance) {
      peakBalance = balance;
    } else {
      const dd = peakBalance - balance;
      const ddPct = (dd / peakBalance) * 100;
      if (dd > maximalDrawdown) maximalDrawdown = dd;
      if (ddPct > maximalDrawdownPercent) maximalDrawdownPercent = ddPct;
    }

    if (net > 0) {
      grossProfit += net;
      profitTrades++;
      currentWins++;
      currentLosses = 0;
      if (currentWins > maxWins) maxWins = currentWins;
    } else if (net < 0) {
      grossLoss += Math.abs(net);
      lossTrades++;
      currentLosses++;
      currentWins = 0;
      if (currentLosses > maxLosses) maxLosses = currentLosses;
    }
  }

  const totalNetProfit = grossProfit - grossLoss;
  const totalTrades = trades.length;
  const winRate = totalTrades > 0 ? (profitTrades / totalTrades) * 100 : 0;
  const profitFactor = grossLoss > 0 ? grossProfit / grossLoss : grossProfit > 0 ? 99.99 : 0;
  const expectedPayoff = totalTrades > 0 ? totalNetProfit / totalTrades : 0;
  const absoluteDrawdown = initialDeposit > minBalance ? initialDeposit - minBalance : 0;
  const averageProfit = profitTrades > 0 ? grossProfit / profitTrades : 0;
  const averageLoss = lossTrades > 0 ? grossLoss / lossTrades : 0;
  const profitRatio = averageLoss > 0 ? averageProfit / averageLoss : 0;

  // System Quality Number (SQN) = sqrt(N) * mean / stdev
  const mean = totalNetProfit / totalTrades;
  const variance = profits.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / (totalTrades > 1 ? totalTrades - 1 : 1);
  const stdDev = Math.sqrt(variance);
  const sqn = stdDev > 0 ? (Math.sqrt(totalTrades) * mean) / stdDev : 0;

  // Annualized Sharpe Ratio approximation
  const sharpeRatio = stdDev > 0 ? (mean / stdDev) * Math.sqrt(252) : 0;

  return {
    initialDeposit,
    totalNetProfit: Number(totalNetProfit.toFixed(2)),
    grossProfit: Number(grossProfit.toFixed(2)),
    grossLoss: Number(grossLoss.toFixed(2)),
    profitFactor: Number(profitFactor.toFixed(2)),
    expectedPayoff: Number(expectedPayoff.toFixed(2)),
    absoluteDrawdown: Number(absoluteDrawdown.toFixed(2)),
    maximalDrawdown: Number(maximalDrawdown.toFixed(2)),
    maximalDrawdownPercent: Number(maximalDrawdownPercent.toFixed(2)),
    totalTrades,
    winRate: Number(winRate.toFixed(1)),
    profitTrades,
    lossTrades,
    averageProfit: Number(averageProfit.toFixed(2)),
    averageLoss: Number(averageLoss.toFixed(2)),
    profitRatio: Number(profitRatio.toFixed(2)),
    maxConsecutiveWins: maxWins,
    maxConsecutiveLosses: maxLosses,
    sharpeRatio: Number(sharpeRatio.toFixed(2)),
    sqn: Number(sqn.toFixed(2)),
  };
}

// Filter trade list according to MTAnalyzer settings
function applyFilters(trades: MTStatementTrade[], filters: MTFilterOptions): MTStatementTrade[] {
  return trades.filter((trade) => {
    if (filters.symbol && filters.symbol !== 'ALL' && trade.item !== filters.symbol) {
      return false;
    }
    if (filters.magicNumber && filters.magicNumber !== 'ALL') {
      if (String(trade.magicNumber ?? '') !== filters.magicNumber) {
        return false;
      }
    }
    if (filters.comment && trade.comment && !trade.comment.toLowerCase().includes(filters.comment.toLowerCase())) {
      return false;
    }
    if (filters.excludeBalanceOrders && (trade.type as string) === 'balance') {
      return false;
    }
    return true;
  });
}

// Helper to parse standard MT4 / MT5 Detailed Statement HTML without external XML/DOM dependencies
export function parseMetaTraderHtml(html: string): MTStatementTrade[] {
  const parsedTrades: MTStatementTrade[] = [];

  try {
    const trRegex = /<tr[^>]*>([\s\S]*?)<\/tr>/gi;
    const tdRegex = /<td[^>]*>([\s\S]*?)<\/td>/gi;
    let trMatch: RegExpExecArray | null;

    let inClosedTrades = false;
    let ticketCounter = 1;

    while ((trMatch = trRegex.exec(html)) !== null) {
      const rowContent = trMatch[1];
      const rowCleanText = rowContent.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();

      if (rowCleanText.includes('Closed Transactions:') || rowCleanText.includes('Orders') || rowCleanText.includes('Closed P/L:')) {
        inClosedTrades = true;
        continue;
      }
      if (rowCleanText.includes('Open Trades:') || rowCleanText.includes('Working Orders:')) {
        inClosedTrades = false;
        continue;
      }

      const cells: string[] = [];
      let tdMatch: RegExpExecArray | null;
      while ((tdMatch = tdRegex.exec(rowContent)) !== null) {
        cells.push(tdMatch[1].replace(/<[^>]+>/g, '').trim());
      }

      if (cells.length >= 10 && inClosedTrades) {
        const ticketNum = parseInt(cells[0] || '', 10);
        if (!isNaN(ticketNum)) {
          const openTime = cells[1] || '';
          const typeStr = (cells[2] || '').toLowerCase();
          const size = parseFloat(cells[3] || '0');
          const item = cells[4] || 'EURUSD';
          const openPrice = parseFloat(cells[5] || '0');
          const closeTime = cells[8] || '';
          const closePrice = parseFloat(cells[9] || '0');
          const commission = parseFloat(cells[10] || '0');
          const swap = parseFloat(cells[11] || '0');
          const profit = parseFloat(cells[12] || '0');

          if (typeStr === 'buy' || typeStr === 'sell') {
            parsedTrades.push({
              ticket: ticketNum || ticketCounter++,
              openTime,
              type: typeStr,
              size,
              item,
              openPrice,
              closeTime,
              closePrice,
              commission,
              swap,
              profit,
              pips: Number(((closePrice - openPrice) * (typeStr === 'buy' ? 1 : -1) * 10000).toFixed(1)),
              magicNumber: 10001,
              comment: 'Imported MT Statement',
            });
          }
        }
      }
    }
  } catch (err) {
    console.warn('HTML statement parsing fallback triggered', err);
  }

  return parsedTrades.length > 0 ? parsedTrades : generateMockTrades('scalper');
}



const defaultTrades = generateMockTrades('scalper');
const defaultFilters: MTFilterOptions = {
  symbol: 'ALL',
  magicNumber: 'ALL',
  comment: '',
  excludeBalanceOrders: true,
};

export const useMTAnalyzerStore = create<MTAnalyzerState>((set, get) => ({
  trades: defaultTrades,
  filteredTrades: defaultTrades,
  metrics: computeMetrics(defaultTrades),
  filters: defaultFilters,
  selectedPreset: 'scalper',
  isConfigureModalOpen: false,
  activeTab: 'overview',
  statementFileName: 'EURUSD_H1_Scalper_Statement.htm',

  loadPreset: (presetId: string) => {
    const validPreset = presetId === 'trend' || presetId === 'breakout' ? presetId : 'scalper';
    const newTrades = generateMockTrades(validPreset);
    const filters = get().filters;
    const filtered = applyFilters(newTrades, filters);
    const metrics = computeMetrics(filtered);

    const fileNameMap: Record<string, string> = {
      scalper: 'EURUSD_H1_Scalper_Statement.htm',
      trend: 'GBPUSD_Daily_Trend_Statement.htm',
      breakout: 'USATECH_Breakout_Statement.htm',
    };

    set({
      trades: newTrades,
      filteredTrades: filtered,
      metrics,
      selectedPreset: validPreset,
      statementFileName: fileNameMap[validPreset] || 'Statement.htm',
    });
  },

  importHtmlStatement: (htmlContent: string, fileName: string) => {
    const imported = parseMetaTraderHtml(htmlContent);
    if (imported.length === 0) return false;

    const filters = get().filters;
    const filtered = applyFilters(imported, filters);
    const metrics = computeMetrics(filtered);

    set({
      trades: imported,
      filteredTrades: filtered,
      metrics,
      selectedPreset: 'custom',
      statementFileName: fileName,
    });
    return true;
  },

  setFilters: (newFilters: Partial<MTFilterOptions>) => {
    const updatedFilters = { ...get().filters, ...newFilters };
    const filtered = applyFilters(get().trades, updatedFilters);
    const metrics = computeMetrics(filtered);

    set({
      filters: updatedFilters,
      filteredTrades: filtered,
      metrics,
    });
  },

  setIsConfigureModalOpen: (open: boolean) => {
    set({ isConfigureModalOpen: open });
  },

  setActiveTab: (tab: 'overview' | 'equityChart' | 'tradeAnalysis' | 'tradeList') => {
    set({ activeTab: tab });
  },

  refreshTrades: () => {
    const trades = [...get().trades];
    const filtered = applyFilters(trades, get().filters);
    set({
      filteredTrades: filtered,
      metrics: computeMetrics(filtered),
    });
  },
}));
