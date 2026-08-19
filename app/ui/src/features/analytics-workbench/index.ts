/**
 * Analytics Workbench public surface (FEAT-UI-32).
 */

export {
  AnalyticsWorkspace,
  type AnalyticsWorkspaceProps,
} from "./AnalyticsWorkspace";

export {
  AnalyticsNav,
  ANALYTICS_TABS,
  type AnalyticsNavProps,
  type AnalyticsTab,
  type AnalyticsTabDef,
} from "./AnalyticsNav";

export {
  AnalyticsEvidenceState,
  EvidenceValue,
  EVIDENCE_UNAVAILABLE_TEXT,
  AUTHORITATIVE_EVIDENCE_UNAVAILABLE,
  type AnalyticsEvidenceStateProps,
} from "./AnalyticsEvidenceState";

export {
  AnalyticsLibrary,
  LIBRARY_PAGE_SIZE,
  type AnalyticsLibraryProps,
} from "./AnalyticsLibrary";

export {
  OverviewPanel,
  METRIC_GROUPS,
  type OverviewPanelProps,
} from "./OverviewPanel";

export {
  TradesPanel,
  TRADES_PAGE_SIZE,
  type TradesPanelProps,
} from "./TradesPanel";

export {
  TradeDetailPanel,
  buildReplayHref,
  type TradeDetailPanelProps,
} from "./TradeDetailPanel";

export {
  AnalyticsArtifactDrawer,
  type AnalyticsArtifactDrawerProps,
} from "./AnalyticsArtifactDrawer";

export {
  TimeSeriesChart,
  toSeriesPoints,
  type TimeSeriesChartProps,
} from "./TimeSeriesChart";

export {
  CalendarHeatmap,
  type CalendarHeatmapProps,
} from "./CalendarHeatmap";

export {
  DistributionChart,
  type DistributionChartProps,
} from "./DistributionChart";

export {
  RealismPanel,
  REALISM_BLOCKS,
  type RealismPanelProps,
} from "./RealismPanel";

export {
  ProvenancePanel,
  PROVENANCE_ROWS,
  type ProvenancePanelProps,
} from "./ProvenancePanel";

export {
  ReturnsPanel,
  RETURNS_METRICS,
  UNSUPPORTED_RETURNS_METRICS,
  UnsupportedMetrics,
  summaryRow,
  type AdvancedPanelProps,
} from "./ReturnsPanel";

export {
  RiskPanel,
  RISK_METRICS,
  UNSUPPORTED_RISK_METRICS,
} from "./RiskPanel";

export {
  DistributionPanel,
  DISTRIBUTION_METRICS,
  UNSUPPORTED_DISTRIBUTION_METRICS,
} from "./DistributionPanel";
