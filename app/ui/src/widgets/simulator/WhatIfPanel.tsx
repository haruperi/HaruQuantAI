/**
 * What-if branch panel (FEAT-UI-31).
 *
 * Forks one session into an advisory branch. The branch is a separate session
 * with its own identity and its own journal: this panel never suggests the
 * parent changed, and it never presents branch evidence as canonical.
 */

"use client";

import { useCallback, useState, type ReactNode } from "react";

import {
  ApiClientError,
  apiClients,
  type LiveSessionProjection,
} from "@/clients";

/** Resolve a failure message without implying the branch was created. */
function failureMessage(cause: unknown): string {
  if (cause instanceof ApiClientError || cause instanceof Error) {
    return cause.message;
  }
  return "The what-if branch could not be created.";
}

/** Parse operator override text into a bounded mapping. */
export function parseOverrides(text: string): Record<string, string> {
  const overrides: Record<string, string> = {};
  for (const line of text.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    const separator = trimmed.indexOf("=");
    if (separator <= 0) continue;
    const key = trimmed.slice(0, separator).trim();
    const value = trimmed.slice(separator + 1).trim();
    if (key) overrides[key] = value;
  }
  return overrides;
}

/** Props accepted by `WhatIfPanel`. */
export interface WhatIfPanelProps {
  sessionId: string;
  session: LiveSessionProjection | null;
  onBranchCreated?: (branch: LiveSessionProjection) => void;
  className?: string;
}

/** Advisory branch controls for one interactive session. */
export function WhatIfPanel({
  sessionId,
  session,
  onBranchCreated,
  className = "",
}: WhatIfPanelProps): ReactNode {
  const [overrideText, setOverrideText] = useState("");
  const [name, setName] = useState("");
  const [branch, setBranch] = useState<LiveSessionProjection | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const createBranch = useCallback(async () => {
    if (creating) return;
    setCreating(true);
    setError(null);
    try {
      const response = await apiClients.simulationWorkbench.branchLiveSession(
        sessionId,
        {
          overrides: parseOverrides(overrideText),
          ...(name.trim() ? { name: name.trim() } : {}),
        },
      );
      if (response.status === "error") {
        setError(response.error.message);
        return;
      }
      setBranch(response.data);
      onBranchCreated?.(response.data);
    } catch (cause) {
      setError(failureMessage(cause));
    } finally {
      setCreating(false);
    }
  }, [creating, sessionId, overrideText, name, onBranchCreated]);

  return (
    <section
      className={`simulation-whatif ${className}`.trim()}
      aria-label="What-if branch panel"
    >
      <h4>What-if branch</h4>
      <p className="simulation-whatif__note">
        A branch replays this session&apos;s inputs to the current cursor and
        continues under your overrides. The parent session is never modified,
        and branch evidence stays advisory.
      </p>

      <p>
        Divergence cursor: {session ? session.cursor : "—"}
      </p>

      <label htmlFor="whatif-name">Branch name</label>
      <input
        id="whatif-name"
        value={name}
        onChange={(event) => setName(event.target.value)}
      />

      <label htmlFor="whatif-overrides">Overrides</label>
      <textarea
        id="whatif-overrides"
        value={overrideText}
        onChange={(event) => setOverrideText(event.target.value)}
        placeholder="one key=value per line"
      />

      <button
        type="button"
        onClick={() => void createBranch()}
        disabled={!session || creating}
      >
        {creating ? "Branching…" : "Create branch"}
      </button>

      {error ? <p role="alert">{error}</p> : null}

      {branch ? (
        <dl className="simulation-whatif__result" aria-label="Branch result">
          <dt>Branch session</dt>
          <dd className="font-mono">{branch.session_id}</dd>
          <dt>Parent session</dt>
          <dd className="font-mono">
            {branch.branch?.parent_session_id ?? sessionId}
          </dd>
          <dt>Divergence cursor</dt>
          <dd>{branch.branch?.divergence_cursor ?? branch.cursor}</dd>
          <dt>Evidence class</dt>
          <dd>{branch.evidence_class}</dd>
        </dl>
      ) : null}
    </section>
  );
}
