import { describe, expect, it } from "vitest";

import {
  DEFAULT_WATCHLISTS_CONFIG,
  PERSISTED_STATE_SCHEMA_VERSION,
  parseWatchlistsConfig,
  resolveWatchlistsConfig,
} from "./config";

describe("FEAT-UI-03 strict configuration — D-UI §4.8", () => {
  it("documents the defaults", () => {
    expect(DEFAULT_WATCHLISTS_CONFIG).toEqual({
      refreshSeconds: 30,
      persistedStateSchemaVersion: 1,
    });
  });

  it("parses a complete valid configuration", () => {
    const config = parseWatchlistsConfig({
      refreshSeconds: 60,
      persistedStateSchemaVersion: 1,
    });
    expect(config.refreshSeconds).toBe(60);
  });

  it("rejects unknown fields instead of silently passing", () => {
    expect(() =>
      parseWatchlistsConfig({
        ...DEFAULT_WATCHLISTS_CONFIG,
        page: 1,
      }),
    ).toThrow();
  });

  it("rejects out-of-bound values", () => {
    for (const override of [
      { refreshSeconds: 4 },
      { refreshSeconds: 601 },
      { refreshSeconds: "30" },
    ]) {
      expect(() =>
        parseWatchlistsConfig({ ...DEFAULT_WATCHLISTS_CONFIG, ...override }),
      ).toThrow();
    }
  });

  it("pins the persisted state schema version", () => {
    expect(() =>
      parseWatchlistsConfig({
        ...DEFAULT_WATCHLISTS_CONFIG,
        persistedStateSchemaVersion: 2,
      }),
    ).toThrow();
    expect(PERSISTED_STATE_SCHEMA_VERSION).toBe(1);
  });

  it("overlays partial input on the documented defaults", () => {
    expect(resolveWatchlistsConfig(undefined)).toEqual(DEFAULT_WATCHLISTS_CONFIG);
    expect(resolveWatchlistsConfig({ refreshSeconds: 120 })).toEqual({
      ...DEFAULT_WATCHLISTS_CONFIG,
      refreshSeconds: 120,
    });
  });
});
