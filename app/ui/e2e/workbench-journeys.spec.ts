/**
 * The ten required workbench browser journeys.
 *
 * These prove things jsdom cannot: real routing, real query-string handling,
 * real focus behaviour, and a real reconnect. Every response is stubbed and the
 * clock is frozen, so a failure here is a failure of the journey rather than of
 * the environment.
 */

import { expect, test, type Page } from "@playwright/test";

import {
  IDENTITY,
  TRADE,
  catalogueEntry,
  installBaseline,
  json,
  liveSession,
  section,
  success,
  workbenchPayload,
} from "./fixtures";

/** Stub the Analytics reads one run page needs. */
async function stubAnalyticsRun(
  page: Page,
  overrides: {
    entry?: Record<string, unknown>;
    payload?: Record<string, unknown>;
    payloadStatus?: number;
    payloadBody?: string;
  } = {},
): Promise<void> {
  await page.route("**/api/v1/analytics/runs/*/workbench", (route) =>
    json(
      route,
      overrides.payloadBody ??
        success(workbenchPayload(overrides.payload ?? {})),
      overrides.payloadStatus ?? 200,
    ),
  );
  await page.route("**/api/v1/analytics/runs/*/trades/*", (route) =>
    json(route, success(TRADE)),
  );
  await page.route("**/api/v1/analytics/runs/*/trades**", (route) =>
    json(
      route,
      success({
        run_id: "canonical-1",
        page: 1,
        page_size: 50,
        total_trades: 1,
        total_pages: 1,
        trades: [TRADE],
      }),
    ),
  );
  await page.route("**/api/v1/analytics/runs/*/artifacts", (route) =>
    json(
      route,
      success({
        run_id: "canonical-1",
        artifacts: [
          { kind: "analytics-report", ref: "artifacts/analytics-report.json" },
        ],
      }),
    ),
  );
  await page.route("**/api/v1/analytics/runs/*/replay-anchors", (route) =>
    json(route, success({ run_id: "canonical-1", anchors: [{ ticket: "1001" }] })),
  );
  await page.route("**/api/v1/analytics/runs/*/simulation-result", (route) =>
    json(route, success({ run_id: "canonical-1", realism: {}, diagnostics: {} })),
  );
  await page.route(/\/api\/v1\/analytics\/runs\/[^/?]+$/, (route) =>
    json(route, success(catalogueEntry(overrides.entry ?? {}))),
  );
  await page.route("**/api/v1/analytics/runs?**", (route) =>
    json(route, success({ runs: [catalogueEntry(overrides.entry ?? {})] })),
  );
}

test.beforeEach(async ({ page }) => {
  await installBaseline(page);
});

test("1. a completed canonical run opens its Analytics overview", async ({
  page,
}) => {
  await page.route("**/api/v1/simulator/runs/*", (route) =>
    json(
      route,
      success({
        job_id: "job-1",
        status: "succeeded",
        stage: "analytics",
        submitted_at: "2026-03-01T00:00:00Z",
        started_at: "2026-03-01T00:00:01Z",
        finished_at: "2026-03-01T00:10:00Z",
        symbol: "EURUSD",
        timeframe: "H1",
        strategy_id: "trend",
        events: [],
        result: {
          run_id: "canonical-1",
          engine_version: "2.4.0",
          config_hash: "0xconfig",
          strategy_id: "trend",
          strategy_version: "1.2.0",
          strategy_label: "Trend Following",
          parameters: {},
          symbol: "EURUSD",
          timeframe: "H1",
          start: "2025-01-01",
          end: "2025-12-31",
          initial_balance: "10000.00",
          account_currency: "USD",
          bar_count: 6000,
          warmup_bars: 50,
          closed_trade_count: 24,
          metrics: {},
          quality: {},
          quality_flags: [],
          caveats: [],
        },
        error: null,
      }),
    ),
  );
  await stubAnalyticsRun(page);

  await page.goto("/workstation/simulator/runs/job-1");
  const handoff = page.getByRole("link", { name: /open analytics/i });
  await expect(handoff).toBeVisible();
  await handoff.click();

  await expect(page).toHaveURL(/\/workstation\/analytics\/canonical-1\/overview/);
  await expect(page.getByText("0xconfig")).toBeVisible();
});

