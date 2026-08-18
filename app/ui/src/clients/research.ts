/**
 * Research workbench client (20 operations).
 *
 * A complete Research pass exceeds the API's endpoint deadline, so the run
 * surface is a job: `createRun` returns an accepted identity immediately, and
 * progress is observed by polling `getRun` or consuming `openRunEvents`.
 *
 * Every scientific value in these schemas is Research-owned and arrives already
 * calculated. The client validates shape and never derives a score, readiness
 * verdict, classification, or statistic.
 */

import { z } from "zod";

import type { ApiResponse } from "./contracts";
import { researchRoutes } from "./routes";
import { request, type RequestOptions } from "./request";
import { openStream, type StreamTransportOptions } from "./stream";
import type { StreamEvent } from "./contracts";

// --- Shared evidence shapes ---------------------------------------------

/** One structured Research warning. */
export const researchWarningSchema = z.object({
  code: z.string(),
  message: z.string(),
  severity: z.string(),
  field_path: z.string().nullable().optional(),
  details: z.record(z.string(), z.unknown()).default({}),
});
export type ResearchWarning = z.infer<typeof researchWarningSchema>;

/**
 * Explicit lifecycle state of one stage view.
 *
 * These are never collapsed into a single "unavailable": a stage the caller
 * did not select reads differently from one the run has not reached, and both
 * read differently from one Research could not produce.
 */
export const STAGE_STATES = [
  "queued",
  "running",
  "completed",
  "partial",
  "not_selected",
  "unavailable",
  "failed",
  "cancelled",
] as const;
export type StageState = (typeof STAGE_STATES)[number];

/** Navigable stage view names, in workbench navigation order. */
export const STAGE_VIEWS = [
  "overview",
  "data",
  "features",
  "validation",
  "metrics",
  "studies",
  "seasonality",
  "market-structure",
  "modeling",
  "profile",
  "intelligence",
  "stress",
  "artifacts",
  "provenance",
] as const;
export type StageView = (typeof STAGE_VIEWS)[number];

/** Terminal and in-flight run statuses. */
export const RESEARCH_RUN_STATUSES = [
  "queued",
  "running",
  "completed",
  "failed",
  "cancelled",
] as const;
export type ResearchRunStatus = (typeof RESEARCH_RUN_STATUSES)[number];

/** Research-owned readiness vocabulary. Never derived in the browser. */
export const READINESS_VALUES = [
  "BLOCKED",
  "REVIEW_READY",
  "INSUFFICIENT_EVIDENCE",
] as const;
export type Readiness = (typeof READINESS_VALUES)[number];

const stageStatusSchema = z.object({
  state: z.string(),
  reason: z.string().nullable(),
});

/** Server-owned scorecard evidence. */
export const scorecardSchema = z.object({
  available: z.boolean(),
  score: z.number().nullable().optional(),
  readiness: z.string().nullable().optional(),
  reasons: z.array(z.string()).default([]),
  score_rows: z.array(z.record(z.string(), z.unknown())).default([]),
  stage_count: z.number().nullable().optional(),
  advisory_only: z.boolean().optional(),
  snapshot_id: z.string().nullable().optional(),
  schema_version: z.string().nullable().optional(),
});
export type Scorecard = z.infer<typeof scorecardSchema>;

/** One safe artifact reference with hash and audit identity. */
export const artifactSchema = z.object({
  artifact_id: z.string(),
  kind: z.string(),
  format: z.string(),
  relative_path: z.string(),
  size_bytes: z.number(),
  sha256: z.string(),
  atomic: z.boolean(),
  schema_version: z.string(),
  audit_event_id: z.string(),
});
export type ResearchArtifact = z.infer<typeof artifactSchema>;

/** Data-owned dataset identity resolved server-side for one run. */
export const datasetIdentitySchema = z.object({
  symbol: z.string(),
  timeframe: z.string().nullable(),
  data_kind: z.string(),
  record_count: z.number(),
  start: z.string().nullable(),
  end: z.string().nullable(),
  available_at: z.string().nullable(),
  normalization_version: z.string(),
  cache_status: z.string(),
  precision_policy: z.string(),
  source_metadata: z.record(z.string(), z.string()).default({}),
  license_metadata: z.record(z.string(), z.string()).default({}),
  quality: z
    .object({
      status: z.string(),
      decision: z.string(),
      score: z.string(),
      record_count: z.number(),
      checked_count: z.number(),
      truncated: z.boolean(),
    })
    .nullable(),
});
export type DatasetIdentity = z.infer<typeof datasetIdentitySchema>;

