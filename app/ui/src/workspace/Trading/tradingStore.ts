import { create } from 'zustand';
import type { BrokerAccount, ExecutionLogEntry, OrderKind, OrderSide, PendingOrder, Position } from '../../app/types';

interface TradingState {
  accounts: BrokerAccount[];
  selectedAccountId: string;
  positions: Position[];
  pendingOrders: PendingOrder[];
  logs: ExecutionLogEntry[];
  tradingPaused: boolean;
  killSwitchModalOpen: boolean;

  // Actions
  selectAccount: (id: string) => void;
  toggleTrading: () => void;
  setKillSwitchModalOpen: (open: boolean) => void;
  closePosition: (ticket: number) => void;
  closeAllPositions: () => void;
  cancelOrder: (ticket: number) => void;
  cancelAllOrders: () => void;
  executeEmergencyKillSwitch: () => void;
  submitOrder: (params: {
    symbol: string;
    side: OrderSide;
    kind: OrderKind;
    lots: number;
    price?: number;
    stopLoss?: number;
    takeProfit?: number;
    comment?: string;
  }) => { success: boolean; message: string };
  modifyPosition: (ticket: number, stopLoss: number, takeProfit: number) => void;
  addLog: (level: ExecutionLogEntry['level'], source: string, message: string) => void;
}

const initialAccounts: BrokerAccount[] = [
  {
    id: 'mt5-demo',
    broker: 'MetaTrader 5',
    accountNumber: '50184201',
    server: 'MetaQuotes-Demo',
    connected: true,
    latencyMs: 14,
    balance: 118420.0,
    equity: 121060.0,
    margin: 14200.0,
    freeMargin: 106860.0,
    marginLevel: 852.5,
    currency: 'USD',
    leverage: 100,
  },
  {
    id: 'ctrader-live',
    broker: 'cTrader',
    accountNumber: '891044',
    server: 'Spotware-Live',
    connected: true,
    latencyMs: 8,
    balance: 50000.0,
    equity: 50000.0,
    margin: 0.0,
    freeMargin: 50000.0,
    marginLevel: 0,
    currency: 'EUR',
    leverage: 30,
  },
  {
    id: 'binance-futures',
    broker: 'Binance Futures',
    accountNumber: 'BN-882190',
    server: 'fapi.binance.com',
    connected: true,
    latencyMs: 22,
    balance: 24500.0,
    equity: 24420.0,
    margin: 3200.0,
    freeMargin: 21220.0,
    marginLevel: 763.1,
    currency: 'USDT',
    leverage: 20,
  },
];

const initialPositions: Position[] = [
  {
    id: 'pos-1',
    ticket: 108421,
    symbol: 'EURUSD',
    side: 'Buy',
    lots: 1.5,
    openPrice: 1.0825,
    currentPrice: 1.0862,
    stopLoss: 1.078,
    takeProfit: 1.092,
    swap: -3.2,
    pnl: 555.0,
    pnlPercent: 0.34,
    openTime: '2026-09-21 08:30:15',
    magicNumber: 10101,
    comment: 'SQX Trend Crossover',
  },
  {
    id: 'pos-2',
    ticket: 108422,
    symbol: 'NQ100',
    side: 'Buy',
    lots: 0.5,
    openPrice: 20120.5,
    currentPrice: 20285.0,
    stopLoss: 19950.0,
    takeProfit: 20500.0,
    swap: 0.0,
    pnl: 1645.0,
    pnlPercent: 0.82,
    openTime: '2026-09-21 09:15:42',
    magicNumber: 10102,
    comment: 'Morning Breakout',
  },
  {
    id: 'pos-3',
    ticket: 108423,
    symbol: 'GBPUSD',
    side: 'Sell',
    lots: 2.0,
    openPrice: 1.312,
    currentPrice: 1.3094,
    stopLoss: 1.316,
    takeProfit: 1.302,
    swap: -5.4,
    pnl: 520.0,
    pnlPercent: 0.2,
    openTime: '2026-09-21 10:00:00',
    magicNumber: 10103,
    comment: 'London Mean Revert',
  },
  {
    id: 'pos-4',
    ticket: 108424,
    symbol: 'BTCUSDT',
    side: 'Buy',
    lots: 0.2,
    openPrice: 64200.0,
    currentPrice: 63800.0,
    stopLoss: 62500.0,
    takeProfit: 68000.0,
    swap: -1.8,
    pnl: -80.0,
    pnlPercent: -0.62,
    openTime: '2026-09-21 11:20:00',
    magicNumber: 20201,
    comment: 'Crypto Momentum',
  },
];

