/**
 * Session recovery panel (FEAT-UI-31).
 *
 * Implements restore, verify, and rearm as three separate steps. Rearm is
 * never implied by a successful restore: a reconstructed session stays
 * exposure-blocked until an operator looks at the integrity result and
 * approves it, and a failed integrity check disables rearm outright.
 */

"use client";

import { useCallback, useState, type ReactNode } from "react";

import {
  ApiClientError,
  apiClients,
  type LiveSessionProjection,
} from "@/clients";

/** Integrity states the owner reports for a reconstructed session. */
export const INTEGRITY_VERIFIED = "verified";

/** Resolve a failure message without implying the session was rearmed. */
function failureMessage(cause: unknown): string {
  if (cause instanceof ApiClientError || cause instanceof Error) {
    return cause.message;
  }
  return "The recovery operation could not be completed.";
}

/** Props accepted by `SimulationRecoveryPanel`. */
export interface SimulationRecoveryPanelProps {
  sessionId: string;
  session: LiveSessionProjection | null;
  onSessionChanged?: (session: LiveSessionProjection) => void;
  className?: string;
}

/** Restore, verify, and rearm controls for one durable session. */
export function SimulationRecoveryPanel({
  sessionId,
  session,
  onSessionChanged,
  className = "",
}: SimulationRecoveryPanelProps): ReactNode {
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const recovery = session?.recovery ?? null;
  const integrityStatus = recovery?.integrity_status ?? null;
  const verified = integrityStatus === INTEGRITY_VERIFIED;
  const restored = recovery?.status === "recovery_blocked";

  const run = useCallback(
    async (action: "restore" | "rearm") => {
      setBusy(true);
      setError(null);
      try {
        const response =
          action === "restore"
            ? await apiClients.simulationWorkbench.restoreLiveSession(sessionId)
            : await apiClients.simulationWorkbench.rearmLiveSession(
                sessionId,
                true,
              );
        if (response.status === "error") {
          setError(response.error.message);
          return;
        }
        onSessionChanged?.(response.data);
      } catch (cause) {
        setError(failureMessage(cause));
      } finally {
        setBusy(false);
      }
    },
    [sessionId, onSessionChanged],
  );

  return (
    <section
      className={`simulation-recovery ${className}`.trim()}
      aria-label="Session recovery"
    >
      <h4>Recovery</h4>

      <ol className="simulation-recovery__steps">
        <li>Restore the persisted session from its durable checkpoint.</li>
        <li>Verify the reconstructed state against its recorded digest.</li>
        <li>Rearm explicitly before the session may act on the market again.</li>
      </ol>

      <dl className="simulation-recovery__facts">
        <dt>Recovery status</dt>
        <dd>{recovery?.status ?? "healthy"}</dd>
        <dt>Integrity</dt>
        <dd>{integrityStatus ?? "not verified"}</dd>
        <dt>Persisted state hash</dt>
        <dd className="font-mono">{recovery?.persisted_state_hash ?? "—"}</dd>
        <dt>Recovery generation</dt>
        <dd>{recovery?.recovery_generation ?? "—"}</dd>
        <dt>Recovery run</dt>
        <dd className="font-mono">{recovery?.recovery_run_id ?? "—"}</dd>
        <dt>Last checkpoint</dt>
        <dd>{recovery?.last_checkpoint_at ?? "—"}</dd>
        <dt>Exposure</dt>
        <dd>{session?.exposure_blocked ? "blocked" : "permitted"}</dd>
      </dl>

      {error ? <p role="alert">{error}</p> : null}

      <div className="simulation-recovery__actions">
        <button
          type="button"
          onClick={() => void run("restore")}
          disabled={busy || !session}
        >
          Restore session
        </button>
        <button
          type="button"
          onClick={() => void run("rearm")}
          disabled={busy || !restored || !verified}
        >
          Rearm session
        </button>
      </div>

      {restored && !verified ? (
        <p role="note">
          Integrity verification did not succeed, so this session cannot be
          rearmed. Its recorded evidence remains readable.
        </p>
      ) : null}
    </section>
  );
}