/** One bounded OHLC preview row for the chart. */
export const barPreviewSchema = z.object({
  timestamp: z.string(),
  open: z.string(),
  high: z.string(),
  low: z.string(),
  close: z.string(),
  volume: z.string(),
  spread: z.string().nullable(),
});
export type BarPreview = z.infer<typeof barPreviewSchema>;

/** Reproducibility evidence for one run. */
export const provenanceSchema = z.object({
  available: z.boolean(),
  report_id: z.string().optional(),
  schema_id: z.string().optional(),
  contract_version: z.string().optional(),
  dataset_hash: z.string().optional(),
  configuration_hash: z.string().optional(),
  seeds: z.record(z.string(), z.number()).optional(),
  dependency_versions: z.record(z.string(), z.string()).optional(),
  source_references: z.array(z.string()).optional(),
  selected_stages: z.array(z.string()).optional(),
  generated_at: z.string().nullable().optional(),
  duration_ms: z.number().nullable().optional(),
  advisory_only: z.boolean().optional(),
  warnings: z.array(researchWarningSchema).optional(),
});
export type Provenance = z.infer<typeof provenanceSchema>;

/** Composite overview evidence assembled from Research-owned fields. */
export const overviewSchema = z.object({
  available: z.boolean(),
  hypothesis: z.string().optional(),
  selected_stages: z.array(z.string()).optional(),
  scorecard: scorecardSchema.optional(),
  study_counts: z
    .object({
      confirmed: z.number(),
      contradicted: z.number(),
      inconclusive: z.number(),
    })
    .optional(),
  structure: z
    .object({
      score: z.number().nullable().optional(),
      verdict: z.string().nullable().optional(),
      strategy_fit: z.record(z.string(), z.unknown()).default({}),
    })
    .nullable()
    .optional(),
  sessions: z.array(z.unknown()).optional(),
  modeling_insights: z.record(z.string(), z.unknown()).optional(),
  warnings: z.array(researchWarningSchema).optional(),
});
export type Overview = z.infer<typeof overviewSchema>;

/** Effective configuration, excluding server-owned roots and ceilings. */
export const effectiveConfigurationSchema = z
  .object({
    selected_stages: z.array(z.string()).optional(),
    session_timezone: z.string().optional(),
    session_windows: z.array(z.string()).optional(),
    feature_windows: z.record(z.string(), z.number()).optional(),
    forward_horizons: z.array(z.number()).optional(),
    allowed_forward_columns: z.array(z.string()).optional(),
    statistics: z
      .object({
        seed: z.number(),
        bootstrap_samples: z.number(),
        permutation_samples: z.number(),
        null_samples: z.number(),
        block_size: z.number(),
        correction: z.string().nullable(),
      })
      .optional(),
    market_structure: z
      .object({
        enable_quality: z.boolean(),
        quality_windows: z.array(z.number()),
        calibration_candidates: z.number(),
        validation_horizon: z.number(),
      })
      .optional(),
    modeling: z
      .object({
        feature_columns: z.array(z.string()),
        pca_components: z.number(),
        clusters: z.number(),
        minimum_samples: z.number(),
        seed: z.number(),
      })
      .optional(),
    studies: z.object({ continue_on_study_error: z.boolean() }).optional(),
  })
  .passthrough();
export type EffectiveConfiguration = z.infer<
  typeof effectiveConfigurationSchema
>;

// --- Presets -------------------------------------------------------------

/** One server-owned preset. Filesystem roots and ceilings never appear here. */
export const presetSchema = z.object({
  preset_id: z.string(),
  name: z.string(),
  description: z.string(),
  selected_stages: z.array(z.string()),
  statistics: z.object({
    seed: z.number(),
    bootstrap_samples: z.number(),
    permutation_samples: z.number(),
    block_size: z.number(),
    null_samples: z.number(),
    correction: z.string().nullable(),
  }),
  feature_windows: z.record(z.string(), z.number()),
  forward_horizons: z.array(z.number()),
  enable_market_structure_quality: z.boolean(),
  modeling_clusters: z.number(),
  modeling_pca_components: z.number(),
  continue_on_study_error: z.boolean(),
  approved_override_keys: z.array(z.string()),
});
export type ResearchPreset = z.infer<typeof presetSchema>;

