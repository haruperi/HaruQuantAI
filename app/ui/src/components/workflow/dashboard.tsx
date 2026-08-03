/**
 * Freshness-aware dashboard presentation (FR-API-047).
 *
 * Fetches the six approved dashboard snapshots in parallel and renders a
 * freshness-aware grid (timestamp + stale warning per snapshot). Currency
 * strength is explicitly excluded. Snapshots are owner-authored opaque
 * payloads; fields are rendered defensively.
 */

"use client";

import { useEffect, useState, type ReactNode } from "react";

import { ApiClientError, apiClients, unwrapData } from "@/clients";
import type { DashboardSnapshot } from "@/clients";

/** One dashboard panel with its loading/error/stale state. */
interface PanelState {
  readonly name: string;
  readonly snapshot: DashboardSnapshot | null;
  readonly stale: boolean;
  readonly staleReason: string | null;
  readonly loading: boolean;
  readonly error: string | null;
}

const PANELS: ReadonlyArray<{ key: string; label: string; fetch: () => ReturnType<typeof apiClients.dashboards.broker> }> = [
  { key: "broker", label: "Broker", fetch: () => apiClients.dashboards.broker() },
  { key: "equityCurve", label: "Equity Curve", fetch: () => apiClients.dashboards.equityCurve() },
  { key: "summary", label: "Summary", fetch: () => apiClients.dashboards.summary() },
  { key: "systemResources", label: "System Resources", fetch: () => apiClients.dashboards.systemResources() },
  { key: "marketHours", label: "Market Hours", fetch: () => apiClients.dashboards.marketHours() },
  { key: "forexCalendar", label: "Forex Calendar", fetch: () => apiClients.dashboards.forexCalendar() },
];

/** Render one opaque snapshot payload as a bounded JSON field view. */
function renderSnapshotData(data: unknown): ReactNode {
  if (data === null || data === undefined) return <em>no data</em>;
  if (typeof data === "object") {
    return (
      <pre className="workflow-snapshot-data">
        {JSON.stringify(data, null, 2)}
      </pre>
    );
  }
  return <span>{String(data)}</span>;
}

/** Freshness-aware dashboard view. */
export function DashboardView(): ReactNode {
  const [panels, setPanels] = useState<PanelState[]>(
    PANELS.map((p) => ({
      name: p.label,
      snapshot: null,
      stale: false,
      staleReason: null,
      loading: true,
      error: null,
    }))
  );

  useEffect(() => {
    let cancelled = false;
    async function loadAll(): Promise<void> {
      const results = await Promise.allSettled(PANELS.map((p) => p.fetch()));
      if (cancelled) return;
      setPanels(
        results.map((result, idx) => {
          const panel = PANELS[idx];
          if (result.status === "fulfilled") {
            const response = result.value;
            if (response.status === "error") {
              return {
                name: panel.label,
                snapshot: null,
                stale: false,
                staleReason: null,
                loading: false,
                error: response.error.message,
              };
            }
            const snapshot = unwrapData(response);
            return {
              name: panel.label,
              snapshot,
              stale: Boolean(response.metadata?.stale),
              staleReason: response.metadata?.stale_reason ?? null,
              loading: false,
              error: null,
            };
          }
          const message =
            result.reason instanceof ApiClientError
              ? result.reason.message
              : "unavailable";
          return {
            name: panel.label,
            snapshot: null,
            stale: false,
            staleReason: null,
            loading: false,
            error: message,
          };
        })
      );
    }
    void loadAll();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="workflow-dashboard" role="region" aria-label="Dashboard">
      <div className="workflow-dashboard-grid">
        {panels.map((panel) => (
          <div key={panel.name} className="workflow-panel">
            <div className="workflow-panel-header">
              <span>{panel.name}</span>
              {panel.stale && (
                <span
                  className="workflow-stale-warning"
                  role="warning"
                  title={panel.staleReason ?? "stale snapshot"}
                >
                  stale
                </span>
              )}
            </div>
            <div className="workflow-panel-body">
              {panel.loading && <span>loading…</span>}
              {panel.error && <span className="workflow-error">{panel.error}</span>}
              {!panel.loading && !panel.error && panel.snapshot && (
                <>
                  {panel.snapshot.timestamp && (
                    <div className="workflow-timestamp">{panel.snapshot.timestamp}</div>
                  )}
                  {renderSnapshotData(panel.snapshot.data)}
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
