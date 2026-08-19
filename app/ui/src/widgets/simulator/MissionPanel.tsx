/**
 * Mission outcome panel (FEAT-UI-31).
 *
 * Renders the Simulator-owned mission completion result and the qualification
 * links it unlocks. A mission passes because the Simulator evaluated it as
 * passed; nothing here infers completion from a satisfied step count.
 */

"use client";

import type { ReactNode } from "react";
import Link from "next/link";

/** One qualification a completed mission points to. */
export interface QualificationLink {
  qualification_id: string;
  label: string;
  href: string;
}

/** One Simulator-owned mission outcome projection. */
export interface MissionOutcomeEvidence {
  status: "PASSED" | "FAILED" | "INCOMPLETE";
  reason: string;
  safe_stand_down: boolean;
  satisfied_steps: number;
  required_steps: number;
  qualifications?: readonly QualificationLink[];
}

/** Exact text shown when no mission outcome was supplied. */
export const NO_MISSION_OUTCOME =
  "No mission outcome was supplied for this session.";

/** Props accepted by `MissionPanel`. */
export interface MissionPanelProps {
  outcome?: MissionOutcomeEvidence | null;
  className?: string;
}

/** Owner mission completion and qualification links. */
export function MissionPanel({
  outcome = null,
  className = "",
}: MissionPanelProps): ReactNode {
  if (!outcome) {
    return (
      <section
        className={`simulation-mission ${className}`.trim()}
        aria-label="Mission outcome"
      >
        <h4>Mission</h4>
        <p>{NO_MISSION_OUTCOME}</p>
      </section>
    );
  }

  return (
    <section
      className={`simulation-mission ${className}`.trim()}
      aria-label="Mission outcome"
    >
      <h4>Mission</h4>

      <dl className="simulation-scenario__facts">
        <dt>Status</dt>
        <dd>{outcome.status}</dd>
        <dt>Reason</dt>
        <dd>{outcome.reason}</dd>
        <dt>Safe stand-down</dt>
        <dd>{outcome.safe_stand_down ? "yes" : "no"}</dd>
        <dt>Steps satisfied</dt>
        <dd>
          {outcome.satisfied_steps} of {outcome.required_steps}
        </dd>
      </dl>

      <h5>Qualifications</h5>
      {outcome.status === "PASSED" &&
      outcome.qualifications &&
      outcome.qualifications.length > 0 ? (
        <ul>
          {outcome.qualifications.map((qualification) => (
            <li key={qualification.qualification_id}>
              <Link href={qualification.href}>{qualification.label}</Link>
            </li>
          ))}
        </ul>
      ) : (
        <p>
          {outcome.status === "PASSED"
            ? "This mission unlocked no qualification."
            : "Qualifications are listed only once the owner records a pass."}
        </p>
      )}
    </section>
  );
}
