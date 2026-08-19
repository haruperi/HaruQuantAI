/**
 * Navigable stage registry for the Research workbench (FEAT-UI-28).
 *
 * The registry names the stages and describes what each one shows. It does not
 * decide whether a stage has evidence: that status is server-derived and
 * arrives on the run detail as `stage_status`.
 */

import type { StageView } from "@/clients";

/** One navigable stage in the workbench. */
export interface StageDefinition {
  /** Route segment and API stage key. */
  readonly id: StageView;
  /** Short navigation label. */
  readonly label: string;
  /** One-line description of the evidence the stage renders. */
  readonly description: string;
  /** Research stages that must run for this view to carry evidence. */
  readonly requires: readonly string[];
  /** Grouping used by the stage navigator. */
  readonly group: "run" | "evidence" | "audit";
}

/** Every navigable stage, in workbench navigation order. */
export const STAGE_DEFINITIONS: readonly StageDefinition[] = [
  {
    id: "overview",
    label: "Overview",
    description: "Hypothesis, readiness, study outcomes, and warnings.",
    requires: [],
    group: "run",
  },
  {
    id: "data",
    label: "Data & Quality",
    description: "Dataset identity, quality decision, cleaning, and preview.",
    requires: ["data"],
    group: "run",
  },
  {
    id: "features",
    label: "Features",
    description: "Feature frame shape, windows, horizons, and warmup loss.",
    requires: ["features"],
    group: "evidence",
  },
  {
    id: "validation",
    label: "Validation",
    description: "Leakage evidence, chronological splits, and seeded statistics.",
    requires: ["leakage", "statistics"],
    group: "evidence",
  },
  {
    id: "metrics",
    label: "Metrics",
    description: "The seven canonical metric families with validity.",
    requires: ["metrics"],
    group: "evidence",
  },
  {
    id: "studies",
    label: "Edge Studies",
    description: "Mean reversion, trend persistence, session edge, and nulls.",
    requires: ["studies"],
    group: "evidence",
  },
  {
    id: "seasonality",
    label: "Seasonality",
    description: "Intraday bias, heatmaps, calendar, and session evidence.",
    requires: ["seasonality"],
    group: "evidence",
  },
  {
    id: "market-structure",
    label: "Market Structure",
    description: "Score inputs, regimes, quality, validation, and calibration.",
    requires: ["market_structure"],
    group: "evidence",
  },
  {
    id: "modeling",
    label: "Modeling",
    description: "PCA variance, clusters, and cluster-conditioned evidence.",
    requires: ["modeling"],
    group: "evidence",
  },
  {
    id: "profile",
    label: "Profile & Scorecard",
    description: "Final score, readiness, score rows, and reasons.",
    requires: ["profiles"],
    group: "evidence",
  },
  {
    id: "intelligence",
    label: "Intelligence",
    description: "Point-in-time fundamental, sentiment, and applicability.",
    requires: [],
    group: "evidence",
  },
  {
    id: "stress",
    label: "Stress",
    description: "Historical and reasoned shocks with basis validation.",
    requires: [],
    group: "evidence",
  },
  {
    id: "artifacts",
    label: "Artifacts",
    description: "Persisted reports with content hash and audit identity.",
    requires: [],
    group: "audit",
  },
  {
    id: "provenance",
    label: "Provenance",
    description: "Hashes, seeds, dependency versions, and the raw report.",
    requires: [],
    group: "audit",
  },
];

/** Stage lookup by route segment. */
export const STAGE_BY_ID: Readonly<Record<string, StageDefinition>> =
  Object.fromEntries(STAGE_DEFINITIONS.map((stage) => [stage.id, stage]));

/** Whether a route segment names a registered stage. */
export function isStageView(value: string): value is StageView {
  return value in STAGE_BY_ID;
}
