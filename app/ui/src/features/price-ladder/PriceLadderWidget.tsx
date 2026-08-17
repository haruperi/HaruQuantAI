'use client';

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ChevronDown, ChevronUp, Settings, Target, X, Plus, Minus } from 'lucide-react';

import {
  apiClients,
  listPositions,
  listWorkingOrders,
  type Position,
  type WorkingOrder,
} from '../../clients';
import { buildGovernedOptions, GovernedPreflightError } from '../../context';
import { useWorkspaceStore, type SelectableAccountMode } from '../workspaces';
import type { OrderSide } from '../../types/market';
import { useDepthStream } from './useDepthStream';

/** The registered Discretionary Manual Order strategy identity (Risk-side constant). */
const STRATEGY_ID = 'discretionary-manual-order';

/**
 * The registered strategy version for one execution route.
 *
 * Strategy registers the discretionary manual-order strategy per environment,
 * so the version name follows the route exactly rather than being guessed.
 */
function strategyVersionFor(route: SelectableAccountMode): string {
  return `1.0.0-${route}`;
}

function newId(prefix: string): string {
  const suffix =
    typeof globalThis.crypto?.randomUUID === 'function'
      ? globalThis.crypto.randomUUID()
      : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
  return `${prefix}-${suffix}`;
}

type OrderTypeChoice = 'MARKET' | 'LIMIT';

interface LadderRow {
  readonly price: number;
  readonly bidVolume: number | null;
  readonly askVolume: number | null;
}

/** Build the real union price ladder from one book's real bid/ask levels. */
function buildRows(
  bids: readonly { price: number; volume: number }[],
  asks: readonly { price: number; volume: number }[]
): LadderRow[] {
  const byPrice = new Map<number, LadderRow>();
  for (const level of bids) {
    byPrice.set(level.price, { price: level.price, bidVolume: level.volume, askVolume: null });
  }
  for (const level of asks) {
    const existing = byPrice.get(level.price);
    byPrice.set(level.price, {
      price: level.price,
      bidVolume: existing?.bidVolume ?? null,
      askVolume: level.volume,
    });
  }
  return Array.from(byPrice.values()).sort((a, b) => b.price - a.price);
}

function maxVolume(rows: readonly LadderRow[]): number {
  let max = 1;
  for (const row of rows) {
    if (row.bidVolume !== null) max = Math.max(max, row.bidVolume);
    if (row.askVolume !== null) max = Math.max(max, row.askVolume);
  }
  return max;
}

interface Props {
  /** Real broker-native instrument symbol. */
  symbol?: string;
  /**
   * Real Trading account identifier this ladder trades and reads orders for.
   * Depth still renders without one; every order/cancel action stays
   * disabled until a real account is configured for this widget.
   */
  accountId?: string;
  /**
   * Real execution route. Omitted, it follows the app-wide account mode, which
   * is the only correct default: submitting on any other route is refused by
   * the boundary, and a ladder that silently traded a different route than the
   * shell displays would be actively misleading.
   */
  route?: SelectableAccountMode;
  /** Optional bound portfolio scope. */
  portfolioId?: string | null;
  /** Hands off a price-activated ticket to the host; this widget owns no ticket UI. */
  onOpenTicket?: (params: { symbol: string; side: OrderSide; price: number }) => void;
}

