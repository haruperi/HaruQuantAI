import { describe, expect, it } from "vitest";

import {
  DEFAULT_POSITIONS_CONFIG,
  PERSISTED_STATE_SCHEMA_VERSION,
  parsePositionsConfig,
  resolvePositionsConfig,
} from "./config";

describe("PositionsConfig (FEAT-UI-09)", () => {
  it("resolves default configuration when input is undefined", () => {
    const resolved = resolvePositionsConfig(undefined);
    expect(resolved).toEqual(DEFAULT_POSITIONS_CONFIG);
  });

  it("accepts valid partial configuration overlays", () => {
    const resolved = resolvePositionsConfig({ defaultTab: "orders" });
    expect(resolved.defaultTab).toBe("orders");
    expect(resolved.persistedStateSchemaVersion).toBe(
      PERSISTED_STATE_SCHEMA_VERSION,
    );
  });

  it("fails loudly when unknown fields are supplied", () => {
    expect(() =>
      parsePositionsConfig({
        defaultTab: "positions",
        persistedStateSchemaVersion: PERSISTED_STATE_SCHEMA_VERSION,
        unknownField: "forbidden",
      }),
    ).toThrow();
  });
});
