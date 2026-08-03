/**
 * Trading session presentation (FR-API-050 Trading).
 *
 * Reads the aggregate trading session (account + positions + orders) via the
 * typed client. The three governed action buttons (submit/cancel/close) are
 * DISABLED by default and only enable when a governed preflight
 * (`buildGovernedOptions`) has been built — they never auto-submit. Backend
 * gates (kill-switch, risk review, approval, evidence freshness) remain the
 * sole authority over every mutation.
 */

"use client";

import { useEffect, useState, type ReactNode } from "react";

import { ApiClientError, apiClients } from "@/clients";
import type { TradingProjection } from "@/clients";
import { buildGovernedOptions, GovernedPreflightError } from "@/context";

/** Props accepted by `TradingView`. */
export interface TradingViewProps {
  className?: string;
}

/** Bounded JSON view of an opaque projection section. */
function renderSection(projection: TradingProjection, key: string): ReactNode {
  const value = projection[key];
  if (value === null || value === undefined) return <em>none</em>;
  if (Array.isArray(value)) {
    return value.length === 0 ? <em>empty</em> : <pre>{JSON.stringify(value, null, 2)}</pre>;
  }
  if (typeof value === "object") {
    return <pre>{JSON.stringify(value, null, 2)}</pre>;
  }
  return <span>{String(value)}</span>;
}

/** Trading session view with governed-action gating. */
export function TradingView({ className }: TradingViewProps = {}): ReactNode {
  const [projection, setProjection] = useState<TradingProjection | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Governed actions stay disabled until a preflight context is explicitly built.
  const [preflightReady, setPreflightReady] = useState(false);
  const [preflightError, setPreflightError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load(): Promise<void> {
      setLoading(true);
      setError(null);
      try {
        const response = await apiClients.trading.session();
        if (cancelled) return;
        if (response.status === "error") {
          setError(response.error.message);
        } else {
          setProjection(response.data);
        }
      } catch (cause) {
        if (cancelled) return;
        setError(cause instanceof ApiClientError ? cause.message : "unavailable");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  /** Build the governed preflight; never auto-submit. */
  function armGovernedActions(): void {
    setActionError(null);
    try {
      buildGovernedOptions({
        workflow: "trading.session",
        permission: "trading:write",
        actorId: "operator",
        evidenceId: `session-${Date.now()}`,
      });
      setPreflightReady(true);
      setPreflightError(null);
    } catch (cause) {
      setPreflightReady(false);
      setPreflightError(
        cause instanceof GovernedPreflightError ? cause.message : "preflight failed"
      );
    }
  }

  async function submitOrder(): Promise<void> {
    setActionError(null);
    try {
      const response = await apiClients.trading.submitOrder({ side: "BUY", symbol: "EURUSD", qty: 1 });
      if (response.status === "error") setActionError(response.error.message);
    } catch (cause) {
      setActionError(cause instanceof ApiClientError ? cause.message : "unavailable");
    }
  }

  return (
    <div className={`workflow-trading ${className ?? ""}`.trim()} role="region" aria-label="Trading">
      {loading && <span>loading…</span>}
      {error && <span className="workflow-error">{error}</span>}
      {!loading && !error && projection && (
        <>
          <div className="workflow-trading-account">
            <h4>Account</h4>
            {renderSection(projection, "account")}
          </div>
          <div className="workflow-trading-positions">
            <h4>Positions</h4>
            {renderSection(projection, "positions")}
          </div>
          <div className="workflow-trading-orders">
            <h4>Orders</h4>
            {renderSection(projection, "orders")}
          </div>
        </>
      )}

      <div className="workflow-trading-actions">
        <h4>Governed Actions</h4>
        <p className="workflow-governed-notice">
          These actions are disabled until you arm the governed preflight. They
          never auto-submit; backend gates remain authoritative.
        </p>
        <button type="button" onClick={armGovernedActions}>
          {preflightReady ? "Re-arm preflight" : "Arm preflight"}
        </button>
        {preflightError && <span className="workflow-error">{preflightError}</span>}
        <button type="button" onClick={() => void submitOrder()} disabled={!preflightReady}>
          Submit Order
        </button>
        <button type="button" disabled={!preflightReady}>
          Cancel Order
        </button>
        <button type="button" disabled={!preflightReady}>
          Close Position
        </button>
        {actionError && <span className="workflow-error">{actionError}</span>}
      </div>
    </div>
  );
}