const initialPendingOrders: PendingOrder[] = [
  {
    id: 'ord-1',
    ticket: 209110,
    symbol: 'EURUSD',
    kind: 'Buy Limit',
    lots: 1.0,
    orderPrice: 1.079,
    currentPrice: 1.0862,
    stopLoss: 1.074,
    takeProfit: 1.088,
    expiration: '2026-09-22 23:59:59',
    magicNumber: 10101,
    comment: 'Support Pullback',
  },
  {
    id: 'ord-2',
    ticket: 209111,
    symbol: 'US500',
    kind: 'Sell Limit',
    lots: 0.8,
    orderPrice: 5750.0,
    currentPrice: 5712.5,
    stopLoss: 5790.0,
    takeProfit: 5680.0,
    expiration: '2026-09-23 23:59:59',
    magicNumber: 10105,
    comment: 'Resistance Fade',
  },
];

const initialLogs: ExecutionLogEntry[] = [
  {
    id: 'log-1',
    timestamp: '2026-09-21 08:30:15',
    level: 'SUCCESS',
    source: 'Router',
    message: 'Order #108421 BUY 1.50 EURUSD filled at 1.08250 on MetaTrader 5',
  },
  {
    id: 'log-2',
    timestamp: '2026-09-21 09:15:42',
    level: 'SUCCESS',
    source: 'Router',
    message: 'Order #108422 BUY 0.50 NQ100 filled at 20120.50 on MetaTrader 5',
  },
  {
    id: 'log-3',
    timestamp: '2026-09-21 10:00:00',
    level: 'SUCCESS',
    source: 'Router',
    message: 'Order #108423 SELL 2.00 GBPUSD filled at 1.31200 on MetaTrader 5',
  },
  {
    id: 'log-4',
    timestamp: '2026-09-21 11:20:00',
    level: 'INFO',
    source: 'Bridge',
    message: 'Order #108424 BUY 0.20 BTCUSDT routed to Binance Futures',
  },
];

