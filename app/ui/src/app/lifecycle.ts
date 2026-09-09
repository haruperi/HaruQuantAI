/** Account-scoped request and projection lifecycle for session access. */

import { ApiClientError } from "@/clients";

import type {
  SessionScopeSnapshot,
  VerifiedSessionScope,
} from "./contracts";

const MAX_PROJECTIONS = 128;
const MAX_KEY_LENGTH = 128;
const SAFE_KEY = /^[A-Za-z0-9._:-]+$/;

type ProjectionClearer = () => void | Promise<void>;

/** Return a stable non-secret comparison key for a verified scope. */
export function sessionScopeKey(scope: VerifiedSessionScope): string {
  return `${scope.principalId}\u001f${scope.accountId}\u001f${scope.workspaceId}`;
}

/** Validate one server-derived scope before it becomes renderable. */
function validateScope(scope: VerifiedSessionScope): void {
  if (
    scope.principalId.trim().length === 0 ||
    scope.accountId.trim().length === 0 ||
    scope.workspaceId.trim().length === 0
  ) {
    throw new ApiClientError({
      message: "verified session scope is incomplete",
      status: 0,
      code: "VALIDATION_FAILED",
    });
  }
}

/** Validate a bounded projection registration key. */
function validateProjectionKey(key: string): void {
  if (
    key.length === 0 ||
    key.length > MAX_KEY_LENGTH ||
    !SAFE_KEY.test(key)
  ) {
    throw new ApiClientError({
      message: "session projection key is invalid",
      status: 0,
      code: "VALIDATION_FAILED",
    });
  }
}

/** Own one current access generation and all registered scoped effects. */
export class SessionAccessLifecycle {
  private controller = new AbortController();
  private readonly projections = new Map<string, ProjectionClearer>();
  private readonly pendingClears = new Set<Promise<void>>();
  private currentScope: VerifiedSessionScope | null = null;
  private currentGeneration = 0;
  private disposed = false;

  /** Whether the access contribution has been withdrawn. */
  public get isDisposed(): boolean {
    return this.disposed;
  }

  /** Return a read-only view of the current lifecycle generation. */
  public snapshot(): SessionScopeSnapshot {
    return {
      generation: this.currentGeneration,
      scope: this.currentScope,
      signal: this.controller.signal,
    };
  }

  /** Whether a completion still belongs to the active verified scope. */
  public isCurrent(generation: number): boolean {
    return (
      !this.disposed &&
      generation === this.currentGeneration &&
      this.currentScope !== null &&
      !this.controller.signal.aborted
    );
  }

  /** Register one account-bound presentation projection for exact cleanup. */
  public registerProjection(key: string, clear: ProjectionClearer): () => void {
    this.assertAvailable();
    validateProjectionKey(key);
    if (
      !this.projections.has(key) &&
      this.projections.size + this.pendingClears.size >= MAX_PROJECTIONS
    ) {
      throw new ApiClientError({
        message: "session projection limit reached",
        status: 0,
        code: "VALIDATION_FAILED",
      });
    }
    if (this.projections.has(key)) {
      throw new ApiClientError({
        message: `session projection already registered: ${key}`,
        status: 0,
        code: "IDEMPOTENCY_CONFLICT",
      });
    }
    this.projections.set(key, clear);
    let active = true;
    return () => {
      if (!active) return;
      active = false;
      if (this.projections.get(key) !== clear) return;
      this.projections.delete(key);
      this.startClear(clear);
    };
  }

  /** Abort and clear the old scope before publishing the next verified scope. */
  public async transition(
    nextScope: VerifiedSessionScope | null,
  ): Promise<SessionScopeSnapshot> {
    this.assertAvailable();
    if (nextScope !== null) validateScope(nextScope);
    if (
      this.currentScope !== null &&
      nextScope !== null &&
      sessionScopeKey(this.currentScope) === sessionScopeKey(nextScope)
    ) {
      return this.snapshot();
    }
    if (this.currentScope === null && nextScope === null) {
      return this.snapshot();
    }

    this.currentGeneration += 1;
    const transitionGeneration = this.currentGeneration;
    this.controller.abort(
      this.currentScope === null
        ? "session-scope-started"
        : "session-scope-changed",
    );
    this.currentScope = null;
    this.startRegisteredClears();
    await this.awaitPendingClears();
    this.assertAvailable();
    if (transitionGeneration !== this.currentGeneration) {
      throw new ApiClientError({
        message: "session scope transition was superseded",
        status: 0,
        code: "GOVERNED_REQUEST_STALE",
      });
    }
    this.controller = new AbortController();
    this.currentScope = nextScope;
    return this.snapshot();
  }

  /** Withdraw this lifecycle and release every owned effect idempotently. */
  public async dispose(): Promise<void> {
    if (this.disposed) return;
    this.disposed = true;
    this.currentGeneration += 1;
    this.controller.abort("session-access-disposed");
    this.currentScope = null;
    this.startRegisteredClears();
    await this.awaitPendingClears();
  }

  /** Start one owned clearer and contain its failure until settlement. */
  private startClear(clear: ProjectionClearer): void {
    const pending = (async () => {
      try {
        await clear();
      } catch {
        // Cleanup failure cannot restore or authorize a stale scope.
      }
    })();
    this.pendingClears.add(pending);
    void pending.then(() => {
      this.pendingClears.delete(pending);
    });
  }

  /** Transfer every active registration into pending clear ownership. */
  private startRegisteredClears(): void {
    const clearers = [...this.projections.values()];
    this.projections.clear();
    for (const clear of clearers) this.startClear(clear);
  }

  /** Await clear work, including work registered while an earlier batch settles. */
  private async awaitPendingClears(): Promise<void> {
    while (this.pendingClears.size > 0) {
      await Promise.all([...this.pendingClears]);
    }
  }

  private assertAvailable(): void {
    if (this.disposed) {
      throw new ApiClientError({
        message: "session access capability is unavailable",
        status: 0,
        code: "DEPENDENCY_UNAVAILABLE",
      });
    }
  }
}
