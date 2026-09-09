/** Public presentation contracts for FEAT-UI-SESSION_ACCESS. */

/** Distinct fail-closed access states rendered by the application boundary. */
export type SessionAccessState =
  | "recovering"
  | "authorized"
  | "unauthenticated"
  | "unauthorized"
  | "expired"
  | "unavailable";

/** Non-secret server-verified identity fields that define one UI scope. */
export interface VerifiedSessionScope {
  readonly principalId: string;
  readonly accountId: string;
  readonly workspaceId: string;
}

/** Current generation exposed to account-bound presentation consumers. */
export interface SessionScopeView {
  readonly generation: number;
  readonly scope: VerifiedSessionScope;
  readonly signal: AbortSignal;
  isCurrent(generation: number): boolean;
  /** Register cleanup; the returned React-safe disposer initiates it once. */
  registerProjection(
    key: string,
    clear: () => void | Promise<void>,
  ): () => void;
}

/** Snapshot returned by the non-React lifecycle owner. */
export interface SessionScopeSnapshot {
  readonly generation: number;
  readonly scope: VerifiedSessionScope | null;
  readonly signal: AbortSignal;
}
