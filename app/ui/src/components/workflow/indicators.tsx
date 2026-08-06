/**
 * Read-only Indicators catalogue, capability matrix, and spec inspection workspace.
 *
 * Reads the indicator catalogue and capability matrix via the typed client.
 * Provides interactive search/filtering and detailed spec inspection.
 * Calculation, upload, and mutation controls are explicitly absent (Indicators is a pure read-only domain).
 */

"use client";

import { useEffect, useState, type ReactNode } from "react";

import { ApiClientError, apiClients, unwrapData } from "@/clients";
import type { CapabilityMatrix, IndicatorCatalogue, IndicatorSpec } from "@/clients";

/** Props accepted by `IndicatorWorkspace`. */
export interface IndicatorWorkspaceProps {
  /** Optional class for the root element. */
  className?: string;
}

/** Read-only indicator catalogue/capability/spec workspace. */
export function IndicatorWorkspace({ className }: IndicatorWorkspaceProps = {}): ReactNode {
  const [catalogue, setCatalogue] = useState<IndicatorCatalogue | null>(null);
  const [capabilities, setCapabilities] = useState<CapabilityMatrix | null>(null);
  const [selectedSpec, setSelectedSpec] = useState<IndicatorSpec | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [specLoading, setSpecLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load(): Promise<void> {
      setLoading(true);
      setError(null);
      try {
        const [catRes, capRes] = await Promise.all([
          apiClients.indicators.catalogue(),
          apiClients.indicators.capabilities(),
        ]);
        if (cancelled) return;

        if (catRes.status === "error") {
          setError(catRes.error.message);
        } else if (capRes.status === "error") {
          setError(capRes.error.message);
        } else {
          setCatalogue(unwrapData(catRes));
          setCapabilities(unwrapData(capRes));
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

  async function selectIndicator(indicatorId: string): Promise<void> {
    setSelectedId(indicatorId);
    setSelectedSpec(null);
    setSpecLoading(true);
    try {
      const response = await apiClients.indicators.getSpec(indicatorId);
      if (response.status === "error") {
        setError(response.error.message);
      } else {
        setSelectedSpec(unwrapData(response));
      }
    } catch (cause) {
      setError(cause instanceof ApiClientError ? cause.message : "unavailable");
    } finally {
      setSpecLoading(false);
    }
  }

  const filteredCatalogue = catalogue?.filter((spec) => {
    const q = search.toLowerCase().trim();
    if (!q) return true;
    return (
      spec.indicator_id.toLowerCase().includes(q) ||
      spec.name.toLowerCase().includes(q) ||
      spec.warmup_policy.toLowerCase().includes(q)
    );
  });

  const totalCount = catalogue?.length ?? 0;
  const vectorizedCount = catalogue?.filter((s) => s.vectorized).length ?? 0;
  const mvpCount = catalogue?.filter((s) => s.tier === "core_mvp").length ?? 0;

  return (
    <div className={`workflow-indicators ${className ?? ""}`.trim()} role="region" aria-label="Indicators">
      {loading && <span>loading…</span>}
      {error && <span className="workflow-error">{error}</span>}
      {!loading && !error && catalogue && (
        <div className="workflow-indicators-content">
          <div className="workflow-indicators-summary">
            <div className="summary-card">
              <span className="card-label">Total Built-ins</span>
              <span className="card-value">{totalCount}</span>
            </div>
            <div className="summary-card">
              <span className="card-label">Vectorized</span>
              <span className="card-value">{vectorizedCount}</span>
            </div>
            <div className="summary-card">
              <span className="card-label">Core MVP Tier</span>
              <span className="card-value">{mvpCount}</span>
            </div>
          </div>

          <div className="workflow-indicators-filter">
            <input
              type="text"
              placeholder="Search indicators by name or policy…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              aria-label="Filter indicators"
            />
          </div>

          <div className="workflow-indicators-layout">
            <div className="workflow-indicator-list">
              <h4>Catalogue ({filteredCatalogue?.length ?? 0})</h4>
              <ul>
                {filteredCatalogue?.map((spec) => (
                  <li key={spec.indicator_id} className={selectedId === spec.indicator_id ? "selected" : ""}>
                    <button type="button" onClick={() => void selectIndicator(spec.indicator_id)}>
                      <strong>{spec.name}</strong> ({spec.indicator_id})
                    </button>
                  </li>
                ))}
              </ul>
            </div>

            {selectedId && (
              <div className="workflow-indicator-spec">
                <h5>Specification for {selectedId}</h5>
                {specLoading && <span>loading spec…</span>}
                {!specLoading && selectedSpec && (
                  <div className="spec-details">
                    <div><strong>ID:</strong> {selectedSpec.indicator_id}</div>
                    <div><strong>Name:</strong> {selectedSpec.name}</div>
                    <div><strong>Formula Version:</strong> {selectedSpec.formula_version}</div>
                    <div><strong>Warmup Policy:</strong> {selectedSpec.warmup_policy}</div>
                    <div><strong>Required Columns:</strong> {selectedSpec.required_columns.join(", ")}</div>
                    <div><strong>Output Templates:</strong> {selectedSpec.output_templates.join(", ")}</div>
                    <div><strong>Import Path:</strong> <code>{selectedSpec.import_path}</code></div>
                    <div>
                      <strong>Parameter Schema:</strong>
                      <pre>{JSON.stringify(selectedSpec.parameter_schema, null, 2)}</pre>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
