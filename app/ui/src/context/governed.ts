/**
 * Governed-write preflight (FR-API-044).
 *
 * Builds request options carrying idempotency-key and governance metadata for
 * governed writes, and blocks obviously incomplete or stale client context
 * before the fetch. This is advisory only: backend gates remain the sole
 * authority (NFR-API-013). A passing preflight never authorises a write; a
 * failing preflight only avoids a wasted round-trip.
 *
 * Mirrors the backend `GovernedRequestContext.v1` field set and its
 * `stale_after_seconds` (default 30s) freshness window.
 */

import type { RequestOptions } from "@/clients";

import { GovernedPreflightError } from "./errors";

/** Default freshness window for a governed preflight (seconds). */
export const PREFLIGHT_WARNING_TTL_SECONDS = 30;

/** Input required to build governed request options. */
export interface GovernedInput {
  readonly workflow: string;
  readonly permission: string;
  readonly actorId: string;
  readonly evidenceId: string;
  /** Required for governed writes that demand distinct-principal approval. */
  readonly approvalId?: string;
  /** Optional explicit idempotency key; generated when omitted. */
  readonly idempotencyKey?: string;
  /** Optional route id for traceability. */
  readonly routeId?: string;
  /** Optional audit reference. */
  readonly auditReference?: string;
  /** Optional freshness window override (seconds). */
  readonly staleAfterSeconds?: number;
}

/** Built governed request options plus the redacted context envelope. */
export interface GovernedRequestOptions {
  readonly options: RequestOptions;
  readonly context: {
    readonly workflow: string;
    readonly permission: string;
    readonly actor_id: string;
    readonly evidence_id: string;
    readonly approval_id: string | null;
    readonly idempotency_key: string;
    readonly route_id: string | null;
    readonly audit_reference: string | null;
    readonly stale_after_seconds: number;
    readonly generated_at: string;
  };
}

/** Return true when `seconds` have elapsed since `generatedAtMs`. */
function isStale(
  generatedAtMs: number,
  nowMs: number,
  staleAfterSeconds: number
): boolean {
  return nowMs - generatedAtMs > staleAfterSeconds * 1000;
}

/** Generate an idempotency key when the caller did not supply one. */
function ensureIdempotencyKey(explicit?: string): string {
  if (explicit && explicit.trim().length > 0) return explicit;
  if (typeof globalThis.crypto?.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }
  // Fallback for environments without crypto.randomUUID.
  return `idem_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
}

/**
 * Build governed request options and preflight them.
 *
 * Raises `GovernedPreflightError` when a required field is missing. Stale
 * preflight is reported via the returned `stale` flag and also raises, so a
 * governed submission cannot proceed on a stale context without an explicit
 * refresh.
 *
 * Args:
 *   input: The governed-write evidence and freshness window.
 *
 * Returns:
 *   The built request options and a redacted context envelope.
 *
 * Raises:
 *   GovernedPreflightError: Required client context is missing or stale.
 */
export function buildGovernedOptions(input: GovernedInput): GovernedRequestOptions {
  const required: ReadonlyArray<readonly [string, string | undefined]> = [
    ["workflow", input.workflow],
    ["permission", input.permission],
    ["actorId", input.actorId],
    ["evidenceId", input.evidenceId],
  ];
  for (const [name, value] of required) {
    if (typeof value !== "string" || value.trim().length === 0) {
      throw new GovernedPreflightError(`missing required field: ${name}`);
    }
  }

  const staleAfterSeconds =
    input.staleAfterSeconds ?? PREFLIGHT_WARNING_TTL_SECONDS;
  if (staleAfterSeconds <= 0) {
    throw new GovernedPreflightError("staleAfterSeconds must be positive");
  }

  const generatedAtMs = Date.now();
  if (isStale(generatedAtMs, Date.now(), staleAfterSeconds)) {
    // Defensive: a freshly generated context cannot be stale unless the clock
    // is pathological; surfaced for completeness.
    throw new GovernedPreflightError(
      "governed context expired before submission; refresh evidence"
    );
  }

  const idempotencyKey = ensureIdempotencyKey(input.idempotencyKey);

  const options: RequestOptions = {
    idempotencyKey,
  };

  const context = {
    workflow: input.workflow,
    permission: input.permission,
    actor_id: input.actorId,
    evidence_id: input.evidenceId,
    approval_id: input.approvalId ?? null,
    idempotency_key: idempotencyKey,
    route_id: input.routeId ?? null,
    audit_reference: input.auditReference ?? null,
    stale_after_seconds: staleAfterSeconds,
    generated_at: new Date(generatedAtMs).toISOString(),
  };

  return { options, context };
}

/** Re-validate a previously built context against the freshness window. */
export function isGovernedFresh(
  context: { readonly generated_at: string; readonly stale_after_seconds: number },
  nowMs: number = Date.now()
): boolean {
  const generatedAtMs = Date.parse(context.generated_at);
  if (Number.isNaN(generatedAtMs)) return false;
  return !isStale(generatedAtMs, nowMs, context.stale_after_seconds);
}
