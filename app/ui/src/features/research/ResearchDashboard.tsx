/**
 * Research dashboard (FEAT-UI-28, plan §10.1).
 *
 * The workbench entry point and research ledger — the V2 realization of V1's
 * "Discovery" placeholder. It deliberately shows failed, contradicted, and
 * inconclusive results alongside successful ones: a ledger that hides negative
 * evidence is not a ledger.
 */

"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { Badge, EvidenceTable, KeyValues, Section, StateBadge } from "./evidence";
import { EvidenceGate } from "./ResearchRunStatus";
import {
  CLASSIFICATION_TONES,
  READINESS_TONES,
  formatNumber,
  formatScore,
  formatTimestamp,
} from "./research-selectors";
import { useDashboard } from "./use-research";

/** Research ledger and entry point. */
export function ResearchDashboard(): ReactNode {
  const dashboard = useDashboard();

  return (
    <div className="research-page">
      <header className="research-page__head">
        <p className="research-eyebrow">Research workbench</p>
        <h1>Research</h1>
        <p>
          Experiments, runs, and the evidence behind them. Every conclusion on
          this page is a Research-owned field.
        </p>
        <div className="research-links">
          <Link className="research-button research-button--primary" href="/workstation/research/new">
            New experiment
          </Link>
          <Link className="research-button" href="/workstation/research/experiments">
            All experiments
          </Link>
          <Link className="research-button" href="/workstation/research/automation">
            Run batch
          </Link>
          <Link className="research-button" href="/workstation/research/compare">
            Compare runs
          </Link>
          <Link className="research-button" href="/workstation/research/expectancy">
            Expectancy
          </Link>
          <Link className="research-button" href="/workstation/research/drift">
            Drift monitor
          </Link>
        </div>
      </header>

      <EvidenceGate
        loading={dashboard.loading}
        error={dashboard.error}
        reload={dashboard.reload}
        ready={dashboard.data !== null}
        loadingLabel="Loading the research ledger…"
      >
        {dashboard.data ? (
          <>
            <Section
              title="Evidence distribution"
              description="Across every retained run, including failures and inconclusive outcomes."
            >
              <div className="research-count-row">
                {Object.entries(dashboard.data.status_distribution).map(
                  ([status, count]) => (
                    <div key={status} className="research-count">
                      <StateBadge state={status} />
                      <strong>{count}</strong>
                    </div>
                  )
                )}
              </div>
              <div className="research-count-row">
                {Object.entries(dashboard.data.readiness_distribution).map(
                  ([readiness, count]) => (
                    <div key={readiness} className="research-count">
                      <Badge tone={READINESS_TONES[readiness] ?? "unknown"}>
                        {readiness}
                      </Badge>
                      <strong>{count}</strong>
                    </div>
                  )
                )}
              </div>
              <div className="research-count-row">
                {(["confirmed", "contradicted", "inconclusive"] as const).map(
                  (key) => (
                    <div key={key} className="research-count">
                      <Badge tone={CLASSIFICATION_TONES[key]}>{key} studies</Badge>
                      <strong>{dashboard.data?.study_counts[key] ?? 0}</strong>
                    </div>
                  )
                )}
                <div className="research-count">
                  <Badge
                    tone={dashboard.data.warning_total > 0 ? "warning" : "positive"}
                  >
                    warnings
                  </Badge>
                  <strong>{dashboard.data.warning_total}</strong>
                </div>
              </div>
            </Section>

            <Section
              title="Experiments"
              description="Each experiment is one research question and its run ledger."
            >
              <EvidenceTable
                columns={[
                  "Experiment",
                  "Hypothesis",
                  "Runs",
                  "Latest run",
                  "Readiness",
                  "Created",
                ]}
                emptyLabel="No experiments yet. Start one from New experiment."
                rows={dashboard.data.experiments.map((experiment) => [
                  <Link
                    key={experiment.experiment_id}
                    href={`/workstation/research/experiments/${experiment.experiment_id}`}
                  >
                    {experiment.name}
                  </Link>,
                  experiment.hypothesis,
                  formatNumber(experiment.run_count, 0),
                  experiment.latest_run ? (
                    <StateBadge
                      key={`${experiment.experiment_id}-s`}
                      state={experiment.latest_run.status}
                    />
                  ) : (
                    "—"
                  ),
                  experiment.latest_run?.readiness ? (
                    <Badge
                      key={`${experiment.experiment_id}-r`}
                      tone={
                        READINESS_TONES[experiment.latest_run.readiness] ?? "unknown"
                      }
                    >
                      {experiment.latest_run.readiness}
                    </Badge>
                  ) : (
                    "—"
                  ),
                  formatTimestamp(experiment.created_at),
                ])}
              />
            </Section>

            <Section
              title="Recent runs"
              description="Newest first. Failed and cancelled runs stay discoverable."
            >
              <EvidenceTable
                columns={[
                  "Run",
                  "Symbol",
                  "Timeframe",
                  "Status",
                  "Readiness",
                  "Score",
                  "Warnings",
                  "Created",
                ]}
                emptyLabel="No runs yet."
                rows={dashboard.data.recent_runs.map((run) => [
                  <Link
                    key={run.run_id}
                    href={`/workstation/research/experiments/${run.experiment_id}/runs/${run.run_id}/overview`}
                  >
                    {run.run_id.slice(0, 16)}…
                  </Link>,
                  run.symbol,
                  run.timeframe,
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
                  formatNumber(run.warning_count, 0),
                  formatTimestamp(run.created_at),
                ])}
              />
            </Section>

            <Section
              title="Advisory status"
              description="Research output never carries execution authority."
            >
              <KeyValues
                columns={2}
                items={[
                  [
                    "Advisory only",
                    <Badge key="a" tone="warning">
                      {dashboard.data.advisory_only ? "yes" : "no"}
                    </Badge>,
                  ],
                  [
                    "Owner",
                    "Research owns every score, classification, and readiness verdict shown here.",
                  ],
                ]}
              />
            </Section>
          </>
        ) : null}
      </EvidenceGate>
    </div>
  );
}
