import { describe, it, expect } from "vitest";
import {
  DraftStore,
  SecretPayloadError,
  findSecretKey,
  createFeature,
  SPEC,
  type DraftIdentity,
} from "../index";
import type { DraftEnvelope } from "../../../contracts/generated/ui";
import type { JsonObject } from "../../../contracts/generated/common";

function makeDraft(overrides: Partial<DraftEnvelope> = {}): DraftEnvelope {
  return {
    draft_id: "018f9a2b-7c1d-7abc-9def-012345670001",
    schema_id: "schema-strategy-params",
    workspace_id: "workstation-main",
    actor_id: "actor-default",
    entity_version: 1,
    payload: { symbol: "EURUSD" },
    created_at_iso: "2026-08-26T00:00:00.000000Z",
    updated_at_iso: "2026-08-26T00:00:00.000000Z",
    schema_version: 1,
    ...overrides,
  };
}

const IDENTITY: DraftIdentity = {
  schema_id: "schema-strategy-params",
  workspace_id: "workstation-main",
  actor_id: "actor-default",
  entity_version: 1,
};

function memoryStorage(): Storage & { data: Map<string, string> } {
  const data = new Map<string, string>();
  return {
    data,
    get length() {
      return data.size;
    },
    key: (i) => Array.from(data.keys())[i] ?? null,
    getItem: (k) => (data.has(k) ? data.get(k)! : null),
    setItem: (k, v) => void data.set(k, String(v)),
    removeItem: (k) => void data.delete(k),
    clear: () => void data.clear(),
  };
}

describe("FEAT-UI-EDIT_INPUTS draft store (FR-UI-PRESERVE_DRAFTS)", () => {
  it("registers the feature manifest with the ratified capability", () => {
    expect(SPEC.featureId).toBe("FEAT-UI-EDIT_INPUTS");
    expect(SPEC.providesCapabilities).toContain("ui.edit-inputs@1");
    const feature = createFeature();
    expect(feature.manifest.featureId).toBe("FEAT-UI-EDIT_INPUTS");
    expect(feature.draftStore).toBeInstanceOf(DraftStore);
  });

  it("round-trips a draft: refresh restores compatible drafts", () => {
    const store = new DraftStore(memoryStorage());
    store.save(makeDraft());
    const result = store.load(IDENTITY);
    expect(result.status).toBe("restored");
    if (result.status === "restored") {
      expect(result.draft.payload).toEqual({ symbol: "EURUSD" });
    }
  });

  it("reports entity-version mismatches for explicit resolution", () => {
    const store = new DraftStore(memoryStorage());
    store.save(makeDraft());

    // Same identity slot, stale entity version: resolution required.
    const versionMismatch = store.load({ ...IDENTITY, entity_version: 2 });
    expect(versionMismatch.status).toBe("mismatch");

    // A different identity scope is a distinct (empty) slot, not a mismatch.
    const otherScope = store.load({
      ...IDENTITY,
      workspace_id: "workstation-research",
    });
    expect(otherScope.status).toBe("none");

    // Resolution path: explicit clear makes the slot empty again.
    store.clear(IDENTITY);
    expect(store.load(IDENTITY).status).toBe("none");
  });

  it("rejects secret-shaped payload keys (R11 non-secret rule)", () => {
    const store = new DraftStore(memoryStorage());
    expect(() =>
      store.save(makeDraft({ payload: { api_key: "x" } as JsonObject }))
    ).toThrow(SecretPayloadError);
    expect(() =>
      store.save(makeDraft({ payload: { nested: { Password: "x" } } }))
    ).toThrow(SecretPayloadError);
    expect(findSecretKey({ safe: { value: 1 } })).toBeNull();
  });

  it("never throws on storage failures", () => {
    const failing = {
      getItem: (): string | null => {
        throw new Error("denied");
      },
      setItem: (): void => {
        throw new Error("quota");
      },
      removeItem: (): void => {
        throw new Error("denied");
      },
    };
    const store = new DraftStore(failing);
    expect(() => store.save(makeDraft())).not.toThrow();
    expect(store.load(IDENTITY).status).toBe("none");
    expect(() => store.clear(IDENTITY)).not.toThrow();
  });
});
