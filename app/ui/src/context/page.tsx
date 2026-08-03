/**
 * Bounded redacted page context (FR-API-043).
 *
 * Registers only bounded, redacted current-page entities and approved actions
 * for route-aware workflows. Mirrors the backend `PageContext.v1` contract:
 * `visible_entity_ids` is capped at 200 entries and deduplicated, and neither
 * field may carry a sensitive key. Sensitive keys are rejected so secrets
 * never reach page-scoped context.
 */

"use client";

import {
  createContext,
  useContext,
  useMemo,
  type ReactNode,
} from "react";

import { PageContextError } from "./errors";

/** Maximum visible entity identifiers (backend `_MAX_VISIBLE_IDS`). */
const MAX_VISIBLE_ENTITY_IDS = 200;

/** Heuristic sensitive-key substrings; mirrors Utils `is_sensitive_key`. */
const SENSITIVE_KEY_FRAGMENTS = [
  "password",
  "secret",
  "token",
  "api_key",
  "apikey",
  "credential",
  "private_key",
  "session",
  "authorization",
] as const;

/** Return true when a key looks sensitive and must be rejected. */
function isSensitiveKey(key: string): boolean {
  const lowered = key.toLowerCase();
  return SENSITIVE_KEY_FRAGMENTS.some((fragment) =>
    lowered.includes(fragment)
  );
}

/** Normalise and deduplicate a string tuple, rejecting empties and secrets. */
function normaliseIdTuple(
  values: readonly string[] | undefined,
  field: "approved_actions" | "visible_entity_ids"
): readonly string[] {
  const source = values ?? [];
  const seen = new Set<string>();
  const result: string[] = [];
  for (const raw of source) {
    if (typeof raw !== "string") {
      throw new PageContextError(`${field} entries must be strings`);
    }
    const trimmed = raw.trim();
    if (trimmed.length === 0) {
      throw new PageContextError(`${field} must not contain empty entries`);
    }
    if (isSensitiveKey(trimmed)) {
      throw new PageContextError(
        `${field} rejected a sensitive-looking identifier`
      );
    }
    if (seen.has(trimmed)) {
      // Deduplicate silently, matching the backend validator's de-dup intent.
      continue;
    }
    seen.add(trimmed);
    result.push(trimmed);
  }
  if (field === "visible_entity_ids" && result.length > MAX_VISIBLE_ENTITY_IDS) {
    throw new PageContextError(
      `visible_entity_ids exceeds the ${MAX_VISIBLE_ENTITY_IDS} entry limit`
    );
  }
  return result;
}

/** Input accepted by the page-context provider. */
export interface PageContextInput {
  readonly route: string;
  readonly user_id: string;
  readonly page_name: string;
  readonly approved_actions?: readonly string[];
  readonly visible_entity_ids?: readonly string[];
}

/** Validated, bounded page context value. */
export interface PageContextValue {
  readonly route: string;
  readonly user_id: string;
  readonly page_name: string;
  readonly approved_actions: readonly string[];
  readonly visible_entity_ids: readonly string[];
}

const PageContext = createContext<PageContextValue | null>(null);

/** Props accepted by `PageContextProvider`. */
export interface PageContextProps extends PageContextInput {
  readonly children?: ReactNode;
}

/**
 * Register a bounded, redacted page context for the current route.
 *
 * Validates the inputs eagerly and throws `PageContextError` on any violation
 * so invalid context never propagates to descendants.
 */
export function PageContextProvider({
  route,
  user_id,
  page_name,
  approved_actions,
  visible_entity_ids,
  children,
}: PageContextProps): ReactNode {
  if (typeof route !== "string" || !route.startsWith("/")) {
    throw new PageContextError("route must start with '/'");
  }
  if (typeof user_id !== "string" || user_id.trim().length === 0) {
    throw new PageContextError("user_id is required");
  }
  if (typeof page_name !== "string" || page_name.trim().length === 0) {
    throw new PageContextError("page_name is required");
  }

  const value = useMemo<PageContextValue>(() => {
    const actions = normaliseIdTuple(approved_actions, "approved_actions");
    const ids = normaliseIdTuple(visible_entity_ids, "visible_entity_ids");
    return {
      route,
      user_id,
      page_name,
      approved_actions: actions,
      visible_entity_ids: ids,
    };
    // `route`, `user_id`, `page_name` are validated above and re-checked by
    // the deps array; arrays are normalised inside.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [route, user_id, page_name, approved_actions, visible_entity_ids]);

  return <PageContext.Provider value={value}>{children}</PageContext.Provider>;
}

/**
 * Read the current bounded page context.
 *
 * Returns `null` when no `PageContextProvider` is mounted, so callers can
 * degrade gracefully rather than throw outside a route-aware view.
 */
export function usePageContext(): PageContextValue | null {
  return useContext(PageContext);
}
