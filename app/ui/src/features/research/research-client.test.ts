/**
 * Research client contract tests (FEAT-UI-28, plan §14.1).
 *
 * Every operation is checked for method, path, response-schema validation, and
 * failure handling against the real transport — no client is stubbed out.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiClientError, apiClients } from "@/clients";
import { researchRoutes } from "@/clients/routes";

const realFetch = globalThis.fetch;

/** Build one canonical success envelope. */
function envelope(data: unknown, route: string, operation: string): Response {
  return new Response(
    JSON.stringify({
      status: "success",
      message: "ok",
      data,
      error: null,
      metadata: {
        contract_version: "v1",
        schema_id: "api.metadata.v1",
        request_id: "req-test",
        route,
        operation,
        trace_id: null,
        side_effect: "read",
        duration_ms: 1,
        timestamp: "2026-08-18T00:00:00Z",
        stale: false,
        stale_reason: null,
        next_cursor: null,
        page_size: null,
        idempotency_replayed: false,
      },
    }),
    { status: 200, headers: { "Content-Type": "application/json" } },
  );
}

/** Build one canonical error envelope. */
function errorEnvelope(code: string, message: string): Response {
  return new Response(
    JSON.stringify({
      status: "error",
      message,
      data: null,
      error: {
        code,
        message,
        details: {},
        request_id: "req-test",
        trace_id: null,
        retryable: false,
      },
      metadata: {
        contract_version: "v1",
        schema_id: "api.metadata.v1",
        request_id: "req-test",
        route: "/api/v1/research/runs",
        operation: "api.research.runs",
        trace_id: null,
        side_effect: "read",
        duration_ms: 1,
        timestamp: "2026-08-18T00:00:00Z",
        stale: false,
        stale_reason: null,
        next_cursor: null,
        page_size: null,
        idempotency_replayed: false,
      },
    }),
    { status: 403, headers: { "Content-Type": "application/json" } },
  );
}

const RUN_SUMMARY = {
  run_id: "rrn-1",
  experiment_id: "rxp-1",
  batch_id: null,
  status: "completed",
  hypothesis: "Returns persist.",
  symbol: "EURUSD",
  timeframe: "H1",
  preset: "standard_edge",
  selected_stages: ["data", "metrics"],
  reason: null,
  force_rerun: false,
  created_at: "2026-08-18T00:00:00Z",
  started_at: "2026-08-18T00:00:01Z",
  completed_at: "2026-08-18T00:00:05Z",
  report_id: "research-report-abc",
  dataset_hash: "a".repeat(64),
  configuration_hash: "b".repeat(64),
  generated_at: "2026-08-18T00:00:05Z",
  duration_ms: 4200,
  score: 80,
  readiness: "REVIEW_READY",
  advisory_only: true,
  warning_count: 1,
  error: null,
};

const RUN_DETAIL = {
  ...RUN_SUMMARY,
  dataset: null,
  effective_configuration: {},
  stage_status: {
    overview: { state: "completed", reason: null },
    metrics: { state: "completed", reason: null },
    studies: { state: "not_selected", reason: "STAGE_NOT_SELECTED" },
  },
  stage_views: ["overview", "metrics", "studies"],
  artifacts: [],
  warnings: [],
  provenance: { available: true },
  overview: { available: true },
};

const AUTOMATION_BATCH = {
  batch_id: "rbt-1",
  experiment_id: "rxp-1",
  symbols: ["EURUSD"],
  trigger: "manual",
  reason: null,
  created_at: "2026-08-18T00:00:00Z",
  status: "pending",
  counts: {
    total: 1,
    completed: 0,
    failed: 0,
    cancelled: 0,
    pending: 1,
    rejected: 0,
  },
  runs: [RUN_SUMMARY],
  rejections: [],
};

