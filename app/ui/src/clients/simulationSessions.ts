/**
 * Simulation journal playback client (2 operations).
 *
 * Playback replays a *completed* run's finalized hash-chained journal. It is
 * not a live engine: no frame can be mutated and no what-if branch exists, so
 * nothing here can change a recorded simulation outcome.
 *
 * `frames` is an SSE route. Callers consume it through `consumeStream` in
 * `context/streams`, which validates monotonic sequence, filters heartbeats,
 * surfaces terminal errors, and supports `Last-Event-ID` cursor resume.
 */

import { z } from "zod";

import type { ApiResponse } from "./contracts";
import { simulationSessionRoutes } from "./routes";
import { request, type RequestOptions } from "./request";

/** Opaque Simulator-owned session record. */
export const simulationSessionSchema = z.record(z.string(), z.unknown());
export type SimulationSession = z.infer<typeof simulationSessionSchema>;

/**
 * Create one durable playback session for a completed run (requires
 * `simulation:read`). Creation is idempotent: the same run and key return the
 * same session rather than starting a second replay.
 */
export function createSession(
  body: Record<string, unknown>,
  options?: RequestOptions
): Promise<ApiResponse<SimulationSession>> {
  return request<SimulationSession>(simulationSessionRoutes.createSession, {
    schema: simulationSessionSchema,
    body,
    ...options,
  });
}

/**
 * The SSE frame-stream contract for one playback session.
 *
 * Returned rather than fetched because the stream is consumed through
 * `consumeStream`, not the request/response transport.
 */
export const framesContract = simulationSessionRoutes.frames;

/** Aggregated playback client. */
export const simulationSessions = { createSession, framesContract };
