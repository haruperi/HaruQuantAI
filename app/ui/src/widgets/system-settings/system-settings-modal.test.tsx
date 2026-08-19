/**
 * Unit tests for SystemSettingsModal field rendering (settings field rendering).
 *
 * Verifies the data-driven control selection: enum settings render a
 * `<select>` populated from manifest `allowed_values`, boolean settings
 * render a Disabled/Enabled select storing canonical "true"/"false", the
 * TIMEZONE setting renders the curated UTC-offset list, and other settings
 * remain free-text inputs.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, waitFor } from "@testing-library/react";

import { SystemSettingsModal } from "./SystemSettingsModal";

// Hoist fixtures so the hoisted vi.mock factories can reference them.
const { manifestFixture, settingsFixture, readSystem, tradingStoreState } = vi.hoisted(() => ({
  manifestFixture: [
    { key: "LOG_LEVEL", label: "Log level", description: "Minimum application log severity.", value_kind: "string", allowed_values: ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], minimum: null, maximum: null, activation: "restart_required" as const },
    { key: "RUNTIME_BROKER", label: "Runtime broker", description: "Provider selected for composed broker operations.", value_kind: "string", allowed_values: ["binance", "ctrader", "dukascopy", "mt5", "yahoo"], minimum: null, maximum: null, activation: "restart_required" as const },
    { key: "TIMEZONE", label: "Display timezone", description: "IANA timezone used for operator-facing presentation.", value_kind: "string", allowed_values: [], minimum: null, maximum: null, activation: "restart_required" as const },
    { key: "MT5_ENABLED", label: "Enable MT5", description: "Allow composition of the MT5 provider.", value_kind: "boolean", allowed_values: [], minimum: null, maximum: null, activation: "restart_required" as const },
    { key: "GOOGLE_USE_VERTEXAI", label: "Use Vertex AI", description: "Select Vertex AI.", value_kind: "boolean", allowed_values: [], minimum: null, maximum: null, activation: "restart_required" as const },
    { key: "APP_NAME", label: "Application name", description: "Display name.", value_kind: "string", allowed_values: [], minimum: null, maximum: null, activation: "restart_required" as const },
  ],
  settingsFixture: {
    scope: "system" as const,
    subject_id: "system",
    user_id: null,
    settings: { LOG_LEVEL: "INFO", RUNTIME_BROKER: "mt5", TIMEZONE: "UTC+2", MT5_ENABLED: "true", GOOGLE_USE_VERTEXAI: "false", APP_NAME: "HaruQuantAI" },
    version: 1,
    updated_at: "2026-01-01T00:00:00Z",
    restart_required: false,
  },
  readSystem: vi.fn(),
  tradingStoreState: {
    isSettingsOpen: true,
    closeSettings: vi.fn(),
    openSettings: vi.fn(),
  },
}));

// Stub the zustand store: modal open by default so the component renders.
vi.mock("@/store/useTradingStore", () => ({
  useTradingStore: () => tradingStoreState,
}));

// Mock the settings client so the modal loads synchronously in tests.
vi.mock("@/clients", () => ({
  apiClients: {
    settings: {
      readManifest: vi.fn().mockResolvedValue({ ok: true, data: manifestFixture }),
      readSystem,
      readCredentials: vi.fn().mockResolvedValue({ ok: true, data: [] }),
      updateSystem: vi.fn(),
      updateCredential: vi.fn(),
    },
  },
  unwrapData: (response: { data: unknown }) => response.data,
}));

describe("SystemSettingsModal — field control rendering", () => {
  beforeEach(() => {
    cleanup();
    tradingStoreState.isSettingsOpen = true;
    readSystem.mockReset();
    readSystem.mockResolvedValue({ ok: true, data: settingsFixture });
  });
  afterEach(() => {
    cleanup();
  });

  /**
   * Find a field's control by locating its label span text, then returning the
   * select/input within the same field container. Robust to the nested-span
   * label markup where getByLabelText cannot form a stable association.
   */
  function findControl(labelText: string): HTMLElement {
    const labels = Array.from(document.querySelectorAll(".system-settings-field-label"));
    const target = labels.find((el) => el.textContent === labelText);
    if (!target) throw new Error(`Field label "${labelText}" not found`);
    const field = target.closest(".system-settings-field");
    const control = field?.querySelector("select, input");
    if (!control) throw new Error(`No control found under "${labelText}"`);
    return control as HTMLElement;
  }

  it("renders enum settings as a select with manifest allowed values", async () => {
    render(<SystemSettingsModal />);
    await waitFor(() => {
      expect(findControl("Log level")).toBeTruthy();
    });
    const logLevel = findControl("Log level") as HTMLSelectElement;
    expect(logLevel.tagName).toBe("SELECT");
    const options = Array.from(logLevel.options).map((o) => o.value);
    expect(options).toEqual(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]);
    expect(logLevel.value).toBe("INFO");
  });

  it("renders runtime broker enum from manifest allowed values", async () => {
    render(<SystemSettingsModal />);
    await waitFor(() => {
      expect(findControl("Runtime broker")).toBeTruthy();
    });
    const broker = findControl("Runtime broker") as HTMLSelectElement;
    const options = Array.from(broker.options).map((o) => o.value);
    expect(options).toEqual(["binance", "ctrader", "dukascopy", "mt5", "yahoo"]);
    expect(broker.value).toBe("mt5");
  });

  it("renders boolean settings as Disabled/Enabled select storing true/false", async () => {
    render(<SystemSettingsModal />);
    await waitFor(() => {
      expect(findControl("Enable MT5")).toBeTruthy();
    });
    const mt5 = findControl("Enable MT5") as HTMLSelectElement;
    expect(mt5.tagName).toBe("SELECT");
    const options = Array.from(mt5.options).map((o) => ({ value: o.value, label: o.textContent }));
    expect(options).toEqual([
      { value: "false", label: "Disabled" },
      { value: "true", label: "Enabled" },
    ]);
    expect(mt5.value).toBe("true");

    const vertex = findControl("Use Vertex AI") as HTMLSelectElement;
    expect(vertex.value).toBe("false");
  });

  it("renders timezone as a UTC-offset select", async () => {
    render(<SystemSettingsModal />);
    await waitFor(() => {
      expect(findControl("Display timezone")).toBeTruthy();
    });
    const tz = findControl("Display timezone") as HTMLSelectElement;
    expect(tz.tagName).toBe("SELECT");
    const options = Array.from(tz.options).map((o) => o.value);
    expect(options).toContain("UTC");
    expect(options).toContain("UTC-12");
    expect(options).toContain("UTC+14");
    expect(tz.value).toBe("UTC+2");
  });

  it("keeps non-dropdown settings as free-text inputs", async () => {
    render(<SystemSettingsModal />);
    await waitFor(() => {
      expect(findControl("Application name")).toBeTruthy();
    });
    const appName = findControl("Application name") as HTMLInputElement;
    expect(appName.tagName).toBe("INPUT");
    expect(appName.value).toBe("HaruQuantAI");
  });

  it("refreshes the timezone whenever the modal is reopened", async () => {
    const { rerender } = render(<SystemSettingsModal />);
    await waitFor(() => expect((findControl("Display timezone") as HTMLSelectElement).value).toBe("UTC+2"));

    tradingStoreState.isSettingsOpen = false;
    rerender(<SystemSettingsModal />);
    readSystem.mockResolvedValue({
      ok: true,
      data: {
        ...settingsFixture,
        settings: { ...settingsFixture.settings, TIMEZONE: "UTC-6" },
        version: 2,
      },
    });
    tradingStoreState.isSettingsOpen = true;
    rerender(<SystemSettingsModal />);

    await waitFor(() => expect((findControl("Display timezone") as HTMLSelectElement).value).toBe("UTC-6"));
    expect(readSystem).toHaveBeenCalledTimes(2);
  });
});
