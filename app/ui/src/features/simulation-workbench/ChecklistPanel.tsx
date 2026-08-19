/**
 * Checklist runtime panel (FEAT-UI-31).
 *
 * Renders the Simulator-owned checklist runtime for a practice session. Step
 * state is evaluated by the Simulator against actual evidence, so this panel
 * shows what the owner concluded and never marks a step satisfied itself.
 */

"use client";

import type { ReactNode } from "react";

/** One Simulator-owned checklist step runtime projection. */
export interface ChecklistStepEvidence {
  step_id: string;
  state: string;
  evidence?: boolean | number | string | null;
  reason?: string | null;
  mandatory?: boolean;
}

/** One Simulator-owned checklist runtime projection. */
export interface ChecklistEvidence {
  checklist_id: string;
  version: string;
  mode?: string;
  steps: readonly ChecklistStepEvidence[];
}

/** Exact text shown when no checklist evidence was supplied. */
export const NO_CHECKLIST_EVIDENCE =
  "No checklist evidence was supplied for this session.";

/** Props accepted by `ChecklistPanel`. */
export interface ChecklistPanelProps {
  checklist?: ChecklistEvidence | null;
  className?: string;
}

/** Owner-evaluated checklist steps for one practice session. */
export function ChecklistPanel({
  checklist = null,
  className = "",
}: ChecklistPanelProps): ReactNode {
  if (!checklist) {
    return (
      <section
        className={`simulation-checklist ${className}`.trim()}
        aria-label="Checklist evidence"
      >
        <h4>Checklist</h4>
        <p>{NO_CHECKLIST_EVIDENCE}</p>
      </section>
    );
  }

  return (
    <section
      className={`simulation-checklist ${className}`.trim()}
      aria-label="Checklist evidence"
    >
      <h4>Checklist</h4>
      <p className="simulation-checklist__note">
        {checklist.checklist_id} ({checklist.version})
        {checklist.mode ? ` · ${checklist.mode} mode` : ""}
      </p>

      <table className="simulation-scenario__table">
        <caption className="sr-only">Owner-evaluated checklist steps</caption>
        <thead>
          <tr>
            <th scope="col">Step</th>
            <th scope="col">State</th>
            <th scope="col">Mandatory</th>
            <th scope="col">Evidence</th>
            <th scope="col">Reason</th>
          </tr>
        </thead>
        <tbody>
          {checklist.steps.map((step) => (
            <tr key={step.step_id}>
              <td className="font-mono">{step.step_id}</td>
              <td>{step.state}</td>
              <td>{step.mandatory === false ? "no" : "yes"}</td>
              <td>
                {step.evidence === null || step.evidence === undefined
                  ? "—"
                  : String(step.evidence)}
              </td>
              <td>{step.reason ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
