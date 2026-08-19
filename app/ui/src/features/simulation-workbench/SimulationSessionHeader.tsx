/**
 * Interactive session header (FEAT-UI-31).
 *
 * Shows the authoritative cursor, timestamp, dataset identity, and evidence
 * class for one live session, plus the pacing controls. Every value shown is
 * the server's: the header renders the cursor the session reported and never
 * a locally predicted one.
 */

"use client";

import type { ReactNode } from "react";

import type { LiveSessionProjection } from "@/clients";
import { SimulationStatusBadge } from "./SimulationStatusBadge";

/** Props accepted by `SimulationSessionHeader`. */
export interface SimulationSessionHeaderProps {
  session: LiveSessionProjection | null;
  playing: boolean;
  busy?: boolean;
  onPlay: () => void;
  onPause: () => void;
  onStep: (ticks: number) => void;
  onSeek: (targetCursor: number) => void;
  className?: string;
}

/** Bounded step sizes offered by the pacing controls. */
export const STEP_SIZES: readonly number[] = [1, 10, 100];

/** Authoritative session identity, pacing state, and controls. */
export function SimulationSessionHeader({
  session,
  playing,
  busy = false,
  onPlay,
  onPause,
  onStep,
  onSeek,
  className = "",
}: SimulationSessionHeaderProps): ReactNode {
  const finalized = Boolean(
    (session as { finalized?: boolean } | null)?.finalized,
  );
  const blocked = Boolean(session?.exposure_blocked) || finalized;

  return (
    <header
      className={`simulation-session-header ${className}`.trim()}
      aria-label="Simulation session header"
    >
      <div className="simulation-session-header__identity">
        <h3>Interactive session</h3>
        <SimulationStatusBadge
          status={session?.completed ? "completed" : "running"}
          evidenceClass={session?.evidence_class ?? "practice"}
        />
        <span className="simulation-session-header__mode">
          {session?.mode ?? "unknown mode"}
        </span>
      </div>

      <dl className="simulation-session-header__facts">
        <dt>Cursor</dt>
        <dd>
          {session ? `${session.cursor} of ${session.tick_count}` : "—"}
        </dd>
        <dt>Timestamp</dt>
        <dd>{session?.timestamp ?? "—"}</dd>
        <dt>Dataset</dt>
        <dd className="font-mono">
          {session?.dataset?.dataset_id ?? "—"}
          {session?.dataset?.revision ? ` @ ${session.dataset.revision}` : ""}
        </dd>
        <dt>State freshness</dt>
        <dd>{session?.state_freshness ?? "unknown"}</dd>
      </dl>

      <div className="simulation-session-header__controls">
        <button
          type="button"
          onClick={playing ? onPause : onPlay}
          disabled={!session || blocked || Boolean(session?.completed)}
        >
          {playing ? "Pause" : "Play"}
        </button>
        {STEP_SIZES.map((size) => (
          <button
            key={size}
            type="button"
            onClick={() => onStep(size)}
            disabled={!session || playing || busy || blocked || session.completed}
          >
            Step {size}
          </button>
        ))}
        <button
          type="button"
          onClick={() => session && onSeek(session.tick_count)}
          disabled={!session || playing || busy || blocked || session.completed}
        >
          Seek to end
        </button>
      </div>

      {blocked ? (
        <p role="note" className="simulation-session-header__blocked">
          {finalized
            ? "This session is finalized and accepts no further advance."
            : "Exposure is blocked until this session is explicitly rearmed."}
        </p>
      ) : null}
    </header>
  );
}
