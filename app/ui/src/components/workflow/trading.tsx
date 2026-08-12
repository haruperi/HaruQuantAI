/** Trading session and explicitly governed mutation controls (FR-UI-015). */

"use client";

import { useEffect, useState, type ReactNode } from "react";

import { ApiClientError, apiClients } from "@/clients";
import type { TradingMutationInput, TradingProjection } from "@/clients";
import { buildGovernedOptions, GovernedPreflightError } from "@/context";

/** Props accepted by `TradingView`. */
export interface TradingViewProps {
  className?: string;
}

interface MutationDraft {
  route: "paper" | "live";
  accountId: string;
  strategyId: string;
  strategyVersion: string;
  intentId: string;
  symbol: string;
  side: "BUY" | "SELL";
  orderType: "MARKET" | "LIMIT" | "STOP" | "STOP_LIMIT";
  quantityUnit: string;
  quantity: string;
  riskDecisionId: string;
  actionPolicyVerdictId: string;
  approvalTokenRef: string;
  brokerOrderId: string;
  brokerPositionId: string;
}

const INITIAL_DRAFT: MutationDraft = {
  route: "paper",
  accountId: "",
  strategyId: "",
  strategyVersion: "",
  intentId: "",
  symbol: "",
  side: "BUY",
  orderType: "MARKET",
  quantityUnit: "units",
  quantity: "",
  riskDecisionId: "",
  actionPolicyVerdictId: "",
  approvalTokenRef: "",
  brokerOrderId: "",
  brokerPositionId: "",
};

/** Bounded JSON view of an opaque projection section. */
function renderSection(projection: TradingProjection, key: string): ReactNode {
  const value = projection[key];
  if (value === null || value === undefined) return <em>none</em>;
  if (Array.isArray(value)) {
    return value.length === 0 ? <em>empty</em> : <pre>{JSON.stringify(value, null, 2)}</pre>;
  }
  if (typeof value === "object") return <pre>{JSON.stringify(value, null, 2)}</pre>;
  return <span>{String(value)}</span>;
}

function newId(prefix: string): string {
  const suffix = typeof globalThis.crypto?.randomUUID === "function"
    ? globalThis.crypto.randomUUID()
    : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
  return `${prefix}-${suffix}`;
}

function hasCommonAuthority(draft: MutationDraft): boolean {
  return [
    draft.accountId,
    draft.strategyId,
    draft.strategyVersion,
    draft.intentId,
    draft.symbol,
    draft.quantityUnit,
    draft.quantity,
    draft.riskDecisionId,
    draft.actionPolicyVerdictId,
    draft.approvalTokenRef,
  ].every((value) => value.trim().length > 0) && Number(draft.quantity) > 0;
}

function buildMutation(
  draft: MutationDraft,
  action: "submit_order" | "cancel_order" | "close_position",
  idempotencyKey: string
): TradingMutationInput {
  const now = new Date();
  return {
    request_id: newId("req"),
    workflow_id: newId("wf"),
    correlation_id: newId("cor"),
    route: draft.route,
    action,
    account_id: draft.accountId,
    strategy_id: draft.strategyId,
    strategy_version: draft.strategyVersion,
    intent_id: draft.intentId,
    symbol: draft.symbol,
    side: draft.side,
    order_type: draft.orderType,
    quantity_unit: draft.quantityUnit,
    quantity: draft.quantity,
    target_broker_order_id: action === "cancel_order" ? draft.brokerOrderId : null,
    target_broker_position_id: action === "close_position" ? draft.brokerPositionId : null,
    order_id: action === "cancel_order" ? draft.brokerOrderId : null,
    position_id: action === "close_position" ? draft.brokerPositionId : null,
    risk_decision_id: draft.riskDecisionId,
    action_policy_verdict_id: draft.actionPolicyVerdictId,
    approval_token_ref: draft.approvalTokenRef,
    idempotency_key: idempotencyKey,
    canonical_material_version: "v1",
    system_time: now.toISOString(),
    valid_until: new Date(now.getTime() + 5 * 60_000).toISOString(),
  };
}

