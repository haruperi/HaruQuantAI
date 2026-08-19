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

export {
  InteractiveSimulationWorkspace,
  PLAY_TICKS_PER_BEAT,
  PLAY_INTERVAL_MS,
  VIEWPORT_ROWS,
  type InteractiveSimulationWorkspaceProps,
} from "./InteractiveSimulationWorkspace";

export {
  SimulationSessionHeader,
  STEP_SIZES,
  type SimulationSessionHeaderProps,
} from "./SimulationSessionHeader";

export { MarketViewport, type MarketViewportProps } from "./MarketViewport";

export {
  ManualCommandPanel,
  MANUAL_COMMANDS,
  type ManualCommandPanelProps,
} from "./ManualCommandPanel";

export {
  SessionStatePanels,
  type SessionStatePanelsProps,
} from "./SessionStatePanels";

export {
  WhatIfPanel,
  parseOverrides,
  type WhatIfPanelProps,
} from "./WhatIfPanel";

export {
  SimulationRecoveryPanel,
  INTEGRITY_VERIFIED,
  type SimulationRecoveryPanelProps,
} from "./SimulationRecoveryPanel";

export {
  SimulationFinalizeDialog,
  FINALIZE_ADVISORY_NOTICE,
  type SimulationFinalizeDialogProps,
} from "./SimulationFinalizeDialog";

export {
  SimulationPlaybackWorkspace,
  MAX_RETAINED_FRAMES,
  SUPPRESSED_FRAME_FIELDS,
  withoutOrderTickets,
  type SimulationPlaybackWorkspaceProps,
} from "./SimulationPlaybackWorkspace";

export {
  ScenarioPanel,
  NO_SCENARIO_EVIDENCE,
  type ScenarioEvent,
  type ScenarioEvidence,
  type ScenarioPanelProps,
} from "./ScenarioPanel";

export {
  ChecklistPanel,
  NO_CHECKLIST_EVIDENCE,
  type ChecklistEvidence,
  type ChecklistStepEvidence,
  type ChecklistPanelProps,
} from "./ChecklistPanel";

export {
  MissionPanel,
  NO_MISSION_OUTCOME,
  type MissionOutcomeEvidence,
  type MissionPanelProps,
  type QualificationLink,
} from "./MissionPanel";

export {
  PortfolioSimulationPanel,
  NO_PORTFOLIO_INFERENCE,
  MAX_PORTFOLIO_COMPONENTS,
  type PortfolioComponent,
  type PortfolioSimulationRequest,
  type PortfolioSimulationPanelProps,
} from "./PortfolioSimulationPanel";
