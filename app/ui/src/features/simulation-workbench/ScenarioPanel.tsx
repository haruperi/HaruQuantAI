/**
 * Scenario evidence panel (FEAT-UI-31).
 *
 * Renders the Simulator-owned scenario catalogue, its injected fault events,
 * and the emergency steps attached to a practice session. Every value is
 * owner-supplied; this panel triggers no fault, schedules no event, and
 * decides no outcome.
 */

"use client";

import type { ReactNode } from "react";

/** One Simulator-owned injected scenario event. */
export interface ScenarioEvent {
  event_id: string;
  event_type: string;
  priority: number;
  effective_at?: string;
  perceived_at?: string;
  suspends_normal_transitions?: boolean;
}

/** One Simulator-owned scenario or mission definition projection. */
export interface ScenarioEvidence {
  mission_id: string;
  version: string;
  difficulty?: number;
  seed?: number;
  market_data_ref?: string;
  competence_tags?: readonly string[];
  triggers?: readonly Record<string, unknown>[];
  events?: readonly ScenarioEvent[];
  emergency_steps?: readonly string[];
  assistance_mode?: string;
}

/** Exact text shown when no scenario evidence was supplied. */
export const NO_SCENARIO_EVIDENCE =
  "No scenario evidence was supplied for this session.";

/** Props accepted by `ScenarioPanel`. */
export interface ScenarioPanelProps {
  scenario?: ScenarioEvidence | null;
  className?: string;
}

/** Owner scenario catalogue, faults, and emergency steps. */
export function ScenarioPanel({
  scenario = null,
  className = "",
}: ScenarioPanelProps): ReactNode {
  if (!scenario) {
    return (
      <section
        className={`simulation-scenario ${className}`.trim()}
        aria-label="Scenario evidence"
      >
        <h4>Scenario</h4>
        <p>{NO_SCENARIO_EVIDENCE}</p>
      </section>
    );
  }

  return (
    <section
      className={`simulation-scenario ${className}`.trim()}
      aria-label="Scenario evidence"
    >
      <h4>Scenario</h4>

      <dl className="simulation-scenario__facts">
        <dt>Mission</dt>
        <dd className="font-mono">
          {scenario.mission_id} ({scenario.version})
        </dd>
        <dt>Difficulty</dt>
        <dd>{scenario.difficulty ?? "—"}</dd>
        <dt>Seed</dt>
        <dd className="font-mono">{scenario.seed ?? "—"}</dd>
        <dt>Market data</dt>
        <dd className="font-mono">{scenario.market_data_ref ?? "—"}</dd>
        <dt>Assistance mode</dt>
        <dd>{scenario.assistance_mode ?? "—"}</dd>
        <dt>Competence tags</dt>
        <dd>
          {scenario.competence_tags && scenario.competence_tags.length > 0
            ? scenario.competence_tags.join(", ")
            : "—"}
        </dd>
      </dl>

      <h5>Fault profile</h5>
      {scenario.events && scenario.events.length > 0 ? (
        <table className="simulation-scenario__table">
          <caption className="sr-only">Injected scenario events</caption>
          <thead>
            <tr>
              <th scope="col">Event</th>
              <th scope="col">Type</th>
              <th scope="col">Priority</th>
              <th scope="col">Effective at</th>
              <th scope="col">Suspends transitions</th>
            </tr>
          </thead>
          <tbody>
            {scenario.events.map((event) => (
              <tr key={event.event_id}>
                <td className="font-mono">{event.event_id}</td>
                <td>{event.event_type}</td>
                <td>{event.priority}</td>
                <td>{event.effective_at ?? "—"}</td>
                <td>{event.suspends_normal_transitions ? "yes" : "no"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p>No fault event is scheduled for this scenario.</p>
      )}

      <h5>Emergency steps</h5>
      {scenario.emergency_steps && scenario.emergency_steps.length > 0 ? (
        <ol>
          {scenario.emergency_steps.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
      ) : (
        <p>No emergency step is defined for this scenario.</p>
      )}
    </section>
  );
}
