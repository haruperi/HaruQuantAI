/**
 * Live what-if Simulation session client (5 operations).
 *
 * A live session is a *resumable* engine: it advances tick by tick and can be
 * branched at the current cursor to explore an alternative. This is the exact
 * opposite of `simulationSessions`, which replays a finalized journal and can
 * never change an outcome.
 *
 * Two invariants the caller must respect and the backend enforces:
 *
 * - Branching is a governed write and requires an idempotency key, because a
 *   repeat would open a second engine rather than return the first branch.
 * - Stepping is deliberately *not* idempotency-keyed. Advancing is cumulative,
 *   not repeatable — a retried step is a further step, so the caller must
 *   reconcile against the returned cursor rather than assume replay.
 *
 * Live results are advisory. The Simulator marks them so; nothing here may be
 * presented as a recorded, reproducible run.
 */

import { z } from "zod";

import type { ApiResponse } from "./contracts";
import { liveSimulationRoutes } from "./routes";
import { request, type RequestOptions } from "./request";

/** Opaque Simulator-owned live session state. */
export const liveSessionSchema = z.record(z.string(), z.unknown());
export type LiveSession = z.infer<typeof liveSessionSchema>;

/** Largest tick count the backend accepts in one step. */
export const MAX_STEP_TICKS = 10_000;

/**
 * Open one resumable live session (requires `simulation:run`; governed).
 *
 * The body is the Simulator-owned backtest request. Creation is idempotent:
 * the same request and key re-attach to the existing session rather than
 * opening a second engine.
 */
export function createSession(
  body: Record<string, unknown>,
  options?: RequestOptions
): Promise<ApiResponse<LiveSession>> {
  return request<LiveSession>(liveSimulationRoutes.createSession, {
    schema: liveSessionSchema,
    body,
    ...options,
  });
}

/** Read current session state without advancing it (requires `simulation:read`). */
export function readSession(
  sessionId: string,
  options?: RequestOptions
): Promise<ApiResponse<LiveSession>> {
  return request<LiveSession>(liveSimulationRoutes.readSession, {
    schema: liveSessionSchema,
    pathParams: { session_id: sessionId },
    ...options,
  });
}

/**
 * Advance the session by `ticks` (requires `simulation:run`).
 *
 * Not idempotency-keyed: see the module note. Callers must treat the returned
 * cursor as authoritative rather than tracking position locally.
 */
export function step(
  sessionId: string,
  ticks: number,
  options?: RequestOptions
): Promise<ApiResponse<LiveSession>> {
  return request<LiveSession>(liveSimulationRoutes.step, {
    schema: liveSessionSchema,
    pathParams: { session_id: sessionId },
    query: { ticks },
    body: {},
    ...options,
  });
}

/**
 * Branch at the current cursor with parameter overrides (requires
 * `simulation:run`; governed, idempotent).
 *
 * The branch replays the parent's inputs up to the divergence point on its own
 * engine, so the parent is unaffected. Overrides are forwarded unchanged; the
 * Simulator validates them.
 */
export function branch(
  sessionId: string,
  overrides: Record<string, unknown>,
  options?: RequestOptions
): Promise<ApiResponse<LiveSession>> {
  return request<LiveSession>(liveSimulationRoutes.branch, {
    schema: liveSessionSchema,
    pathParams: { session_id: sessionId },
    body: { overrides },
    ...options,
  });
}

/**
 * Release a session and its engine (requires `simulation:run`).
 *
 * Sessions are a bounded in-process resource and also expire on their own, so
 * closing is a courtesy that frees capacity early rather than a correctness
 * requirement.
 */
export function closeSession(
  sessionId: string,
  options?: RequestOptions
): Promise<ApiResponse<LiveSession>> {
  return request<LiveSession>(liveSimulationRoutes.closeSession, {
    schema: liveSessionSchema,
    pathParams: { session_id: sessionId },
    ...options,
  });
}

/** Aggregated live what-if client. */
export const liveSimulation = {
  createSession,
  readSession,
  step,
  branch,
  closeSession,
};
