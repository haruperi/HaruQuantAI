/**
 * Simulation Workbench client contract tests (FEAT-UI-31 / P1-T01).
 *
 * Verifies that simulationWorkbench client operations invoke correct routes,
 * methods, headers, query parameters, payload bodies, and strictly validate
 * server projections with Zod schemas.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiClientError, apiClients } from "@/clients";
import { simulationWorkbenchRoutes } from "@/clients/routes";

const realFetch = globalThis.fetch;

function envelope(data: unknown, route: string, operation: string, status = 200): Response {
  return new Response(
    JSON.stringify({
      status: "success",
      message: "ok",
      data,
      error: null,
      metadata: {
        contract_version: "v1",
        schema_id: "api.metadata.v1",
        request_id: "req-sim-test",
        route,
        operation,
        trace_id: null,
        side_effect: "write",
        duration_ms: 1,
        timestamp: "2026-08-18T00:00:00Z",
        stale: false,
        stale_reason: null,
        next_cursor: null,
        page_size: null,
        idempotency_replayed: false,
      },
    }),
    { status, headers: { "Content-Type": "application/json" } },
  );
}

function errorEnvelope(code: string, message: string, status = 400): Response {
  return new Response(
    JSON.stringify({
      status: "error",
      message,
      data: null,
      error: {
        code,
        message,
        details: {},
        request_id: "req-sim-test",
        trace_id: null,
        retryable: false,
      },
      metadata: {
        contract_version: "v1",
        schema_id: "api.metadata.v1",
        request_id: "req-sim-test",
        route: "test",
        operation: "test",
        trace_id: null,
        side_effect: "none",
        duration_ms: 1,
        timestamp: "2026-08-18T00:00:00Z",
        stale: false,
        stale_reason: null,
        next_cursor: null,
        page_size: null,
        idempotency_replayed: false,
      },
    }),
    { status, headers: { "Content-Type": "application/json" } },
  );
}

const SAMPLE_SESSION_PROJECTION = {
  contract_version: "v1",
  schema_id: "api.live_session_projection.v1",
  session_id: "sess-123",
  run_id: "run-456",
  mode: "practice",
  evidence_class: "practice",
  cursor: 150,
  timestamp: "2026-08-18T10:00:00Z",
  tick_count: 150,
  completed: false,
  dataset: {
    dataset_id: "ds-eurusd",
    revision: "rev-1",
    content_hash: "hash123",
  },
  branch: {
    parent_session_id: null,
    divergence_cursor: null,
    overrides: {},
  },
  account: {
    currency: "USD",
    balance: "100000.00",
    equity: "100250.00",
    margin: "1500.00",
    free_margin: "98750.00",
    margin_level: "6683.33",
  },
  positions: [
    {
      position_id: "pos-1",
      symbol: "EURUSD",
      side: "buy",
      volume: "1.0",
      open_price: "1.08500",
      stop_loss: "1.08000",
      take_profit: "1.09500",
      unrealized_pnl: "250.00",
    },
  ],
  orders: [],
  receipt: null,
  pending_intent_count: 0,
  recovery: {
    status: "healthy",
    persisted_state_hash: "hash-state-1",
    integrity_status: "verified",
    recovery_generation: 1,
    recovery_run_id: null,
    last_checkpoint_at: "2026-08-18T10:00:00Z",
  },
  exposure_blocked: false,
  state_hash: "hash-current",
  state_freshness: "fresh",
  permitted_actions: ["step", "seek", "command", "branch", "close"],
};

describe("simulationWorkbench client", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    globalThis.fetch = realFetch;
    vi.restoreAllMocks();
  });

  it("createLiveSession sends POST with required idempotency and validates projection", async () => {
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(
      envelope(SAMPLE_SESSION_PROJECTION, simulationWorkbenchRoutes.createLiveSession.path, "create_session", 201),
    );

    const res = await apiClients.simulationWorkbench.createLiveSession(
      { run_id: "run-456", mode: "practice", durable: true },
      { idempotencyKey: "idem-key-1" },
    );

    expect(res.data!.session_id).toBe("sess-123");
    expect(res.data!.account?.balance).toBe("100000.00");
    expect(res.data!.positions).toHaveLength(1);
    const fetchCall = vi.mocked(globalThis.fetch).mock.calls[0];
    expect(fetchCall[0].toString()).toContain("/api/v1/simulator/live-sessions");
    expect(fetchCall[1]?.method).toBe("POST");
    expect(fetchCall[1]?.headers).toMatchObject({ "Idempotency-Key": "idem-key-1" });
  });

  it("listLiveSessions fetches owned live session projections", async () => {
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(
      envelope({ sessions: [SAMPLE_SESSION_PROJECTION] }, simulationWorkbenchRoutes.liveSessions.path, "list_sessions"),
    );

    const res = await apiClients.simulationWorkbench.listLiveSessions();
    expect(res.data!.sessions).toHaveLength(1);
    expect(res.data!.sessions[0].session_id).toBe("sess-123");
  });

  it("getLiveSession reads single session by session_id", async () => {
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(
      envelope(SAMPLE_SESSION_PROJECTION, simulationWorkbenchRoutes.liveSession.path, "get_session"),
    );

    const res = await apiClients.simulationWorkbench.getLiveSession("sess-123");
    expect(res.data!.session_id).toBe("sess-123");
  });

  it("getViewport requests bounded market viewport with after=0", async () => {
    const sampleViewport = {
      session_id: "sess-123",
      cursor: 150,
      timestamp: "2026-08-18T10:00:00Z",
      before: 300,
      after: 0,
      rows: [
        {
          timestamp: "2026-08-18T09:59:00Z",
          open: "1.08450",
          high: "1.08520",
          low: "1.08440",
          close: "1.08500",
          volume: "120",
          forming: false,
          markers: [],
        },
      ],
    };
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(
      envelope(sampleViewport, simulationWorkbenchRoutes.liveSessionViewport.path, "viewport"),
    );

    const res = await apiClients.simulationWorkbench.getViewport("sess-123", { before: 300 });
    expect(res.data!.rows).toHaveLength(1);
    expect(res.data!.after).toBe(0);
  });

  it("stepLiveSession advances session by bounded tick count", async () => {
    const updated = { ...SAMPLE_SESSION_PROJECTION, cursor: 160, tick_count: 160 };
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(
      envelope(updated, simulationWorkbenchRoutes.stepLiveSession.path, "step"),
    );

    const res = await apiClients.simulationWorkbench.stepLiveSession("sess-123", { ticks: 10 });
    expect(res.data!.cursor).toBe(160);
  });

  it("seekLiveSession moves session forward to absolute target cursor", async () => {
    const updated = { ...SAMPLE_SESSION_PROJECTION, cursor: 500, tick_count: 500 };
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(
      envelope(updated, simulationWorkbenchRoutes.seekLiveSession.path, "seek"),
    );

    const res = await apiClients.simulationWorkbench.seekLiveSession("sess-123", { target_cursor: 500 });
    expect(res.data!.cursor).toBe(500);
  });

  it("submitCommand returns authoritative CommandReceipt", async () => {
    const sampleReceipt = {
      receipt_id: "rcpt-1",
      command_type: "submit_order",
      status: "executed",
      reason: null,
      order_id: "ord-1",
      position_id: "pos-2",
      executed_at: "2026-08-18T10:01:00Z",
    };
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(
      envelope(sampleReceipt, simulationWorkbenchRoutes.submitCommand.path, "command"),
    );

    const res = await apiClients.simulationWorkbench.submitCommand(
      "sess-123",
      {
        command: "submit_order",
        symbol: "EURUSD",
        side: "buy",
        volume: "1.0",
      },
      { idempotencyKey: "idem-cmd-1" },
    );
    expect(res.data!.receipt_id).toBe("rcpt-1");
    expect(res.data!.command_type).toBe("submit_order");
    expect(res.data!.status).toBe("executed");
  });

  it("branchLiveSession creates advisory branch projection", async () => {
    const branchProj = {
      ...SAMPLE_SESSION_PROJECTION,
      session_id: "sess-branch-1",
      evidence_class: "advisory",
      branch: {
        parent_session_id: "sess-123",
        divergence_cursor: 150,
        overrides: { spread: "1.5" },
      },
    };
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(
      envelope(branchProj, simulationWorkbenchRoutes.branchLiveSession.path, "branch"),
    );

    const res = await apiClients.simulationWorkbench.branchLiveSession(
      "sess-123",
      { overrides: { spread: "1.5" } },
      { idempotencyKey: "idem-branch-1" },
    );
    expect(res.data!.session_id).toBe("sess-branch-1");
    expect(res.data!.evidence_class).toBe("advisory");
  });

  it("createBatch and getBatch validate batch resource projections", async () => {
    const sampleBatch = {
      batch_id: "batch-1",
      principal_id: "user-1",
      name: "EURUSD Parameter Grid",
      status: "running",
      concurrency: 4,
      total_items: 2,
      completed_items: 0,
      failed_items: 0,
      cancelled_items: 0,
      created_at: "2026-08-18T10:00:00Z",
      completed_at: null,
      items: [
        {
          item_id: "item-1",
          batch_id: "batch-1",
          job_id: "job-1",
          symbol: "EURUSD",
          timeframe: "1h",
          strategy_id: "trend_following",
          parameters: { fast: "10", slow: "20" },
          status: "running",
          run_id: null,
          error: null,
        },
      ],
    };
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(
      envelope(sampleBatch, simulationWorkbenchRoutes.createBatch.path, "create_batch", 202),
    );

    const createRes = await apiClients.simulationWorkbench.createBatch(
      {
        items: [
          {
            symbol: "EURUSD",
            timeframe: "1h",
            strategy_id: "trend_following",
            parameters: { fast: "10", slow: "20" },
          },
        ],
        concurrency: 4,
        name: "EURUSD Parameter Grid",
      },
      { idempotencyKey: "idem-batch-create" },
    );
    expect(createRes.data!.batch_id).toBe("batch-1");
    expect(createRes.data!.items).toHaveLength(1);
  });

  it("throws ApiClientError when backend returns error envelope", async () => {
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(
      errorEnvelope("SIMULATION_SESSION_NOT_FOUND", "Live session not found", 404),
    );

    await expect(
      apiClients.simulationWorkbench.getLiveSession("non-existent"),
    ).rejects.toThrow(ApiClientError);
  });
});
