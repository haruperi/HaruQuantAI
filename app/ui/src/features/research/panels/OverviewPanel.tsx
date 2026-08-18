/**
 * Overview panel (FEAT-UI-28, plan §10.4).
 *
 * Composes the run's headline evidence from Research-owned fields only. The
 * "next action" wording is derived from explicit server statuses — it is never
 * a trading instruction and never an invented recommendation.
 */

"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import type { ResearchRunDetail, ResearchStageView } from "@/clients";

import {
  Badge,
  ContributionBar,
  EvidenceTable,
  KeyValues,
  Section,
  WarningList,
} from "../evidence";
import {
  CLASSIFICATION_TONES,
  READINESS_TONES,
  asNumber,
  asText,
  formatNumber,
  formatScore,
} from "../research-selectors";

/** Props accepted by every stage panel. */
export interface PanelProps {
  detail: ResearchRunDetail;
  view: ResearchStageView;
}

/** Deterministic next-step wording derived from explicit server statuses. */
function nextAction(detail: ResearchRunDetail): string {
  if (detail.status === "failed") {
    return "This run failed. Review the error and provenance, then queue a new run.";
  }
  if (detail.status === "cancelled") {
    return "This run was cancelled. Queue a new run to gather evidence.";
  }
  if (detail.status !== "completed") {
    return "The run is still in flight. Evidence appears as each stage completes.";
  }
  if (!detail.readiness) {
    return "No scorecard stage ran, so Research published no readiness verdict.";
  }
  if (detail.readiness === "REVIEW_READY") {
    return "Research reports review-ready evidence. A human review decides what happens next.";
  }
  if (detail.readiness === "INSUFFICIENT_EVIDENCE") {
    return "Research reports insufficient evidence. Widen the dataset or select more stages.";
  }
  return "Research reports blocked readiness. Resolve the listed reasons before rerunning.";
}

/** Run overview. */
export function OverviewPanel({ detail, view }: PanelProps): ReactNode {
  const overview = detail.overview;
  const scorecard = overview.scorecard;
  const counts = overview.study_counts;
  const structure = overview.structure ?? null;
  const rows = (scorecard?.score_rows ?? []) as Array<Record<string, unknown>>;
  const maxRow = Math.max(
    1,
    ...rows.map((row) => Math.abs(asNumber(row.score) ?? 0))
  );

  return (
    <div className="research-panel">
      <Section
        title="Hypothesis"
        description="The explicit question this run was queued to test."
      >
        <p className="research-hypothesis">{overview.hypothesis ?? detail.hypothesis}</p>
        <KeyValues
          columns={4}
          items={[
            ["Symbol", detail.symbol],
            ["Timeframe", detail.timeframe],
            ["Preset", detail.preset],
            ["Run reason", detail.reason ?? "—"],
            [
              "Selected stages",
              (overview.selected_stages ?? detail.selected_stages).join(", "),
            ],
            ["Advisory only", <Badge key="a" tone="warning">yes</Badge>],
          ]}
        />
      </Section>

      <Section
        title="Readiness"
        description="Score, readiness, and score rows exactly as Research published them."
      >
        <KeyValues
          columns={3}
          items={[
            [
              "Final score",
              <span key="s" className="is-mono">
                {formatScore(scorecard?.score ?? detail.score)}
              </span>,
            ],
            [
              "Readiness",
              detail.readiness ? (
                <Badge key="r" tone={READINESS_TONES[detail.readiness] ?? "unknown"}>
                  {detail.readiness}
                </Badge>
              ) : (
                <Badge key="r" tone="unknown">
                  Not scored
                </Badge>
              ),
            ],
            [
              "Snapshot",
              <span key="sn" className="is-mono">
                {asText(scorecard?.snapshot_id) ?? "—"}
              </span>,
            ],
          ]}
        />
        {rows.length > 0 ? (
          <div className="research-bars">
            {rows.map((row, index) => (
              <ContributionBar
                key={`${asText(row.criterion) ?? index}`}
                label={asText(row.criterion) ?? `row ${index + 1}`}
                value={asNumber(row.score)}
                maximum={maxRow}
              />
            ))}
          </div>
        ) : (
          <p className="research-note">
            No scorecard stage ran, so Research published no score rows.
          </p>
        )}
        <ul className="research-reasons">
          {(scorecard?.reasons ?? []).map((reason) => (
            <li key={reason}>
              <code>{reason}</code>
            </li>
          ))}
        </ul>
      </Section>

      <Section
        title="Study outcomes"
        description="Counts of confirmed, contradicted, and inconclusive studies. Negative evidence is shown, not hidden."
      >
        <div className="research-count-row">
          {(["confirmed", "contradicted", "inconclusive"] as const).map((key) => (
            <div key={key} className="research-count">
              <Badge tone={CLASSIFICATION_TONES[key]}>{key}</Badge>
              <strong>{counts ? counts[key] : 0}</strong>
            </div>
          ))}
        </div>
      </Section>

      <Section
        title="Market structure and sessions"
        description="Advisory structure verdict and the session evidence Research published."
      >
        <KeyValues
          columns={3}
          items={[
            [
              "Structure verdict",
              structure?.verdict ? (
                <Badge key="v" tone="neutral">
                  {structure.verdict}
                </Badge>
              ) : (
                "—"
              ),
            ],
            [
              "Structure score",
              <span key="ss" className="is-mono">
                {formatScore(structure?.score)}
              </span>,
            ],
            [
              "Strategy fit (advisory)",
              asText(
                (structure?.strategy_fit as Record<string, unknown> | undefined)?.[
                  "primary_archetype"
                ]
              ) ?? "—",
            ],
          ]}
        />
        <EvidenceTable
          columns={["Session", "Samples", "Mean return", "Win rate"]}
          emptyLabel="No session evidence was published for this run."
          rows={(overview.sessions ?? []).map((row) => {
            const item = row as Record<string, unknown>;
            return [
              asText(item.session) ?? "—",
              formatNumber(item.sample_count, 0),
              formatNumber(item.mean_return, 6),
              formatNumber(item.win_rate, 3),
            ];
          })}
        />
      </Section>

      <Section
        title="Warnings"
        description="Grouped by the severity Research assigned."
      >
        <WarningList warnings={view.warnings.length ? view.warnings : detail.warnings} />
      </Section>

      <Section
        title="Next step"
        description="Derived from the run status and the readiness Research reported."
      >
        <p className="research-note">{nextAction(detail)}</p>
        <div className="research-links">
          <Link
            className="research-button"
            href={`/workstation/research/experiments/${detail.experiment_id}/runs/${detail.run_id}/provenance`}
          >
            Provenance
          </Link>
          <Link className="research-button" href="/workstation/simulator">
            Continue in Simulator
          </Link>
          <Link className="research-button" href="/workstation/optimization/monte-carlo">
            Open Monte Carlo
          </Link>
          <Link className="research-button" href="/workstation/strategies/import/sqx">
            Open Strategy Import
          </Link>
        </div>
      </Section>
    </div>
  );
}
