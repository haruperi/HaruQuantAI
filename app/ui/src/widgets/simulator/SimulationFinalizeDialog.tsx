/**
 * Session finalization dialog (FEAT-UI-31).
 *
 * Finalization seals an advisory journal; it does not promote practice
 * evidence to canonical. The dialog says so plainly, and reproduction is
 * offered as a separate canonical job rather than as a relabelling of the
 * session the operator just sealed.
 */

"use client";

import { useCallback, useState, type ReactNode } from "react";

import {
  ApiClientError,
  apiClients,
  type LiveSessionProjection,
} from "@/clients";

/** Exact wording shown before a session is sealed. */
export const FINALIZE_ADVISORY_NOTICE =
  "Finalizing seals this session's advisory journal. It does not make the " +
  "session an official canonical run.";

/** Resolve a failure message without implying the session was sealed. */
function failureMessage(cause: unknown): string {
  if (cause instanceof ApiClientError || cause instanceof Error) {
    return cause.message;
  }
  return "The session could not be finalized.";
}

/** Props accepted by `SimulationFinalizeDialog`. */
export interface SimulationFinalizeDialogProps {
  sessionId: string;
  session: LiveSessionProjection | null;
  onSessionChanged?: (session: LiveSessionProjection) => void;
  onReproduced?: (job: Record<string, unknown>) => void;
  className?: string;
}

/** Advisory finalization and canonical reproduction controls. */
export function SimulationFinalizeDialog({
  sessionId,
  session,
  onSessionChanged,
  onReproduced,
  className = "",
}: SimulationFinalizeDialogProps): ReactNode {
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [job, setJob] = useState<Record<string, unknown> | null>(null);

  const finalized = Boolean(
    (session as { finalized?: boolean } | null)?.finalized,
  );

  const finalize = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const response =
        await apiClients.simulationWorkbench.finalizeLiveSession(sessionId);
      if (response.status === "error") {
        setError(response.error.message);
        return;
      }
      setConfirming(false);
      onSessionChanged?.(response.data);
    } catch (cause) {
      setError(failureMessage(cause));
    } finally {
      setBusy(false);
    }
  }, [sessionId, onSessionChanged]);

  const reproduce = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const response =
        await apiClients.simulationWorkbench.reproduceLiveSession(sessionId);
      if (response.status === "error") {
        setError(response.error.message);
        return;
      }
      setJob(response.data);
      onReproduced?.(response.data);
    } catch (cause) {
      setError(failureMessage(cause));
    } finally {
      setBusy(false);
    }
  }, [sessionId, onReproduced]);

  return (
    <section
      className={`simulation-finalize ${className}`.trim()}
      aria-label="Session finalization"
    >
      <h4>Finalize</h4>
      <p className="simulation-finalize__notice">{FINALIZE_ADVISORY_NOTICE}</p>

      {error ? <p role="alert">{error}</p> : null}

      {finalized ? (
        <>
          <p role="status">This session is finalized and sealed.</p>
          <button
            type="button"
            onClick={() => void reproduce()}
            disabled={busy}
          >
            Reproduce as canonical run
          </button>
          {job ? (
            <p role="status" className="font-mono">
              Canonical job: {String(job.job_id ?? job.run_id ?? "submitted")}
            </p>
          ) : null}
        </>
      ) : confirming ? (
        <div role="group" aria-label="Confirm finalization">
          <p>Seal this session? No further step, seek, or command is accepted.</p>
          <button type="button" onClick={() => void finalize()} disabled={busy}>
            Confirm finalize
          </button>
          <button
            type="button"
            onClick={() => setConfirming(false)}
            disabled={busy}
          >
            Cancel
          </button>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setConfirming(true)}
          disabled={!session || busy}
        >
          Finalize session
        </button>
      )}
    </section>
  );
}
