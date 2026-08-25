/**
 * Dev-Only Mock Presentation Fixtures for HaruQuantAI D-UI.
 *
 * All mock data here implements ratified generated wire contracts from app/contracts/
 * and is visibly labeled non-authoritative.
 */

import type {
  AdministerSystemPresentationSuccess,
  AuthorStrategiesPresentationSuccess,
  ComposePortfoliosPresentationSuccess,
  EditCodePresentationSuccess,
  EditInputsPresentationSuccess,
  EditProjectsPresentationSuccess,
  EnsureAccessPresentationSuccess,
  ExploreResultsPresentationSuccess,
  ExtendViewsPresentationSuccess,
  ManageDataPresentationSuccess,
  ManageLayoutsPresentationSuccess,
  MonitorWorkPresentationSuccess,
  OperateDatabanksPresentationSuccess,
  OperateTradingPresentationSuccess,
  RunResearchPresentationSuccess,
  StartWorkPresentationSuccess,
} from "../../contracts/generated/ui";
import type { ActivitySnapshot } from "../../features/monitor_work/activity_model";

export const MOCK_START_WORK_SUCCESS: StartWorkPresentationSuccess = {
  outcome: "SUCCESS",
  request_id: "mock-req-start-work",
  result_version: 1,
  recent_routes: [
    {
      path: "/research",
      workspace_id: "preset-research",
      title: "Research Workspace (Mock)",
      schema_version: 1,
    },
    {
      path: "/data",
      workspace_id: "preset-data",
      title: "Data Workspace (Mock)",
      schema_version: 1,
    },
  ],
  shortcuts: [
    {
      command_id: "cmd.new-strategy",
      title: "Create Strategy Draft",
      category: "Strategy",
      shortcut: "Ctrl+N",
      enabled: true,
      schema_version: 1,
    },
  ],
  news: [
    {
      notification_id: "notif-mock-1",
      title: "Development Mock Mode Active",
      message: "Mock capability provider active for Increment 1 UI workstation foundation.",
      severity: "info",
      timestamp_iso: new Date().toISOString(),
      schema_version: 1,
    },
  ],
  schema_version: 1,
};

export const MOCK_MANAGE_LAYOUTS_SUCCESS: ManageLayoutsPresentationSuccess = {
  outcome: "SUCCESS",
  request_id: "mock-req-manage-layouts",
  result_version: 1,
  layout: {
    layout_id: "layout-mock-chart-ladder",
    workspace_id: "workstation-main",
    actor_id: "actor-mock",
    layout_version: 1,
    capability_snapshot_id: "snap-mock-layouts",
    widget_instances: [
      {
        instance_id: "inst-mock-chart",
        widget_type: "chart",
        workspace_id: "workstation-main",
        configuration_version: 1,
        state_version: 1,
        schema_version: 1,
      },
      {
        instance_id: "inst-mock-ladder",
        widget_type: "price_ladder",
        workspace_id: "workstation-main",
        configuration_version: 1,
        state_version: 1,
        schema_version: 1,
      },
    ],
    placements: [
      {
        instance_id: "inst-mock-chart",
        panel_id: "panel-mock-left",
        panel_order: 0,
        tab_order: 0,
        size_ratio: "0.67",
        schema_version: 1,
      },
      {
        instance_id: "inst-mock-ladder",
        panel_id: "panel-mock-right",
        panel_order: 1,
        tab_order: 0,
        size_ratio: "0.33",
        schema_version: 1,
      },
    ],
    active_panel_id: "inst-mock-chart",
    content_hash: "mock-chart-ladder-hash",
    schema_version: 1,
  },
  migration: null,
  template: {
    template_id: "template-chart-ladder-v1",
    name: "Chart + Ladder (Mock)",
    description: "Mock template payload for the manage-layouts COMPOSE operation.",
    layout: {
      layout_id: "layout-tpl-mock-chart-ladder",
      workspace_id: "template-chart-ladder",
      actor_id: "system",
      layout_version: 1,
      capability_snapshot_id: "snap-tpl-mock",
      widget_instances: [
        {
          instance_id: "inst-tpl-mock-chart",
          widget_type: "chart",
          workspace_id: "template-chart-ladder",
          configuration_version: 1,
          state_version: 1,
          schema_version: 1,
        },
        {
          instance_id: "inst-tpl-mock-ladder",
          widget_type: "price_ladder",
          workspace_id: "template-chart-ladder",
          configuration_version: 1,
          state_version: 1,
          schema_version: 1,
        },
      ],
      placements: [
        {
          instance_id: "inst-tpl-mock-chart",
          panel_id: "panel-tpl-mock-left",
          panel_order: 0,
          tab_order: 0,
          size_ratio: "0.67",
          schema_version: 1,
        },
        {
          instance_id: "inst-tpl-mock-ladder",
          panel_id: "panel-tpl-mock-right",
          panel_order: 1,
          tab_order: 0,
          size_ratio: "0.33",
          schema_version: 1,
        },
      ],
      active_panel_id: "inst-tpl-mock-chart",
      content_hash: "tpl-mock-chart-ladder-hash",
      schema_version: 1,
    },
    schema_version: 1,
  },
  schema_version: 1,
};

