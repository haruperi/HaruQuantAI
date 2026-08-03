/**
 * Usage program 15 — Frontend session and page context (FEAT-API-10).
 *
 * Standalone numbered program, not a pytest test. Exercises the public surface
 * of the context layer (AuthProvider, PageContextProvider, buildGovernedOptions)
 * through an injected fake `fetch` and a self-contained jsdom DOM, so no
 * network is touched and no secrets are read.
 *
 * Run:
 *   cd app/ui && NODE_PATH=./node_modules npx tsx ../../tests/api/usage/15_frontend_context.tsx
 */

import { JSDOM } from "jsdom";

// Establish a DOM before importing React/testing-library, which need globals.
const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost/",
});
const g = globalThis as unknown as Record<string, unknown>;
const define = (key: string, value: unknown) => {
  Object.defineProperty(globalThis, key, {
    value,
    configurable: true,
    writable: true,
  });
};
define("window", dom.window);
define("document", dom.window.document);
define("sessionStorage", dom.window.sessionStorage);
define("HTMLElement", dom.window.HTMLElement);
define("Element", dom.window.Element);
define("Node", dom.window.Node);
define("getComputedStyle", dom.window.getComputedStyle);
define("MouseEvent", dom.window.MouseEvent);
define("Event", dom.window.Event);
define("CustomEvent", dom.window.CustomEvent);
const raf = (cb: FrameRequestCallback) =>
  setTimeout(() => cb(Date.now()), 0) as unknown as number;
define("requestAnimationFrame", raf);
define("cancelAnimationFrame", (id: number) => clearTimeout(id));
dom.window.requestAnimationFrame = raf as never;
dom.window.cancelAnimationFrame = ((id: number) => clearTimeout(id)) as never;
void g;

import React, { type ReactNode, useEffect } from "react";
import { render, waitFor } from "@testing-library/react";

import {
  AuthProvider,
  buildGovernedOptions,
  GovernedPreflightError,
  isGovernedFresh,
  PageContextError,
  PageContextProvider,
  PREFLIGHT_WARNING_TTL_SECONDS,
  useAuth,
  usePageContext,
} from "../../../app/ui/src/context";

/** Build a successful /auth/me identity envelope (server-authoritative). */
function okIdentity(): Response {
  return new Response(
    JSON.stringify({
      status: "success",
      message: "ok",
      data: {
        user_id: "u_1",
        username: "alice",
        expires_at: new Date(Date.now() + 3600_000).toISOString(),
      },
      error: null,
      metadata: envelopeMetadata("/api/v1/auth/me", "api.auth.me"),
    }),
    { status: 200, headers: { "Content-Type": "application/json" } }
  );
}

/** Build a 401 /auth/me envelope (expired session). */
function unauthorizedIdentity(): Response {
  return new Response(
    JSON.stringify({
      status: "error",
      message: "auth required",
      data: null,
      error: {
        code: "AUTHENTICATION_REQUIRED",
        message: "session expired",
        details: {},
        request_id: "req_u",
        trace_id: null,
        retryable: false,
      },
      metadata: envelopeMetadata("/api/v1/auth/me", "api.auth.me"),
    }),
    { status: 401, headers: { "Content-Type": "application/json" } }
  );
}

function envelopeMetadata(route: string, operation: string) {
  return {
    contract_version: "v1",
    schema_id: "api.metadata.v1",
    request_id: "req_u",
    route,
    operation,
    trace_id: null,
    side_effect: "read",
    duration_ms: 1,
    timestamp: "2026-08-03T12:00:00Z",
    stale: false,
    stale_reason: null,
    next_cursor: null,
    page_size: null,
    idempotency_replayed: false,
  };
}

function assert(condition: boolean, message: string): void {
  if (!condition) throw new Error(`usage assertion failed: ${message}`);
}

/** Minimal jsdom-free React render shim using testing-library jsdom. */
async function withRender(node: ReactNode): Promise<() => void> {
  const result = render(<React.Fragment>{node}</React.Fragment>);
  return result.unmount;
}

/** FR-API-042: AuthProvider recovers a valid session from a readiness probe. */
async function testUsageAuthProvider(): Promise<void> {
  // Pre-seed identity so recovery can surface it after a 200 probe.
  window.sessionStorage.setItem(
    "hq:identity",
    JSON.stringify({
      user_id: "u_1",
      username: "alice",
      expires_at: new Date(Date.now() + 3600_000).toISOString(),
    })
  );
  globalThis.fetch = (() =>
    Promise.resolve(okIdentity())) as unknown as typeof fetch;

  let captured: { state: string; username: string } = {
    state: "",
    username: "",
  };
  function Probe(): ReactNode {
    const { state, principal } = useAuth();
    useEffect(() => {
      captured = { state, username: principal?.username ?? "" };
    }, [state, principal]);
    return null;
  }

  await withRender(
    <AuthProvider>
      <Probe />
    </AuthProvider>
  );
  await waitFor(() => assert(captured.state === "authenticated", "expected authenticated"));
  assert(captured.username === "alice", "expected username alice");

  // Now simulate expiry: a 401 probe clears identity.
  window.sessionStorage.setItem(
    "hq:identity",
    JSON.stringify({
      user_id: "u_1",
      username: "alice",
      expires_at: new Date(Date.now() + 3600_000).toISOString(),
    })
  );
  globalThis.fetch = (() =>
    Promise.resolve(unauthorizedIdentity())) as unknown as typeof fetch;
  await withRender(
    <AuthProvider>
      <Probe />
    </AuthProvider>
  );
  await waitFor(() =>
    assert(captured.state === "unauthenticated", "expected unauthenticated after 401")
  );
  assert(
    window.sessionStorage.getItem("hq:identity") === null,
    "expected identity cleared after expiry"
  );
  console.log("[testUsageAuthProvider] ok — session recovery + expiry handled");
}

