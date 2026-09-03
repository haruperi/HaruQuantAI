import { describe, expect, it } from "vitest";

import {
  DEFAULT_MARKET_TICKS_CONFIG,
  PERSISTED_STATE_SCHEMA_VERSION,
  marketTicksConfigSchema,
  parseMarketTicksConfig,
  resolveMarketTicksConfig,
} from "./config";

describe("FEAT-UI-25 strict configuration — D-UI §4.8", () => {
  it("defaults derive symbols from system settings", () => {
    expect(DEFAULT_MARKET_TICKS_CONFIG.symbols).toEqual([]);
    expect(DEFAULT_MARKET_TICKS_CONFIG.staleAfterSeconds).toBe(5);
    expect(DEFAULT_MARKET_TICKS_CONFIG.staleRowAfterSeconds).toBe(5);
    expect(DEFAULT_MARKET_TICKS_CONFIG.reconnectInitialDelayMs).toBe(1_000);
    expect(DEFAULT_MARKET_TICKS_CONFIG.reconnectMaxDelayMs).toBe(10_000);
    expect(DEFAULT_MARKET_TICKS_CONFIG.persistedStateSchemaVersion).toBe(1);
  });

  it("parses a complete valid configuration", () => {
    const config = parseMarketTicksConfig({
      symbols: ["EURUSD", "GBPUSD"],
      staleAfterSeconds: 2.5,
      staleRowAfterSeconds: 3,
      reconnectInitialDelayMs: 500,
      reconnectMaxDelayMs: 5_000,
      persistedStateSchemaVersion: 1,
    });
    expect(config.symbols).toEqual(["EURUSD", "GBPUSD"]);
    expect(config.staleAfterSeconds).toBe(2.5);
  });

  it("rejects unknown fields instead of silently passing", () => {
    expect(() =>
      parseMarketTicksConfig({
        ...DEFAULT_MARKET_TICKS_CONFIG,
        refreshMs: 1_000,
      }),
    ).toThrow();
  });

  it("rejects invalid symbol sets", () => {
    expect(() =>
      parseMarketTicksConfig({
        ...DEFAULT_MARKET_TICKS_CONFIG,
        symbols: ["EUR/USD!"],
      }),
    ).toThrow();
    expect(() =>
      parseMarketTicksConfig({
        ...DEFAULT_MARKET_TICKS_CONFIG,
        symbols: Array.from({ length: 201 }, (_, index) => `S${index}`),
      }),
    ).toThrow();
  });

  it("rejects invalid freshness and reconnect values", () => {
    for (const override of [
      { staleAfterSeconds: 0 },
      { staleAfterSeconds: -1 },
      { staleRowAfterSeconds: "5" },
      { reconnectInitialDelayMs: 10 },
      { reconnectMaxDelayMs: 999 },
    ]) {
      expect(() =>
        parseMarketTicksConfig({
          ...DEFAULT_MARKET_TICKS_CONFIG,
          ...override,
        }),
      ).toThrow();
    }
  });

  it("pins the persisted state schema version", () => {
    expect(() =>
      marketTicksConfigSchema.parse({
        ...DEFAULT_MARKET_TICKS_CONFIG,
        persistedStateSchemaVersion: 2,
      }),
    ).toThrow();
    expect(PERSISTED_STATE_SCHEMA_VERSION).toBe(1);
  });

  it("resolves undefined input to the documented defaults", () => {
    expect(resolveMarketTicksConfig(undefined)).toEqual(
      DEFAULT_MARKET_TICKS_CONFIG,
    );
    expect(resolveMarketTicksConfig({ staleAfterSeconds: 9 })).toEqual({
      ...DEFAULT_MARKET_TICKS_CONFIG,
      staleAfterSeconds: 9,
    });
  });
});
