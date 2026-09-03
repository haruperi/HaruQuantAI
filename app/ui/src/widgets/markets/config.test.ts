import { describe, expect, it } from "vitest";

import {
  DEFAULT_MARKETS_CONFIG,
  PERSISTED_STATE_SCHEMA_VERSION,
  parseMarketsConfig,
  resolveMarketsConfig,
} from "./config";

describe("FEAT-UI-02 strict configuration — D-UI §4.8", () => {
  it("documents the defaults", () => {
    expect(DEFAULT_MARKETS_CONFIG).toEqual({
      pageSize: 50,
      maxPages: 4,
      streamSettlingSeconds: 10,
      persistedStateSchemaVersion: 1,
    });
  });

  it("parses a complete valid configuration", () => {
    const config = parseMarketsConfig({
      pageSize: 25,
      maxPages: 2,
      streamSettlingSeconds: 3,
      persistedStateSchemaVersion: 1,
    });
    expect(config.pageSize).toBe(25);
    expect(config.maxPages).toBe(2);
  });

  it("rejects unknown fields instead of silently passing", () => {
    expect(() =>
      parseMarketsConfig({
        ...DEFAULT_MARKETS_CONFIG,
        refreshMs: 1_000,
      }),
    ).toThrow();
  });

  it("rejects out-of-bound values", () => {
    for (const override of [
      { pageSize: 0 },
      { pageSize: 201 },
      { maxPages: 0 },
      { maxPages: 11 },
      { streamSettlingSeconds: 0 },
      { streamSettlingSeconds: 61 },
      { pageSize: "50" },
    ]) {
      expect(() =>
        parseMarketsConfig({ ...DEFAULT_MARKETS_CONFIG, ...override }),
      ).toThrow();
    }
  });

  it("pins the persisted state schema version", () => {
    expect(() =>
      parseMarketsConfig({
        ...DEFAULT_MARKETS_CONFIG,
        persistedStateSchemaVersion: 2,
      }),
    ).toThrow();
    expect(PERSISTED_STATE_SCHEMA_VERSION).toBe(1);
  });

  it("overlays partial input on the documented defaults", () => {
    expect(resolveMarketsConfig(undefined)).toEqual(DEFAULT_MARKETS_CONFIG);
    expect(resolveMarketsConfig({ pageSize: 100 })).toEqual({
      ...DEFAULT_MARKETS_CONFIG,
      pageSize: 100,
    });
  });
});
