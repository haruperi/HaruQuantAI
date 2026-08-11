/** Authenticated presentation of all registered Data capabilities. */

"use client";

import { useEffect, useState, type ReactNode } from "react";

import {
  ApiClientError,
  apiClients,
  unwrapData,
  type DataCapability,
} from "@/clients";

/** Render all fourteen server-declared Data capability summaries. */
export function DataWorkspace(): ReactNode {
  const [capabilities, setCapabilities] = useState<readonly DataCapability[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load(): Promise<void> {
      try {
        const response = await apiClients.data.capabilities();
        if (!cancelled) setCapabilities(unwrapData(response).capabilities);
      } catch (reason) {
        if (!cancelled) {
          setError(reason instanceof ApiClientError ? reason.message : "unavailable");
        }
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
    <section aria-label="Data capabilities" aria-live="polite">
      <h2>Data capabilities</h2>
      {loading && <p>loading…</p>}
      {error && <p role="alert">{error}</p>}
      {!loading && !error && capabilities.length === 0 && <p>no data</p>}
      <div className="workflow-dashboard-grid">
        {capabilities.map((capability) => (
          <article className="workflow-panel" key={capability.feature_id}>
            <div className="workflow-panel-header">
              <span>{capability.name}</span>
              <span>{capability.feature_id}</span>
            </div>
            <div className="workflow-panel-body">
              <p>{capability.summary}</p>
              <p>status: {capability.availability}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
