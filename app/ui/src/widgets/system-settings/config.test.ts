import { describe, expect, it } from "vitest";

import {
  DEFAULT_SYSTEM_SETTINGS_CONFIG,
  PERSISTED_STATE_SCHEMA_VERSION,
  parseSystemSettingsConfig,
  resolveSystemSettingsConfig,
} from "./config";

describe("SystemSettingsConfig (FEAT-UI-13)", () => {
  it("resolves default configuration when input is undefined", () => {
    const resolved = resolveSystemSettingsConfig(undefined);
    expect(resolved).toEqual(DEFAULT_SYSTEM_SETTINGS_CONFIG);
  });

  it("accepts valid partial configuration overlays", () => {
    const resolved = resolveSystemSettingsConfig({ refreshOnOpen: false });
    expect(resolved.refreshOnOpen).toBe(false);
    expect(resolved.persistedStateSchemaVersion).toBe(
      PERSISTED_STATE_SCHEMA_VERSION,
    );
  });

  it("fails loudly when unknown fields are supplied", () => {
    expect(() =>
      parseSystemSettingsConfig({
        refreshOnOpen: true,
        persistedStateSchemaVersion: PERSISTED_STATE_SCHEMA_VERSION,
        unknownField: "forbidden",
      }),
    ).toThrow();
  });
});
