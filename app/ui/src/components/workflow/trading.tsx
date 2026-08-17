/** Trading session and explicitly governed mutation controls (FR-UI-015). */

"use client";

import { useEffect, useState, type ReactNode } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Crosshair,
  FileKey2,
  Layers3,
  ListChecks,
  LoaderCircle,
  Route,
  ShieldCheck,
  WalletCards,
  Zap,
} from "lucide-react";

import { ApiClientError, apiClients } from "@/clients";
import type { TradingMutationInput, TradingProjection } from "@/clients";
import { buildGovernedOptions, GovernedPreflightError } from "@/context";
import { selectTradingActivityDisabled, useWorkspaceStore } from "@/features/workspaces";

/** Props accepted by `TradingView`. */
export interface TradingViewProps {
  className?: string;
}

interface MutationDraft {
  route: "sim" | "demo" | "live";
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
  route: "demo",
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
  const tradingDisabled = useWorkspaceStore(selectTradingActivityDisabled);
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
    if (tradingDisabled) {
      setPreflightReady(false);
      setPreflightError("Trading disabled until selected and platform modes match.");
      return;
    }
    if (!hasCommonAuthority(draft)) {
      setPreflightReady(false);
      setPreflightError("Complete all authority and order fields before arming.");
      return;
    }
    setPreflightReady(true);
    setPreflightError(null);
  }

  async function execute(action: "submit_order" | "cancel_order" | "close_position"): Promise<void> {
    if (tradingDisabled) return;
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
    <section className={`workflow-trading ${className ?? ""}`.trim()} role="region" aria-label="Trading">
      <header className="workflow-trading__hero">
        <div>
          <span className="workflow-trading__eyebrow"><ShieldCheck size={14} /> Governed execution</span>
          <h2>Trading</h2>
          <p>Review account evidence, assemble an authorized order, and submit it through the governed execution boundary.</p>
        </div>
        <span className={`workflow-trading__route workflow-trading__route--${draft.route}`}><Route size={14} /> {draft.route.toUpperCase()} route</span>
      </header>

      {loading && <div className="workflow-trading__state" role="status"><LoaderCircle className="is-spinning" size={22} /><strong>Loading trading evidence</strong><span>Retrieving the current account, positions, and orders…</span></div>}
      {error && <div className="workflow-trading__alert" role="alert"><AlertTriangle size={18} /><div><strong>Trading evidence unavailable</strong><span>{error}</span></div></div>}
      {!loading && !error && projection && <div className="workflow-trading__evidence" aria-label="Trading evidence">
        <article className="workflow-trading__evidence-card"><span><WalletCards size={15} /> Account</span>{renderSection(projection, "account")}</article>
        <article className="workflow-trading__evidence-card"><span><Layers3 size={15} /> Positions</span>{renderSection(projection, "positions")}</article>
        <article className="workflow-trading__evidence-card"><span><ListChecks size={15} /> Orders</span>{renderSection(projection, "orders")}</article>
      </div>}

      <fieldset className="workflow-trading-actions" disabled={tradingDisabled}>
        <legend className="workflow-trading-actions__heading"><span><Zap size={15} /> Governed Trading Actions</span><small>{preflightReady ? "Preflight armed" : "Awaiting authority"}</small></legend>
        {tradingDisabled && <div className="workflow-trading__warning" role="alert"><AlertTriangle size={17} /><div><strong>Trading disabled</strong><span>Selected and platform modes must match before any action can be armed.</span></div></div>}
        <p className="workflow-trading-actions__note">Demo is the safe broker default. Authority references must come from backend workflow results; this form never invents them.</p>

        <div className="workflow-trading__form-grid">
          <section className="workflow-trading__form-card" aria-labelledby="execution-context-heading">
            <h3 id="execution-context-heading"><Route size={15} /> Execution context</h3>
            <div className="workflow-trading__fields">
              <label><span>Route</span><select aria-label="Route" value={draft.route} onChange={(event) => update("route", event.target.value as MutationDraft["route"])}><option value="demo">demo</option><option value="live">live</option></select></label>
              <label><span>Account ID</span><input aria-label="Account ID" value={draft.accountId} onChange={(event) => update("accountId", event.target.value)} /></label>
              <label><span>Strategy ID</span><input aria-label="Strategy ID" value={draft.strategyId} onChange={(event) => update("strategyId", event.target.value)} /></label>
              <label><span>Strategy version</span><input aria-label="Strategy version" value={draft.strategyVersion} onChange={(event) => update("strategyVersion", event.target.value)} /></label>
              <label className="workflow-trading__field--wide"><span>Intent ID</span><input aria-label="Intent ID" value={draft.intentId} onChange={(event) => update("intentId", event.target.value)} /></label>
            </div>
          </section>

          <section className="workflow-trading__form-card" aria-labelledby="order-details-heading">
            <h3 id="order-details-heading"><Crosshair size={15} /> Order details</h3>
            <div className="workflow-trading__fields">
              <label><span>Symbol</span><input aria-label="Symbol" value={draft.symbol} onChange={(event) => update("symbol", event.target.value)} /></label>
              <label><span>Side</span><select aria-label="Side" value={draft.side} onChange={(event) => update("side", event.target.value as MutationDraft["side"])}><option value="BUY">BUY</option><option value="SELL">SELL</option></select></label>
              <label><span>Order type</span><select aria-label="Order type" value={draft.orderType} onChange={(event) => update("orderType", event.target.value as MutationDraft["orderType"])}><option>MARKET</option><option>LIMIT</option><option>STOP</option><option>STOP_LIMIT</option></select></label>
              <label><span>Quantity unit</span><input aria-label="Quantity unit" value={draft.quantityUnit} onChange={(event) => update("quantityUnit", event.target.value)} /></label>
              <label className="workflow-trading__field--wide"><span>Quantity</span><input aria-label="Quantity" type="number" min="0" value={draft.quantity} onChange={(event) => update("quantity", event.target.value)} /></label>
            </div>
          </section>

          <section className="workflow-trading__form-card" aria-labelledby="authority-evidence-heading">
            <h3 id="authority-evidence-heading"><FileKey2 size={15} /> Authority evidence</h3>
            <div className="workflow-trading__fields workflow-trading__fields--single">
              <label><span>Risk decision ID</span><input aria-label="Risk decision ID" value={draft.riskDecisionId} onChange={(event) => update("riskDecisionId", event.target.value)} /></label>
              <label><span>Action-policy verdict ID</span><input aria-label="Action-policy verdict ID" value={draft.actionPolicyVerdictId} onChange={(event) => update("actionPolicyVerdictId", event.target.value)} /></label>
              <label><span>Approval token reference</span><input aria-label="Approval token reference" value={draft.approvalTokenRef} onChange={(event) => update("approvalTokenRef", event.target.value)} /></label>
            </div>
          </section>

          <section className="workflow-trading__form-card" aria-labelledby="broker-targets-heading">
            <h3 id="broker-targets-heading"><Activity size={15} /> Broker targets</h3>
            <div className="workflow-trading__fields workflow-trading__fields--single">
              <label><span>Broker order ID (cancel)</span><input aria-label="Broker order ID" value={draft.brokerOrderId} onChange={(event) => update("brokerOrderId", event.target.value)} /></label>
              <label><span>Broker position ID (close)</span><input aria-label="Broker position ID" value={draft.brokerPositionId} onChange={(event) => update("brokerPositionId", event.target.value)} /></label>
            </div>
          </section>
        </div>

        {preflightError && <div className="workflow-trading__inline-message workflow-trading__inline-message--error"><AlertTriangle size={15} /><span className="workflow-error">{preflightError}</span></div>}
        {actionError && <div className="workflow-trading__inline-message workflow-trading__inline-message--error"><AlertTriangle size={15} /><span className="workflow-error">{actionError}</span></div>}
        {actionResult && <div className="workflow-trading__inline-message workflow-trading__inline-message--success" role="status"><CheckCircle2 size={15} /><span>{actionResult}</span></div>}

        <div className="workflow-trading__command-bar" aria-label="Trading action controls">
          <button className="workflow-trading__button workflow-trading__button--arm" type="button" onClick={armGovernedActions} disabled={!commonReady}><ShieldCheck size={16} />{preflightReady ? "Re-arm preflight" : "Arm preflight"}</button>
          <div className="workflow-trading__command-actions">
            <button className="workflow-trading__button workflow-trading__button--submit" type="button" onClick={() => void execute("submit_order")} disabled={!preflightReady}><Zap size={16} /> Submit Order</button>
            <button className="workflow-trading__button workflow-trading__button--secondary" type="button" onClick={() => void execute("cancel_order")} disabled={!preflightReady || !draft.brokerOrderId.trim()}>Cancel Order</button>
            <button className="workflow-trading__button workflow-trading__button--secondary" type="button" onClick={() => void execute("close_position")} disabled={!preflightReady || !draft.brokerPositionId.trim()}>Close Position</button>
          </div>
        </div>
      </fieldset>
    </section>
  );
}
