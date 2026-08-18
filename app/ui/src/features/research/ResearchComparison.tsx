/**
 * Run comparison (FEAT-UI-28, plan §10.17).
 *
 * The comparison is computed by the server and rendered here. The browser
 * holds no V1-style snapshot, and computes no delta of its own beyond
 * displaying the ones the API returned.
 */

"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { Badge, EvidenceTable, Section, StateBadge } from "./evidence";
import { EvidenceGate } from "./ResearchRunStatus";
import {
  CLASSIFICATION_TONES,
  READINESS_TONES,
  deltaTone,
  formatDelta,
  formatNumber,
  formatScore,
  formatTimestamp,
  hashPrefix,
} from "./research-selectors";
import { MAX_COMPARISON_RUNS, useResearchStore } from "./research-store";
import { useComparison, useRuns } from "./use-research";

/** Run selection and server-derived comparison. */
export function ResearchComparison(): ReactNode {
  const runs = useRuns();
  const selection = useResearchStore((state) => state.comparisonSelection);
  const toggle = useResearchStore((state) => state.toggleComparisonRun);
  const clear = useResearchStore((state) => state.clearComparison);
  const comparison = useComparison(selection);

  return (
    <div className="research-page">
      <header className="research-page__head">
        <p className="research-eyebrow">Research workbench</p>
        <h1>Compare runs</h1>
        <p>
          Select between two and {MAX_COMPARISON_RUNS} runs. The first selected
          run is the baseline every delta is measured against.
        </p>
        <div className="research-links">
          <Link className="research-button" href="/workstation/research">
            Back to ledger
          </Link>
          <button type="button" className="research-button" onClick={clear}>
            Clear selection
          </button>
        </div>
      </header>

      <Section
        title="Run history"
        description="Every retained run, newest first — including failed, cancelled, and inconclusive results."
      >
        <EvidenceGate
          loading={runs.loading}
          error={runs.error}
          reload={runs.reload}
          ready={runs.data !== null}
          loadingLabel="Loading run history…"
        >
          <EvidenceTable
            columns={[
              "Compare",
              "Run",
              "Experiment",
              "Symbol",
              "Timeframe",
              "Dataset hash",
              "Config hash",
              "Status",
              "Readiness",
              "Score",
              "Created",
              "Duration",
              "Warnings",
            ]}
            emptyLabel="No runs are retained yet."
            rows={(runs.data?.runs ?? []).map((run) => [
              <input
                key={`${run.run_id}-c`}
                type="checkbox"
                aria-label={`Compare run ${run.run_id}`}
                checked={selection.includes(run.run_id)}
                onChange={() => toggle(run.run_id)}
              />,
              <Link
                key={`${run.run_id}-l`}
                href={`/workstation/research/experiments/${run.experiment_id}/runs/${run.run_id}/overview`}
              >
                {run.run_id.slice(0, 14)}…
              </Link>,
              run.experiment_id.slice(0, 12) + "…",
              run.symbol,
              run.timeframe,
              <span key={`${run.run_id}-d`} className="is-mono">
                {hashPrefix(run.dataset_hash, 8)}
              </span>,
              <span key={`${run.run_id}-cf`} className="is-mono">
                {hashPrefix(run.configuration_hash, 8)}
              </span>,
              <StateBadge key={`${run.run_id}-s`} state={run.status} />,
              run.readiness ? (
                <Badge
                  key={`${run.run_id}-r`}
                  tone={READINESS_TONES[run.readiness] ?? "unknown"}
                >
                  {run.readiness}
                </Badge>
              ) : (
                "—"
              ),
              formatScore(run.score),
              formatTimestamp(run.created_at),
              formatNumber(run.duration_ms, 0),
              formatNumber(run.warning_count, 0),
            ])}
          />
        </EvidenceGate>
      </Section>

      {selection.length < 2 ? (
        <p className="research-note">
          Select at least two runs to request a comparison.
        </p>
      ) : (
        <EvidenceGate
          loading={comparison.loading}
          error={comparison.error}
          reload={comparison.reload}
          ready={comparison.data !== null}
          loadingLabel="Requesting the server-derived comparison…"
        >
          {comparison.data ? (
            <>
              <Section
                title="Headline"
                description="Score, readiness, stage presence, warnings, and provenance."
              >
                <EvidenceTable
                  columns={[
                    "Run",
                    "Symbol",
                    "Status",
                    "Readiness",
                    "Score",
                    "Δ score",
                    "Stages",
                    "Warnings",
                    "Dataset hash",
                    "Config hash",
                  ]}
                  rows={comparison.data.entries.map((entry, index) => [
                    <span key={`${entry.run_id}-r`}>
                      {index === 0 ? "baseline · " : ""}
                      {(entry.run_id ?? "").slice(0, 12)}…
                    </span>,
                    entry.symbol ?? "—",
                    <StateBadge key={`${entry.run_id}-s`} state={entry.status ?? "unavailable"} />,
                    entry.readiness ? (
                      <Badge
                        key={`${entry.run_id}-rd`}
                        tone={READINESS_TONES[entry.readiness] ?? "unknown"}
                      >
                        {entry.readiness}
                      </Badge>
                    ) : (
                      "—"
                    ),
                    formatScore(entry.score),
                    <Badge
                      key={`${entry.run_id}-d`}
                      tone={deltaTone(entry.score_delta)}
                    >
                      {formatDelta(entry.score_delta, 1)}
                    </Badge>,
                    String(entry.stages.length),
                    String(entry.warning_count),
                    <span key={`${entry.run_id}-dh`} className="is-mono">
                      {hashPrefix(entry.dataset_hash, 8)}
                    </span>,
                    <span key={`${entry.run_id}-ch`} className="is-mono">
                      {hashPrefix(entry.configuration_hash, 8)}
                    </span>,
                  ])}
                />
              </Section>

              <Section
                title="Metric deltas"
                description="Every metric family the compared runs published, with its delta against the baseline."
              >
                <EvidenceTable
                  columns={[
                    "Metric",
                    ...comparison.data.entries.map(
                      (entry, index) =>
                        `${index === 0 ? "baseline " : ""}${(entry.run_id ?? "").slice(0, 8)}`
                    ),
                  ]}
                  emptyLabel="No comparable metrics were published."
                  rows={comparison.data.metric_names.map((name) => [
                    <code key={name}>{name}</code>,
                    ...comparison.data!.entries.map((entry, index) => (
                      <span key={`${name}-${index}`} className="is-mono">
                        {formatNumber(entry.metrics[name]?.value, 6)}
                        {index === 0 ? null : (
                          <>
                            {" "}
                            <Badge tone={deltaTone(entry.metrics[name]?.delta)}>
                              {formatDelta(entry.metrics[name]?.delta, 6)}
                            </Badge>
                          </>
                        )}
                      </span>
                    )),
                  ])}
                />
              </Section>

              <Section
                title="Study classification changes"
                description="A changed classification is flagged; unchanged ones are shown as-is."
              >
                <EvidenceTable
                  columns={[
                    "Study",
                    ...comparison.data.entries.map((entry) =>
                      (entry.run_id ?? "").slice(0, 8)
                    ),
                  ]}
                  emptyLabel="No studies were published by the compared runs."
                  rows={comparison.data.study_names.map((name) => [
                    <code key={name}>{name}</code>,
                    ...comparison.data!.entries.map((entry, index) => {
                      const study = entry.studies[name];
                      return (
                        <span key={`${name}-${index}`}>
                          <Badge
                            tone={
                              CLASSIFICATION_TONES[study?.classification ?? ""] ??
                              "unknown"
                            }
                          >
                            {study?.classification ?? "—"}
                          </Badge>
                          {index > 0 && study?.changed ? " changed" : ""}
                        </span>
                      );
                    }),
                  ])}
                />
              </Section>

              <Section
                title="Provenance differences"
                description="Seeds and dependency versions behind each compared run."
              >
                <EvidenceTable
                  columns={["Run", "Seeds", "Dependency versions", "Report id"]}
                  rows={comparison.data.entries.map((entry) => [
                    (entry.run_id ?? "").slice(0, 12) + "…",
                    <span key={`${entry.run_id}-sd`} className="is-mono">
                      {JSON.stringify(entry.seeds)}
                    </span>,
                    <span key={`${entry.run_id}-dv`} className="is-mono">
                      {JSON.stringify(entry.dependency_versions)}
                    </span>,
                    <span key={`${entry.run_id}-ri`} className="is-mono">
                      {entry.report_id ?? "—"}
                    </span>,
                  ])}
                />
              </Section>
            </>
          ) : null}
        </EvidenceGate>
      )}
    </div>
  );
}
