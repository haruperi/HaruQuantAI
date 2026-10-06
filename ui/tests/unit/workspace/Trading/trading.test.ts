import { describe, expect, it, beforeEach } from 'vitest';
import { useTradingStore } from '../../../../app/workspace/Trading/tradingStore';

describe('Live Trading Workspace Store (FEAT-UI-TRADING)', () => {
  beforeEach(() => {
    // Reset store state by re-initializing positions and pending orders if modified
    const store = useTradingStore.getState();
    if (store.tradingPaused) {
      store.toggleTrading();
    }
  });

  it('initializes with multi-broker accounts, default positions, and active status', () => {
    const state = useTradingStore.getState();
    expect(state.accounts.length).toBeGreaterThanOrEqual(3);
    expect(state.selectedAccountId).toBe('mt5-demo');
    expect(state.positions.length).toBeGreaterThanOrEqual(1);
    expect(state.tradingPaused).toBe(false);

    const activeAcc = state.accounts.find((a) => a.id === state.selectedAccountId);
    expect(activeAcc).toBeDefined();
    expect(activeAcc?.equity).toBeGreaterThan(0);
    expect(activeAcc?.balance).toBeGreaterThan(0);
  });

  it('submits a new market order, adding to positions and execution log', () => {
    const store = useTradingStore.getState();
    const initialPosCount = store.positions.length;
    const initialLogCount = store.logs.length;

    const result = store.submitOrder({
      symbol: 'GBPUSD',
      side: 'Buy',
      kind: 'Market',
      lots: 0.5,
      price: 1.2750,
      stopLoss: 1.2700,
      takeProfit: 1.2850,
      comment: 'Test Market Order',
    });

    expect(result.success).toBe(true);

    const state = useTradingStore.getState();
    expect(state.positions.length).toBe(initialPosCount + 1);
    expect(state.logs.length).toBe(initialLogCount + 1);

    const newPos = state.positions.find((p) => p.symbol === 'GBPUSD');
    expect(newPos).toBeDefined();
    expect(newPos?.side).toBe('Buy');
    expect(newPos?.lots).toBe(0.5);
  });

  it('submits a pending limit order, adding to pending orders list', () => {
    const store = useTradingStore.getState();
    const initialPendingCount = store.pendingOrders.length;

    const result = store.submitOrder({
      symbol: 'EURUSD',
      side: 'Buy',
      kind: 'Limit',
      lots: 1.0,
      price: 1.0750,
      stopLoss: 1.0700,
      takeProfit: 1.0900,
      comment: 'Test Limit Order',
    });

    expect(result.success).toBe(true);

    const state = useTradingStore.getState();
    expect(state.pendingOrders.length).toBe(initialPendingCount + 1);
    const newPending = state.pendingOrders.find((o) => o.symbol === 'EURUSD' && o.orderPrice === 1.0750);
    expect(newPending).toBeDefined();
    expect(newPending?.kind).toBe('Buy Limit');
  });

  it('cancels an active pending order', () => {
    const store = useTradingStore.getState();
    store.submitOrder({
      symbol: 'XAUUSD',
      side: 'Sell',
      kind: 'Stop',
      lots: 0.2,
      price: 2600,
    });

    const pending = useTradingStore.getState().pendingOrders.find((o) => o.symbol === 'XAUUSD');
    expect(pending).toBeDefined();

    if (pending) {
      store.cancelOrder(pending.ticket);
      const afterCancel = useTradingStore.getState().pendingOrders.find((o) => o.ticket === pending.ticket);
      expect(afterCancel).toBeUndefined();
    }
  });

  it('modifies an existing open position Stop Loss and Take Profit', () => {
    const store = useTradingStore.getState();
    const pos = store.positions[0];
    expect(pos).toBeDefined();

    store.modifyPosition(pos.ticket, 1.0750, 1.0990);
    const updated = useTradingStore.getState().positions.find((p) => p.ticket === pos.ticket);
    expect(updated?.stopLoss).toBe(1.0750);
    expect(updated?.takeProfit).toBe(1.0990);
  });

  it('closes an individual position and updates positions list', () => {
    const store = useTradingStore.getState();
    const posToClose = store.positions[0];
    const initialCount = store.positions.length;

    store.closePosition(posToClose.ticket);
    const state = useTradingStore.getState();
    expect(state.positions.length).toBe(initialCount - 1);
    expect(state.positions.some((p) => p.ticket === posToClose.ticket)).toBe(false);
  });

  it('activates emergency kill switch: liquidates all open positions and cancels all orders', () => {
    const store = useTradingStore.getState();
    expect(store.positions.length).toBeGreaterThan(0);

    store.executeEmergencyKillSwitch();
    const state = useTradingStore.getState();

    expect(state.positions.length).toBe(0);
    expect(state.pendingOrders.length).toBe(0);
    expect(state.tradingPaused).toBe(true);

    // Latest log entry should record emergency kill switch liquidation
    const latestLog = state.logs[0];
    expect(latestLog.source).toBe('KILL_SWITCH');
    expect(latestLog.message).toContain('EMERGENCY KILL SWITCH ACTIVATED');
  });
});