const presetCatalogueSchema = z.object({
  presets: z.array(presetSchema),
  stages: z.array(z.string()),
  stage_views: z.array(z.string()),
  stress_scenarios: z.array(
    z.object({
      scenario_key: z.string(),
      name: z.string(),
      assumption_ref: z.string(),
      rationale: z.string(),
      shocks: z.array(
        z.object({ shock_type: z.string(), magnitude: z.number() }),
      ),
    }),
  ),
});
export type ResearchPresetCatalogue = z.infer<typeof presetCatalogueSchema>;

// --- Runs and experiments -----------------------------------------------

/** One run row for ledgers, history tables, and comparisons. */
export const runSummarySchema = z.object({
  run_id: z.string(),
  experiment_id: z.string(),
  batch_id: z.string().nullable(),
  status: z.string(),
  hypothesis: z.string(),
  symbol: z.string(),
  timeframe: z.string(),
  preset: z.string(),
  selected_stages: z.array(z.string()),
  reason: z.string().nullable(),
  force_rerun: z.boolean(),
  created_at: z.string().nullable(),
  started_at: z.string().nullable(),
  completed_at: z.string().nullable(),
  report_id: z.string().nullable(),
  dataset_hash: z.string().nullable(),
  configuration_hash: z.string().nullable(),
  generated_at: z.string().nullable(),
  duration_ms: z.number().nullable(),
  score: z.number().nullable().optional(),
  readiness: z.string().nullable().optional(),
  advisory_only: z.boolean(),
  warning_count: z.number(),
  error: z
    .object({
      code: z.string(),
      message: z.string(),
      details: z.record(z.string(), z.unknown()).optional(),
    })
    .nullable(),
});
export type ResearchRunSummary = z.infer<typeof runSummarySchema>;

/** Complete run header carried on every stage of the workbench. */
export const runDetailSchema = runSummarySchema.extend({
  dataset: datasetIdentitySchema.nullable().optional(),
  effective_configuration: effectiveConfigurationSchema.default({}),
  stage_status: z.record(z.string(), stageStatusSchema),
  stage_views: z.array(z.string()),
  artifacts: z.array(artifactSchema),
  warnings: z.array(researchWarningSchema),
  provenance: provenanceSchema,
  overview: overviewSchema,
});
export type ResearchRunDetail = z.infer<typeof runDetailSchema>;

/** One experiment summary with its latest run. */
export const experimentSummarySchema = z.object({
  experiment_id: z.string(),
  name: z.string(),
  hypothesis: z.string(),
  notes: z.string().nullable(),
  tags: z.array(z.string()),
  created_at: z.string(),
  run_count: z.number(),
  latest_run: runSummarySchema.nullable(),
});
export type ResearchExperimentSummary = z.infer<typeof experimentSummarySchema>;

/** One experiment with its complete run ledger. */
export const experimentDetailSchema = experimentSummarySchema.extend({
  runs: z.array(runSummarySchema),
});
export type ResearchExperimentDetail = z.infer<typeof experimentDetailSchema>;

const experimentListSchema = z.object({
  experiments: z.array(experimentSummarySchema),
});
const runListSchema = z.object({ runs: z.array(runSummarySchema) });

/** Research ledger shown on the workbench entry page. */
export const dashboardSchema = z.object({
  experiments: z.array(experimentSummarySchema),
  recent_runs: z.array(runSummarySchema),
  readiness_distribution: z.record(z.string(), z.number()),
  status_distribution: z.record(z.string(), z.number()),
  study_counts: z.object({
    confirmed: z.number(),
    contradicted: z.number(),
    inconclusive: z.number(),
  }),
  warning_total: z.number(),
  advisory_only: z.boolean(),
});
export type ResearchDashboard = z.infer<typeof dashboardSchema>;

/**
 * One navigable stage view.
 *
 * `evidence` is intentionally an open record: each stage carries a different
 * Research-owned evidence shape, and the panels narrow it with their own
 * per-stage schemas rather than forcing one union here.
 */
export const stageViewSchema = z.object({
  stage: z.string(),
  state: z.string(),
  reason: z.string().nullable(),
  evidence: z.record(z.string(), z.unknown()),
  warnings: z.array(researchWarningSchema),
});
export type ResearchStageView = z.infer<typeof stageViewSchema>;

