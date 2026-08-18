/**
 * Research workbench component tests (FEAT-UI-28, plan §14.2).
 *
 * Covers stage status and prerequisites, warning grouping, readiness and score
 * rendering, study classification, seasonality heatmap cells, artifact
 * metadata, and the explicit non-success evidence states.
 */

import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { ResearchRunDetail, ResearchStageView } from "@/clients";

import { ResearchStageNav } from "./ResearchStageNav";
import { ResearchWarnings } from "./ResearchWarnings";
import { EvidenceState, Heatmap, WarningList } from "./evidence";
import { MetricsPanel } from "./panels/MetricsPanel";
import { MarketStructurePanel } from "./panels/MarketStructurePanel";
import { OverviewPanel } from "./panels/OverviewPanel";
import { ProfilePanel } from "./panels/ProfilePanel";
import { SeasonalityPanel } from "./panels/SeasonalityPanel";
import { StudiesPanel } from "./panels/StudiesPanel";
import { StressPanel } from "./panels/StressPanel";
import { annotatedStages, groupWarnings } from "./research-selectors";

const clientMocks = vi.hoisted(() => ({
  createStressScenario: vi.fn(),
  listPresets: vi.fn(),
}));

vi.mock("@/clients", () => ({
  ApiClientError: class ApiClientError extends Error {},
  apiClients: { research: clientMocks },
}));

/** One completed run detail carrying realistic Research evidence. */
function makeDetail(
  overrides: Partial<ResearchRunDetail> = {},
): ResearchRunDetail {
  return {
    run_id: "rrn-1",
    experiment_id: "rxp-1",
    batch_id: null,
    status: "completed",
    hypothesis: "Returns mean-revert over one research bar.",
    symbol: "EURUSD",
    timeframe: "H1",
    preset: "standard_edge",
    selected_stages: ["data", "metrics", "studies"],
    reason: "unit test",
    force_rerun: false,
    created_at: "2026-08-18T00:00:00Z",
    started_at: "2026-08-18T00:00:01Z",
    completed_at: "2026-08-18T00:00:09Z",
    report_id: "research-report-abc",
    dataset_hash: "a".repeat(64),
    configuration_hash: "b".repeat(64),
    generated_at: "2026-08-18T00:00:09Z",
    duration_ms: 8400,
    score: 80,
    readiness: "REVIEW_READY",
    advisory_only: true,
    warning_count: 2,
    error: null,
    dataset: null,
    effective_configuration: {},
    stage_status: {
      overview: { state: "completed", reason: null },
      data: { state: "completed", reason: null },
      features: { state: "not_selected", reason: "STAGE_NOT_SELECTED" },
      validation: { state: "not_selected", reason: "STAGE_NOT_SELECTED" },
      metrics: { state: "completed", reason: null },
      studies: { state: "unavailable", reason: "STAGE_PRODUCED_NO_EVIDENCE" },
      seasonality: { state: "not_selected", reason: "STAGE_NOT_SELECTED" },
      "market-structure": {
        state: "not_selected",
        reason: "STAGE_NOT_SELECTED",
      },
      modeling: { state: "not_selected", reason: "STAGE_NOT_SELECTED" },
      profile: { state: "completed", reason: null },
      intelligence: { state: "completed", reason: null },
      stress: { state: "completed", reason: null },
      artifacts: { state: "completed", reason: null },
      provenance: { state: "completed", reason: null },
    },
    stage_views: ["overview", "data", "metrics"],
    artifacts: [],
    warnings: [
      {
        code: "SPARSE_BUCKET",
        message: "Seasonality bucket has too few samples",
        severity: "warning",
        field_path: "session.tokyo",
        details: {},
      },
      {
        code: "STUDY_FAILED",
        message: "A selected edge study failed",
        severity: "error",
        field_path: "studies.session",
        details: {},
      },
    ],
    provenance: {
      available: true,
      report_id: "research-report-abc",
      seeds: { statistics: 7, modeling: 7 },
      dependency_versions: { research: "v1" },
      source_references: ["ref-1"],
      selected_stages: ["data", "metrics"],
      generated_at: "2026-08-18T00:00:09Z",
      duration_ms: 8400,
      advisory_only: true,
      warnings: [],
    },
    overview: {
      available: true,
      hypothesis: "Returns mean-revert over one research bar.",
      selected_stages: ["data", "metrics", "studies"],
      scorecard: {
        available: true,
        score: 80,
        readiness: "REVIEW_READY",
        reasons: ["all_available_evidence_assembled"],
        score_rows: [
          { criterion: "metrics", score: 20, families: 7 },
          { criterion: "edges", score: 25, confirmed: 1 },
        ],
        snapshot_id: "research-snapshot-xyz",
      },
      study_counts: { confirmed: 1, contradicted: 1, inconclusive: 1 },
      structure: { score: 42, verdict: "ranging", strategy_fit: {} },
      sessions: [
        {
          session: "london",
          sample_count: 225,
          mean_return: 0.00019,
          win_rate: 0.49,
        },
      ],
      modeling_insights: {},
      warnings: [],
    },
    ...overrides,
  };
}