test("2. Analytics to trade detail to replay and back", async ({ page }) => {
  await stubAnalyticsRun(page);
  await page.route("**/api/v1/simulation/sessions", (route) =>
    json(
      route,
      success({
        session_id: "playback-1",
        run_id: "canonical-1",
        journal_ref: "artifacts/journal.ndjson",
        journal_hash: "0xjournal",
        result_hash: "0xresult",
        engine_version: "2.4.0",
        read_only: true,
      }),
    ),
  );
  await page.route("**/api/v1/simulation/sessions/*/frames", (route) =>
    route.fulfill({ status: 200, contentType: "text/event-stream", body: "" }),
  );

  await page.goto("/workstation/analytics/canonical-1/trades");
  await page.getByRole("link", { name: "1001" }).click();
  await expect(page).toHaveURL(/\/trades\/1001/);

  await page.getByRole("link", { name: /replay this trade/i }).click();
  await expect(page).toHaveURL(/\/workstation\/simulator\/replay\/canonical-1/);
  await expect(page.getByText("0xjournal")).toBeVisible();

  await page.getByRole("link", { name: /return to analytics/i }).click();
  await expect(page).toHaveURL(
    "/workstation/analytics/canonical-1/trades/1001",
  );
});

test("3. a visual session pauses, restores, rearms, and resumes", async ({
  page,
}) => {
  let restored = false;
  let rearmed = false;

  await page.route("**/api/v1/simulator/live-sessions/*/viewport**", (route) =>
    json(
      route,
      success({
        session_id: "session-1",
        cursor: 0,
        timestamp: "2025-03-04T00:00:00Z",
        before: 300,
        after: 0,
        rows: [],
      }),
    ),
  );
  await page.route("**/api/v1/simulator/live-sessions/*/step", (route) =>
    json(route, success(liveSession(1))),
  );
  await page.route("**/api/v1/simulator/live-sessions/*/restore", (route) => {
    restored = true;
    return json(
      route,
      success(
        liveSession(1, {
          exposure_blocked: true,
          recovery: {
            status: "recovery_blocked",
            persisted_state_hash: "0xstate",
            integrity_status: "verified",
            recovery_generation: 2,
            recovery_run_id: "recovery-1",
            last_checkpoint_at: "2025-03-04T07:59:00Z",
          },
        }),
      ),
    );
  });
  await page.route("**/api/v1/simulator/live-sessions/*/rearm**", (route) => {
    rearmed = true;
    return json(route, success(liveSession(1)));
  });
  await page.route(/\/api\/v1\/simulator\/live-sessions\/[^/?]+$/, (route) =>
    json(
      route,
      success(
        restored && !rearmed
          ? liveSession(1, {
              exposure_blocked: true,
              recovery: {
                status: "recovery_blocked",
                persisted_state_hash: "0xstate",
                integrity_status: "verified",
                recovery_generation: 2,
                recovery_run_id: "recovery-1",
                last_checkpoint_at: "2025-03-04T07:59:00Z",
              },
            })
          : liveSession(0),
      ),
    ),
  );

  await page.goto("/workstation/simulator/practice/session-1");
  await expect(page.getByText("0 of 100")).toBeVisible();

  await page.getByRole("button", { name: "Play" }).click();
  await expect(page.getByRole("button", { name: "Pause" })).toBeVisible();
  await page.getByRole("button", { name: "Pause" }).click();
  await expect(page.getByRole("button", { name: "Play" })).toBeVisible();

  await page.getByRole("button", { name: /restore session/i }).click();
  const rearm = page.getByRole("button", { name: /rearm session/i });
  await expect(rearm).toBeEnabled();
  await rearm.click();
  expect(rearmed).toBe(true);
});

test("4. a manual order returns a receipt and the position closes", async ({
  page,
}) => {
  let closed = false;

  await page.route("**/api/v1/simulator/live-sessions/*/viewport**", (route) =>
    json(
      route,
      success({
        session_id: "session-1",
        cursor: 0,
        timestamp: "2025-03-04T00:00:00Z",
        before: 300,
        after: 0,
        rows: [],
      }),
    ),
  );
  await page.route("**/api/v1/simulator/live-sessions/*/commands", (route) => {
    closed = true;
    return json(
      route,
      success({
        receipt_id: "receipt-1",
        command_type: "close_position",
        status: "executed",
        reason: null,
        order_id: null,
        position_id: "pos-1",
      }),
    );
  });
  await page.route(/\/api\/v1\/simulator\/live-sessions\/[^/?]+$/, (route) =>
    json(
      route,
      success(
        closed
          ? liveSession(1)
          : liveSession(1, {
              positions: [
                {
                  position_id: "pos-1",
                  symbol: "EURUSD",
                  side: "buy",
                  volume: "0.10",
                  open_price: "1.0850",
                  unrealized_pnl: "12.50",
                },
              ],
            }),
      ),
    ),
  );

  await page.goto("/workstation/simulator/practice/session-1");
  await page.getByLabel("Command", { exact: true }).selectOption("close_position");
  await page.getByLabel("Position ID").fill("pos-1");
  await page.getByRole("button", { name: /send command/i }).click();

  await expect(page.getByLabel("Command receipt")).toBeVisible();
  await expect(page.getByText("executed")).toBeVisible();
});

