/**
 * Frontend context layer barrel (FEAT-API-10, Section 4.10).
 *
 * Public surface for authenticated UI session, bounded page context, and
 * governed-write preflight. The stream consumer (FR-API-045) is deferred
 * pending a backend stream route and is intentionally absent here.
 */

export { AuthProvider, useAuth } from "./auth";
export type { AuthContextValue, AuthPrincipal, AuthState } from "./auth";

export { PageContextProvider, usePageContext } from "./page";
export type { PageContextInput, PageContextProps, PageContextValue } from "./page";

export {
  buildGovernedOptions,
  isGovernedFresh,
  PREFLIGHT_WARNING_TTL_SECONDS,
} from "./governed";
export type { GovernedInput, GovernedRequestOptions } from "./governed";

export { ContextError, GovernedPreflightError, PageContextError } from "./errors";

export { consumeStream, StreamGapError } from "./streams";
export type { StreamOptions } from "./streams";