export const useTradingStore = create<TradingState>((set, get) => ({
  accounts: initialAccounts,
  selectedAccountId: 'mt5-demo',
  positions: initialPositions,
  pendingOrders: initialPendingOrders,
  logs: initialLogs,
  tradingPaused: false,
  killSwitchModalOpen: false,

  selectAccount: (id: string) => set({ selectedAccountId: id }),

  toggleTrading: () => {
    const next = !get().tradingPaused;
    set({ tradingPaused: next });
    get().addLog(
      next ? 'WARN' : 'INFO',
      'ExecutionController',
      next ? 'Automated strategy execution PAUSED by operator' : 'Automated strategy execution RESUMED'
    );
  },

  setKillSwitchModalOpen: (open: boolean) => set({ killSwitchModalOpen: open }),

  closePosition: (ticket: number) => {
    const pos = get().positions.find(p => p.ticket === ticket);
    if (!pos) return;
    set({ positions: get().positions.filter(p => p.ticket !== ticket) });
    get().addLog(
      'INFO',
      'Router',
      `Closed position #${ticket} ${pos.symbol} ${pos.side} ${pos.lots} lots at market with P/L $${pos.pnl.toFixed(2)}`
    );
  },

  closeAllPositions: () => {
    const count = get().positions.length;
    set({ positions: [] });
    get().addLog('WARN', 'EmergencyController', `FLATTEN ALL: Closed all ${count} open market positions`);
  },

  cancelOrder: (ticket: number) => {
    const ord = get().pendingOrders.find(o => o.ticket === ticket);
    if (!ord) return;
    set({ pendingOrders: get().pendingOrders.filter(o => o.ticket !== ticket) });
    get().addLog('INFO', 'Router', `Cancelled pending order #${ticket} ${ord.symbol} ${ord.kind}`);
  },

  cancelAllOrders: () => {
    const count = get().pendingOrders.length;
    set({ pendingOrders: [] });
    get().addLog('WARN', 'EmergencyController', `Cancelled all ${count} active pending orders`);
  },

  executeEmergencyKillSwitch: () => {
    const posCount = get().positions.length;
    const ordCount = get().pendingOrders.length;
    set({
      positions: [],
      pendingOrders: [],
      tradingPaused: true,
      killSwitchModalOpen: false,
    });
    get().addLog(
      'ERROR',
      'KILL_SWITCH',
      `EMERGENCY KILL SWITCH ACTIVATED: Closed ${posCount} positions, cancelled ${ordCount} orders, trading locked.`
    );
  },

  submitOrder: ({ symbol, side, kind, lots, price, stopLoss, takeProfit, comment }) => {
    if (get().tradingPaused) {
      return { success: false, message: 'Execution halted: Trading is currently paused' };
    }
    if (lots <= 0) {
      return { success: false, message: 'Invalid volume: Lots must be greater than 0' };
    }

    const ticket = Math.floor(100000 + Math.random() * 900000);
    const now = new Date().toISOString().replace('T', ' ').slice(0, 19);

    if (kind === 'Market') {
      const simulatedPrice = symbol.includes('USD') ? 1.085 : symbol.includes('NQ') ? 20250.0 : 64000.0;
      const newPos: Position = {
        id: `pos-${ticket}`,
        ticket,
        symbol,
        side,
        lots,
        openPrice: simulatedPrice,
        currentPrice: simulatedPrice,
        stopLoss: stopLoss ?? 0,
        takeProfit: takeProfit ?? 0,
        swap: 0,
        pnl: 0,
        pnlPercent: 0,
        openTime: now,
        magicNumber: 99999,
        comment: comment || 'Manual Order',
      };
      set({ positions: [newPos, ...get().positions] });
      get().addLog('SUCCESS', 'ManualExecution', `Market ${side} order #${ticket} for ${lots} ${symbol} filled at ${simulatedPrice}`);
      return { success: true, message: `Position #${ticket} opened successfully` };
    }

    const pendingKind = side === 'Buy' ? (price && price < 1.1 ? 'Buy Limit' : 'Buy Stop') : 'Sell Limit';
    const newOrd: PendingOrder = {
      id: `ord-${ticket}`,
      ticket,
      symbol,
      kind: pendingKind,
      lots,
      orderPrice: price ?? 1.08,
      currentPrice: 1.085,
      stopLoss: stopLoss ?? 0,
      takeProfit: takeProfit ?? 0,
      expiration: 'GTC',
      magicNumber: 99999,
      comment: comment || 'Manual Pending',
    };
    set({ pendingOrders: [newOrd, ...get().pendingOrders] });
    get().addLog('SUCCESS', 'ManualExecution', `Pending ${pendingKind} order #${ticket} placed for ${lots} ${symbol} @ ${price}`);
    return { success: true, message: `Pending order #${ticket} placed` };
  },

  modifyPosition: (ticket: number, stopLoss: number, takeProfit: number) => {
    set({
      positions: get().positions.map(p =>
        p.ticket === ticket ? { ...p, stopLoss, takeProfit } : p
      ),
    });
    get().addLog('INFO', 'Router', `Modified position #${ticket} SL=${stopLoss} TP=${takeProfit}`);
  },

  addLog: (level, source, message) => {
    const entry: ExecutionLogEntry = {
      id: `log-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      timestamp: new Date().toISOString().replace('T', ' ').slice(0, 19),
      level,
      source,
      message,
    };
    set({ logs: [entry, ...get().logs.slice(0, 99)] });
  },
}));
