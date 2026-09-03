import { describe, expect, it } from "vitest";

import {
  DEFAULT_TRADE_LOG_CONFIG,
  PERSISTED_STATE_SCHEMA_VERSION,
  parseTradeLogConfig,
  resolveTradeLogConfig,
} from "./config";

describe("TradeLogConfig (FEAT-UI-08)", () => {
  it("resolves default configuration when input is undefined", () => {
    const resolved = resolveTradeLogConfig(undefined);
    expect(resolved).toEqual(DEFAULT_TRADE_LOG_CONFIG);
  });

  it("accepts valid partial configuration overlays", () => {
    const resolved = resolveTradeLogConfig({ defaultProduct: "MNQU5" });
    expect(resolved.defaultProduct).toBe("MNQU5");
    expect(resolved.persistedStateSchemaVersion).toBe(
      PERSISTED_STATE_SCHEMA_VERSION,
    );
  });

  it("fails loudly when unknown fields are supplied", () => {
    expect(() =>
      parseTradeLogConfig({
        defaultProduct: "MNQU5",
        persistedStateSchemaVersion: PERSISTED_STATE_SCHEMA_VERSION,
        unknownField: "forbidden",
      }),
    ).toThrow();
  });
});