/** The registered report, exposed for the secondary diagnostic viewer. */
export const runReportSchema = z.object({
  available: z.boolean(),
  reason: z.string().nullable(),
  status: z.string(),
  report: z
    .object({
      report_id: z.string(),
      schema_id: z.string(),
      contract_version: z.string(),
      hypothesis: z.string(),
      evidence: z.record(z.string(), z.unknown()),
      seeds: z.record(z.string(), z.number()),
      configuration_hash: z.string(),
      dataset_hash: z.string(),
      source_references: z.array(z.string()),
      warnings: z.array(researchWarningSchema),
      generated_at: z.string().nullable(),
      dependency_versions: z.record(z.string(), z.string()),
      duration_ms: z.number().nullable(),
      advisory_only: z.boolean(),
    })
    .nullable(),
});
export type ResearchRunReport = z.infer<typeof runReportSchema>;

const artifactListSchema = z.object({
  run_id: z.string(),
  artifacts: z.array(artifactSchema),
  artifact_root_owner: z.string(),
});
export type ResearchArtifactList = z.infer<typeof artifactListSchema>;

/** One compared run with its deltas against the baseline. */
export const comparisonEntrySchema = z.object({
  run_id: z.string().nullable(),
  experiment_id: z.string().nullable(),
  symbol: z.string().nullable(),
  timeframe: z.string().nullable(),
  status: z.string().nullable(),
  created_at: z.string().nullable(),
  report_id: z.string().nullable(),
  dataset_hash: z.string().nullable(),
  configuration_hash: z.string().nullable(),
  score: z.number().nullable().optional(),
  readiness: z.string().nullable().optional(),
  score_delta: z.number().nullable(),
  stages: z.array(z.string()),
  warning_count: z.number(),
  metrics: z.record(
    z.string(),
    z.object({ value: z.number().nullable(), delta: z.number().nullable() }),
  ),
  studies: z.record(
    z.string(),
    z.object({
      classification: z.string().nullable().optional(),
      changed: z.boolean(),
    }),
  ),
  seeds: z.record(z.string(), z.number()).default({}),
  dependency_versions: z.record(z.string(), z.string()).default({}),
});
export type ResearchComparisonEntry = z.infer<typeof comparisonEntrySchema>;

/** Server-derived comparison across runs. */
export const comparisonSchema = z.object({
  baseline_run_id: z.string().nullable(),
  metric_names: z.array(z.string()),
  study_names: z.array(z.string()),
  entries: z.array(comparisonEntrySchema),
});
export type ResearchComparison = z.infer<typeof comparisonSchema>;

/** One automation batch with per-symbol run status. */
export const automationBatchSchema = z.object({
  batch_id: z.string(),
  experiment_id: z.string(),
  symbols: z.array(z.string()),
  trigger: z.string(),
  reason: z.string().nullable(),
  created_at: z.string(),
  status: z.string(),
  counts: z.object({
    total: z.number(),
    completed: z.number(),
    failed: z.number(),
    cancelled: z.number(),
    pending: z.number(),
    rejected: z.number(),
  }),
  runs: z.array(runSummarySchema),
  rejections: z.array(
    z.object({ symbol: z.string(), code: z.string(), detail: z.string() }),
  ),
});
export type ResearchAutomationBatch = z.infer<typeof automationBatchSchema>;

/** Approved expectancy profile and whether a transition is permitted. */
export const expectancySchema = z.object({
  available: z.boolean(),
  reason: z.string().nullable(),
  profile: z.record(z.string(), z.unknown()).nullable(),
  transition_permitted: z.boolean().optional(),
});
export type ResearchExpectancy = z.infer<typeof expectancySchema>;

/** Refreshed expectancy evidence returned after a governed transition. */
export const expectancyTransitionSchema = z.object({
  available: z.boolean(),
  reason: z.string().nullable(),
  profile: z.record(z.string(), z.unknown()).nullable(),
});
export type ResearchExpectancyTransition = z.infer<
  typeof expectancyTransitionSchema
>;

/** Bounded governance evidence submitted for one expectancy transition. */
export interface ResearchExpectancyTransitionInput {
  target_state:
    "draft" | "under_review" | "approved" | "suspended" | "expired" | "revoked";
  decision: string;
  reason: string;
  superseded_by?: string | null;
}

