import { create } from 'zustand';
import { initialProducts } from '../mock/productsData';
import type { TradingStoreState } from '../types/store';
import type { Position, TradeLogEntry, Order } from '../types/market';

export const useTradingStore = create<TradingStoreState>((set) => ({
  // Account Financial State
  practiceBalance: 100000.00,
  challengeBalance: 100218.75,
  netPL: 0.00,
  margin: 0.00,
  available: 100000.00,
  ranking: '2nd',
  mode: 'practice', // 'practice' | 'challenge'
  theme: 'dark',   // 'dark' | 'light'

  // Market Quotes Data
  products: initialProducts,
  selectedSymbol: 'ESU5',

  // Trading State: Orders, Positions, Trade Log
  orders: [
    {
      id: 'ORD-101',
      side: 'SELL',
      symbol: 'MGCQ5',
      month: 'Aug 25',
      strike: '-',
      cp: '-',
      qty: 1,
      leaves: 1,
      type: 'LMT',
      fillPx: '-',
      limitPx: 3315.8,
      stopPx: '-',
      status: 'Working',
      timestamp: '11:14:20'
    },
    {
      id: 'ORD-102',
      side: 'SELL',
      symbol: 'MGCQ5',
      month: 'Aug 25',
      strike: '-',
      cp: '-',
      qty: 1,
      leaves: 1,
      type: 'STP',
      fillPx: '-',
      limitPx: '-',
      stopPx: 3305.8,
      status: 'Working',
      timestamp: '11:14:35'
    },
    {
      id: 'ORD-103',
      side: 'BUY',
      symbol: 'MGCQ5',
      month: 'Aug 25',
      strike: '-',
      cp: '-',
      qty: 1,
      leaves: 0,
      type: 'MKT',
      fillPx: 3308.3,
      limitPx: '-',
      stopPx: '-',
      status: 'Filled',
      timestamp: '11:15:02'
    },
    {
      id: 'ORD-104',
      side: 'SELL',
      symbol: 'CLQ5',
      month: 'Aug 25',
      strike: '-',
      cp: '-',
      qty: 1,
      leaves: 0,
      type: 'MKT',
      fillPx: 65.07,
      limitPx: '-',
      stopPx: '-',
      status: 'Filled',
      timestamp: '11:16:10'
    },
    {
      id: 'ORD-105',
      side: 'BUY',
      symbol: 'ESU5',
      month: 'Sep 25',
      strike: '-',
      cp: '-',
      qty: 1,
      leaves: 0,
      type: 'STP',
      fillPx: 6244.0,
      limitPx: '-',
      stopPx: 6244.0,
      status: 'Filled',
      timestamp: '11:18:45'
    }
  ],

  positions: [
    {
      symbol: 'CLQ5',
      contract: 'WTI Crude Oil',
      month: 'Aug 25',
      strike: '-',
      cp: '-',
      position: 'Short 1',
      buys: 0,
      sells: 1,
      averagePx: 65.07,
      unrealizedPL: -10.00,
      realizedPL: 0.00
    },
    {
      symbol: 'ESU5',
      contract: 'E-mini S&P 500',
      month: 'Sep 25',
      strike: '-',
      cp: '-',
      position: 'Long 1',
      buys: 1,
      sells: 0,
      averagePx: 6244.00,
      unrealizedPL: -187.50,
      realizedPL: 0.00
    },
    {
      symbol: 'MGCQ5',
      contract: 'Micro Gold',
      month: 'Aug 25',
      strike: '-',
      cp: '-',
      position: 'Long 1',
      buys: 1,
      sells: 0,
      averagePx: 3308.30,
      unrealizedPL: 0.00,
      realizedPL: 0.00
    }
  ],

  tradeLog: [
    {
      id: 1,
      symbol: 'MNQU5',
      transactionDate: '6/27/2025 | 2:36:10 PM',
      openClose: 'Open',
      side: 'BUY',
      cp: '-',
      strike: '-',
      qty: 1,
      type: 'MKT',
      px: 0.0,
      tif: 'DAY',
      fillPx: 22681.25,
      stop: '-',
      stopPx: '$0.0',
      notes: 'Breakout entry on morning high'
    },
    {
      id: 2,
      symbol: 'MNQU5',
      transactionDate: '6/27/2025 | 2:40:53 PM',
      openClose: 'Close',
      side: 'SELL',
      cp: '-',
      strike: '-',
      qty: 1,
      type: 'MKT',
      px: 0.0,
      tif: 'DAY',
      fillPx: 22695.0,
      stop: '-',
      stopPx: '$0.0',
      notes: 'Profit target hit +13.75 pts'
    }
  ],

  // Active Order Ticket State
  isOrderTicketOpen: false,
  orderTicketProps: {
    symbol: 'ESU5',
    side: 'BUY',
    type: 'Market',
    defaultTab: 'futures'
  },

  // System Settings modal state (in-place popup; no navigation).
  isSettingsOpen: false,

  // State Actions
  setMode: (mode) => set({ mode }),
  toggleTheme: () => set((state) => ({ theme: state.theme === 'dark' ? 'light' : 'dark' })),
  resetBalance: () => set(() => ({
    practiceBalance: 100000.00,
    netPL: 0.00,
    margin: 0.00,
    available: 100000.00
  })),

  // Order Ticket Controls
  openOrderTicket: (props = {}) => set((state) => ({
    isOrderTicketOpen: true,
    orderTicketProps: { ...state.orderTicketProps, ...props }
  })),
  closeOrderTicket: () => set({ isOrderTicketOpen: false }),

  // System Settings Modal Controls
  openSettings: () => set({ isSettingsOpen: true }),
  closeSettings: () => set({ isSettingsOpen: false }),

  // Order Execution & Simulation Engine
  submitOrder: (orderData) => set((state) => {
    const { symbol, side, qty, orderType, limitPrice, stopPrice, tif, cp, strike } = orderData;
    const targetProduct = state.products.find((p) => p.symbol === symbol) || state.products[0];
    const fillPrice = orderType === 'Market' ? (side === 'BUY' ? targetProduct.ask : targetProduct.bid) : (limitPrice || targetProduct.lastPrice);

    const newOrder: Order = {
      id: `ORD-${Math.floor(1000 + Math.random() * 9000)}`,
      side,
      symbol,
      month: targetProduct.contractMonth,
      strike: strike || '-',
      cp: cp || '-',
      qty: Number(qty),
      leaves: orderType === 'Market' ? 0 : Number(qty),
      type: orderType === 'Market' ? 'MKT' : orderType === 'Limit' ? 'LMT' : 'STP',
      fillPx: orderType === 'Market' ? fillPrice : '-',
      limitPx: limitPrice || '-',
      stopPx: stopPrice || '-',
      status: orderType === 'Market' ? 'Filled' : 'Working',
      timestamp: new Date().toLocaleTimeString('en-US', { hour12: false })
    };

    const updatedPositions: Position[] = [...state.positions];
    const updatedLog: TradeLogEntry[] = [...state.tradeLog];

    if (orderType === 'Market') {
      const existingPosIndex = updatedPositions.findIndex((p) => p.symbol === symbol);
      if (existingPosIndex >= 0) {
        const existingPos = updatedPositions[existingPosIndex];
        const isLong = existingPos.position.includes('Long');
        const posQty = parseInt(existingPos.position.replace(/[^0-9]/g, '')) || 1;

        if ((side === 'BUY' && isLong) || (side === 'SELL' && !isLong)) {
          // Increase position size
          const newQty = posQty + Number(qty);
          updatedPositions[existingPosIndex] = {
            ...existingPos,
            position: `${isLong ? 'Long' : 'Short'} ${newQty}`,
            buys: side === 'BUY' ? existingPos.buys + Number(qty) : existingPos.buys,
            sells: side === 'SELL' ? existingPos.sells + Number(qty) : existingPos.sells
          };
        } else {
          // Reduce or close position
          if (posQty <= Number(qty)) {
            updatedPositions.splice(existingPosIndex, 1);
          } else {
            const newQty = posQty - Number(qty);
            updatedPositions[existingPosIndex] = {
              ...existingPos,
              position: `${isLong ? 'Long' : 'Short'} ${newQty}`
            };
          }
        }
      } else {
        // Create new position
        updatedPositions.push({
          symbol,
          contract: targetProduct.name,
          month: targetProduct.contractMonth,
          strike: strike || '-',
          cp: cp || '-',
          position: `${side === 'BUY' ? 'Long' : 'Short'} ${qty}`,
          buys: side === 'BUY' ? Number(qty) : 0,
          sells: side === 'SELL' ? Number(qty) : 0,
          averagePx: fillPrice,
          unrealizedPL: 0.00,
          realizedPL: 0.00
        });
      }

      // Add to Trade Log
      updatedLog.unshift({
        id: Date.now(),
        symbol,
        transactionDate: `${new Date().toLocaleDateString()} | ${new Date().toLocaleTimeString()}`,
        openClose: 'Open',
        side,
        cp: cp || '-',
        strike: strike || '-',
        qty: Number(qty),
        type: newOrder.type,
        px: 0.0,
        tif: tif || 'DAY',
        fillPx: fillPrice,
        stop: '-',
        stopPx: '$0.0',
        notes: 'Simulated Order Execution'
      });
    }

    return {
      orders: [newOrder, ...state.orders],
      positions: updatedPositions,
      tradeLog: updatedLog,
      isOrderTicketOpen: false
    };
  }),

  flattenPositions: () => set((state) => {
    // Flatten all active positions instantly
    const newLogEntries: TradeLogEntry[] = state.positions.map((pos) => ({
      id: Date.now() + Math.random(),
      symbol: pos.symbol,
      transactionDate: `${new Date().toLocaleDateString()} | ${new Date().toLocaleTimeString()}`,
      openClose: 'Close',
      side: pos.position.includes('Long') ? 'SELL' : 'BUY',
      cp: pos.cp,
      strike: pos.strike,
      qty: parseInt(pos.position.replace(/[^0-9]/g, '')) || 1,
      type: 'MKT',
      px: 0.0,
      tif: 'DAY',
      fillPx: pos.averagePx,
      stop: '-',
      stopPx: '$0.0',
      notes: 'Flatten All Positions Shortcut'
    }));

    return {
      positions: [],
      tradeLog: [...newLogEntries, ...state.tradeLog]
    };
  }),

  cancelAllOrders: () => set((state) => ({
    orders: state.orders.map((o) => o.status === 'Working' ? { ...o, status: 'Cancelled' as const, leaves: 0 } : o)
  })),

  cancelOrder: (orderId) => set((state) => ({
    orders: state.orders.map((o) => o.id === orderId ? { ...o, status: 'Cancelled' as const, leaves: 0 } : o)
  })),

  // Real-Time Ticker Simulator Loop
  updateQuotes: () => set((state) => {
    const updatedProducts = state.products.map((p) => {
      const delta = (Math.random() - 0.49) * (p.lastPrice > 1000 ? 0.75 : 0.05);
      const newLast = parseFloat((p.lastPrice + delta).toFixed(2));
      const newChange = parseFloat((p.change + delta).toFixed(2));
      const newChangePct = parseFloat(((newChange / p.priorSettle) * 100).toFixed(2));
      const newBid = parseFloat((newLast - (p.lastPrice > 1000 ? 0.25 : 0.01)).toFixed(2));
      const newAsk = parseFloat((newLast + (p.lastPrice > 1000 ? 0.25 : 0.01)).toFixed(2));

      return {
        ...p,
        lastPrice: newLast,
        change: newChange,
        changePercent: newChangePct,
        high: Math.max(p.high, newLast),
        low: Math.min(p.low, newLast),
        bid: newBid,
        ask: newAsk,
        volume: p.volume + Math.floor(Math.random() * 3)
      };
    });

    // Update Unrealized P/L for open positions
    const updatedPositions = state.positions.map((pos) => {
      const prod = updatedProducts.find((p) => p.symbol === pos.symbol);
      if (!prod) return pos;
      const isLong = pos.position.includes('Long');
      const qty = parseInt(pos.position.replace(/[^0-9]/g, '')) || 1;
      const diff = isLong ? (prod.lastPrice - pos.averagePx) : (pos.averagePx - prod.lastPrice);
      const multiplier = pos.symbol.startsWith('M') ? 5 : 50; // Contract multiplier
      const uPL = parseFloat((diff * qty * multiplier).toFixed(2));
      return { ...pos, unrealizedPL: uPL };
    });

    const totalNetPL = updatedPositions.reduce((acc, pos) => acc + pos.unrealizedPL, 0);

    return {
      products: updatedProducts,
      positions: updatedPositions,
      netPL: totalNetPL,
      available: state.practiceBalance + totalNetPL
    };
  })
}));
