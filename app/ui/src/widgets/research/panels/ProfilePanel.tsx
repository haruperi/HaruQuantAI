/**
 * Profile & Scorecard panel (FEAT-UI-28, plan §10.13).
 *
 * Covers the V1 Scorecard using V2 readiness vocabulary. The browser renders
 * the score rows, readiness, and reasons Research published; it never rebuilds
 * the scorecard.
 */

"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import {
  Badge,
  ContributionBar,
  EvidenceTable,
  KeyValues,
  Section,
  WarningList,
} from "../evidence";
import {
  READINESS_TONES,
  asNumber,
  asText,
  evidenceBranch,
  evidenceRecord,
  formatNumber,
  formatScore,
  formatTimestamp,
} from "../research-selectors";
import type { PanelProps } from "./OverviewPanel";

/** Scorecard and profile snapshot. */
export function ProfilePanel({ detail, view }: PanelProps): ReactNode {
  const stage = evidenceBranch(view, "profiles");
  const scorecard =
    evidenceRecord(view.evidence as Record<string, unknown>, "scorecard") ?? stage;

  if (stage === null && !scorecard?.available) {
    return (
      <p className="research-note">
        The profiles stage did not run for this run, so Research published no
        scorecard.
      </p>
    );
  }

  const rows = ((scorecard?.score_rows ?? stage?.score_rows ?? []) as Array<
    Record<string, unknown>
  >) ?? [];
  const reasons = (scorecard?.reasons ?? stage?.reasons ?? []) as string[];
  const readiness = asText(scorecard?.readiness ?? stage?.readiness);
  const maxRow = Math.max(1, ...rows.map((row) => Math.abs(asNumber(row.score) ?? 0)));

  return (
    <div className="research-panel">
      <Section
        title="Readiness"
        description="The V2 readiness vocabulary: BLOCKED, REVIEW_READY, or INSUFFICIENT_EVIDENCE."
      >
        <KeyValues
          columns={4}
          items={[
            [
              "Final score",
              <span key="s" className="is-mono">
                {formatScore(scorecard?.score ?? stage?.score)}
              </span>,
            ],
            [
              "Readiness",
              readiness ? (
                <Badge key="r" tone={READINESS_TONES[readiness] ?? "unknown"}>
                  {readiness}
                </Badge>
              ) : (
                <Badge key="r" tone="unknown">
                  Not scored
                </Badge>
              ),
            ],
            ["Stages assembled", formatNumber(stage?.stage_count, 0)],
            [
              "Advisory only",
              <Badge key="a" tone="warning">
                yes
              </Badge>,
            ],
            [
              "Snapshot id",
              <span key="sn" className="is-mono">
                {asText(stage?.snapshot_id) ?? "—"}
              </span>,
            ],
            [
              "Snapshot generated",
              formatTimestamp(asText(stage?.snapshot_generated_at)),
            ],
            [
              "Report id",
              <span key="ri" className="is-mono">
                {detail.report_id ?? "—"}
              </span>,
            ],
            ["Schema", asText(stage?.schema_version) ?? "—"],
          ]}
        />
      </Section>

      <Section
        title="Score rows"
        description="Every criterion, its weight contribution, and its supporting counts."
      >
        <div className="research-bars">
          {rows.map((row, index) => (
            <ContributionBar
              key={asText(row.criterion) ?? index}
              label={asText(row.criterion) ?? `row ${index + 1}`}
              value={asNumber(row.score)}
              maximum={maxRow}
            />
          ))}
        </div>
        <EvidenceTable
          columns={["Criterion", "Score", "Supporting evidence"]}
          emptyLabel="No score rows were published."
          rows={rows.map((row, index) => [
            <code key={index}>{asText(row.criterion) ?? "—"}</code>,
            <span key={`${index}-s`} className="is-mono">
              {formatNumber(row.score, 2)}
            </span>,
            Object.entries(row)
              .filter(([key]) => key !== "criterion" && key !== "score")
              .map(([key, value]) => `${key}=${String(value)}`)
              .join(", ") || "—",
          ])}
        />
      </Section>

      <Section
        title="Reasons"
        description="The reasons Research attached to this readiness verdict."
      >
        {reasons.length === 0 ? (
          <p className="research-note">No reasons were published.</p>
        ) : (
          <ul className="research-reasons">
            {reasons.map((reason) => (
              <li key={reason}>
                <code>{reason}</code>
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section
        title="Compare and export"
        description="Comparison and artifacts are server-derived; nothing here is rebuilt in the browser."
      >
        <div className="research-links">
          <Link className="research-button" href="/workstation/research/compare">
            Compare runs
          </Link>
          <Link
            className="research-button"
            href={`/workstation/research/experiments/${detail.experiment_id}/runs/${detail.run_id}/artifacts`}
          >
            Artifacts
          </Link>
        </div>
      </Section>

      <Section title="Warnings" description="Warnings attached to the scorecard.">
        <WarningList warnings={view.warnings} />
      </Section>
    </div>
  );
}
