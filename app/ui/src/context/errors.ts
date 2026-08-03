/**
 * Bounded error types for the frontend context layer.
 *
 * These mirror the spirit of the backend stable error codes: each carries a
 * deterministic code and a bounded, secret-safe message so callers can render
 * a traceable failure. Browser context never confers authority and never
 * stores domain truth, so these errors are advisory signals for the UI.
 */

/** Base class for context-layer failures. */
export abstract class ContextError extends Error {
  public readonly code: string;

  public constructor(code: string, message: string) {
    super(message);
    this.name = "ContextError";
    this.code = code;
  }
}

/**
 * Raised when a page context is invalid: it exceeds the bounded
 * `visible_entity_ids` limit (200), contains duplicates, or carries a
 * sensitive key. Mirrors the backend `PageContext` validators.
 */
export class PageContextError extends ContextError {
  public constructor(message: string) {
    super("PAGE_CONTEXT_INVALID", message);
    this.name = "PageContextError";
  }
}

/**
 * Raised when a governed-write preflight is obviously incomplete or stale.
 *
 * This is advisory: a blocked preflight never substitutes for backend
 * authorization. Backend gates remain the sole authority (NFR-API-013).
 */
export class GovernedPreflightError extends ContextError {
  public constructor(message: string) {
    super("GOVERNED_PREFLIGHT_FAILED", message);
    this.name = "GovernedPreflightError";
  }
}