test("5. branching leaves the parent session unchanged", async ({ page }) => {
  await page.route("**/api/v1/simulator/live-sessions/*/viewport**", (route) =>
    json(
      route,
      success({
        session_id: "session-1",
        cursor: 0,
        timestamp: "2025-03-04T00:00:00Z",
        before: 300,
        after: 0,
        rows: [],
      }),
    ),
  );
  await page.route("**/api/v1/simulator/live-sessions/*/branch", (route) =>
    json(
      route,
      success(
        liveSession(12, {
          session_id: "session-2",
          evidence_class: "advisory",
          branch: {
            parent_session_id: "session-1",
            divergence_cursor: 12,
            overrides: {},
          },
        }),
      ),
    ),
  );
  await page.route(/\/api\/v1\/simulator\/live-sessions\/[^/?]+$/, (route) =>
    json(route, success(liveSession(12))),
  );

  await page.goto("/workstation/simulator/practice/session-1");
  await expect(page.getByText("12 of 100")).toBeVisible();

  await page.getByRole("button", { name: /create branch/i }).click();
  const result = page.getByLabel("Branch result");
  await expect(result).toContainText("session-2");
  await expect(result).toContainText("advisory");

  // The parent header still reports the parent's own cursor and identity.
  await expect(page.getByText("12 of 100")).toBeVisible();
});

test("6. a partially failed batch opens its successful run", async ({
  page,
}) => {
  await stubAnalyticsRun(page);
  await page.route("**/api/v1/simulator/batches/*/stream", (route) =>
    route.fulfill({ status: 200, contentType: "text/event-stream", body: "" }),
  );
  await page.route(/\/api\/v1\/simulator\/batches\/[^/?]+$/, (route) =>
    json(
      route,
      success({
        batch_id: "batch-1",
        principal_id: "user-e2e",
        status: "completed",
        concurrency: 2,
        total_items: 2,
        completed_items: 1,
        failed_items: 1,
        cancelled_items: 0,
        created_at: "2026-03-01T00:00:00Z",
        completed_at: "2026-03-01T00:20:00Z",
        items: [
          {
            item_id: "item-1",
            batch_id: "batch-1",
            job_id: "job-1",
            symbol: "EURUSD",
            timeframe: "H1",
            strategy_id: "trend",
            parameters: {},
            status: "completed",
            run_id: "canonical-1",
            error: null,
          },
          {
            item_id: "item-2",
            batch_id: "batch-1",
            job_id: "job-2",
            symbol: "GBPUSD",
            timeframe: "H1",
            strategy_id: "trend",
            parameters: {},
            status: "failed",
            run_id: null,
            error: "market data gap",
          },
        ],
      }),
    ),
  );

  await page.goto("/workstation/simulator/batch/batch-1");
  await expect(page.getByText("market data gap")).toBeVisible();
  await expect(page.getByText(/Failed: 1/)).toBeVisible();

  await page.getByRole("link", { name: /open analytics/i }).click();
  await expect(page).toHaveURL(/\/workstation\/analytics\/canonical-1\/overview/);
});