export const PriceLadderWidget: React.FC<Props> = ({
  symbol = 'EURUSD',
  accountId,
  route: routeOverride,
  portfolioId = null,
  onOpenTicket,
}) => {
  const { orderConfirmationRequired, accountMode } = useWorkspaceStore();
  // An unresolved mode leaves no route to trade on; order entry is already
  // disabled in that state (FR-UI-021), so the ladder never invents one.
  const route: SelectableAccountMode | null =
    routeOverride ?? (accountMode === 'unknown' ? null : accountMode);
  const hasAccount = Boolean(accountId);

  const [orderQty, setOrderQty] = useState(1);
  const [orderType, setOrderType] = useState<OrderTypeChoice>('MARKET');
  const [tif, setTif] = useState<'DAY' | 'GTC'>('DAY');
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [confirmingCancelAll, setConfirmingCancelAll] = useState(false);
  const [confirmingFlatten, setConfirmingFlatten] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const { book, status: depthStatus, error: depthError } = useDepthStream(symbol);
  const rows = useMemo(
    () => (book ? buildRows(book.bids, book.asks) : []),
    [book]
  );
  const bestBid = useMemo(
    () => rows.reduce<number | null>((acc, r) => (r.bidVolume !== null ? Math.max(acc ?? -Infinity, r.price) : acc), null),
    [rows]
  );
  const bestAsk = useMemo(
    () => rows.reduce<number | null>((acc, r) => (r.askVolume !== null ? Math.min(acc ?? Infinity, r.price) : acc), null),
    [rows]
  );
  const peakVolume = useMemo(() => maxVolume(rows), [rows]);

  const [workingOrders, setWorkingOrders] = useState<WorkingOrder[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const refreshOrders = useCallback(async () => {
    if (!accountId || route === null) return;
    try {
      const response = await apiClients.trading.session({
        query: { authority_id: accountId, route },
      });
      if (response.status === 'success') {
        setWorkingOrders(listWorkingOrders(response.data).filter((o) => o.intent.symbol === symbol));
        setPositions(listPositions(response.data).filter((p) => p.symbol === symbol));
      }
    } catch {
      // A refresh failure leaves the last known real orders in place rather
      // than clearing them to an invented empty state.
    }
  }, [accountId, route, symbol]);

  useEffect(() => {
    void refreshOrders();
    const timer = setInterval(() => void refreshOrders(), 5000);
    return () => clearInterval(timer);
  }, [refreshOrders]);

  /**
   * Signed net open quantity for this symbol. Longs count positive and shorts
   * negative, so a hedged book nets to the exposure actually carried.
   */
  const netPosition = useMemo(
    () =>
      positions.reduce((total, position) => {
        const quantity = Number(position.quantity);
        if (!Number.isFinite(quantity)) return total;
        if (position.side === 'LONG') return total + quantity;
        if (position.side === 'SHORT') return total - quantity;
        return total;
      }, 0),
    [positions]
  );

  const [stats, setStats] = useState<{
    last: number | null;
    volume: number | null;
    change: number | null;
    changePercent: number | null;
  } | null>(null);
  useEffect(() => {
    let cancelled = false;
    const load = async (): Promise<void> => {
      try {
        const response = await apiClients.data.quotes([symbol]);
        if (cancelled || response.status !== 'success') return;
        const row = response.data.rows.find((entry) => entry.symbol === symbol);
        // An absent row leaves the previous real values in place; the stats
        // strip renders an em dash rather than inventing a price.
        if (!row) return;
        setStats({
          last: row.last,
          volume: row.volume,
          change: row.change,
          changePercent: row.change_percent,
        });
      } catch {
        // Quote enrichment is supplementary; depth remains the widget's
        // authoritative feed and must never be blocked by it.
      }
    };
    void load();
    const timer = setInterval(() => void load(), 5000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [symbol]);

  const ordersByPrice = useMemo(() => {
    const map = new Map<number, WorkingOrder[]>();
    for (const order of workingOrders) {
      const price = order.intent.price !== null && order.intent.price !== undefined
        ? Number(order.intent.price)
        : null;
      if (price === null) continue;
      const existing = map.get(price) ?? [];
      existing.push(order);
      map.set(price, existing);
    }
    return map;
  }, [workingOrders]);

  const centerRef = useRef<HTMLTableRowElement | null>(null);
  const recenter = useCallback(() => {
    centerRef.current?.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }, []);
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent): void => {
      if (event.code === 'Space' && !(event.target instanceof HTMLInputElement)) {
        event.preventDefault();
        recenter();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [recenter]);

  const submitQuickOrder = useCallback(
    async (side: OrderSide, price: number | null) => {
      if (price === null && orderType === 'LIMIT') return;
      const resolvedPrice = price ?? bestBid ?? bestAsk;
      if (resolvedPrice === null) {
        setActionError('No real price is available yet.');
        return;
      }
      if (orderConfirmationRequired && onOpenTicket) {
        onOpenTicket({ symbol, side, price: resolvedPrice });
        return;
      }
      if (!accountId) {
        setActionError('No Trading account is configured for this widget.');
        return;
      }
      setBusy(true);
      setActionError(null);
      if (route === null) {
        setActionError('Account mode is not resolved');
        return;
      }
      try {
        const requestId = newId('req');
        const workflowId = newId('wf');
        const correlationId = newId('cor');
        const idempotencyKey = newId('idem');
        const preflight = await apiClients.trading.preflightOrder({
          request_id: requestId,
          workflow_id: workflowId,
          correlation_id: correlationId,
          route,
          account_id: accountId,
          portfolio_id: portfolioId,
          symbol,
          side,
          order_type: orderType,
          quantity: orderQty,
          current_price: resolvedPrice,
          idempotency_key: idempotencyKey,
        });
        if (preflight.status === 'error') {
          setActionError(preflight.error.message);
          return;
        }
        const decision = preflight.data;
        if (
          decision.state !== 'approve' ||
          decision.action_policy_verdict_id === null ||
          decision.approval_token_ref === null
        ) {
          setActionError(`Order not approved: ${decision.state} (${decision.reasons.join(', ') || 'no reason given'})`);
          return;
        }
        const now = new Date();
        const governed = buildGovernedOptions({
          workflow: workflowId,
          permission: 'trading:write',
          actorId: accountId,
          evidenceId: decision.risk_decision_id,
          idempotencyKey,
          routeId: route,
        });
        const submission = await apiClients.trading.submitOrder(
          {
            request_id: requestId,
            workflow_id: workflowId,
            correlation_id: correlationId,
            route,
            action: 'submit_order',
            account_id: accountId,
            portfolio_id: portfolioId,
            strategy_id: STRATEGY_ID,
            strategy_version: strategyVersionFor(route),
            intent_id: newId('intent'),
            symbol,
            side,
            order_type: orderType,
            quantity_unit: 'units',
            quantity: orderQty,
            price: orderType === 'LIMIT' ? resolvedPrice : undefined,
            time_in_force: tif,
            risk_decision_id: decision.risk_decision_id,
            action_policy_verdict_id: decision.action_policy_verdict_id,
            approval_token_ref: decision.approval_token_ref,
            idempotency_key: idempotencyKey,
            canonical_material_version: 'v1',
            system_time: now.toISOString(),
            valid_until: new Date(now.getTime() + 5 * 60_000).toISOString(),
          },
          governed.options
        );
        if (submission.status === 'error') {
          setActionError(submission.error.message);
          return;
        }
        await refreshOrders();
      } catch (cause) {
        setActionError(
          cause instanceof GovernedPreflightError ? cause.message : 'Order submission failed.'
        );
      } finally {
        setBusy(false);
      }
    },
    [accountId, bestAsk, bestBid, onOpenTicket, orderConfirmationRequired, orderQty, orderType, portfolioId, refreshOrders, route, symbol, tif]
  );

  const cancelWorkingOrder = useCallback(
    async (order: WorkingOrder) => {
      if (!order.broker_order_id || !accountId) return;
      setBusy(true);
      setActionError(null);
      try {
        if (route === null) {
          setActionError('Account mode is not resolved');
          return;
        }
        const requestId = newId('req');
        const workflowId = newId('wf');
        const correlationId = newId('cor');
        const idempotencyKey = newId('idem');
        const preflight = await apiClients.trading.preflightCancelOrder(order.broker_order_id, {
          request_id: requestId,
          workflow_id: workflowId,
          correlation_id: correlationId,
          route,
          account_id: accountId,
          portfolio_id: portfolioId,
          representative_symbol: order.intent.symbol,
          target_broker_order_id: order.broker_order_id,
          idempotency_key: idempotencyKey,
        });
        if (preflight.status === 'error') {
          setActionError(preflight.error.message);
          return;
        }
        const decision = preflight.data;
        if (
          decision.state !== 'approve' ||
          decision.action_policy_verdict_id === null ||
          decision.approval_token_ref === null
        ) {
          setActionError(`Cancellation not approved: ${decision.state}`);
          return;
        }
        const now = new Date();
        const governed = buildGovernedOptions({
          workflow: workflowId,
          permission: 'trading:write',
          actorId: accountId,
          evidenceId: decision.risk_decision_id,
          idempotencyKey,
          routeId: route,
        });
        const cancellation = await apiClients.trading.cancelOrder(
          order.broker_order_id,
          {
            request_id: requestId,
            workflow_id: workflowId,
            correlation_id: correlationId,
            route,
            action: 'cancel_order',
            account_id: accountId,
            portfolio_id: portfolioId,
            strategy_id: STRATEGY_ID,
            strategy_version: strategyVersionFor(route),
            intent_id: newId('intent'),
            order_type: order.intent.order_type,
            quantity_unit: 'units',
            target_broker_order_id: order.broker_order_id,
            order_id: order.broker_order_id,
            risk_decision_id: decision.risk_decision_id,
            action_policy_verdict_id: decision.action_policy_verdict_id,
            approval_token_ref: decision.approval_token_ref,
            idempotency_key: idempotencyKey,
            canonical_material_version: 'v1',
            system_time: now.toISOString(),
            valid_until: new Date(now.getTime() + 5 * 60_000).toISOString(),
          },
          governed.options
        );
        if (cancellation.status === 'error') {
          setActionError(cancellation.error.message);
          return;
        }
        await refreshOrders();
      } catch (cause) {
        setActionError(
          cause instanceof GovernedPreflightError ? cause.message : 'Cancellation failed.'
        );
      } finally {
        setBusy(false);
      }
    },
    [accountId, portfolioId, refreshOrders, route]
  );

  const cancelAllOrders = useCallback(async () => {
    if (!accountId) {
      setActionError('No Trading account is configured for this widget.');
      return;
    }
    setBusy(true);
    setActionError(null);
    try {
      if (route === null) {
        setActionError('Account mode is not resolved');
        return;
      }
      const requestId = newId('req');
      const workflowId = newId('wf');
      const correlationId = newId('cor');
      const idempotencyKey = newId('idem');
      const preflight = await apiClients.trading.preflightCancelAllOrders({
        request_id: requestId,
        workflow_id: workflowId,
        correlation_id: correlationId,
        route,
        account_id: accountId,
        portfolio_id: portfolioId,
        representative_symbol: symbol,
        idempotency_key: idempotencyKey,
      });
      if (preflight.status === 'error') {
        setActionError(preflight.error.message);
        return;
      }
      const decision = preflight.data;
      if (
        decision.state !== 'approve' ||
        decision.action_policy_verdict_id === null ||
        decision.approval_token_ref === null
      ) {
        setActionError(`Bulk cancellation not approved: ${decision.state}`);
        return;
      }
      const now = new Date();
      const governed = buildGovernedOptions({
        workflow: workflowId,
        permission: 'trading:write',
        actorId: accountId,
        evidenceId: decision.risk_decision_id,
        idempotencyKey,
        routeId: route,
      });
      const bulk = await apiClients.trading.cancelAllOrders(
        {
          request_id: requestId,
          workflow_id: workflowId,
          correlation_id: correlationId,
          route,
          action: 'cancel_all_orders',
          account_id: accountId,
          portfolio_id: portfolioId,
          strategy_id: STRATEGY_ID,
          strategy_version: strategyVersionFor(route),
          intent_id: newId('intent'),
          order_type: 'MARKET',
          quantity_unit: 'units',
          risk_decision_id: decision.risk_decision_id,
          action_policy_verdict_id: decision.action_policy_verdict_id,
          approval_token_ref: decision.approval_token_ref,
          idempotency_key: idempotencyKey,
          canonical_material_version: 'v1',
          system_time: now.toISOString(),
          valid_until: new Date(now.getTime() + 5 * 60_000).toISOString(),
        },
        governed.options
      );
      if (bulk.status === 'error') {
        setActionError(bulk.error.message);
        return;
      }
      await refreshOrders();
    } catch (cause) {
      setActionError(
        cause instanceof GovernedPreflightError ? cause.message : 'Bulk cancellation failed.'
      );
    } finally {
      setBusy(false);
      setConfirmingCancelAll(false);
    }
  }, [accountId, portfolioId, refreshOrders, route, symbol]);

  /**
   * Close every open position on this symbol.
   *
   * Trading has no close-position preflight of its own, and a mutation cannot
   * be submitted without real approval evidence. A flatten is economically a
   * market order in the opposite direction, so it is reviewed as exactly that
   * — each position gets its own Risk decision for the exposure it unwinds,
   * and a rejected review stops that close rather than forcing it through.
   */
  const flattenPosition = useCallback(async () => {
    if (!accountId) {
      setActionError('No Trading account is configured for this widget.');
      return;
    }
    const closable = positions.filter((position) => position.broker_position_id);
    if (closable.length === 0) {
      setActionError('There is no open position to flatten.');
      return;
    }
    if (route === null) {
      setActionError('Account mode is not resolved');
      return;
    }
    setBusy(true);
    setActionError(null);
    try {
      for (const position of closable) {
        const quantity = Number(position.quantity);
        const closingSide: OrderSide = position.side === 'LONG' ? 'SELL' : 'BUY';
        const resolvedPrice = closingSide === 'SELL' ? bestBid ?? bestAsk : bestAsk ?? bestBid;
        if (resolvedPrice === null) {
          setActionError('No real price is available to value the flatten.');
          return;
        }
        const requestId = newId('req');
        const workflowId = newId('wf');
        const correlationId = newId('cor');
        const idempotencyKey = newId('idem');
        const preflight = await apiClients.trading.preflightOrder({
          request_id: requestId,
          workflow_id: workflowId,
          correlation_id: correlationId,
          route,
          account_id: accountId,
          portfolio_id: portfolioId,
          symbol,
          side: closingSide,
          order_type: 'MARKET',
          quantity,
          current_price: resolvedPrice,
          idempotency_key: idempotencyKey,
        });
        if (preflight.status === 'error') {
          setActionError(preflight.error.message);
          return;
        }
        const decision = preflight.data;
        if (
          decision.state !== 'approve' ||
          decision.action_policy_verdict_id === null ||
          decision.approval_token_ref === null
        ) {
          setActionError(
            `Flatten not approved: ${decision.state} (${decision.reasons.join(', ') || 'no reason given'})`
          );
          return;
        }
        const now = new Date();
        const governed = buildGovernedOptions({
          workflow: workflowId,
          permission: 'trading:write',
          actorId: accountId,
          evidenceId: decision.risk_decision_id,
          idempotencyKey,
          routeId: route,
        });
        const closure = await apiClients.trading.closePosition(
          position.broker_position_id,
          {
            request_id: requestId,
            workflow_id: workflowId,
            correlation_id: correlationId,
            route,
            action: 'close_position',
            account_id: accountId,
            portfolio_id: portfolioId,
            strategy_id: STRATEGY_ID,
            strategy_version: strategyVersionFor(route),
            intent_id: newId('intent'),
            symbol,
            side: closingSide,
            order_type: 'MARKET',
            quantity_unit: 'units',
            quantity,
            target_broker_position_id: position.broker_position_id,
            position_id: position.position_id,
            risk_decision_id: decision.risk_decision_id,
            action_policy_verdict_id: decision.action_policy_verdict_id,
            approval_token_ref: decision.approval_token_ref,
            idempotency_key: idempotencyKey,
            canonical_material_version: 'v1',
            system_time: now.toISOString(),
            valid_until: new Date(now.getTime() + 5 * 60_000).toISOString(),
          },
          governed.options
        );
        if (closure.status === 'error') {
          setActionError(closure.error.message);
          return;
        }
      }
      await refreshOrders();
    } catch (cause) {
      setActionError(
        cause instanceof GovernedPreflightError ? cause.message : 'Flatten failed.'
      );
    } finally {
      setBusy(false);
      setConfirmingFlatten(false);
    }
  }, [accountId, bestAsk, bestBid, portfolioId, positions, refreshOrders, route, symbol]);

  /** Cancel every working order resting on one side of the ladder. */
  const cancelSide = useCallback(
    async (side: OrderSide) => {
      for (const order of workingOrders.filter((entry) => entry.intent.side === side)) {
        await cancelWorkingOrder(order);
      }
    },
    [cancelWorkingOrder, workingOrders]
  );

  const scrollRef = useRef<HTMLDivElement | null>(null);
  const scrollLadder = useCallback((direction: -1 | 1) => {
    scrollRef.current?.scrollBy({ top: direction * 120, behavior: 'smooth' });
  }, []);

  /** Render one side's resting working orders as cancellable qty chips. */
  const renderOrderChips = (orders: readonly WorkingOrder[]): React.ReactNode =>
    orders.map((order) => (
      <span key={order.request_id} className="ladder-order-chip">
        {String(order.intent.approved_volume)}
        <button
          type="button"
          disabled={busy || !order.broker_order_id}
          onClick={() => void cancelWorkingOrder(order)}
          title={order.broker_order_id ? 'Cancel this order' : 'Awaiting broker acknowledgement'}
          style={{
            border: 'none',
            background: 'transparent',
            cursor: order.broker_order_id ? 'pointer' : 'default',
            padding: 0,
          }}
        >
          <X size={9} color="var(--cme-sell-red)" />
        </button>
      </span>
    ));

  const handleCellClick = (side: OrderSide, price: number): void => {
    if (onOpenTicket) {
      onOpenTicket({ symbol, side, price });
      return;
    }
    void submitQuickOrder(side, orderType === 'LIMIT' ? price : null);
  };

  return (
    <div className="price-ladder-container">
      <div className="ladder-titlebar">
        <span className="ladder-symbol-chip">{symbol}</span>
        <span className="ladder-position-readout">
          Position <b>{netPosition > 0 ? `+${netPosition}` : netPosition}</b>
        </span>
        <span className="ladder-status-text">
          {hasAccount ? '' : 'NO ACCOUNT — '}
          {depthStatus === 'connected' ? 'LIVE' : depthStatus.toUpperCase()}
        </span>
        <button
          type="button"
          className="ladder-gear"
          aria-label="Price Ladder settings"
          aria-expanded={settingsOpen}
          onClick={() => setSettingsOpen((open) => !open)}
        >
          <Settings size={13} />
        </button>
      </div>

      {settingsOpen && (
        <div className="ladder-settings-popover">
          <span className="ladder-settings-label">Order type</span>
          <div style={{ display: 'flex', gap: '4px' }}>
            <button
              className={`btn-cme btn-outline btn-sm ${orderType === 'MARKET' ? 'active' : ''}`}
              onClick={() => setOrderType('MARKET')}
              style={{ flex: 1 }}
            >
              MARKET
            </button>
            <button
              className={`btn-cme btn-outline btn-sm ${orderType === 'LIMIT' ? 'active' : ''}`}
              onClick={() => setOrderType('LIMIT')}
              style={{ flex: 1 }}
            >
              LIMIT
            </button>
          </div>
        </div>
      )}

      <div className="ladder-header-controls">
        <div className="ladder-action-row">
          <div className="ladder-tif-group">
            <button
              className={`btn-cme btn-outline btn-sm ${tif === 'DAY' ? 'active' : ''}`}
              onClick={() => setTif('DAY')}
            >
              DAY
            </button>
            <button
              className={`btn-cme btn-outline btn-sm ${tif === 'GTC' ? 'active' : ''}`}
              onClick={() => setTif('GTC')}
            >
              GTC
            </button>
          </div>
          <button
            className="btn-cme btn-outline btn-sm ladder-flatten"
            disabled={busy || !hasAccount || positions.length === 0}
            onClick={() => setConfirmingFlatten(true)}
            title={
              positions.length === 0
                ? 'No open position on this symbol'
                : 'Close every open position on this symbol'
            }
          >
            FLATTEN
          </button>
          <button
            className="btn-cme btn-outline btn-sm"
            disabled={busy || workingOrders.length === 0}
            onClick={() => setConfirmingCancelAll(true)}
            title="Cancel All Working Orders"
          >
            CANCEL ALL
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <button
            className="btn-cme btn-buy btn-sm"
            disabled={busy || (!hasAccount && !onOpenTicket)}
            onClick={() => void submitQuickOrder('BUY', null)}
            style={{ flex: 1 }}
          >
            BUY {orderType === 'MARKET' ? 'MKT' : 'LMT'}
          </button>

          <div style={{ display: 'flex', alignItems: 'center', background: 'var(--cme-navy-darkest)', border: '1px solid var(--cme-navy-border)', borderRadius: 'var(--radius-sm)' }}>
            <button className="btn-cme btn-outline btn-sm" onClick={() => setOrderQty(Math.max(1, orderQty - 1))} style={{ border: 'none' }}>
              <Minus size={10} />
            </button>
            <span style={{ fontFamily: 'var(--font-mono)', padding: '0 8px', fontWeight: 700 }}>{orderQty}</span>
            <button className="btn-cme btn-outline btn-sm" onClick={() => setOrderQty(orderQty + 1)} style={{ border: 'none' }}>
              <Plus size={10} />
            </button>
          </div>

          <button
            className="btn-cme btn-sell btn-sm"
            disabled={busy || (!hasAccount && !onOpenTicket)}
            onClick={() => void submitQuickOrder('SELL', null)}
            style={{ flex: 1 }}
          >
            SELL {orderType === 'MARKET' ? 'MKT' : 'LMT'}
          </button>
        </div>

        <div className="ladder-stats-strip">
          <div className="ladder-stat">
            <span className="ladder-stat-label">BID</span>
            <span className="ladder-stat-value bid">
              {bestBid !== null ? bestBid.toFixed(5) : '—'}
            </span>
          </div>
          <div className="ladder-stat">
            <span className="ladder-stat-label">ASK</span>
            <span className="ladder-stat-value ask">
              {bestAsk !== null ? bestAsk.toFixed(5) : '—'}
            </span>
          </div>
          <div className="ladder-stat">
            <span className="ladder-stat-label">LAST</span>
            <span className="ladder-stat-value">
              {stats?.last != null ? stats.last.toFixed(5) : '—'}
            </span>
          </div>
          <div className="ladder-stat">
            <span className="ladder-stat-label">VOLUME</span>
            <span className="ladder-stat-value">
              {stats?.volume != null ? stats.volume.toLocaleString() : '—'}
            </span>
          </div>
          <div className="ladder-stat">
            <span className="ladder-stat-label">CHANGE</span>
            <span
              className={`ladder-stat-value ${
                stats?.change == null ? '' : stats.change >= 0 ? 'up' : 'down'
              }`}
            >
              {stats?.change != null
                ? `${stats.change >= 0 ? '+' : ''}${stats.change.toFixed(2)}`
                : '—'}
            </span>
          </div>
        </div>

        {(depthError ?? actionError) && (
          <div style={{ fontSize: '11px', color: 'var(--cme-sell-red)' }}>{depthError ?? actionError}</div>
        )}
      </div>

      <div style={{ flex: 1, overflowY: 'auto' }} ref={scrollRef}>
        <table className="ladder-table">
          <thead>
            <tr>
              <th style={{ width: '18%' }}>QTY</th>
              <th style={{ width: '27%' }}>BUY</th>
              <th style={{ width: '28%' }}>PRICE</th>
              <th style={{ width: '27%' }}>SELL</th>
              <th style={{ width: '18%' }}>QTY</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '16px', color: 'var(--text-muted)' }}>
                  {depthStatus === 'connecting' ? 'Connecting to real depth feed…' : 'No real depth available.'}
                </td>
              </tr>
            )}
            {rows.map((row) => {
              const isBestBid = row.price === bestBid;
              const isBestAsk = row.price === bestAsk;
              const orders = ordersByPrice.get(row.price) ?? [];
              return (
                <tr key={row.price} ref={isBestBid || isBestAsk ? centerRef : undefined}>
                  <td className="ladder-cell ladder-order-cell">
                    {renderOrderChips(orders.filter((order) => order.intent.side === 'BUY'))}
                  </td>

                  <td className="ladder-cell bid-depth-cell" onClick={() => handleCellClick('BUY', row.price)}>
                    {row.bidVolume !== null && (
                      <>
                        <div className="depth-bar-bid" style={{ width: `${Math.min(100, (row.bidVolume / peakVolume) * 100)}%` }} />
                        <span className="cell-content">{row.bidVolume}</span>
                      </>
                    )}
                  </td>

                  <td className={`ladder-cell ladder-price-cell ${isBestBid || isBestAsk ? 'last-price' : ''}`}>
                    {row.price.toFixed(5)}
                  </td>

                  <td className="ladder-cell ask-depth-cell" onClick={() => handleCellClick('SELL', row.price)}>
                    {row.askVolume !== null && (
                      <>
                        <div className="depth-bar-ask" style={{ width: `${Math.min(100, (row.askVolume / peakVolume) * 100)}%` }} />
                        <span className="cell-content">{row.askVolume}</span>
                      </>
                    )}
                  </td>

                  <td className="ladder-cell ladder-order-cell">
                    {renderOrderChips(orders.filter((order) => order.intent.side === 'SELL'))}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="ladder-footer-bar">
        <button
          type="button"
          className="ladder-footer-btn"
          aria-label="Cancel all resting buy orders"
          title="Cancel all resting buy orders"
          disabled={busy || workingOrders.every((order) => order.intent.side !== 'BUY')}
          onClick={() => void cancelSide('BUY')}
        >
          <X size={13} color="var(--cme-sell-red)" />
        </button>
        <button
          type="button"
          className="ladder-footer-btn"
          aria-label="Scroll ladder up"
          title="Scroll ladder up"
          onClick={() => scrollLadder(-1)}
        >
          <ChevronUp size={14} />
        </button>
        <button
          type="button"
          className="ladder-footer-btn"
          aria-label="Re-center price ladder"
          title="Re-Center Price Ladder (Spacebar)"
          onClick={recenter}
        >
          <Target size={14} color="var(--cme-blue-cyan)" />
        </button>
        <button
          type="button"
          className="ladder-footer-btn"
          aria-label="Scroll ladder down"
          title="Scroll ladder down"
          onClick={() => scrollLadder(1)}
        >
          <ChevronDown size={14} />
        </button>
        <button
          type="button"
          className="ladder-footer-btn"
          aria-label="Cancel all resting sell orders"
          title="Cancel all resting sell orders"
          disabled={busy || workingOrders.every((order) => order.intent.side !== 'SELL')}
          onClick={() => void cancelSide('SELL')}
        >
          <X size={13} color="var(--cme-sell-red)" />
        </button>
      </div>

      {confirmingFlatten && (
        <div role="alertdialog" aria-modal="true" style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 10 }}>
          <div style={{ background: 'var(--cme-navy-dark)', border: '1px solid var(--cme-navy-border)', borderRadius: 'var(--radius-sm)', padding: '16px', minWidth: '260px' }}>
            <p style={{ marginTop: 0 }}>
              Flatten {positions.length} open {symbol} position(s)?
            </p>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Each close is reviewed by Risk as an opposing market order and can be
              rejected. This always requires confirmation, regardless of the workspace
              confirmation setting.
            </p>
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
              <button className="btn-cme btn-outline btn-sm" onClick={() => setConfirmingFlatten(false)}>
                Keep Position
              </button>
              <button className="btn-cme btn-sell btn-sm" disabled={busy} onClick={() => void flattenPosition()}>
                Confirm Flatten
              </button>
            </div>
          </div>
        </div>
      )}

      {confirmingCancelAll && (
        <div role="alertdialog" aria-modal="true" style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 10 }}>
          <div style={{ background: 'var(--cme-navy-dark)', border: '1px solid var(--cme-navy-border)', borderRadius: 'var(--radius-sm)', padding: '16px', minWidth: '260px' }}>
            <p style={{ marginTop: 0 }}>Cancel all {workingOrders.length} working {symbol} order(s)?</p>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              This always requires confirmation, regardless of the workspace confirmation setting.
            </p>
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
              <button className="btn-cme btn-outline btn-sm" onClick={() => setConfirmingCancelAll(false)}>
                Keep Orders
              </button>
              <button className="btn-cme btn-sell btn-sm" disabled={busy} onClick={() => void cancelAllOrders()}>
                Confirm Cancel All
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
