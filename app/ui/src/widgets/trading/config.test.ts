import { describe, expect, it } from "vitest";

import {
  DEFAULT_TRADING_CONFIG,
  PERSISTED_STATE_SCHEMA_VERSION,
  parseTradingConfig,
  resolveTradingConfig,
} from "./config";

describe("TradingConfig (FEAT-UI-06)", () => {
  it("resolves default configuration when input is undefined", () => {
    const resolved = resolveTradingConfig(undefined);
    expect(resolved).toEqual(DEFAULT_TRADING_CONFIG);
  });

  it("accepts valid partial configuration overlays", () => {
    const resolved = resolveTradingConfig({
      defaultSymbol: "GBPUSD",
      ticketHostOnly: true,
    });
    expect(resolved.defaultSymbol).toBe("GBPUSD");
    expect(resolved.ticketHostOnly).toBe(true);
    expect(resolved.persistedStateSchemaVersion).toBe(
      PERSISTED_STATE_SCHEMA_VERSION,
    );
  });

  it("fails loudly when unknown fields are supplied", () => {
    expect(() =>
      parseTradingConfig({
        defaultSymbol: "EURUSD",
        ticketHostOnly: false,
        persistedStateSchemaVersion: PERSISTED_STATE_SCHEMA_VERSION,
        unknownField: "forbidden",
      }),
    ).toThrow();
  });
});