/** Trading session view with explicit, fail-closed governed actions. */
export function TradingView({ className }: TradingViewProps = {}): ReactNode {
  const [projection, setProjection] = useState<TradingProjection | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState<MutationDraft>(INITIAL_DRAFT);
  const [preflightReady, setPreflightReady] = useState(false);
  const [preflightError, setPreflightError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionResult, setActionResult] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load(): Promise<void> {
      try {
        const response = await apiClients.trading.session();
        if (!cancelled) {
          if (response.status === "error") setError(response.error.message);
          else setProjection(response.data);
        }
      } catch (cause) {
        if (!cancelled) setError(cause instanceof ApiClientError ? cause.message : "unavailable");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => { cancelled = true; };
  }, []);

  function update<K extends keyof MutationDraft>(key: K, value: MutationDraft[K]): void {
    setDraft((current) => ({ ...current, [key]: value }));
    setPreflightReady(false);
    setActionResult(null);
  }

  function armGovernedActions(): void {
    setActionError(null);
    if (!hasCommonAuthority(draft)) {
      setPreflightReady(false);
      setPreflightError("Complete all authority and order fields before arming.");
      return;
    }
    setPreflightReady(true);
    setPreflightError(null);
  }

  async function execute(action: "submit_order" | "cancel_order" | "close_position"): Promise<void> {
    setActionError(null);
    setActionResult(null);
    try {
      const idempotencyKey = newId("idem");
      const input = buildMutation(draft, action, idempotencyKey);
      const governed = buildGovernedOptions({
        workflow: input.workflow_id,
        permission: "trading:write",
        actorId: "operator",
        evidenceId: input.risk_decision_id,
        idempotencyKey,
        routeId: input.route,
      });
      const response = action === "submit_order"
        ? await apiClients.trading.submitOrder(input, governed.options)
        : action === "cancel_order"
          ? await apiClients.trading.cancelOrder(draft.brokerOrderId, input, governed.options)
          : await apiClients.trading.closePosition(draft.brokerPositionId, input, governed.options);
      if (response.status === "error") setActionError(response.error.message);
      else setActionResult(`${action} accepted by the API boundary.`);
    } catch (cause) {
      setActionError(
        cause instanceof ApiClientError || cause instanceof GovernedPreflightError
          ? cause.message
          : "unavailable"
      );
    } finally {
      setPreflightReady(false);
    }
  }

  const commonReady = hasCommonAuthority(draft);
  return (
    <div className={`workflow-trading ${className ?? ""}`.trim()} role="region" aria-label="Trading">
      {loading && <span>loading…</span>}
      {error && <span className="workflow-error">{error}</span>}
      {!loading && !error && projection && <>
        <div><h4>Account</h4>{renderSection(projection, "account")}</div>
        <div><h4>Positions</h4>{renderSection(projection, "positions")}</div>
        <div><h4>Orders</h4>{renderSection(projection, "orders")}</div>
      </>}

      <fieldset className="workflow-trading-actions">
        <legend>Governed Trading Actions</legend>
        <p>Paper is the safe default. Authority references must come from backend workflow results; this form never invents them.</p>
        <label>Route<select aria-label="Route" value={draft.route} onChange={(event) => update("route", event.target.value as MutationDraft["route"])}><option value="paper">paper</option><option value="live">live</option></select></label>
        <label>Account ID<input aria-label="Account ID" value={draft.accountId} onChange={(event) => update("accountId", event.target.value)} /></label>
        <label>Strategy ID<input aria-label="Strategy ID" value={draft.strategyId} onChange={(event) => update("strategyId", event.target.value)} /></label>
        <label>Strategy version<input aria-label="Strategy version" value={draft.strategyVersion} onChange={(event) => update("strategyVersion", event.target.value)} /></label>
        <label>Intent ID<input aria-label="Intent ID" value={draft.intentId} onChange={(event) => update("intentId", event.target.value)} /></label>
        <label>Symbol<input aria-label="Symbol" value={draft.symbol} onChange={(event) => update("symbol", event.target.value)} /></label>
        <label>Side<select aria-label="Side" value={draft.side} onChange={(event) => update("side", event.target.value as MutationDraft["side"])}><option value="BUY">BUY</option><option value="SELL">SELL</option></select></label>
        <label>Order type<select aria-label="Order type" value={draft.orderType} onChange={(event) => update("orderType", event.target.value as MutationDraft["orderType"])}><option>MARKET</option><option>LIMIT</option><option>STOP</option><option>STOP_LIMIT</option></select></label>
        <label>Quantity unit<input aria-label="Quantity unit" value={draft.quantityUnit} onChange={(event) => update("quantityUnit", event.target.value)} /></label>
        <label>Quantity<input aria-label="Quantity" type="number" min="0" value={draft.quantity} onChange={(event) => update("quantity", event.target.value)} /></label>
        <label>Risk decision ID<input aria-label="Risk decision ID" value={draft.riskDecisionId} onChange={(event) => update("riskDecisionId", event.target.value)} /></label>
        <label>Action-policy verdict ID<input aria-label="Action-policy verdict ID" value={draft.actionPolicyVerdictId} onChange={(event) => update("actionPolicyVerdictId", event.target.value)} /></label>
        <label>Approval token reference<input aria-label="Approval token reference" value={draft.approvalTokenRef} onChange={(event) => update("approvalTokenRef", event.target.value)} /></label>
        <label>Broker order ID (cancel)<input aria-label="Broker order ID" value={draft.brokerOrderId} onChange={(event) => update("brokerOrderId", event.target.value)} /></label>
        <label>Broker position ID (close)<input aria-label="Broker position ID" value={draft.brokerPositionId} onChange={(event) => update("brokerPositionId", event.target.value)} /></label>
        <button type="button" onClick={armGovernedActions} disabled={!commonReady}>{preflightReady ? "Re-arm preflight" : "Arm preflight"}</button>
        {preflightError && <span className="workflow-error">{preflightError}</span>}
        <button type="button" onClick={() => void execute("submit_order")} disabled={!preflightReady}>Submit Order</button>
        <button type="button" onClick={() => void execute("cancel_order")} disabled={!preflightReady || !draft.brokerOrderId.trim()}>Cancel Order</button>
        <button type="button" onClick={() => void execute("close_position")} disabled={!preflightReady || !draft.brokerPositionId.trim()}>Close Position</button>
        {actionError && <span className="workflow-error">{actionError}</span>}
        {actionResult && <span role="status">{actionResult}</span>}
      </fieldset>
    </div>
  );
}
