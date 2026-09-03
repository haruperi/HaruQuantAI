import { describe, expect, it } from "vitest";

import { SYSTEM_SETTINGS_MANIFEST } from "./manifest";

describe("SYSTEM_SETTINGS_MANIFEST (FEAT-UI-13)", () => {
  it("declares the permanent feature identity and type", () => {
    expect(SYSTEM_SETTINGS_MANIFEST.featureId).toBe("FEAT-UI-13");
    expect(SYSTEM_SETTINGS_MANIFEST.widgetType).toBe("systemSettings");
    expect(SYSTEM_SETTINGS_MANIFEST.widgetVersion).toBe(1);
  });

  it("declares the transport capability dependency", () => {
    expect(SYSTEM_SETTINGS_MANIFEST.requiredCapabilities).toEqual([
      "interfaces.serve-api-events@1",
    ]);
  });

  it("declares explicit removal semantics", () => {
    expect(SYSTEM_SETTINGS_MANIFEST.removal.persistedState).toBe("none");
    expect(SYSTEM_SETTINGS_MANIFEST.removal.description).toContain(
      "haruquantai.db",
    );
  });
});
