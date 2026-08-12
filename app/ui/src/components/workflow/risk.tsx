/**
 * Risk state presentation (FR-UI-014).
 *
 * Read-only view of the current kill-switch state and recent risk decisions.
 * No mutation controls — Risk remains the sole authority over its state.
 */

"use client";

import { useEffect, useState, type ReactNode } from "react";

import { ApiClientError, apiClients } from "@/clients";
import type { KillSwitchState, RiskDecision } from "@/clients";

/** Props accepted by `RiskView`. */
export interface RiskViewProps {
  className?: string;
}

/** Read-only string accessor for an opaque payload. */
function str(payload: Record<string, unknown>, key: string): string {
  const value = payload[key];
  if (value === null || value === undefined) return "—";
  return typeof value === "object" ? JSON.stringify(value) : String(value);
}

/** Read-only risk view. */
export function RiskView({ className }: RiskViewProps = {}): ReactNode {
  const [killSwitch, setKillSwitch] = useState<KillSwitchState | null>(null);
  const [decisions, setDecisions] = useState<RiskDecision[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load(): Promise<void> {
      setLoading(true);
      setError(null);
      try {
        const [ksRes, decRes] = await Promise.all([
          apiClients.risk.killSwitch(),
          apiClients.risk.decisions(),
        ]);
        if (cancelled) return;
        if (ksRes.status === "error" || decRes.status === "error") {
          const err = ksRes.status === "error" ? ksRes.error : decRes.error;
          setError(err?.message ?? "risk read failed");
        } else {
          setKillSwitch(ksRes.data);
          setDecisions(decRes.data ?? []);
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

  return (
    <div className={`workflow-risk ${className ?? ""}`.trim()} role="region" aria-label="Risk">
      {loading && <span>loading…</span>}
      {error && <span className="workflow-error">{error}</span>}
      {!loading && !error && killSwitch && (
        <div className="workflow-risk-state">
          <h4>Kill Switch</h4>
          <div><strong>State:</strong> {str(killSwitch, "state")}</div>
          <div><strong>Scope level:</strong> {str(killSwitch, "scope_level")}</div>
          <div><strong>Reason:</strong> {str(killSwitch, "reason")}</div>
          <div><strong>Version:</strong> {str(killSwitch, "version")}</div>
          <div><strong>Updated:</strong> {str(killSwitch, "updated_at")}</div>
        </div>
      )}
      {!loading && !error && (
        <div className="workflow-risk-decisions">
          <h4>Recent Decisions</h4>
          {decisions.length === 0 ? (
            <span>none</span>
          ) : (
            <ul>
              {decisions.slice(0, 20).map((d, idx) => (
                <li key={str(d, "decision_id") || idx}>
                  {str(d, "decision_id")} — {str(d, "state")}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
