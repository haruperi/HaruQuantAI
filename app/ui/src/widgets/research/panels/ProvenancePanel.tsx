/**
 * Provenance panel (FEAT-UI-28, plan §10.16).
 *
 * Hashes, seeds, dependency versions, source references, and duration — the
 * evidence that makes a run reproducible. The raw report is available here as
 * a secondary diagnostic viewer, never as the primary result surface.
 */

"use client";

import { useState, type ReactNode } from "react";

import { Badge, EvidenceTable, KeyValues, Section, WarningList } from "../evidence";
import { useRunReport } from "../use-research";
import {
  formatDuration,
  formatTimestamp,
} from "../research-selectors";
import type { PanelProps } from "./OverviewPanel";

/** Reproducibility evidence and the diagnostic report viewer. */
export function ProvenancePanel({ detail, view }: PanelProps): ReactNode {
  const [showRaw, setShowRaw] = useState(false);
  const report = useRunReport(showRaw ? detail.run_id : null);
  const provenance = detail.provenance;

  return (
    <div className="research-panel">
      <Section
        title="Identity and hashes"
        description="The identifiers that make this run reproducible."
      >
        <KeyValues
          columns={3}
          items={[
            ["Run id", <span key="r" className="is-mono">{detail.run_id}</span>],
            [
              "Report id",
              <span key="rp" className="is-mono">
                {detail.report_id ?? "—"}
              </span>,
            ],
            ["Schema", provenance.schema_id ?? "—"],
            [
              "Dataset hash",
              <span key="d" className="is-mono research-wrap">
                {detail.dataset_hash ?? "—"}
              </span>,
            ],
            [
              "Configuration hash",
              <span key="c" className="is-mono research-wrap">
                {detail.configuration_hash ?? "—"}
              </span>,
            ],
            ["Contract version", provenance.contract_version ?? "—"],
            ["Generated", formatTimestamp(provenance.generated_at)],
            ["Duration", formatDuration(provenance.duration_ms)],
            [
              "Advisory only",
              <Badge key="a" tone="warning">
                {provenance.advisory_only === false ? "no" : "yes"}
              </Badge>,
            ],
          ]}
        />
      </Section>

      <Section
        title="Seeds and dependency versions"
        description="Every seeded component and the versions the run executed against."
      >
        <div className="research-two-up">
          <EvidenceTable
            caption="Seeds"
            columns={["Component", "Seed"]}
            emptyLabel="No seeds were published."
            rows={Object.entries(provenance.seeds ?? {}).map(([name, value]) => [
              <code key={name}>{name}</code>,
              String(value),
            ])}
          />
          <EvidenceTable
            caption="Dependency versions"
            columns={["Dependency", "Version"]}
            emptyLabel="No dependency versions were published."
            rows={Object.entries(provenance.dependency_versions ?? {}).map(
              ([name, value]) => [<code key={name}>{name}</code>, String(value)]
            )}
          />
        </div>
      </Section>

      <Section
        title="Stages and sources"
        description="What this run selected, and the source references its evidence rests on."
      >
        <div className="research-chips">
          {(provenance.selected_stages ?? detail.selected_stages).map((stage) => (
            <Badge key={stage} tone="neutral">
              {stage}
            </Badge>
          ))}
        </div>
        <EvidenceTable
          caption="Source references"
          columns={["Reference"]}
          emptyLabel="No source references were published."
          rows={(provenance.source_references ?? []).map((reference) => [
            <span key={reference} className="is-mono research-wrap">
              {reference}
            </span>,
          ])}
        />
      </Section>

      <Section
        title="Effective configuration"
        description="The configuration the server resolved. Filesystem roots and resource ceilings are server-owned and never exposed."
      >
        <EvidenceTable
          columns={["Setting", "Value"]}
          emptyLabel="No effective configuration was published."
          rows={Object.entries(detail.effective_configuration ?? {}).map(
            ([key, value]) => [
              <code key={key}>{key}</code>,
              <span key={`${key}-v`} className="is-mono research-wrap">
                {typeof value === "object" ? JSON.stringify(value) : String(value)}
              </span>,
            ]
          )}
        />
      </Section>

      <Section
        title="Diagnostic report viewer"
        description="The registered report as JSON. This is a secondary diagnostic view, not the primary result surface."
        actions={
          <button
            type="button"
            className="research-button"
            onClick={() => setShowRaw((value) => !value)}
          >
            {showRaw ? "Hide raw report" : "Load raw report"}
          </button>
        }
      >
        {!showRaw ? (
          <p className="research-note">
            The raw report is loaded on request so a large payload is never
            fetched by default.
          </p>
        ) : report.loading ? (
          <p className="research-note">Loading the registered report…</p>
        ) : report.error ? (
          <p className="research-error" role="alert">
            {report.error}
          </p>
        ) : report.data?.available ? (
          <pre className="research-raw">
            {JSON.stringify(report.data.report, null, 2)}
          </pre>
        ) : (
          <p className="research-note">
            No report was produced ({report.data?.reason ?? "unknown"}).
          </p>
        )}
      </Section>

      <Section title="Warnings" description="Every warning attached to the report.">
        <WarningList warnings={view.warnings.length ? view.warnings : detail.warnings} />
      </Section>
    </div>
  );
}