/** One stage view carrying the named evidence branch. */
function makeView(
  stage: string,
  evidence: Record<string, unknown>,
  state = "completed",
): ResearchStageView {
  return { stage, state, reason: null, evidence, warnings: [] };
}

describe("stage navigation — server-derived status", () => {
  it("annotates each registered stage with its server state", () => {
    const stages = annotatedStages(makeDetail());
    const byId = Object.fromEntries(
      stages.map((stage) => [stage.id, stage.state]),
    );
    expect(byId.metrics).toBe("completed");
    expect(byId.studies).toBe("unavailable");
    expect(byId.seasonality).toBe("not_selected");
  });

  it("keeps unselected stages visible and labelled rather than hiding them", () => {
    render(
      <ResearchStageNav
        detail={makeDetail()}
        experimentId="rxp-1"
        runId="rrn-1"
        activeStage="metrics"
      />,
    );
    const nav = screen.getByRole("navigation", { name: "Research stages" });
    expect(within(nav).getByText("Seasonality")).toBeDefined();
    expect(within(nav).getAllByText("Not selected").length).toBeGreaterThan(0);
    expect(within(nav).getByText("Unavailable")).toBeDefined();
  });

  it("marks the active stage as the current page", () => {
    render(
      <ResearchStageNav
        detail={makeDetail()}
        experimentId="rxp-1"
        runId="rrn-1"
        activeStage="metrics"
      />,
    );
    const active = screen.getByRole("link", { current: "page" });
    expect(active.textContent).toContain("Metrics");
  });
});

describe("evidence states — never collapsed into one message", () => {
  it("distinguishes not-selected from unavailable", () => {
    const { rerender, container } = render(
      <EvidenceState state="not_selected" reason="STAGE_NOT_SELECTED" />,
    );
    expect(container.textContent).toContain("was not selected");
    rerender(
      <EvidenceState state="unavailable" reason="STAGE_PRODUCED_NO_EVIDENCE" />,
    );
    expect(container.textContent).toContain("produced no evidence");
    rerender(<EvidenceState state="running" />);
    expect(container.textContent).toContain("still running");
    rerender(<EvidenceState state="cancelled" />);
    expect(container.textContent).toContain("cancelled");
  });
});

describe("warning grouping", () => {
  it("orders groups by severity, most severe first", () => {
    const groups = groupWarnings(makeDetail().warnings);
    expect(groups[0].severity).toBe("error");
    expect(groups[1].severity).toBe("warning");
  });

  it("renders every warning with its code", () => {
    render(<ResearchWarnings warnings={makeDetail().warnings} />);
    expect(screen.getByText("SPARSE_BUCKET")).toBeDefined();
    expect(screen.getByText("STUDY_FAILED")).toBeDefined();
  });

  it("states plainly when there are no warnings", () => {
    const { container } = render(<WarningList warnings={[]} />);
    expect(container.textContent).toContain("No warnings reported");
  });
});