/** Explicit measurements used to create a draft expectancy profile. */
export interface ResearchExpectancyCreateInput {
  run_id: string;
  exact_version: string;
  strategy_ref: string;
  regimes?: string[];
  sessions?: string[];
  sample_from_utc: string;
  sample_to_utc: string;
  sample_size: number;
  out_of_sample_status: "in_sample" | "out_of_sample" | "walk_forward";
  win_rate: number;
  avg_win_r: number;
  avg_loss_r: number;
  expected_value_r: number;
  max_drawdown_r: number;
  min_reward_risk: number;
  next_review_at_utc?: string | null;
  expires_at_utc?: string | null;
}

/** Selection of one immutable Research-owned reasoned scenario. */
export interface ResearchStressScenarioCreateInput {
  scenario_key:
    | "broad_market_dislocation"
    | "severe_fx_repricing"
    | "liquidity_withdrawal"
    | "venue_connectivity_disruption"
    | "extreme_combined_tail";
  hypothesis: string;
}

export const stressScenarioCreateSchema = z.object({
  available: z.boolean(),
  reason: z.string().nullable().optional(),
  evidence: z.record(z.string(), z.unknown()),
});
export type ResearchStressScenarioCreate = z.infer<
  typeof stressScenarioCreateSchema
>;

/** Latest performance-drift evidence. A suspension is advisory only. */
export const driftSchema = z.object({
  available: z.boolean(),
  reason: z.string().nullable(),
  evidence: z.record(z.string(), z.unknown()).nullable(),
  suspension_enacted_by_ui: z.boolean().optional(),
});
export type ResearchDrift = z.infer<typeof driftSchema>;

// --- Request inputs ------------------------------------------------------

/** Safe dataset selection. Market rows never travel in a request body. */
export interface ResearchDatasetSelection {
  symbol: string;
  timeframe?: string;
  source_id?: string | null;
  start?: string | null;
  end?: string | null;
  bar_limit?: number;
  asset_class?: string | null;
}

/** Safe run-create input. The server resolves everything else. */
export interface ResearchRunCreateInput {
  dataset: ResearchDatasetSelection;
  dataset_id?: string | null;
  preset?: string;
  selected_stages?: string[];
  approved_overrides?: Record<string, unknown>;
  seed?: number | null;
  performance_report_id?: string | null;
  reason?: string | null;
  force_rerun?: boolean;
  save_artifacts?: boolean;
  hypothesis?: string | null;
}

/** Experiment-create input. */
export interface ResearchExperimentCreateInput {
  name: string;
  hypothesis: string;
  notes?: string | null;
  tags?: string[];
}

/** Automation-batch input. */
export interface ResearchAutomationInput {
  experiment_id: string;
  symbols: string[];
  timeframe?: string;
  source_id?: string | null;
  start?: string | null;
  end?: string | null;
  bar_limit?: number;
  preset?: string;
  selected_stages?: string[];
  approved_overrides?: Record<string, unknown>;
  use_cache?: boolean;
  force_rerun?: boolean;
  save_artifacts?: boolean;
  trigger?: "manual" | "scheduled";
  reason?: string | null;
}

// --- Operations ----------------------------------------------------------

/** List every server-owned preset (requires `research:read`). */
export function listPresets(
  options?: RequestOptions,
): Promise<ApiResponse<ResearchPresetCatalogue>> {
  return request<ResearchPresetCatalogue>(researchRoutes.presets, {
    schema: presetCatalogueSchema,
    ...options,
  });
}

/** Read the research ledger for the entry page (requires `research:read`). */
export function getDashboard(
  options?: RequestOptions,
): Promise<ApiResponse<ResearchDashboard>> {
  return request<ResearchDashboard>(researchRoutes.dashboard, {
    schema: dashboardSchema,
    ...options,
  });
}

/** Create one experiment (requires `research:run`). */
export function createExperiment(
  input: ResearchExperimentCreateInput,
  options?: RequestOptions,
): Promise<ApiResponse<ResearchExperimentDetail>> {
  return request<ResearchExperimentDetail>(researchRoutes.createExperiment, {
    schema: experimentDetailSchema,
    body: { tags: [], notes: null, ...input },
    ...options,
  });
}

/** List owned experiments, newest first (requires `research:read`). */
export function listExperiments(
  options?: RequestOptions,
): Promise<ApiResponse<{ experiments: ResearchExperimentSummary[] }>> {
  return request<{ experiments: ResearchExperimentSummary[] }>(
    researchRoutes.experiments,
    { schema: experimentListSchema, ...options },
  );
}

