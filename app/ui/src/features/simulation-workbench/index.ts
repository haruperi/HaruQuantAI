/**
 * Simulation Workbench public surface (FEAT-UI-31).
 */

export {
  SimulationWorkbench,
  type SimulationMode,
  type SimulationWorkbenchProps,
} from "./SimulationWorkbench";

export { SimulationHome, type SimulationHomeProps } from "./SimulationHome";
export {
  SimulationRunBuilder,
  BUILDER_STAGES,
  BUILDER_MODES,
  RUN_DEFAULTS,
  type BuilderStage,
  type BuilderMode,
  type RunBuilderSubmission,
  type SimulationRunBuilderProps,
} from "./SimulationRunBuilder";
export { CanonicalRunMonitor } from "./CanonicalRunMonitor";
export { BatchRunMonitor } from "./BatchRunMonitor";
export { useSimulationWorkbenchStore } from "./simulation-store";
export type { SimulationWorkbenchStore } from "./simulation-store";
export {
  ACTIVE_RUN_STATUSES,
  ACTIVE_BATCH_STATUSES,
  isRunActive,
  isBatchActive,
  isRunSettled,
  batchCompletionRatio,
} from "./simulation-selectors";
export type { StreamState } from "./simulation-selectors";

export {
  SimulationStatusBadge,
  type SimulationStatusBadgeProps,
} from "./SimulationStatusBadge";