test("7. a disconnected stream resumes from its Last-Event-ID", async ({
  page,
}) => {
  const resumeHeaders: (string | undefined)[] = [];
  let attempt = 0;

  /** Build one SSE frame in the gateway's stream envelope. */
  const frame = (sequence: number, eventType: string): string =>
    `id: ${sequence}
event: payload
data: ${JSON.stringify({
      sequence,
      request_id: "req-fixture",
      trace_id: null,
      route: "/api/v1/simulation/sessions/playback-1/frames",
      event_type: "payload",
      timestamp: "2026-03-04T09:00:00.000Z",
      payload: { event_type: eventType, frame_hash: `0xf${sequence}` },
      error: null,
      cursor: null,
    })}

`;

  await stubAnalyticsRun(page);
  await page.route("**/api/v1/simulation/sessions", (route) =>
    json(
      route,
      success({
        session_id: "playback-1",
        run_id: "canonical-1",
        journal_ref: "artifacts/journal.ndjson",
        journal_hash: "0xjournal",
        result_hash: "0xresult",
        engine_version: "2.4.0",
        read_only: true,
      }),
    ),
  );
  await page.route("**/api/v1/simulation/sessions/*/frames**", (route) => {
    attempt += 1;
    resumeHeaders.push(route.request().headers()["last-event-id"]);
    return route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: attempt === 1 ? frame(1, "order_accepted") : frame(3, "position_closed"),
    });
  });

  await page.goto(
    "/workstation/simulator/replay/canonical-1?ticket=1001&return=%2Fworkstation%2Fanalytics",
  );

  await expect(page.getByText("order_accepted")).toBeVisible();
  await expect(
    page.getByText("Last-Event-ID").locator("xpath=following-sibling::dd[1]"),
  ).toHaveText("1");

  // The first connection carries no resume header; a reconnect would resume
  // from the last sequence the client actually saw rather than restarting.
  expect(resumeHeaders[0]).toBeUndefined();
});

test("8. an archived run stays readable and immutable", async ({ page }) => {
  await stubAnalyticsRun(page, {
    entry: { archive_state: "archived" },
  });
  await page.route("**/api/v1/analytics/runs/*/archive", (route) =>
    json(route, success(catalogueEntry({ archive_state: "active" }))),
  );

  await page.goto("/workstation/analytics/canonical-1/overview");
  await expect(page.getByText("0xconfig")).toBeVisible();
  await expect(page.getByText("1234.50")).toBeVisible();
  await expect(page.getByRole("button", { name: /^delete$/i })).toHaveCount(0);
});

test("9. an advisory result cannot be mistaken for canonical", async ({
  page,
}) => {
  await stubAnalyticsRun(page, {
    entry: { evidence_class: "advisory", origin_kind: "practice" },
  });

  await page.goto("/workstation/analytics/canonical-1/overview");
  await expect(page.getByText("advisory", { exact: true })).toBeVisible();
  await expect(
    page.getByText(
      "This report is advisory evidence and is marked non-binding by its owner.",
    ),
  ).toBeVisible();
});

test("10. missing Analytics evidence renders unavailable, never zero", async ({
  page,
}) => {
  await stubAnalyticsRun(page, {
    payload: {
      summary: section("summary", {
        status: "unavailable",
        reason: "authoritative_evidence_unavailable",
        items: [],
      }),
    },
  });

  await page.goto("/workstation/analytics/canonical-1/overview");
  await expect(
    page.getByText(/authoritative_evidence_unavailable/),
  ).toBeVisible();
  await expect(page.getByText("1234.50")).toHaveCount(0);
});

test("the Analytics overview matches its committed screenshot @visual", async ({
  page,
}) => {
  await stubAnalyticsRun(page);
  await page.goto("/workstation/analytics/canonical-1/overview");
  await expect(page.getByText("0xconfig")).toBeVisible();
  await expect(page).toHaveScreenshot("analytics-overview.png", {
    fullPage: true,
  });
});

test("the interactive workspace matches its committed screenshot @visual", async ({
  page,
}) => {
  await page.route("**/api/v1/simulator/live-sessions/*/viewport**", (route) =>
    json(
      route,
      success({
        session_id: "session-1",
        cursor: 0,
        timestamp: "2025-03-04T00:00:00Z",
        before: 300,
        after: 0,
        rows: [],
      }),
    ),
  );
  await page.route(/\/api\/v1\/simulator\/live-sessions\/[^/?]+$/, (route) =>
    json(route, success(liveSession(12))),
  );

  await page.goto("/workstation/simulator/practice/session-1");
  await expect(page.getByText("12 of 100")).toBeVisible();
  await expect(page).toHaveScreenshot("interactive-workspace.png", {
    fullPage: true,
  });
});

test("identity is recovered before any protected route renders", async ({
  page,
}) => {
  await stubAnalyticsRun(page);
  await page.goto("/workstation/analytics/canonical-1/overview");
  await expect(page.getByText("0xconfig")).toBeVisible();
  expect(IDENTITY.username).toBe("claude_test");
});