describe("overview panel", () => {
  it("renders readiness, score rows, and every study outcome", () => {
    const detail = makeDetail();
    const { container } = render(
      <OverviewPanel detail={detail} view={makeView("overview", {})} />,
    );
    expect(container.textContent).toContain("REVIEW_READY");
    expect(container.textContent).toContain("80.0");
    expect(container.textContent).toContain("contradicted");
    expect(container.textContent).toContain("inconclusive");
    expect(container.textContent).toContain("all_available_evidence_assembled");
  });

  it("offers cross-domain links instead of duplicating those workflows", () => {
    render(
      <OverviewPanel detail={makeDetail()} view={makeView("overview", {})} />,
    );
    expect(screen.getByText("Continue in Simulator")).toBeDefined();
    expect(screen.getByText("Open Monte Carlo")).toBeDefined();
    expect(screen.getByText("Open Strategy Import")).toBeDefined();
  });

  it("says a failed run failed rather than recommending an action", () => {
    const { container } = render(
      <OverviewPanel
        detail={makeDetail({ status: "failed", readiness: null })}
        view={makeView("overview", {})}
      />,
    );
    expect(container.textContent).toContain("This run failed");
  });
});

describe("metrics panel", () => {
  it("renders an unavailable family as a dash, never as zero", () => {
    const view = makeView("metrics", {
      metrics: {
        metrics: {
          returns: { value: 0.0074, unit: "ratio", sample_size: 59 },
          spread: { value: null, unit: null, undefined_reason: "NO_SPREAD" },
        },
      },
    });
    const { container } = render(
      <MetricsPanel detail={makeDetail()} view={view} />,
    );
    expect(container.textContent).toContain("Returns");
    expect(container.textContent).toContain("0.0074");
    expect(container.textContent).toContain("NO_SPREAD");
    expect(container.textContent).toContain("not reported");
    expect(container.textContent).not.toContain("0.000000 ratio");
  });
});

describe("studies panel", () => {
  it("shows the classification each study received, including contradicted", () => {
    const view = makeView("studies", {
      studies: {
        results: [
          {
            study: "mean_reversion",
            classification: "confirmed",
            statistics: { observed_samples: 120 },
            null_evidence: { percentile: 0.98 },
            seed: 7,
            warnings: [],
          },
          {
            study: "trend_persistence",
            classification: "contradicted",
            statistics: { observed_samples: 90 },
            null_evidence: { percentile: 0.02 },
            seed: 7,
            warnings: [],
          },
        ],
      },
    });
    const { container } = render(
      <StudiesPanel detail={makeDetail()} view={view} />,
    );
    expect(container.textContent).toContain("confirmed");
    expect(container.textContent).toContain("contradicted");
    expect(container.textContent).toContain("Null evidence");
  });

  it("states that the stage did not run when no evidence exists", () => {
    const { container } = render(
      <StudiesPanel detail={makeDetail()} view={makeView("studies", {})} />,
    );
    expect(container.textContent).toContain("did not run");
  });
});

describe("seasonality panel", () => {
  it("renders hour buckets from the evidence the server published", () => {
    const view = makeView("seasonality", {
      seasonality: {
        adr_period: 14,
        row_count: 600,
        sessions: [],
        hours: [
          { hour: 0, sample_count: 24, mean_return: 0.0017, win_rate: 0.62 },
          { hour: 1, sample_count: 24, mean_return: -0.0022, win_rate: 0.41 },
        ],
        hour_by_weekday: [
          { weekday: 0, hour: 0, sample_count: 3, mean_return: 0.0094 },
        ],
        calendar: { year: [], month: [], day_of_month: [], day_of_week: [] },
        daily_extremes: {
          day_count: 25,
          high_ownership: [],
          low_ownership: [],
        },
        opportunity: { session: "new_york", best_hour: 19 },
        extremes: { max_return: 0.02, min_return: -0.02 },
      },
    });
    const { container } = render(
      <SeasonalityPanel detail={makeDetail()} view={view} />,
    );
    expect(container.textContent).toContain("0.0017");
    expect(container.textContent).toContain("-0.0022");
  });
});

describe("heatmap primitive", () => {
  it("marks an absent cell instead of drawing it as a value", () => {
    const { container } = render(
      <Heatmap
        rowLabels={["Mon"]}
        columnLabels={["00", "01"]}
        values={[[0.5, null]]}
      />,
    );
    const cells = container.querySelectorAll(".research-heatmap__cell");
    expect(cells.length).toBe(2);
    expect(cells[1].className).toContain("research-heatmap__cell--empty");
    expect(cells[1].textContent).toBe("·");
  });
});

