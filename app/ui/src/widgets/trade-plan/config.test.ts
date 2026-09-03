import { describe, expect, it } from "vitest";

import {
  DEFAULT_TRADE_PLAN_CONFIG,
  PERSISTED_STATE_SCHEMA_VERSION,
  parseTradePlanConfig,
  resolveTradePlanConfig,
} from "./config";

describe("TradePlanConfig (FEAT-UI-10)", () => {
  it("resolves default configuration when input is undefined", () => {
    const resolved = resolveTradePlanConfig(undefined);
    expect(resolved).toEqual(DEFAULT_TRADE_PLAN_CONFIG);
  });

  it("accepts valid partial configuration overlays", () => {
    const resolved = resolveTradePlanConfig({ defaultRiskRewardRatio: "2:1" });
    expect(resolved.defaultRiskRewardRatio).toBe("2:1");
    expect(resolved.persistedStateSchemaVersion).toBe(
      PERSISTED_STATE_SCHEMA_VERSION,
    );
  });

  it("fails loudly when unknown fields are supplied", () => {
    expect(() =>
      parseTradePlanConfig({
        defaultRiskRewardRatio: "3:1",
        persistedStateSchemaVersion: PERSISTED_STATE_SCHEMA_VERSION,
        unknownField: "forbidden",
      }),
    ).toThrow();
  });
});
