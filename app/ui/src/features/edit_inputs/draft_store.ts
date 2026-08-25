/**
 * Local draft preservation for FEAT-UI-EDIT_INPUTS (FR-UI-PRESERVE_DRAFTS,
 * wire record R11).
 *
 * Drafts are persisted locally, scoped by schema/workspace/actor identity and
 * entity version. Refresh restores compatible drafts; identity mismatches are
 * reported for explicit resolution and never silently overwritten. Payloads
 * are guarded against secret-shaped keys (heuristic, case-insensitive,
 * recursive) — the authoritative non-secret policy remains backend-side at
 * the Stage 6 de-mock. Storage never throws (donor-adapted safe wrapper).
 */

import type { DraftEnvelope } from "../../contracts/generated/ui";

export interface DraftIdentity {
  readonly schema_id: string;
  readonly workspace_id: string;
  readonly actor_id: string;
  readonly entity_version: number;
}

export type DraftLoadResult =
  | { status: "restored"; draft: DraftEnvelope }
  | { status: "mismatch"; reason: string }
  | { status: "none" };

export class SecretPayloadError extends Error {
  public constructor(offendingKey: string) {
    super(
      `Draft payload contains a secret-shaped key '${offendingKey}'; non-secret payloads only (R11).`
    );
    this.name = "SecretPayloadError";
  }
}

const KEY_PREFIX = "haruquantai.draft.v1";

const SECRET_KEY_PATTERN =
  /(secret|password|passwd|token|credential|api[_-]?key|private[_-]?key)/i;

/** Recursively detect secret-shaped keys in a JSON payload. */
export function findSecretKey(value: unknown, path = ""): string | null {
  if (Array.isArray(value)) {
    for (const item of value) {
      const found = findSecretKey(item, path);
      if (found) return found;
    }
    return null;
  }
  if (typeof value === "object" && value !== null) {
    for (const [key, child] of Object.entries(value)) {
      if (SECRET_KEY_PATTERN.test(key)) {
        return path ? `${path}.${key}` : key;
      }
      const found = findSecretKey(child, path ? `${path}.${key}` : key);
      if (found) return found;
    }
  }
  return null;
}

/** Safe localStorage wrapper: never throws. */
function safeStorage(): Pick<Storage, "getItem" | "setItem" | "removeItem"> {
  try {
    if (typeof window !== "undefined" && window.localStorage) {
      return window.localStorage;
    }
  } catch {
    // Privacy modes can throw on localStorage access.
  }
  const noop = (): void => undefined;
  return { getItem: () => null, setItem: noop, removeItem: noop };
}

function isDraftEnvelope(value: unknown): value is DraftEnvelope {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Partial<DraftEnvelope>;
  return (
    typeof candidate.draft_id === "string" &&
    typeof candidate.schema_id === "string" &&
    typeof candidate.workspace_id === "string" &&
    typeof candidate.actor_id === "string" &&
    typeof candidate.entity_version === "number" &&
    typeof candidate.payload === "object" &&
    candidate.payload !== null
  );
}

function keyFor(identity: Omit<DraftIdentity, "entity_version">): string {
  return `${KEY_PREFIX}.${identity.actor_id}.${identity.schema_id}.${identity.workspace_id}`;
}

export class DraftStore {
  private readonly storage: Pick<Storage, "getItem" | "setItem" | "removeItem">;

  public constructor(
    storage: Pick<Storage, "getItem" | "setItem" | "removeItem"> = safeStorage()
  ) {
    this.storage = storage;
  }

  /** Persist a non-secret draft envelope. Throws SecretPayloadError on guard hit. */
  public save(draft: DraftEnvelope): void {
    const secretKey = findSecretKey(draft.payload);
    if (secretKey) {
      throw new SecretPayloadError(secretKey);
    }
    try {
      this.storage.setItem(
        keyFor(draft),
        JSON.stringify(draft)
      );
    } catch {
      // Quota/serialization failures must never break work.
    }
  }

  /**
   * Load a draft for the given identity. A stored draft whose identity or
   * entity version does not match is reported as a mismatch requiring
   * explicit resolution (clear or deliberate overwrite) — never silently
   * remapped.
   */
  public load(identity: DraftIdentity): DraftLoadResult {
    let raw: string | null = null;
    try {
      raw = this.storage.getItem(keyFor(identity));
    } catch {
      raw = null;
    }
    if (raw === null) {
      return { status: "none" };
    }
    let parsed: unknown;
    try {
      parsed = JSON.parse(raw);
    } catch {
      return { status: "mismatch", reason: "Stored draft is corrupt; explicit resolution required." };
    }
    if (!isDraftEnvelope(parsed)) {
      return { status: "mismatch", reason: "Stored draft has an invalid shape; explicit resolution required." };
    }
    if (
      parsed.schema_id !== identity.schema_id ||
      parsed.workspace_id !== identity.workspace_id ||
      parsed.actor_id !== identity.actor_id
    ) {
      return { status: "mismatch", reason: "Stored draft belongs to a different identity scope." };
    }
    if (parsed.entity_version !== identity.entity_version) {
      return {
        status: "mismatch",
        reason: `Stored draft targets entity version ${parsed.entity_version}, current is ${identity.entity_version}.`,
      };
    }
    return { status: "restored", draft: parsed };
  }

  /** Explicitly discard a stored draft (the resolution path for mismatches). */
  public clear(identity: Omit<DraftIdentity, "entity_version">): void {
    try {
      this.storage.removeItem(keyFor(identity));
    } catch {
      // Never throws.
    }
  }
}