describe("profile panel", () => {
  it("renders score rows and the snapshot identity Research published", () => {
    const view = makeView("profiles", {
      profiles: {
        score: 80,
        readiness: "REVIEW_READY",
        reasons: ["all_available_evidence_assembled"],
        score_rows: [{ criterion: "metrics", score: 20, families: 7 }],
        stage_count: 9,
        snapshot_id: "research-snapshot-xyz",
        snapshot_generated_at: "2026-08-18T00:00:09Z",
      },
    });
    const { container } = render(
      <ProfilePanel detail={makeDetail()} view={view} />,
    );
    expect(container.textContent).toContain("REVIEW_READY");
    expect(container.textContent).toContain("research-snapshot-xyz");
    expect(container.textContent).toContain("metrics");
  });
});

describe("market-structure geometry", () => {
  it("renders confirmed swings, directional legs, and truncation evidence", () => {
    render(
      <MarketStructurePanel
        detail={makeDetail()}
        view={makeView("market-structure", {
          market_structure: {
            schema_version: "v1",
            score: 72,
            verdict: "trending",
            strategy_fit: { advisory_only: true },
            structure: {
              swing_window: 5,
              atr_period: 14,
              atr: 2,
              trend_threshold: 0.5,
              range_threshold: 0.2,
              swing_points: [
                {
                  position: 5,
                  timestamp: "2026-01-01T05:00:00Z",
                  kind: "high",
                  price: 110,
                },
                {
                  position: 11,
                  timestamp: "2026-01-01T11:00:00Z",
                  kind: "low",
                  price: 90,
                },
              ],
              trend_legs: [
                {
                  start_position: 5,
                  end_position: 11,
                  direction: "down",
                  bar_count: 6,
                  price_change: -20,
                  atr_multiple: 10,
                },
              ],
              geometry_point_limit: 256,
              geometry_total_points: 300,
              geometry_truncated: true,
            },
          },
        })}
      />,
    );

    fireEvent.click(screen.getByRole("tab", { name: "Geometry" }));
    expect(screen.getByText("Confirmed swing points")).toBeDefined();
    expect(screen.getByText("Directional trend legs")).toBeDefined();
    expect(screen.getByText("truncated")).toBeDefined();
    expect(screen.getByText("down")).toBeDefined();
  });

  it("retains the explicit fallback for reports predating geometry", () => {
    render(
      <MarketStructurePanel
        detail={makeDetail()}
        view={makeView("market-structure", {
          market_structure: {
            schema_version: "v1",
            score: 20,
            verdict: "ranging",
            strategy_fit: { advisory_only: true },
            structure: { swing_window: 5, atr_period: 14, atr: 1 },
          },
        })}
      />,
    );

    fireEvent.click(screen.getByRole("tab", { name: "Geometry" }));
    expect(
      screen.getByText(/does not publish per-swing points or trend-leg series/),
    ).toBeDefined();
  });

  it("creates only a registered reasoned stress scenario", async () => {
    clientMocks.listPresets.mockResolvedValue({
      status: "success",
      data: {
        presets: [],
        stages: [],
        stage_views: [],
        stress_scenarios: [
          {
            scenario_key: "broad_market_dislocation",
            name: "Broad market dislocation",
            assumption_ref: "HQA-STRESS-ASSUMPTION-001-v1",
            rationale: "Approved rationale",
            shocks: [],
          },
        ],
      },
    });
    clientMocks.createStressScenario.mockResolvedValue({
      status: "success",
      data: { available: true, evidence: { scenario_id: "id-scenario" } },
    });
    const onScenarioChange = vi.fn();
    render(
      <StressPanel
        detail={makeDetail()}
        view={makeView("stress", {
          stress: {
            available: false,
            reason: "NO_EVIDENCE",
            creation_permitted: true,
          },
        })}
        scenarioId=""
        onScenarioChange={onScenarioChange}
      />,
    );

    expect(await screen.findByText("Broad market dislocation")).toBeDefined();
    fireEvent.change(screen.getByLabelText("Stress objective"), {
      target: { value: "Can the evidence tolerate a broad dislocation?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create scenario" }));

    expect(await screen.findByText("Scenario id-scenario.")).toBeDefined();
    expect(onScenarioChange).toHaveBeenCalledWith("id-scenario");
  });
});
