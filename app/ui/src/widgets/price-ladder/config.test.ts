import { describe, expect, it } from "vitest";

import {
  DEFAULT_PRICE_LADDER_CONFIG,
  PERSISTED_STATE_SCHEMA_VERSION,
  parsePriceLadderConfig,
  resolvePriceLadderConfig,
} from "./config";

describe("PriceLadderConfig (FEAT-UI-05)", () => {
  it("resolves default configuration when input is undefined", () => {
    const resolved = resolvePriceLadderConfig(undefined);
    expect(resolved).toEqual(DEFAULT_PRICE_LADDER_CONFIG);
  });

  it("accepts valid partial configuration overlays", () => {
    const resolved = resolvePriceLadderConfig({
      defaultSymbol: "USDJPY",
      variant: "trading",
    });
    expect(resolved.defaultSymbol).toBe("USDJPY");
    expect(resolved.variant).toBe("trading");
    expect(resolved.persistedStateSchemaVersion).toBe(
      PERSISTED_STATE_SCHEMA_VERSION,
    );
  });

  it("fails loudly when unknown fields are supplied", () => {
    expect(() =>
      parsePriceLadderConfig({
        defaultSymbol: "EURUSD",
        variant: "standalone",
        persistedStateSchemaVersion: PERSISTED_STATE_SCHEMA_VERSION,
        unknownField: "forbidden",
      }),
    ).toThrow();
  });
});
