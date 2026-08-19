/** cTrader-inspired governed order-entry host. */
"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";
import { AlertTriangle, LoaderCircle, ShieldCheck } from "lucide-react";
import { ApiClientError, apiClients, type ExecutionSession } from "@/clients";
import { PriceLadderWidget } from "@/features/price-ladder";
import { useWorkspaceStore } from "@/features/workspaces";
import { OrderTicket } from "./OrderTicket";

export interface TradingWidgetProps { className?: string; accountId?: string; symbol?: string; ticketHostOnly?: boolean }

function selectSession(sessions: readonly ExecutionSession[], mode: "sim" | "demo" | "live"): ExecutionSession | null {
  const matching = sessions.filter((session) => session.mode === mode);
  return matching.find((session) => session.is_active) ?? matching.find((session) => session.is_default) ?? null;
}

/** Trading widget with route and account context resolved from system state. */
export function TradingWidget({ className, accountId: configuredAccountId, symbol, ticketHostOnly = false }: TradingWidgetProps = {}): ReactNode {
  const accountMode = useWorkspaceStore((state) => state.accountMode);
  const [sessions, setSessions] = useState<ExecutionSession[]>([]);
  const [activeSymbol, setActiveSymbol] = useState(symbol ?? "EURUSD");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true); setError(null);
    void apiClients.trading.listExecutionSessions().then((response) => {
      if (cancelled) return;
      if (response.status === "error") throw new Error(response.error.message);
      setSessions(response.data);
    }).catch((cause: unknown) => {
      if (!cancelled) setError(cause instanceof ApiClientError || cause instanceof Error ? cause.message : "Execution context is unavailable.");
    }).finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [accountMode]);

  const session = useMemo(() => accountMode === "unknown" ? null : selectSession(sessions, accountMode), [accountMode, sessions]);
  const accountId = session?.provider_account_ref ?? configuredAccountId;
  const unavailable = accountMode === "unknown"
    ? "Select an account mode in System Settings before placing an order."
    : !session && !configuredAccountId
      ? `No active or default ${accountMode.toUpperCase()} execution session is configured.`
      : !accountId ? "The selected execution session has no provider account reference." : null;

  if (ticketHostOnly) return <OrderTicket accountId={accountId} symbol={activeSymbol} />;
  return <section className={`workflow-trading ${className ?? ""}`.trim()} role="region" aria-label="Trading">
    <header className="workflow-trading__hero"><div><span className="workflow-trading__eyebrow"><ShieldCheck size={14} /> Governed execution</span><h2>New order</h2><p>Execution route and broker account follow the active system session automatically.</p></div><span className={`workflow-trading__route workflow-trading__route--${accountMode}`}>{accountMode === "unknown" ? "Mode unavailable" : `${accountMode.toUpperCase()} · ${session?.name ?? "No session"}`}</span></header>
    {loading && <div className="workflow-trading__state" role="status"><LoaderCircle className="is-spinning" size={22} /><strong>Resolving execution context</strong></div>}
    {!loading && error && <div className="workflow-trading__alert" role="alert"><AlertTriangle size={18} /><div><strong>Execution context unavailable</strong><span>{error}</span></div></div>}
    {!loading && !error && unavailable && <div className="workflow-trading__warning" role="alert"><AlertTriangle size={18} /><div><strong>Order entry unavailable</strong><span>{unavailable}</span></div></div>}
    {!loading && !error && accountId && accountMode !== "unknown" && (
      <div className="workflow-trading__execution-grid">
        <div className="workflow-trading__ticket-pane">
          <OrderTicket accountId={accountId} symbol={activeSymbol} onSymbolChange={setActiveSymbol} embedded />
        </div>
        <aside className="workflow-trading__ladder-pane" aria-label="Trading price ladder">
          <PriceLadderWidget variant="trading" symbol={activeSymbol} accountId={accountId} route={accountMode} />
        </aside>
      </div>
    )}
  </section>;
}
