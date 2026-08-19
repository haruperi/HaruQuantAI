/**
 * Provenance and artifacts panel (FEAT-UI-32).
 *
 * The V2 destination for reproducibility evidence: exact hashes, versions,
 * revisions, seed, lineage, precision metadata, warnings, and the artifact
 * manifest. Every hash is rendered exactly as the owner recorded it, never
 * shortened, reformatted, or recomputed.
 */

"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";

import {
  ApiClientError,
  apiClients,
  type AnalyticsWorkbenchPayload,
  type ArtifactInventory,
} from "@/clients";
import { EvidenceValue } from "./AnalyticsEvidenceState";

/** Ordered lineage rows exactly as the provenance screen specifies. */
export const PROVENANCE_ROWS: readonly (readonly [string, string])[] = [
  ["request_hash", "Request hash"],
  ["config_hash", "Config hash"],
  ["data_hash", "Data hash"],
  ["report_hash", "Report hash"],
  ["strategy_version", "Strategy version"],
  ["dataset_revision", "Dataset revision"],
  ["provider_specification_revision", "Provider specification revision"],
  ["execution_model", "Execution model"],
  ["calculation_model", "Calculation model"],
  ["calibration_checksum", "Calibration checksum"],
  ["seed", "Seed"],
  ["engine_version", "Engine version"],
  ["dependency_versions", "Dependency versions"],
  ["precision", "Precision metadata"],
  ["trace_id", "Trace ID"],
  ["audit_id", "Audit ID"],
];

/** Resolve a failure message without implying a successful read. */
function failureMessage(cause: unknown): string {
  if (cause instanceof ApiClientError || cause instanceof Error) {
    return cause.message;
  }
  return "The run provenance evidence is unavailable.";
}

/** Render one lineage value verbatim, or mark it unavailable. */
function lineageValue(value: unknown): ReactNode {
  if (value === null || value === undefined || value === "") {
    return <EvidenceValue value={null} />;
  }
  if (typeof value === "object") {
    return <span className="font-mono">{JSON.stringify(value)}</span>;
  }
  return <span className="font-mono">{String(value)}</span>;
}

/** Props accepted by `ProvenancePanel`. */
export interface ProvenancePanelProps {
  runId: string;
  className?: string;
}

/** Reproducibility lineage, warnings, and artifact manifest for one run. */
export function ProvenancePanel({
  runId,
  className = "",
}: ProvenancePanelProps): ReactNode {
  const [payload, setPayload] = useState<AnalyticsWorkbenchPayload | null>(null);
  const [inventory, setInventory] = useState<ArtifactInventory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [payloadResponse, artifactResponse] = await Promise.all([
        apiClients.analyticsWorkbench.getWorkbenchPayload(runId),
        apiClients.analyticsWorkbench.getArtifacts(runId),
      ]);
      if (payloadResponse.status === "error") {
        setError(payloadResponse.error.message);
        return;
      }
      setPayload(payloadResponse.data);
      if (artifactResponse.status === "success") {
        setInventory(artifactResponse.data);
      }
    } catch (cause) {
      setError(failureMessage(cause));
    } finally {
      setLoading(false);
    }
  }, [runId]);

  useEffect(() => {
    void load();
  }, [load]);

  const lineage = (payload?.lineage ?? {}) as Record<string, unknown>;

  return (
    <section
      className={`analytics-provenance ${className}`.trim()}
      aria-label="Run provenance"
    >
      <h3>Provenance and artifacts</h3>

      {loading ? <p role="status">Loading provenance evidence…</p> : null}
      {error ? <p role="alert">{error}</p> : null}

      {payload ? (
        <>
          <section aria-labelledby="provenance-lineage">
            <h4 id="provenance-lineage">Reproducibility lineage</h4>
            <dl className="analytics-provenance__grid">
              {PROVENANCE_ROWS.map(([key, label]) => (
                <div key={key} className="analytics-provenance__row">
                  <dt>{label}</dt>
                  <dd>{lineageValue(lineage[key])}</dd>
                </div>
              ))}
              <div className="analytics-provenance__row">
                <dt>Report ID</dt>
                <dd className="font-mono">{payload.report_id}</dd>
              </div>
              <div className="analytics-provenance__row">
                <dt>Payload ID</dt>
                <dd className="font-mono">{payload.payload_id}</dd>
              </div>
              <div className="analytics-provenance__row">
                <dt>Generated at</dt>
                <dd>{payload.generated_at}</dd>
              </div>
            </dl>
          </section>

          <section aria-labelledby="provenance-warnings">
            <h4 id="provenance-warnings">Warnings</h4>
            {payload.warnings.length > 0 ? (
              <ul>
                {payload.warnings.map((warning, index) => (
                  <li key={`${String(warning.code ?? index)}`}>
                    {String(
                      warning.message ?? warning.detail ?? warning.code ?? "",
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <p>No warning was recorded.</p>
            )}
          </section>

          <section aria-labelledby="provenance-manifest">
            <h4 id="provenance-manifest">Artifact manifest</h4>
            {inventory && inventory.artifacts.length > 0 ? (
              <table className="analytics-provenance__manifest">
                <caption className="sr-only">Recorded run artifacts</caption>
                <thead>
                  <tr>
                    <th scope="col">Kind</th>
                    <th scope="col">Reference</th>
                  </tr>
                </thead>
                <tbody>
                  {inventory.artifacts.map((artifact) => (
                    <tr key={`${artifact.kind}:${artifact.ref}`}>
                      <td>{artifact.kind}</td>
                      <td className="font-mono">{artifact.ref}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p>No artifact reference is recorded for this run.</p>
            )}
            <p className="analytics-provenance__note">
              Artifacts are immutable owner records. This view references them
              and never deletes or rewrites one.
            </p>
          </section>
        </>
      ) : null}
    </section>
  );
}
