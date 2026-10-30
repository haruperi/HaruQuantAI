import { describe, expect, it, beforeEach } from 'vitest';
import { useTradingStore } from '../../../workspaces/trading/tradingStore';

describe('tradingStore (Phase LT.5)', () => {
  beforeEach(() => {
    const store = useTradingStore.getState();
    if (store.tradingPaused) {
      store.toggleTrading();
    }
  });

  it('selects account and updates selectedAccountId', () => {
    const store = useTradingStore.getState();
    store.selectAccount('ctrader-live');
    expect(useTradingStore.getState().selectedAccountId).toBe('ctrader-live');

    store.selectAccount('binance-futures');
    expect(useTradingStore.getState().selectedAccountId).toBe('binance-futures');
  });

  it('toggles trading pause state', () => {
    const store = useTradingStore.getState();
    expect(store.tradingPaused).toBe(false);

    store.toggleTrading();
    expect(useTradingStore.getState().tradingPaused).toBe(true);

    store.toggleTrading();
    expect(useTradingStore.getState().tradingPaused).toBe(false);
  });

  it('closes a single position by ticket', () => {
    const store = useTradingStore.getState();
    store.submitOrder({
      symbol: 'USDJPY',
      side: 'Buy',
      kind: 'Market',
      lots: 0.1,
    });

    const pos = useTradingStore.getState().positions.find(p => p.symbol === 'USDJPY');
    expect(pos).toBeDefined();

    if (pos) {
      store.closePosition(pos.ticket);
      const after = useTradingStore.getState().positions.find(p => p.ticket === pos.ticket);
      expect(after).toBeUndefined();
    }
  });

  it('flattens all positions via closeAllPositions', () => {
    const store = useTradingStore.getState();
    store.closeAllPositions();
    expect(useTradingStore.getState().positions.length).toBe(0);
  });

  it('cancels all orders via cancelAllOrders', () => {
    const store = useTradingStore.getState();
    store.submitOrder({
      symbol: 'EURUSD',
      side: 'Sell',
      kind: 'Limit',
      lots: 0.1,
      price: 1.12,
    });
    expect(useTradingStore.getState().pendingOrders.length).toBeGreaterThan(0);

    store.cancelAllOrders();
    expect(useTradingStore.getState().pendingOrders.length).toBe(0);
  });

  it('executes emergency kill switch', () => {
    const store = useTradingStore.getState();
    store.executeEmergencyKillSwitch();

    const state = useTradingStore.getState();
    expect(state.tradingPaused).toBe(true);
    expect(state.positions.length).toBe(0);
    expect(state.pendingOrders.length).toBe(0);
    expect(state.logs.some(l => l.level === 'ERROR' && l.source === 'KILL_SWITCH')).toBe(true);
  });
});
