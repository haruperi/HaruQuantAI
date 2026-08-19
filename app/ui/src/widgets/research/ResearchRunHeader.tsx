/**
 * Persistent run header (FEAT-UI-28).
 *
 * Carries the run's identity, status, readiness, hashes, and permitted actions
 * across every stage. Every value shown is a field the API returned; the
 * advisory-only badge is always present because Research never issues an
 * instruction.
 */

"use client";

import Link from "next/link";
import { useState, type ReactNode } from "react";

import { ApiClientError, apiClients } from "@/clients";
import type { ResearchRunDetail } from "@/clients";

import { Badge, StateBadge } from "./evidence";
import {
  READINESS_TONES,
  formatDuration,
  formatScore,
  formatTimestamp,
  hashPrefix,
  isRunActive,
} from "./research-selectors";
import { useResearchStore } from "./research-store";

/** Props accepted by `ResearchRunHeader`. */
export interface ResearchRunHeaderProps {
  detail: ResearchRunDetail;
  experimentName?: string;
  onChanged?: () => void;
}

/** Persistent header shown on every run stage. */
export function ResearchRunHeader({
  detail,
  experimentName,
  onChanged,
}: ResearchRunHeaderProps): ReactNode {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const streamState = useResearchStore((state) => state.streamState);
  const toggleComparisonRun = useResearchStore(
    (state) => state.toggleComparisonRun
  );
  const selection = useResearchStore((state) => state.comparisonSelection);
  const active = isRunActive(detail.status);

  async function cancel(): Promise<void> {
    setBusy(true);
    setError(null);
    try {
      const response = await apiClients.research.cancelRun(detail.run_id);
      if (response.status === "error") setError(response.error.message);
      else onChanged?.();
    } catch (cause) {
      setError(cause instanceof ApiClientError ? cause.message : "unavailable");
    } finally {
      setBusy(false);
    }
  }

  return (
    <header className="research-run-header">
      <div className="research-run-header__identity">
        <p className="research-eyebrow">
          {experimentName ?? "Research run"} · {detail.preset}
        </p>
        <h2>
          {detail.symbol} · {detail.timeframe}
        </h2>
        <p className="research-run-header__hypothesis">{detail.hypothesis}</p>
      </div>

      <dl className="research-run-header__facts">
        <div>
          <dt>Status</dt>
          <dd>
            <StateBadge state={detail.status} />
          </dd>
        </div>
        <div>
          <dt>Readiness</dt>
          <dd>
            {detail.readiness ? (
              <Badge tone={READINESS_TONES[detail.readiness] ?? "unknown"}>
                {detail.readiness}
              </Badge>
            ) : (
              <Badge tone="unknown">Not scored</Badge>
            )}
          </dd>
        </div>
        <div>
          <dt>Score</dt>
          <dd className="is-mono">
            {formatScore(detail.score)}
          </dd>
        </div>
        <div>
          <dt>Run</dt>
          <dd className="is-mono" title={detail.run_id}>
            {hashPrefix(detail.run_id, 16)}
          </dd>
        </div>
        <div>
          <dt>Report</dt>
          <dd className="is-mono" title={detail.report_id ?? undefined}>
            {hashPrefix(detail.report_id, 16)}
          </dd>
        </div>
        <div>
          <dt>Dataset hash</dt>
          <dd className="is-mono" title={detail.dataset_hash ?? undefined}>
            {hashPrefix(detail.dataset_hash)}
          </dd>
        </div>
        <div>
          <dt>Config hash</dt>
          <dd className="is-mono" title={detail.configuration_hash ?? undefined}>
            {hashPrefix(detail.configuration_hash)}
          </dd>
        </div>
        <div>
          <dt>Generated</dt>
          <dd>{formatTimestamp(detail.generated_at)}</dd>
        </div>
        <div>
          <dt>Duration</dt>
          <dd>{formatDuration(detail.duration_ms)}</dd>
        </div>
        <div>
          <dt>Warnings</dt>
          <dd>
            <Badge tone={detail.warning_count > 0 ? "warning" : "positive"}>
              {detail.warning_count}
            </Badge>
          </dd>
        </div>
      </dl>

      <div className="research-run-header__actions">
        <Badge tone="warning" title="Research output is advisory only">
          Advisory only
        </Badge>
        {active ? (
          <Badge tone="neutral">stream: {streamState}</Badge>
        ) : null}
        <button
          type="button"
          className="research-button"
          onClick={() => toggleComparisonRun(detail.run_id)}
          aria-pressed={selection.includes(detail.run_id)}
        >
          {selection.includes(detail.run_id) ? "In comparison" : "Compare"}
        </button>
        <Link
          className="research-button"
          href={`/workstation/research/experiments/${detail.experiment_id}/runs/${detail.run_id}/artifacts`}
        >
          Artifacts
        </Link>
        <Link
          className="research-button"
          href={`/workstation/research/new?experiment=${detail.experiment_id}&symbol=${detail.symbol}&timeframe=${detail.timeframe}&preset=${detail.preset}`}
        >
          Rerun
        </Link>
        {active ? (
          <button
            type="button"
            className="research-button research-button--danger"
            onClick={() => void cancel()}
            disabled={busy}
          >
            Cancel
          </button>
        ) : null}
      </div>
      {error ? (
        <p className="research-error" role="alert">
          {error}
        </p>
      ) : null}
    </header>
  );
}
