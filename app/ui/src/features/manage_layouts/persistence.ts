/**
 * Bounded layout persistence for FEAT-UI-MANAGE_LAYOUTS.
 *
 * Persists `WorkspaceLayoutSnapshot`s to localStorage, scoped by
 * actor/workspace/layout-schema-version (FR-UI-PERSIST_LAYOUTS). The storage
 * wrapper never throws (donor `store.ts` safe-wrapper pattern, V3-native);
 * snapshots from a different schema version are discarded deterministically
 * with a recorded diagnostic (FR-UI-RESTORE_LAYOUTS); restored placements are
 * truncated to `maxRestoredTabs` (FR-UI-MANAGE_TABS bounded restoration).
 */

import type { WorkspaceLayoutSnapshot } from "../../contracts/generated/ui";

export interface RestoreDiagnostic {
  readonly code:
    | "NO_PERSISTED_LAYOUT"
    | "SCHEMA_VERSION_MISMATCH"
    | "CORRUPT_SNAPSHOT"
    | "TRUNCATED_TABS";
  readonly detail: string;
}

export interface RestoreResult {
  readonly snapshot: WorkspaceLayoutSnapshot | null;
  readonly diagnostics: readonly RestoreDiagnostic[];
}

export interface LayoutPersistence {
  save(workspaceId: string, snapshot: WorkspaceLayoutSnapshot): void;
  load(workspaceId: string): RestoreResult;
  clear(workspaceId: string): void;
}

interface PersistedEnvelope {
  readonly schema_version: number;
  readonly actor_id: string;
  readonly snapshot: WorkspaceLayoutSnapshot;
}

const KEY_PREFIX = "haruquantai.layout";

function isSnapshot(value: unknown): value is WorkspaceLayoutSnapshot {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Partial<WorkspaceLayoutSnapshot>;
  return (
    typeof candidate.layout_id === "string" &&
    typeof candidate.workspace_id === "string" &&
    Array.isArray(candidate.widget_instances) &&
    Array.isArray(candidate.placements)
  );
}

/** Safe localStorage wrapper: never throws (donor-adapted pattern). */
function safeStorage(): Pick<Storage, "getItem" | "setItem" | "removeItem"> {
  try {
    if (typeof window !== "undefined" && window.localStorage) {
      return window.localStorage;
    }
  } catch {
    // Accessing localStorage can itself throw (privacy modes).
  }
  const noop = (): void => undefined;
  return { getItem: () => null, setItem: noop, removeItem: noop };
}

export function truncatePlacements(
  snapshot: WorkspaceLayoutSnapshot,
  maxTabs: number
): { snapshot: WorkspaceLayoutSnapshot; truncated: boolean } {
  const instances = snapshot.widget_instances ?? [];
  const placements = snapshot.placements ?? [];
  if (instances.length <= maxTabs) {
    return { snapshot, truncated: false };
  }
  const keptInstances = instances.slice(0, maxTabs);
  const keptIds = new Set(keptInstances.map((i) => i.instance_id));
  return {
    snapshot: {
      ...snapshot,
      widget_instances: keptInstances,
      placements: placements.filter((p) => keptIds.has(p.instance_id)),
      active_panel_id:
        snapshot.active_panel_id && keptIds.has(snapshot.active_panel_id)
          ? snapshot.active_panel_id
          : keptInstances[0]?.instance_id ?? null,
    },
    truncated: true,
  };
}

export function createLayoutPersistence(options: {
  readonly schemaVersion: number;
  readonly maxRestoredTabs: number;
  readonly actorId?: string;
}): LayoutPersistence {
  const { schemaVersion, maxRestoredTabs } = options;
  const actorId = options.actorId ?? "actor-default";
  const storage = safeStorage();

  const keyFor = (workspaceId: string): string =>
    `${KEY_PREFIX}.v${schemaVersion}.${actorId}.${workspaceId}`;

  return {
    save(workspaceId, snapshot) {
      try {
        const envelope: PersistedEnvelope = {
          schema_version: schemaVersion,
          actor_id: actorId,
          snapshot,
        };
        storage.setItem(keyFor(workspaceId), JSON.stringify(envelope));
      } catch {
        // Quota or serialization failures must never break work.
      }
    },
    load(workspaceId) {
      let raw: string | null = null;
      try {
        raw = storage.getItem(keyFor(workspaceId));
      } catch {
        raw = null;
      }
      if (raw === null) {
        return {
          snapshot: null,
          diagnostics: [
            {
              code: "NO_PERSISTED_LAYOUT",
              detail: `No persisted layout for workspace '${workspaceId}'; deterministic default applies.`,
            },
          ],
        };
      }
      let parsed: unknown;
      try {
        parsed = JSON.parse(raw);
      } catch {
        return {
          snapshot: null,
          diagnostics: [
            {
              code: "CORRUPT_SNAPSHOT",
              detail: `Persisted layout for '${workspaceId}' is not valid JSON; discarded.`,
            },
          ],
        };
      }
      const envelope = parsed as Partial<PersistedEnvelope>;
      if (
        envelope.schema_version !== schemaVersion ||
        envelope.actor_id !== actorId ||
        !isSnapshot(envelope.snapshot)
      ) {
        return {
          snapshot: null,
          diagnostics: [
            {
              code: "SCHEMA_VERSION_MISMATCH",
              detail: `Persisted layout for '${workspaceId}' does not match schema version ${schemaVersion}/actor; discarded.`,
            },
          ],
        };
      }
      const { snapshot, truncated } = truncatePlacements(
        envelope.snapshot,
        maxRestoredTabs
      );
      const diagnostics: RestoreDiagnostic[] = truncated
        ? [
            {
              code: "TRUNCATED_TABS",
              detail: `Restored layout truncated to ${maxRestoredTabs} tabs.`,
            },
          ]
        : [];
      return { snapshot, diagnostics };
    },
    clear(workspaceId) {
      try {
        storage.removeItem(keyFor(workspaceId));
      } catch {
        // Never throws.
      }
    },
  };
}
