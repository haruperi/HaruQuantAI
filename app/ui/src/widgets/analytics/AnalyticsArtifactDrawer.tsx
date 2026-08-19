/**
 * Analytics artifact drawer (FEAT-UI-32).
 *
 * Lists the immutable artifact references recorded for one run, plus the
 * journal replay anchors. Artifacts are referenced, never deleted, and never
 * rewritten by this view.
 */

"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";
import Link from "next/link";

import {
  ApiClientError,
  apiClients,
  type ArtifactInventory,
  type ReplayAnchorsPayload,
} from "@/clients";
import { buildReplayHref } from "./TradeDetailPanel";

/** Resolve a failure message without implying a successful read. */
function failureMessage(cause: unknown): string {
  if (cause instanceof ApiClientError || cause instanceof Error) {
    return cause.message;
  }
  return "The run artifact inventory is unavailable.";
}

/** Props accepted by `AnalyticsArtifactDrawer`. */
export interface AnalyticsArtifactDrawerProps {
  runId: string;
  className?: string;
}

/** Immutable artifact references and replay anchors for one run. */
export function AnalyticsArtifactDrawer({
  runId,
  className = "",
}: AnalyticsArtifactDrawerProps): ReactNode {
  const [inventory, setInventory] = useState<ArtifactInventory | null>(null);
  const [anchors, setAnchors] = useState<ReplayAnchorsPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [artifactResponse, anchorResponse] = await Promise.all([
        apiClients.analyticsWorkbench.getArtifacts(runId),
        apiClients.analyticsWorkbench.getReplayAnchors(runId),
      ]);
      if (artifactResponse.status === "error") {
        setError(artifactResponse.error.message);
        return;
      }
      setInventory(artifactResponse.data);
      if (anchorResponse.status === "success") {
        setAnchors(anchorResponse.data);
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

  return (
    <section
      className={`analytics-artifacts ${className}`.trim()}
      aria-label="Run artifacts"
    >
      <h3>Artifacts</h3>
      <p className="analytics-artifacts__note">
        Artifact references are immutable owner records. This view reads them
        and never deletes or rewrites one.
      </p>

      {loading ? <p role="status">Loading artifact inventory…</p> : null}
      {error ? <p role="alert">{error}</p> : null}

      {inventory ? (
        inventory.artifacts.length > 0 ? (
          <ul className="analytics-artifacts__list">
            {inventory.artifacts.map((artifact) => (
              <li key={`${artifact.kind}:${artifact.ref}`}>
                <span className="analytics-artifacts__kind">{artifact.kind}</span>
                <span className="font-mono">{artifact.ref}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p>No artifact reference is recorded for this run.</p>
        )
      ) : null}

      {anchors ? (
        <>
          <h4>Replay anchors</h4>
          {anchors.anchors.length > 0 ? (
            <ul className="analytics-artifacts__anchors">
              {anchors.anchors.map((anchor) => (
                <li key={anchor.ticket}>
                  <Link href={buildReplayHref(runId, anchor.ticket)}>
                    Ticket {anchor.ticket}
                  </Link>
                  {anchor.exit_time ? <span> · {anchor.exit_time}</span> : null}
                </li>
              ))}
            </ul>
          ) : (
            <p>No replay anchor is recorded for this run.</p>
          )}
        </>
      ) : null}
    </section>
  );
}
