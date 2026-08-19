/**
 * Deterministic fixtures for the workbench browser journeys.
 *
 * Every response the app can receive is stubbed here. Nothing reaches a live
 * provider, a real database, or a real clock, so a journey that fails failed
 * for the reason it claims to test rather than because a market moved.
 */

import type { Page, Route } from "@playwright/test";

/** Frozen wall clock shared by every journey. */
export const FIXED_NOW = "2026-03-04T09:00:00.000Z";

/** Wrap one payload in the API success envelope. */
export function success(data: unknown, route = "/api/v1/stub"): string {
  return JSON.stringify({
    status: "success",
    message: "ok",
    data,
    error: null,
    metadata: {
      contract_version: "v1",
      schema_id: "api.metadata.v1",
      request_id: "req-fixture",
      route,
      operation: "fixture",
      trace_id: null,
      side_effect: "read",
      duration_ms: 1,
      timestamp: FIXED_NOW,
      stale: false,
      stale_reason: null,
      idempotency_replayed: false,
    },
  });
}

/** Wrap one failure in the API error envelope. */
export function failure(code: string, message: string, route = "/api/v1/stub"): string {
  return JSON.stringify({
    status: "error",
    message,
    data: null,
    error: {
      code,
      message,
      details: {},
      request_id: "req-fixture",
      trace_id: null,
      retryable: false,
    },
    metadata: {
      contract_version: "v1",
      schema_id: "api.metadata.v1",
      request_id: "req-fixture",
      route,
      operation: "fixture",
      trace_id: null,
      side_effect: "read",
      duration_ms: 1,
      timestamp: FIXED_NOW,
      stale: false,
      stale_reason: null,
      idempotency_replayed: false,
    },
  });
}

/** One authenticated identity. */
export const IDENTITY = {
  user_id: "user-e2e",
  username: "claude_test",
  expires_at: "2026-12-31T00:00:00Z",
};

/** One completed canonical run catalogue entry. */
export function catalogueEntry(overrides: Record<string, unknown> = {}) {
  return {
    run_id: "canonical-1",
    principal_id: "user-e2e",
    origin_kind: "canonical_job",
    origin_id: "job-1",
    job_id: "job-1",
    batch_id: null,
    session_id: null,
    strategy_id: "trend",
    strategy_version: "1.2.0",
    strategy_label: "Trend Following",
    symbols: ["EURUSD"],
    timeframe: "H1",
    measurement_start: "2025-01-01T00:00:00Z",
    measurement_end: "2025-12-31T00:00:00Z",
    status: "completed",
    result_ref: "results/canonical-1.json",
    report_id: "report-1",
    report_ref: "artifacts/analytics-report.json",
    artifact_manifest_ref: "artifacts/manifest.json",
    quality_status: "acceptable",
    evidence_class: "canonical",
    created_at: "2026-03-01T00:00:00Z",
    completed_at: "2026-03-01T00:10:00Z",
    name: "Baseline",
    alias: null,
    description: null,
    tags: ["baseline"],
    run_reason: null,
    archive_state: "active",
    ...overrides,
  };
}

/** Build one owner workbench section. */
export function section(key: string, overrides: Record<string, unknown> = {}) {
  return {
    key,
    status: "completed",
    unit: null,
    source_context: "all",
    sample_count: 2,
    reason: null,
    truncated: false,
    total_count: 2,
    items: [],
    ...overrides,
  };
}

/** One complete owner workbench projection. */
export function workbenchPayload(overrides: Record<string, unknown> = {}) {
  return {
    contract_version: "v1",
    schema_id: "analytics.workbench_payload.v1",
    payload_id: "payload-1",
    report_id: "report-1",
    generated_at: FIXED_NOW,
    summary: section("summary", {
      items: [
        { key: "net_pnl", label: "Net PnL", value: "1234.50", unit: "USD" },
        { key: "cagr", label: "CAGR", value: "0.184", unit: "ratio" },
      ],
    }),
    equity_curve: section("equity_curve", {
      items: [
        { timestamp: "2025-01-01", value: 10000 },
        { timestamp: "2025-06-01", value: 10820 },
      ],
    }),
    drawdown_curve: section("drawdown_curve"),
    returns_series: section("returns_series"),
    vami: section("vami"),
    monthly_returns: section("monthly_returns"),
    period_tables: section("period_tables"),
    trade_calendar: section("trade_calendar"),
    streaks: section("streaks"),
    distribution: section("distribution"),
    histogram: section("histogram"),
    outliers: section("outliers"),
    excursions: section("excursions"),
    duration: section("duration"),
    grouped_performance: section("grouped_performance"),
    benchmark: section("benchmark"),
    costs: section("costs"),
    warnings: [],
    quality_flags: [],
    lineage: {
      engine_version: "2.4.0",
      config_hash: "0xconfig",
      data_hash: "0xdata",
      request_hash: "0xrequest",
      report_hash: "0xreport",
      seed: 4242,
    },
    truncation: [],
    non_binding: true,
    ...overrides,
  };
}

/** One canonical closed trade. */
export const TRADE = {
  ticket: "1001",
  symbol: "EURUSD",
  side: "buy",
  volume: "0.10",
  entry_time: "2025-03-04T08:00:00Z",
  entry_price: "1.08500",
  exit_time: "2025-03-04T14:00:00Z",
  exit_price: "1.08750",
  pnl: "25.00",
  commission: "0.70",
  swap: "0.00",
  reason: "take_profit",
  mae: "-4.20",
  mfe: "31.10",
  bars_held: 6,
  duration_seconds: 21600,
};

/** One live practice session projection at a given cursor. */
export function liveSession(
  cursor: number,
  overrides: Record<string, unknown> = {},
) {
  return {
    contract_version: "v1",
    schema_id: "api.live_session_projection.v1",
    session_id: "session-1",
    run_id: "advisory-1",
    mode: "practice",
    evidence_class: "practice",
    cursor,
    timestamp: `2025-03-04T0${Math.min(9, cursor)}:00:00Z`,
    tick_count: 100,
    completed: false,
    dataset: { dataset_id: "ds-1", revision: "rev-1", content_hash: "0xds" },
    account: {
      currency: "USD",
      balance: "10000.00",
      equity: "10000.00",
      margin: "0",
      free_margin: "10000.00",
      margin_level: "0",
    },
    positions: [],
    orders: [],
    pending_intent_count: 0,
    exposure_blocked: false,
    state_hash: "0xstate",
    state_freshness: "fresh",
    permitted_actions: ["read", "step", "seek", "command", "branch"],
    ...overrides,
  };
}

/** Fulfil one stubbed JSON route. */
export async function json(route: Route, body: string, status = 200): Promise<void> {
  await route.fulfill({
    status,
    contentType: "application/json",
    body,
  });
}

/**
 * Install the baseline stubs every journey needs.
 *
 * Journey-specific routes are registered afterwards and take precedence,
 * because Playwright matches the most recently registered handler first.
 */
export async function installBaseline(page: Page): Promise<void> {
  await page.clock.install({ time: new Date(FIXED_NOW) });

  // Playwright matches the most recently registered handler first, so the
  // catch-all is registered before the specific stubs it must not shadow.
  // Anything not explicitly stubbed fails closed rather than reaching a real
  // service, so an unstubbed call is visible instead of silent.
  await page.route("**/api/v1/**", (route) =>
    json(
      route,
      failure("NOT_FOUND", "route not stubbed in this journey"),
      404,
    ),
  );

  await page.route("**/api/v1/auth/me", (route) =>
    json(route, success(IDENTITY, "/api/v1/auth/me")),
  );
}
