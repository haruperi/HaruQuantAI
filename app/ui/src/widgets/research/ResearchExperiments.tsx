/**
 * Experiment ledger and detail (FEAT-UI-28, plan §10.17).
 *
 * The experiment list and one experiment's run history. Failed, cancelled, and
 * inconclusive runs are listed alongside successful ones.
 */

"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { Badge, EvidenceTable, KeyValues, Section, StateBadge } from "./evidence";
import { EvidenceGate } from "./ResearchRunStatus";
import {
  READINESS_TONES,
  formatDuration,
  formatNumber,
  formatScore,
  formatTimestamp,
  hashPrefix,
} from "./research-selectors";
import { useExperiment, useExperiments } from "./use-research";

/** Every owned experiment. */
export function ResearchExperimentList(): ReactNode {
  const experiments = useExperiments();

  return (
    <div className="research-page">
      <header className="research-page__head">
        <p className="research-eyebrow">Research workbench</p>
        <h1>Experiments</h1>
        <div className="research-links">
          <Link className="research-button research-button--primary" href="/workstation/research/new">
            New experiment
          </Link>
          <Link className="research-button" href="/workstation/research">
            Back to ledger
          </Link>
        </div>
      </header>

      <EvidenceGate
        loading={experiments.loading}
        error={experiments.error}
        reload={experiments.reload}
        ready={experiments.data !== null}
        loadingLabel="Loading experiments…"
      >
        <Section
          title="Experiment ledger"
          description="One entry per research question."
        >
          <EvidenceTable
            columns={["Experiment", "Hypothesis", "Tags", "Runs", "Latest", "Created"]}
            emptyLabel="No experiments yet."
            rows={(experiments.data?.experiments ?? []).map((experiment) => [
              <Link
                key={experiment.experiment_id}
                href={`/workstation/research/experiments/${experiment.experiment_id}`}
              >
                {experiment.name}
              </Link>,
              experiment.hypothesis,
              experiment.tags.join(", ") || "—",
              formatNumber(experiment.run_count, 0),
              experiment.latest_run ? (
                <StateBadge
                  key={`${experiment.experiment_id}-s`}
                  state={experiment.latest_run.status}
                />
              ) : (
                "—"
              ),
              formatTimestamp(experiment.created_at),
            ])}
          />
        </Section>
      </EvidenceGate>
    </div>
  );
}

/** One experiment and its run history. */
export function ResearchExperimentDetailView({
  experimentId,
}: {
  experimentId: string;
}): ReactNode {
  const experiment = useExperiment(experimentId);

  return (
    <div className="research-page">
      <EvidenceGate
        loading={experiment.loading}
        error={experiment.error}
        reload={experiment.reload}
        ready={experiment.data !== null}
        loadingLabel="Loading the experiment…"
      >
        {experiment.data ? (
          <>
            <header className="research-page__head">
              <p className="research-eyebrow">Experiment</p>
              <h1>{experiment.data.name}</h1>
              <p>{experiment.data.hypothesis}</p>
              <div className="research-links">
                <Link
                  className="research-button research-button--primary"
                  href={`/workstation/research/new?experiment=${experimentId}`}
                >
                  Queue a run
                </Link>
                <Link className="research-button" href="/workstation/research/compare">
                  Compare runs
                </Link>
                <Link className="research-button" href="/workstation/research/experiments">
                  All experiments
                </Link>
              </div>
            </header>

            <Section title="Experiment" description="Identity and notes.">
              <KeyValues
                columns={4}
                items={[
                  ["Experiment id", experiment.data.experiment_id],
                  ["Created", formatTimestamp(experiment.data.created_at)],
                  ["Runs", formatNumber(experiment.data.run_count, 0)],
                  ["Tags", experiment.data.tags.join(", ") || "—"],
                  ["Notes", experiment.data.notes ?? "—"],
                ]}
              />
            </Section>

            <Section
              title="Run history"
              description="Every retained run for this experiment, newest first."
            >
              <EvidenceTable
                columns={[
                  "Run",
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
                emptyLabel="No runs yet for this experiment."
                rows={experiment.data.runs.map((run) => [
                  <Link
                    key={run.run_id}
                    href={`/workstation/research/experiments/${experimentId}/runs/${run.run_id}/overview`}
                  >
                    {run.run_id.slice(0, 14)}…
                  </Link>,
                  run.symbol,
                  run.timeframe,
                  <span key={`${run.run_id}-d`} className="is-mono">
                    {hashPrefix(run.dataset_hash, 8)}
                  </span>,
                  <span key={`${run.run_id}-c`} className="is-mono">
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
                  formatDuration(run.duration_ms),
                  formatNumber(run.warning_count, 0),
                ])}
              />
            </Section>
          </>
        ) : null}
      </EvidenceGate>
    </div>
  );
}
