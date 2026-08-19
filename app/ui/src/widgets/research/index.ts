/**
 * Research workbench feature barrel (FEAT-UI-28).
 *
 * One feature folder covers the whole workbench: the ledger, the run builder,
 * the stage shell, every evidence panel, and the expectancy and drift monitors.
 */

export { ResearchDashboard } from "./ResearchDashboard";
export { ResearchRunBuilder } from "./ResearchRunBuilder";
export type { ResearchRunBuilderProps } from "./ResearchRunBuilder";
export { ResearchWorkbench } from "./ResearchWorkbench";
export type { ResearchWorkbenchProps } from "./ResearchWorkbench";
export { ResearchStageNav } from "./ResearchStageNav";
export { ResearchRunHeader } from "./ResearchRunHeader";
export {
  ResearchRunStatus,
  EvidenceGate,
  ErrorEvidence,
  LoadingEvidence,
} from "./ResearchRunStatus";
export { ResearchWarnings } from "./ResearchWarnings";
export { ResearchArtifactDrawer } from "./ResearchArtifactDrawer";
export { ResearchComparison } from "./ResearchComparison";
export { ResearchAutomation } from "./ResearchAutomation";
export { ResearchExpectancy } from "./ResearchExpectancy";
export { ResearchDrift } from "./ResearchDrift";
export {
  ResearchExperimentList,
  ResearchExperimentDetailView,
} from "./ResearchExperiments";

export {
  EMPTY_DRAFT,
  MAX_COMPARISON_RUNS,
  useResearchStore,
} from "./research-store";
export type { RunBuilderDraft, StreamConnectionState } from "./research-store";

export { STAGE_BY_ID, STAGE_DEFINITIONS, isStageView } from "./stage-registry";
export type { StageDefinition } from "./stage-registry";

export {
  annotatedStages,
  groupWarnings,
  stageReason,
  stageState,
} from "./research-selectors";

export {
  useArtifacts,
  useAutomationBatch,
  useComparison,
  useDashboard,
  useDrift,
  useExpectancy,
  useExperiment,
  useExperiments,
  usePresets,
  useRun,
  useRunReport,
  useRuns,
  useStage,
} from "./use-research";

export { OverviewPanel } from "./panels/OverviewPanel";
export type { PanelProps } from "./panels/OverviewPanel";
export { DataQualityPanel } from "./panels/DataQualityPanel";
export { FeaturesPanel } from "./panels/FeaturesPanel";
export { ValidationPanel } from "./panels/ValidationPanel";
export { MetricsPanel } from "./panels/MetricsPanel";
export { StudiesPanel } from "./panels/StudiesPanel";
export { SeasonalityPanel } from "./panels/SeasonalityPanel";
export { MarketStructurePanel } from "./panels/MarketStructurePanel";
export { ModelingPanel } from "./panels/ModelingPanel";
export { ProfilePanel } from "./panels/ProfilePanel";
export { IntelligencePanel } from "./panels/IntelligencePanel";
export { StressPanel } from "./panels/StressPanel";
export { ProvenancePanel } from "./panels/ProvenancePanel";