export const MOCK_EDIT_INPUTS_SUCCESS: EditInputsPresentationSuccess = {
  outcome: "SUCCESS",
  request_id: "mock-req-edit-inputs",
  result_version: 1,
  fields: [
    {
      field_name: "symbol",
      label: "Instrument Symbol",
      field_type: "string",
      required: true,
      default_value: "EURUSD",
      schema_version: 1,
    },
  ],
  findings: [],
  draft: {
    draft_id: "draft-mock-1",
    schema_id: "schema-strategy-params",
    workspace_id: "workstation-main",
    actor_id: "actor-mock",
    entity_version: 1,
    payload: { symbol: "EURUSD", is_mock: true },
    created_at_iso: "2026-08-26T00:00:00.000000Z",
    updated_at_iso: "2026-08-26T00:00:00.000000Z",
    schema_version: 1,
  },
  conflict: null,
  confirmation: null,
  schema_version: 1,
};

export const MOCK_AUTHOR_STRATEGIES_SUCCESS: AuthorStrategiesPresentationSuccess = {
  outcome: "SUCCESS",
  request_id: "mock-req-author-strategies",
  result_version: 1,
  projection: {
    view_id: "view-strategy-tree",
    title: "Strategy AST (Mock)",
    data_source: "mock.strategy.tree",
    parameters: { is_mock: true },
    schema_version: 1,
  },
  findings: [],
  strategy_version_id: "strat-mock-v1",
  schema_version: 1,
};

export const MOCK_RUN_RESEARCH_SUCCESS: RunResearchPresentationSuccess = {
  outcome: "SUCCESS",
  request_id: "mock-req-run-research",
  result_version: 1,
  preview: null,
  run: null,
  pinned_versions: ["strat-mock-v1"],
  schema_version: 1,
};

export const MOCK_EDIT_PROJECTS_SUCCESS: EditProjectsPresentationSuccess = {
  outcome: "SUCCESS",
  request_id: "mock-req-edit-projects",
  result_version: 1,
  projection: null,
  project_version_id: "proj-mock-v1",
  progress: null,
  schema_version: 1,
};

export const MOCK_MANAGE_DATA_SUCCESS: ManageDataPresentationSuccess = {
  outcome: "SUCCESS",
  request_id: "mock-req-manage-data",
  result_version: 1,
  projection: {
    view_id: "view-datasets",
    title: "Market Datasets (Mock)",
    data_source: "mock.data.datasets",
    parameters: { is_mock: true },
    schema_version: 1,
  },
  findings: [],
  job: null,
  schema_version: 1,
};

export const MOCK_OPERATE_DATABANKS_SUCCESS: OperateDatabanksPresentationSuccess = {
  outcome: "SUCCESS",
  request_id: "mock-req-operate-databanks",
  result_version: 1,
  page: null,
  selection: {
    selection_id: "sel-databank-mock",
    selected_keys: [],
    is_all_selected: false,
    schema_version: 1,
  },
  bulk_token: null,
  confirmation: null,
  schema_version: 1,
};

export const MOCK_EXPLORE_RESULTS_SUCCESS: ExploreResultsPresentationSuccess = {
  outcome: "SUCCESS",
  request_id: "mock-req-explore-results",
  result_version: 1,
  summary: {
    view_id: "view-results-summary",
    title: "Backtest Results (Mock)",
    data_source: "mock.analytics.results",
    parameters: { is_mock: true },
    schema_version: 1,
  },
  page_state: null,
  chart_alternative: {
    chart_id: "chart-equity-mock",
    title: "Equity Curve (Mock Data)",
    summary_text: "Tabular representation of mock equity series.",
    table_data: [
      { date: "2026-01-01", balance: "10000.00", equity: "10000.00" },
      { date: "2026-01-02", balance: "10150.00", equity: "10180.00" },
    ],
    schema_version: 1,
  },
  context: null,
  schema_version: 1,
};

