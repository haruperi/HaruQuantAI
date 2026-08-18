/**
 * Run status and evidence-state surfaces (FEAT-UI-28).
 *
 * Renders the explicit lifecycle of a run and of one stage load. Loading,
 * empty, unavailable, and failure are distinct states here on purpose — none
 * of them is collapsed into a generic "no data".
 */

"use client";

import type { ReactNode } from "react";

import type { ResearchRunDetail } from "@/clients";

import { EvidenceState, StateBadge } from "./evidence";
import { formatTimestamp } from "./research-selectors";
import { useResearchStore } from "./research-store";

/** Inline spinner-free loading state. */
export function LoadingEvidence({ label }: { label: string }): ReactNode {
  return (
    <div className="research-empty" role="status" aria-live="polite">
      <StateBadge state="running" />
      <p>{label}</p>
    </div>
  );
}

/** Transport or authorization failure surface. */
export function ErrorEvidence({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}): ReactNode {
  return (
    <div className="research-empty research-empty--error" role="alert">
      <StateBadge state="failed" />
      <p>{message}</p>
      {onRetry ? (
        <button type="button" className="research-button" onClick={onRetry}>
          Retry
        </button>
      ) : null}
    </div>
  );
}

/**
 * Resolve one asynchronous evidence load into exactly one surface.
 *
 * This keeps every panel from re-implementing the same four branches, and
 * guarantees a stage state is never silently swallowed.
 */
export function EvidenceGate({
  loading,
  error,
  reload,
  state,
  reason,
  ready,
  loadingLabel,
  children,
}: {
  loading: boolean;
  error: string | null;
  reload?: () => void;
  state?: string;
  reason?: string | null;
  ready: boolean;
  loadingLabel: string;
  children: ReactNode;
}): ReactNode {
  if (loading) return <LoadingEvidence label={loadingLabel} />;
  if (error) return <ErrorEvidence message={error} onRetry={reload} />;
  if (!ready) {
    return <EvidenceState state={state ?? "unavailable"} reason={reason} />;
  }
  return <>{children}</>;
}

/** Live status strip shown above a running run's stages. */
export function ResearchRunStatus({
  detail,
}: {
  detail: ResearchRunDetail;
}): ReactNode {
  const streamState = useResearchStore((state) => state.streamState);
  const cursor = useResearchStore((state) => state.streamCursor);
  const terminal =
    detail.status === "completed" ||
    detail.status === "failed" ||
    detail.status === "cancelled";

  return (
    <div className="research-run-status" role="status" aria-live="polite">
      <StateBadge state={detail.status} />
      <span>
        Queued {formatTimestamp(detail.created_at)} · Started{" "}
        {formatTimestamp(detail.started_at)} · Finished{" "}
        {formatTimestamp(detail.completed_at)}
      </span>
      {terminal ? null : (
        <span className="research-run-status__stream">
          progress stream: {streamState} (event {cursor})
        </span>
      )}
      {detail.error ? (
        <span className="research-error">
          {detail.error.code}: {detail.error.message}
        </span>
      ) : null}
    </div>
  );
}
