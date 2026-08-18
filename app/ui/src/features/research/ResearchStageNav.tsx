/**
 * Progressive stage navigation (FEAT-UI-28).
 *
 * Preserves V1's progressive-stage idea while deriving every status from
 * server evidence rather than browser-held progress. A stage is never hidden:
 * one that was not selected, or that produced no evidence, stays visible and
 * says so.
 */

"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import type { ResearchRunDetail } from "@/clients";

import { StateBadge } from "./evidence";
import { annotatedStages } from "./research-selectors";

/** Props accepted by `ResearchStageNav`. */
export interface ResearchStageNavProps {
  detail: ResearchRunDetail | null;
  experimentId: string;
  runId: string;
  activeStage: string;
}

const GROUP_LABELS: Record<string, string> = {
  run: "Run",
  evidence: "Evidence",
  audit: "Audit",
};

/** Stage navigator rendered beside every run stage. */
export function ResearchStageNav({
  detail,
  experimentId,
  runId,
  activeStage,
}: ResearchStageNavProps): ReactNode {
  const stages = annotatedStages(detail);
  const groups: Array<"run" | "evidence" | "audit"> = ["run", "evidence", "audit"];
  const base = `/workstation/research/experiments/${experimentId}/runs/${runId}`;

  return (
    <nav className="research-stage-nav" aria-label="Research stages">
      {groups.map((group) => (
        <section key={group}>
          <h4>{GROUP_LABELS[group]}</h4>
          <ul>
            {stages
              .filter((stage) => stage.group === group)
              .map((stage) => (
                <li key={stage.id}>
                  <Link
                    href={`${base}/${stage.id}`}
                    className={`research-stage-link${
                      stage.id === activeStage ? " research-stage-link--active" : ""
                    }`}
                    aria-current={stage.id === activeStage ? "page" : undefined}
                    title={stage.description}
                  >
                    <span className="research-stage-link__label">{stage.label}</span>
                    <StateBadge state={stage.state} />
                  </Link>
                </li>
              ))}
          </ul>
        </section>
      ))}
    </nav>
  );
}
