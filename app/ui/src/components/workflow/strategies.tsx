/**
 * Registered strategy catalogue/version workflow presentation (FR-API-048).
 *
 * Reads the strategy version catalogue via the typed client; selecting a row
 * fetches that strategy's version list. Mutation, raw import/export, and SQX
 * controls are explicitly absent (the README excludes them from backend v1).
 */

"use client";

import { useEffect, useState, type ReactNode } from "react";

import { ApiClientError, apiClients, unwrapData } from "@/clients";
import type { StrategyCatalogue } from "@/clients";

/** Props accepted by `StrategyWorkspace`. */
export interface StrategyWorkspaceProps {
  /** Optional class for the root element. */
  className?: string;
}

/** Read-only strategy catalogue/version workspace. */
export function StrategyWorkspace({ className }: StrategyWorkspaceProps = {}): ReactNode {
  const [catalogue, setCatalogue] = useState<StrategyCatalogue | null>(null);
  const [versions, setVersions] = useState<StrategyCatalogue | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load(): Promise<void> {
      setLoading(true);
      setError(null);
      try {
        const response = await apiClients.strategies.catalogue();
        if (cancelled) return;
        if (response.status === "error") {
          setError(response.error.message);
        } else {
          setCatalogue(unwrapData(response));
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

  async function selectStrategy(strategyId: string): Promise<void> {
    setSelectedId(strategyId);
    setVersions(null);
    try {
      const response = await apiClients.strategies.versions(strategyId);
      if (response.status === "error") {
        setError(response.error.message);
      } else {
        setVersions(unwrapData(response));
      }
    } catch (cause) {
      setError(cause instanceof ApiClientError ? cause.message : "unavailable");
    }
  }

  return (
    <div className={`workflow-strategies ${className ?? ""}`.trim()} role="region" aria-label="Strategies">
      {loading && <span>loading…</span>}
      {error && <span className="workflow-error">{error}</span>}
      {!loading && !error && catalogue && (
        <div className="workflow-strategy-list">
          <h4>Catalogue</h4>
          <ul>
            {catalogue.map((entry, idx) => {
              const id = typeof entry.id === "string" ? entry.id : String(idx);
              return (
                <li key={id}>
                  <button type="button" onClick={() => void selectStrategy(id)}>
                    {id}
                  </button>
                </li>
              );
            })}
          </ul>
          {selectedId && (
            <div className="workflow-strategy-versions">
              <h5>Versions for {selectedId}</h5>
              {versions ? (
                <pre>{JSON.stringify(versions, null, 2)}</pre>
              ) : (
                <span>loading…</span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