/** Read one experiment with its run ledger (requires `research:read`). */
export function getExperiment(
  experimentId: string,
  options?: RequestOptions,
): Promise<ApiResponse<ResearchExperimentDetail>> {
  return request<ResearchExperimentDetail>(researchRoutes.experiment, {
    schema: experimentDetailSchema,
    pathParams: { experiment_id: experimentId },
    ...options,
  });
}

/** Queue one background run (requires `research:run`). */
export function createRun(
  experimentId: string,
  input: ResearchRunCreateInput,
  options?: RequestOptions,
): Promise<ApiResponse<ResearchRunDetail>> {
  return request<ResearchRunDetail>(researchRoutes.createRun, {
    schema: runDetailSchema,
    pathParams: { experiment_id: experimentId },
    body: input,
    ...options,
  });
}

/** List owned runs, newest first, including failures (requires `research:read`). */
export function listRuns(
  filters?: { experimentId?: string; batchId?: string },
  options?: RequestOptions,
): Promise<ApiResponse<{ runs: ResearchRunSummary[] }>> {
  return request<{ runs: ResearchRunSummary[] }>(researchRoutes.runs, {
    schema: runListSchema,
    query: {
      experiment_id: filters?.experimentId ?? null,
      batch_id: filters?.batchId ?? null,
    },
    ...options,
  });
}

/** Read one run header with stage status (requires `research:read`). */
export function getRun(
  runId: string,
  options?: RequestOptions,
): Promise<ApiResponse<ResearchRunDetail>> {
  return request<ResearchRunDetail>(researchRoutes.runDetail, {
    schema: runDetailSchema,
    pathParams: { run_id: runId },
    ...options,
  });
}

/** Read the registered report for the diagnostic viewer (requires `research:read`). */
export function getRunReport(
  runId: string,
  options?: RequestOptions,
): Promise<ApiResponse<ResearchRunReport>> {
  return request<ResearchRunReport>(researchRoutes.runReport, {
    schema: runReportSchema,
    pathParams: { run_id: runId },
    ...options,
  });
}

/** Read one navigable stage view (requires `research:read`). */
export function getStage(
  runId: string,
  stage: string,
  query?: { scenarioId?: string; profileId?: string },
  options?: RequestOptions,
): Promise<ApiResponse<ResearchStageView>> {
  return request<ResearchStageView>(researchRoutes.runStage, {
    schema: stageViewSchema,
    pathParams: { run_id: runId, stage },
    query: {
      scenario_id: query?.scenarioId ?? null,
      profile_id: query?.profileId ?? null,
    },
    ...options,
  });
}

/** List safe artifact references for one run (requires `research:read`). */
export function listArtifacts(
  runId: string,
  options?: RequestOptions,
): Promise<ApiResponse<ResearchArtifactList>> {
  return request<ResearchArtifactList>(researchRoutes.runArtifacts, {
    schema: artifactListSchema,
    pathParams: { run_id: runId },
    ...options,
  });
}

/** Request cooperative cancellation of one run (requires `research:run`). */
export function cancelRun(
  runId: string,
  options?: RequestOptions,
): Promise<ApiResponse<ResearchRunDetail>> {
  return request<ResearchRunDetail>(researchRoutes.cancelRun, {
    schema: runDetailSchema,
    pathParams: { run_id: runId },
    ...options,
  });
}

/** Compare two to five owned runs, server-derived (requires `research:read`). */
export function compareRuns(
  runIds: string[],
  options?: RequestOptions,
): Promise<ApiResponse<ResearchComparison>> {
  return request<ResearchComparison>(researchRoutes.compareRuns, {
    schema: comparisonSchema,
    body: { run_ids: runIds },
    ...options,
  });
}

/** Queue one multi-symbol batch (requires `research:run`). */
export function createAutomationBatch(
  input: ResearchAutomationInput,
  options?: RequestOptions,
): Promise<ApiResponse<ResearchAutomationBatch>> {
  return request<ResearchAutomationBatch>(researchRoutes.createAutomation, {
    schema: automationBatchSchema,
    body: input,
    ...options,
  });
}

