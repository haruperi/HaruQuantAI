/**
 * Drift monitor (FEAT-UI-28, plan §10.19).
 *
 * Shows baseline, latest observation, metric deltas, threshold breaches, and
 * any advisory suspension proposal Research recorded. The UI never enacts a
 * suspension — the page states that plainly and offers no control that would.
 */

"use client";

import Link from "next/link";
import { useState, type ReactNode } from "react";

import { Badge, ContributionBar, EvidenceTable, KeyValues, RecordTable, Section } from "./evidence";
import { EvidenceGate } from "./ResearchRunStatus";
import {
  asNumber,
  asText,
  deltaTone,
  evidenceArray,
  evidenceRecord,
  formatDelta,
  formatNumber,
  formatTimestamp,
} from "./research-selectors";
import { useDrift } from "./use-research";

const SEVERITY_TONES: Record<string, "positive" | "warning" | "negative"> = {
  none: "positive",
  low: "warning",
  medium: "warning",
  high: "negative",
  critical: "negative",
};

/** Performance-drift evidence. */
export function ResearchDrift(): ReactNode {
  const [profileId, setProfileId] = useState("");
  const [query, setQuery] = useState<{ profileId?: string }>({});
  const drift = useDrift(query);
  const evidence = drift.data?.evidence ?? null;
  const deltas = evidenceArray(evidence, "metric_deltas") as Array<
    Record<string, unknown>
  >;
  const breaches = evidenceArray(evidence, "threshold_breaches") as Array<
    Record<string, unknown>
  >;
  const proposal = evidenceRecord(evidence, "suspension_proposal");
  const severity = asText(evidence?.severity) ?? "unknown";
  const maxDelta = Math.max(
    1e-9,
    ...deltas.map((row) => Math.abs(asNumber(row.delta) ?? 0))
  );

  return (
    <div className="research-page">
      <header className="research-page__head">
        <p className="research-eyebrow">Research workbench</p>
        <h1>Drift monitor</h1>
        <p>
          Performance drift against an approved expectancy baseline. Any
          suspension proposal here is advisory: this page never enacts one.
        </p>
        <div className="research-links">
          <Link className="research-button" href="/workstation/research">
            Back to ledger
          </Link>
          <Link className="research-button" href="/workstation/research/expectancy">
            Expectancy
          </Link>
          <Link className="research-button" href="/workstation/research/new">
            Create a new experiment
          </Link>
        </div>
      </header>

      <Section
        title="Profile selection"
        description="Drift evidence is keyed by the expectancy profile it was measured against."
        actions={
          <form
            className="research-inline-form"
            onSubmit={(event) => {
              event.preventDefault();
              setQuery({ profileId: profileId.trim() || undefined });
            }}
          >
            <label className="research-inline-field">
              Profile id
              <input
                value={profileId}
                onChange={(event) => setProfileId(event.target.value)}
              />
            </label>
            <button type="submit" className="research-button">
              Load
            </button>
          </form>
        }
      >
        <EvidenceGate
          loading={drift.loading}
          error={drift.error}
          reload={drift.reload}
          ready={drift.data !== null}
          loadingLabel="Loading drift evidence…"
        >
          {drift.data?.available && evidence ? (
            <>
              <KeyValues
                columns={4}
                items={[
                  ["Profile", asText(evidence.profile_id) ?? profileId],
                  [
                    "Severity",
                    <Badge key="s" tone={SEVERITY_TONES[severity] ?? "unknown"}>
                      {severity}
                    </Badge>,
                  ],
                  [
                    "Baseline reference",
                    asText(evidence.baseline_ref) ??
                      asText(evidence.baseline_reference) ??
                      "—",
                  ],
                  [
                    "Observed at",
                    formatTimestamp(
                      asText(evidence.observed_at_utc) ?? asText(evidence.observed_at)
                    ),
                  ],
                  [
                    "Breaches",
                    formatNumber(breaches.length, 0),
                  ],
                  [
                    "Suspension proposed",
                    <Badge
                      key="p"
                      tone={proposal ? "warning" : "positive"}
                    >
                      {proposal ? "yes (advisory)" : "no"}
                    </Badge>,
                  ],
                  [
                    "Enacted by this UI",
                    <Badge key="e" tone="positive">
                      never
                    </Badge>,
                  ],
                  ["Contract", asText(evidence.contract_version) ?? "—"],
                ]}
              />

              <Section
                title="Metric deltas"
                description="Each measured metric against its baseline value."
              >
                <div className="research-bars">
                  {deltas.map((row, index) => (
                    <ContributionBar
                      key={index}
                      label={asText(row.metric) ?? `metric ${index + 1}`}
                      value={asNumber(row.delta)}
                      maximum={maxDelta}
                      tone={deltaTone(row.delta)}
                      display={formatDelta(row.delta, 6)}
                    />
                  ))}
                </div>
                <EvidenceTable
                  columns={["Metric", "Baseline", "Latest", "Delta", "Threshold"]}
                  emptyLabel="No metric deltas were published."
                  rows={deltas.map((row, index) => [
                    <code key={index}>{asText(row.metric) ?? "—"}</code>,
                    formatNumber(row.baseline, 6),
                    formatNumber(row.latest ?? row.observed, 6),
                    <Badge key={`${index}-d`} tone={deltaTone(row.delta)}>
                      {formatDelta(row.delta, 6)}
                    </Badge>,
                    formatNumber(row.threshold, 6),
                  ])}
                />
              </Section>

              <Section
                title="Threshold breaches"
                description="Breaches Research recorded, with the threshold each one crossed."
              >
                <EvidenceTable
                  columns={["Metric", "Detail"]}
                  emptyLabel="No thresholds were breached."
                  rows={breaches.map((breach, index) => [
                    <code key={index}>{asText(breach.metric) ?? "—"}</code>,
                    <RecordTable key={`${index}-r`} record={breach} />,
                  ])}
                />
              </Section>

              <Section
                title="Advisory suspension proposal"
                description="Recorded by Research as a proposal. Acting on it is a governed server-side decision."
              >
                <RecordTable
                  record={proposal}
                  emptyLabel="Research proposed no suspension for this observation."
                />
              </Section>
            </>
          ) : (
            <div className="research-empty" role="status">
              <Badge tone="unknown">Unavailable</Badge>
              <p>
                {asText(drift.data?.reason) === "PROFILE_NOT_SELECTED"
                  ? "Name an expectancy profile id to load the drift evidence recorded against it."
                  : "Research has recorded no drift evidence for that profile."}
              </p>
              <code className="research-empty__reason">
                {asText(drift.data?.reason) ?? "NO_EVIDENCE"}
              </code>
            </div>
          )}
        </EvidenceGate>
      </Section>
    </div>
  );
}
