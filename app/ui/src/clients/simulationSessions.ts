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

/**
 * Simulator-owned playback session record.
 *
 * The strict fields are the ones playback presentation depends on; the record
 * stays open because the Simulator owns the journal contract and may carry
 * additional evidence that this client must forward untouched rather than
 * silently drop.
 */
export const simulationSessionSchema = z
  .object({
    session_id: z.string(),
    run_id: z.string().optional(),
    cursor: z.number().optional(),
    frame_count: z.number().optional(),
    journal_ref: z.string().nullable().optional(),
    journal_hash: z.string().nullable().optional(),
    result_hash: z.string().nullable().optional(),
    engine_version: z.string().nullable().optional(),
    read_only: z.boolean().optional(),
  })
  .catchall(z.unknown());
export type SimulationSession = z.infer<typeof simulationSessionSchema>;

/**
 * One ordered immutable journal frame.
 *
 * A frame is finalized evidence: playback renders it and never edits, reorders,
 * or synthesises one.
 */
export const journalFrameSchema = z
  .object({
    sequence: z.number(),
    at: z.string().optional(),
    event_type: z.string().optional(),
    detail: z.record(z.string(), z.unknown()).optional(),
    frame_hash: z.string().nullable().optional(),
    previous_hash: z.string().nullable().optional(),
  })
  .catchall(z.unknown());
export type JournalFrame = z.infer<typeof journalFrameSchema>;

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