/** Read one batch with per-symbol progress (requires `research:read`). */
export function getAutomationBatch(
  batchId: string,
  options?: RequestOptions,
): Promise<ApiResponse<ResearchAutomationBatch>> {
  return request<ResearchAutomationBatch>(researchRoutes.automationBatch, {
    schema: automationBatchSchema,
    pathParams: { batch_id: batchId },
    ...options,
  });
}

/** Read the approved expectancy profile (requires `research:read`). */
export function getExpectancy(
  query?: { profileId?: string; strategyRef?: string },
  options?: RequestOptions,
): Promise<ApiResponse<ResearchExpectancy>> {
  return request<ResearchExpectancy>(researchRoutes.expectancy, {
    schema: expectancySchema,
    query: {
      profile_id: query?.profileId ?? null,
      strategy_ref: query?.strategyRef ?? null,
    },
    ...options,
  });
}

/** Create one draft profile bound to a completed Research run. */
export function createExpectancy(
  input: ResearchExpectancyCreateInput,
  options?: RequestOptions,
): Promise<ApiResponse<ResearchExpectancyTransition>> {
  return request<ResearchExpectancyTransition>(
    researchRoutes.createExpectancy,
    {
      schema: expectancyTransitionSchema,
      body: { regimes: [], sessions: [], ...input },
      ...options,
    },
  );
}

/** Advance one expectancy profile (requires `research:govern`). */
export function transitionExpectancy(
  profileId: string,
  input: ResearchExpectancyTransitionInput,
  options?: RequestOptions,
): Promise<ApiResponse<ResearchExpectancyTransition>> {
  return request<ResearchExpectancyTransition>(
    researchRoutes.transitionExpectancy,
    {
      schema: expectancyTransitionSchema,
      pathParams: { profile_id: profileId },
      body: input,
      ...options,
    },
  );
}

/** Read the latest performance-drift evidence (requires `research:read`). */
export function getDrift(
  query?: { profileId?: string },
  options?: RequestOptions,
): Promise<ApiResponse<ResearchDrift>> {
  return request<ResearchDrift>(researchRoutes.drift, {
    schema: driftSchema,
    query: { profile_id: query?.profileId ?? null },
    ...options,
  });
}

/** Persist one approved reasoned stress scenario. */
export function createStressScenario(
  input: ResearchStressScenarioCreateInput,
  options?: RequestOptions,
): Promise<ApiResponse<ResearchStressScenarioCreate>> {
  return request<ResearchStressScenarioCreate>(
    researchRoutes.createStressScenario,
    { schema: stressScenarioCreateSchema, body: input, ...options },
  );
}

/**
 * Open the ordered progress stream for one run.
 *
 * Yields validated `StreamEvent` frames until the run is terminal or the
 * caller aborts. This reuses the canonical SSE transport rather than adding a
 * second polling protocol.
 */
export function openRunEvents(
  runId: string,
  options: StreamTransportOptions = {},
): AsyncIterable<StreamEvent> {
  return openStream(researchRoutes.runEvents, {
    pathParams: { run_id: runId },
    ...options,
  });
}

// --- Legacy synchronous operation ---------------------------------------

/** Advisory research report from the original synchronous route. */
export const researchReportSchema = z.record(z.string(), z.unknown());
export type ResearchReport = z.infer<typeof researchReportSchema>;

/** Request body for the original synchronous Edge Lab run. */
export interface ResearchRunInput {
  hypothesis: string;
  dataset: Record<string, unknown>;
  config: Record<string, unknown>;
}

/**
 * Run one Edge Lab profile synchronously (requires `research:run`).
 *
 * Retained for the original boundary. The workbench uses `createRun`, which
 * never asks a browser to construct owner-domain contracts.
 */
export function run(
  input: ResearchRunInput,
  options?: RequestOptions,
): Promise<ApiResponse<ResearchReport>> {
  return request<ResearchReport>(researchRoutes.run, {
    schema: researchReportSchema,
    body: input,
    ...options,
  });
}

/** Aggregated research client. */
export const research = {
  run,
  listPresets,
  getDashboard,
  createExperiment,
  listExperiments,
  getExperiment,
  createRun,
  listRuns,
  getRun,
  getRunReport,
  getStage,
  listArtifacts,
  cancelRun,
  compareRuns,
  createAutomationBatch,
  getAutomationBatch,
  getExpectancy,
  createExpectancy,
  transitionExpectancy,
  getDrift,
  createStressScenario,
  openRunEvents,
};