/** FR-API-043: PageContextProvider registers bounded redacted context. */
async function testUsagePageContext(): Promise<void> {
  let captured: { actions: readonly string[]; ids: readonly string[] } = {
    actions: [],
    ids: [],
  };
  function Probe(): ReactNode {
    const ctx = usePageContext();
    useEffect(() => {
      if (ctx) captured = { actions: ctx.approved_actions, ids: ctx.visible_entity_ids };
    }, [ctx]);
    return null;
  }

  await withRender(
    <PageContextProvider
      route="/workspace"
      user_id="u_1"
      page_name="Workspace"
      approved_actions={["trade", "trade", "view"]}
      visible_entity_ids={["ESU5", "NQU5"]}
    >
      <Probe />
    </PageContextProvider>
  );
  await waitFor(() => assert(captured.actions.length === 2, "expected deduped actions"));
  assert(captured.ids.length === 2, "expected 2 visible ids");

  // Secret rejection: a sensitive identifier must throw at render.
  let threw = false;
  try {
    await withRender(
      <PageContextProvider
        route="/workspace"
        user_id="u_1"
        page_name="Workspace"
        visible_entity_ids={["password"]}
      >
        <Probe />
      </PageContextProvider>
    );
  } catch (error) {
    threw = error instanceof PageContextError;
  }
  assert(threw, "expected PageContextError for a sensitive identifier");
  console.log("[testUsagePageContext] ok — bounded redacted context + secret rejection");
}

/** FR-API-044: buildGovernedOptions preflights governed writes. */
async function testUsageGovernedOptions(): Promise<void> {
  const { options, context } = buildGovernedOptions({
    workflow: "operator.approvals",
    permission: "ops:approve",
    actorId: "u_1",
    evidenceId: "ev_1",
  });
  assert(typeof options.idempotencyKey === "string", "expected idempotency key");
  assert(context.stale_after_seconds === PREFLIGHT_WARNING_TTL_SECONDS, "default TTL");
  assert(isGovernedFresh(context), "freshly built context should be fresh");

  let threw = false;
  try {
    buildGovernedOptions({
      workflow: "operator.approvals",
      permission: "ops:approve",
      actorId: "",
      evidenceId: "ev_1",
    });
  } catch (error) {
    threw = error instanceof GovernedPreflightError;
  }
  assert(threw, "expected GovernedPreflightError for missing actor");
  console.log("[testUsageGovernedOptions] ok — preflight builds + blocks missing field");
}

/** FR-API-045: consumeStream yields ordered payload events from an SSE stream. */
async function testUsageConsumeStream(): Promise<void> {
  const { consumeStream } = await import("../../../app/ui/src/context/streams");
  const { dataRoutes } = await import("../../../app/ui/src/clients/routes");

  const sseFrame = (event: Record<string, unknown>) =>
    new TextEncoder().encode(
      `id: ${event.sequence}\nevent: ${event.event_type}\ndata: ${JSON.stringify(event)}\n\n`
    );
  const baseEvent = (sequence: number, overrides: Partial<Record<string, unknown>> = {}) => ({
    sequence,
    request_id: "req_s",
    trace_id: null,
    route: "/api/v1/data/stream",
    event_type: "payload",
    timestamp: "2026-08-03T12:00:00Z",
    payload: { price: 1.1 + sequence * 0.01 },
    error: null,
    cursor: String(sequence),
    ...overrides,
  });

  globalThis.fetch = (() =>
    Promise.resolve(
      new Response(
        new ReadableStream({
          start(controller) {
            controller.enqueue(sseFrame(baseEvent(0, { event_type: "heartbeat", payload: null })));
            controller.enqueue(sseFrame(baseEvent(1)));
            controller.enqueue(sseFrame(baseEvent(2)));
            controller.close();
          },
        }),
        { status: 200, headers: { "Content-Type": "text/event-stream" } }
      )
    )) as unknown as typeof fetch;

  const seen: number[] = [];
  for await (const event of consumeStream(dataRoutes.stream, {
    query: { symbol: "EURUSD", mode: "ticks", timeframe: "M1" },
  })) {
    seen.push(event.sequence);
  }
  assert(JSON.stringify(seen) === JSON.stringify([1, 2]), "expected ordered payload events [1,2]");
  console.log("[testUsageConsumeStream] ok — ordered payload events consumed");
}

async function main(): Promise<void> {
  console.log("=== Usage program 15 — Frontend session and page context ===");
  await testUsageAuthProvider();
  await testUsagePageContext();
  await testUsageGovernedOptions();
  await testUsageConsumeStream();
  console.log("=== All usage cases passed ===");
}

main().catch((error) => {
  console.error("USAGE PROGRAM FAILED:", error);
  process.exit(1);
});