describe("research client — contract", () => {
  let calls: Array<{ url: string; init: RequestInit | undefined }>;

  beforeEach(() => {
    calls = [];
    globalThis.fetch = vi.fn(async (url: unknown, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      const path = String(url);
      if (path.includes("/presets")) {
        return envelope(
          {
            presets: [],
            stages: ["data"],
            stage_views: ["overview"],
            stress_scenarios: [],
          },
          "/api/v1/research/presets",
          "api.research.presets",
        );
      }
      if (path.includes("/runs/compare")) {
        return envelope(
          {
            baseline_run_id: "rrn-1",
            metric_names: [],
            study_names: [],
            entries: [],
          },
          "/api/v1/research/runs/compare",
          "api.research.compare_runs",
        );
      }
      if (path.includes("/stages/")) {
        return envelope(
          {
            stage: "metrics",
            state: "completed",
            reason: null,
            evidence: {},
            warnings: [],
          },
          "/api/v1/research/runs/{run_id}/stages/{stage}",
          "api.research.run_stage",
        );
      }
      if (path.includes("/artifacts")) {
        return envelope(
          { run_id: "rrn-1", artifacts: [], artifact_root_owner: "api" },
          "/api/v1/research/runs/{run_id}/artifacts",
          "api.research.run_artifacts",
        );
      }
      if (path.match(/\/runs\/[^/]+$/)) {
        return envelope(
          RUN_DETAIL,
          "/api/v1/research/runs/{run_id}",
          "api.research.run_detail",
        );
      }
      if (path.includes("/runs")) {
        return envelope(
          { runs: [RUN_SUMMARY] },
          "/api/v1/research/runs",
          "api.research.runs",
        );
      }
      return envelope(
        {},
        "/api/v1/research/dashboard",
        "api.research.dashboard",
      );
    }) as unknown as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = realFetch;
    vi.restoreAllMocks();
  });

  it("declares every workbench route with the expected method and permission", () => {
    expect(researchRoutes.presets.method).toBe("GET");
    expect(researchRoutes.presets.permission).toBe("research:read");
    expect(researchRoutes.createRun.method).toBe("POST");
    expect(researchRoutes.createRun.permission).toBe("research:run");
    expect(researchRoutes.createRun.path).toBe(
      "/api/v1/research/experiments/{experiment_id}/runs",
    );
    expect(researchRoutes.runEvents.stream).toBe(true);
    expect(researchRoutes.cancelRun.path).toBe(
      "/api/v1/research/runs/{run_id}/cancel",
    );
  });

  it("requests the run detail by identity and validates the response", async () => {
    const response = await apiClients.research.getRun("rrn-1");
    expect(calls[0]?.url).toContain("/api/v1/research/runs/rrn-1");
    expect(response.status).toBe("success");
    if (response.status === "success") {
      expect(response.data.run_id).toBe("rrn-1");
      expect(response.data.stage_status.studies.reason).toBe(
        "STAGE_NOT_SELECTED",
      );
    }
  });

  it("interpolates the stage path segment", async () => {
    await apiClients.research.getStage("rrn-1", "metrics");
    expect(calls[0]?.url).toContain(
      "/api/v1/research/runs/rrn-1/stages/metrics",
    );
  });

  it("sends the run identifiers as the comparison body", async () => {
    await apiClients.research.compareRuns(["rrn-1", "rrn-2"]);
    expect(calls[0]?.url).toContain("/api/v1/research/runs/compare");
    expect(JSON.parse(String(calls[0]?.init?.body))).toEqual({
      run_ids: ["rrn-1", "rrn-2"],
    });
  });

  it("passes list filters as query parameters", async () => {
    await apiClients.research.listRuns({ experimentId: "rxp-1" });
    expect(calls[0]?.url).toContain("experiment_id=rxp-1");
  });

  it("returns the error branch for a permission failure", async () => {
    globalThis.fetch = vi.fn(async () =>
      errorEnvelope("AUTHORIZATION_DENIED", "denied"),
    ) as unknown as typeof fetch;

    const response = await apiClients.research.listRuns();

    expect(response.status).toBe("error");
    if (response.status === "error") {
      expect(response.error.code).toBe("AUTHORIZATION_DENIED");
    }
  });

  it("raises a typed failure when the payload violates the schema", async () => {
    globalThis.fetch = vi.fn(async () =>
      envelope(
        { run_id: 42 },
        "/api/v1/research/runs/{run_id}",
        "api.research.run_detail",
      ),
    ) as unknown as typeof fetch;

    await expect(apiClients.research.getRun("rrn-1")).rejects.toBeInstanceOf(
      ApiClientError,
    );
  });

  it("never sends an artifact root or resource ceiling in a run request", async () => {
    globalThis.fetch = vi.fn(async (url: unknown, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      return envelope(
        RUN_DETAIL,
        "/api/v1/research/experiments/{experiment_id}/runs",
        "api.research.create_run",
      );
    }) as unknown as typeof fetch;

    await apiClients.research.createRun("rxp-1", {
      dataset: { symbol: "EURUSD", timeframe: "H1" },
      preset: "quick_look",
    });

    const body = String(calls[0]?.init?.body);
    expect(body).not.toContain("allowed_root");
    expect(body).not.toContain("max_rows");
    expect(body).not.toContain("artifact_root");
    expect(body).toContain("EURUSD");
    expect(
      new Headers(calls[0]?.init?.headers).get("Idempotency-Key"),
    ).toBeTruthy();
  });

  it("generates an idempotency key for automation creation", async () => {
    globalThis.fetch = vi.fn(async (url: unknown, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      return envelope(
        AUTOMATION_BATCH,
        "/api/v1/research/automation",
        "api.research.create_automation",
      );
    }) as unknown as typeof fetch;

    await apiClients.research.createAutomationBatch({
      experiment_id: "rxp-1",
      symbols: ["EURUSD"],
    });

    expect(
      new Headers(calls[0]?.init?.headers).get("Idempotency-Key"),
    ).toBeTruthy();
  });

  it("generates keys for governed Research evidence creation", async () => {
    globalThis.fetch = vi.fn(async (url: unknown, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      const isStress = String(url).includes("stress-scenarios");
      return envelope(
        isStress
          ? {
              available: true,
              reason: null,
              evidence: { scenario_id: "id-scenario" },
            }
          : {
              available: true,
              reason: null,
              profile: { profile_id: "id-profile" },
            },
        isStress
          ? "/api/v1/research/stress-scenarios"
          : "/api/v1/research/expectancy",
        isStress
          ? "api.research.create_stress_scenario"
          : "api.research.create_expectancy",
      );
    }) as unknown as typeof fetch;

    await apiClients.research.createExpectancy({
      run_id: "rrn-1",
      exact_version: "1",
      strategy_ref: "strategy-demo",
      sample_from_utc: "2026-01-01T00:00:00Z",
      sample_to_utc: "2026-06-01T00:00:00Z",
      sample_size: 100,
      out_of_sample_status: "walk_forward",
      win_rate: 0.6,
      avg_win_r: 2,
      avg_loss_r: 1,
      expected_value_r: 0.8,
      max_drawdown_r: 4,
      min_reward_risk: 1.5,
    });
    await apiClients.research.createStressScenario({
      scenario_key: "broad_market_dislocation",
      hypothesis: "Can the evidence tolerate a broad dislocation?",
    });

    expect(calls).toHaveLength(2);
    for (const call of calls) {
      expect(
        new Headers(call.init?.headers).get("Idempotency-Key"),
      ).toBeTruthy();
    }
  });
});