export const MOCK_COMPOSE_PORTFOLIOS_SUCCESS: ComposePortfoliosPresentationSuccess = {
  outcome: "SUCCESS",
  request_id: "mock-req-compose-portfolios",
  result_version: 1,
  projection: null,
  portfolio_version_id: "port-mock-v1",
  schema_version: 1,
};

export const MOCK_EDIT_CODE_SUCCESS: EditCodePresentationSuccess = {
  outcome: "SUCCESS",
  request_id: "mock-req-edit-code",
  result_version: 1,
  files: ["indicators/custom_rsi.py", "strategies/sample_trend.py"],
  diagnostics: [],
  job: null,
  schema_version: 1,
};

export const MOCK_MONITOR_WORK_SUCCESS: MonitorWorkPresentationSuccess = {
  outcome: "SUCCESS",
  request_id: "mock-req-monitor-work",
  result_version: 1,
  progress: {
    task_id: "task-mock-1",
    stage_name: "Running Mock Simulation",
    progress_percent: "75.5",
    is_indeterminate: false,
    message: "Processing bars...",
    schema_version: 1,
  },
  notification: null,
  error: null,
  schema_version: 1,
};

export const MOCK_MONITOR_WORK_FAILURE: MonitorWorkPresentationSuccess = {
  outcome: "SUCCESS",
  request_id: "mock-req-monitor-work-fail",
  result_version: 1,
  progress: null,
  notification: null,
  error: {
    error_code: "ERR_DATA_FETCH_TIMEOUT",
    title: "Data Fetch Timeout (Mock)",
    detail: "Historical tick feed connection timed out after 30 seconds.",
    causal_reference: "req-fetch-mock-998",
    is_retryable: true,
    suggested_action: "Check connectivity and retry the data sync job.",
    schema_version: 1,
  },
  schema_version: 1,
};

export const MOCK_ACTIVITY_SNAPSHOT: ActivitySnapshot = {
  snapshot_id: "snap-mock-activity-1",
  cursor: "cursor-seq-105",
  is_stale: false,
  generated_at_iso: "2026-08-26T00:00:00.000000Z",
  is_mock: true,
  events: [
    {
      event_id: "evt-mock-101",
      sequence: 101,
      timestamp_iso: "2026-08-26T00:00:01.000000Z",
      severity: "info",
      event_type: "JOB_QUEUED",
      message: "Job queued for execution",
      correlation_id: "job-mock-99",
    },
    {
      event_id: "evt-mock-102",
      sequence: 102,
      timestamp_iso: "2026-08-26T00:00:02.000000Z",
      severity: "info",
      event_type: "JOB_STARTED",
      message: "Job started on worker node-1",
      correlation_id: "job-mock-99",
    },
    {
      event_id: "evt-mock-105",
      sequence: 105,
      timestamp_iso: "2026-08-26T00:00:05.000000Z",
      severity: "warning",
      event_type: "STAGE_RETRY",
      message: "Stage 2 retry attempt 1",
      correlation_id: "job-mock-99",
    },
  ],
};

export const MOCK_ADMINISTER_SYSTEM_SUCCESS: AdministerSystemPresentationSuccess = {
  outcome: "SUCCESS",
  request_id: "mock-req-administer-system",
  result_version: 1,
  preferences: {
    theme: "dark",
    density: "comfortable",
    font_scale: "1",
    locale: "en-US",
    schema_version: 1,
  },
  accessibility: {
    high_contrast: false,
    reduced_motion: false,
    screen_reader_optimized: false,
    schema_version: 1,
  },
  administration: null,
  schema_version: 1,
};

export const MOCK_OPERATE_TRADING_SUCCESS: OperateTradingPresentationSuccess = {
  outcome: "SUCCESS",
  request_id: "mock-req-operate-trading",
  result_version: 1,
  readiness: null,
  preview: null,
  receipt: null,
  kill_switch: null,
  market: null,
  schema_version: 1,
};

export const MOCK_ENSURE_ACCESS_SUCCESS: EnsureAccessPresentationSuccess = {
  outcome: "SUCCESS",
  request_id: "mock-req-ensure-access",
  result_version: 1,
  alternatives: [],
  bindings: [
    {
      key_combination: "Alt+W",
      command_id: "cmd.open-workspace-switcher",
      description: "Open workspace switcher",
      scope: "global",
      schema_version: 1,
    },
  ],
  focus_target: "shell-workspace-outlet",
  schema_version: 1,
};

export const MOCK_EXTEND_VIEWS_SUCCESS: ExtendViewsPresentationSuccess = {
  outcome: "SUCCESS",
  request_id: "mock-req-extend-views",
  result_version: 1,
  widget_type: null,
  removal: null,
  migration: null,
  schema_version: 1,
};
