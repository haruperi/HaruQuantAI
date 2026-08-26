/**
 * Unit tests for SettingsWidget (FR-UI-SET_APPEARANCE, FR-UI-CONFIGURE_CLIENT,
 * FR-UI-MANAGE_LICENSE, FR-UI-DISTINGUISH_STATE) and settingsWidgetDefinition.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { SettingsWidget, settingsWidgetDefinition } from "../index";
import { AdministerSystemClientProvider } from "../../../features/administer_system";
import type { IUiPresentationClient } from "../../../clients/ui_client";

const mockAdministerSystem = vi.fn();

const mockClient: IUiPresentationClient & { isDevOnly?: boolean } = {
  isDevOnly: true,
  startWork: async () => { throw new Error("unused"); },
  manageLayouts: async () => { throw new Error("unused"); },
  editInputs: async () => { throw new Error("unused"); },
  authorStrategies: async () => { throw new Error("unused"); },
  runResearch: async () => { throw new Error("unused"); },
  editProjects: async () => { throw new Error("unused"); },
  manageData: async () => { throw new Error("unused"); },
  operateDatabanks: async () => { throw new Error("unused"); },
  exploreResults: async () => { throw new Error("unused"); },
  composePortfolios: async () => { throw new Error("unused"); },
  editCode: async () => { throw new Error("unused"); },
  monitorWork: async () => { throw new Error("unused"); },
  administerSystem: mockAdministerSystem,
  operateTrading: async () => { throw new Error("unused"); },
  ensureAccess: async () => { throw new Error("unused"); },
  extendViews: async () => { throw new Error("unused"); },
};

const dummyProps = {
  instance: {
    instance_id: "inst-settings-test",
    widget_type: "settings",
    workspace_id: "workstation-main",
    configuration_version: 1,
    state_version: 1,
    schema_version: 1 as const,
  },
  configuration: {},
  state: {},
  onStateChange: () => undefined,
  onConfigChange: () => undefined,
};

function renderWithProvider(client: IUiPresentationClient = mockClient) {
  return render(
    <AdministerSystemClientProvider client={client}>
      <SettingsWidget {...dummyProps} />
    </AdministerSystemClientProvider>
  );
}

describe("SettingsWidget & Definition", () => {
  beforeEach(() => {
    cleanup();
    mockAdministerSystem.mockReset();
    mockAdministerSystem.mockResolvedValue({
      outcome: "SUCCESS",
      request_id: "req-1",
      result_version: 1,
      preferences: {
        theme: "dark",
        density: "comfortable",
        font_scale: "1",
        locale: "en-US",
        schema_version: 1,
      },
      accessibility: {
        high_contrast: false,
        reduced_motion: false,
        screen_reader_optimized: false,
        schema_version: 1,
      },
      administration: null,
      schema_version: 1,
    });
  });

  afterEach(() => {
    cleanup();
  });

  it("exports a valid widget definition with single-feature ownership", () => {
    expect(settingsWidgetDefinition.descriptor.widget_type).toBe("settings");
    expect(settingsWidgetDefinition.descriptor.owning_feature).toBe("FEAT-UI-ADMINISTER_SYSTEM");
    expect(settingsWidgetDefinition.descriptor.type_version).toBe(1);
    expect(typeof settingsWidgetDefinition.component).toBe("function");
  });

  it("renders appearance preferences and handles changes (FR-UI-SET_APPEARANCE)", async () => {
    renderWithProvider();

    await waitFor(() => {
      expect(screen.getByTestId("settings-widget")).toBeTruthy();
    });

    expect(screen.getByTestId("settings-mock-banner")).toBeTruthy();

    const themeSelect = screen.getByTestId("theme-select") as HTMLSelectElement;
    expect(themeSelect.value).toBe("dark");
    fireEvent.change(themeSelect, { target: { value: "light" } });
    expect(themeSelect.value).toBe("light");

    const densitySelect = screen.getByTestId("density-select") as HTMLSelectElement;
    expect(densitySelect.value).toBe("comfortable");
    fireEvent.change(densitySelect, { target: { value: "compact" } });
    expect(densitySelect.value).toBe("compact");

    const fontScaleSelect = screen.getByTestId("font-scale-select") as HTMLSelectElement;
    expect(fontScaleSelect.value).toBe("1");

    const highContrastToggle = screen.getByTestId("high-contrast-toggle") as HTMLInputElement;
    expect(highContrastToggle.checked).toBe(false);
    fireEvent.click(highContrastToggle);
    expect(highContrastToggle.checked).toBe(true);

    const saveBtn = screen.getByTestId("save-appearance-btn");
    fireEvent.click(saveBtn);
    expect(screen.getByTestId("settings-status-message").textContent).toContain("Appearance preferences saved");

    const resetBtn = screen.getByTestId("reset-appearance-btn");
    fireEvent.click(resetBtn);
    expect(screen.getByTestId("settings-status-message").textContent).toContain("Appearance reset to defaults");
  });

  it("renders tab selection structurally and with visible active state (FR-UI-DISTINGUISH_STATE)", async () => {
    renderWithProvider();

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: /Appearance/i })).toBeTruthy();
    });

    const tabAppearance = screen.getByRole("tab", { name: /Appearance/i });
    const tabClient = screen.getByRole("tab", { name: /Client Configuration/i });

    // Verify stable IDs and attributes on appearance tab
    expect(tabAppearance.id).toBe("tab-appearance");
    expect(tabAppearance).toHaveAttribute("aria-selected", "true");
    expect(tabAppearance.textContent).toContain("(Active)");

    // Dereference aria-controls to tabpanel and aria-labelledby back to tab
    const appearanceControlsId = tabAppearance.getAttribute("aria-controls");
    expect(appearanceControlsId).toBe("section-appearance");
    const appearancePanel = document.getElementById(appearanceControlsId!);
    expect(appearancePanel).toBeTruthy();
    expect(appearancePanel).toHaveAttribute("role", "tabpanel");
    expect(appearancePanel).toHaveAttribute("aria-labelledby", "tab-appearance");

    // Client tab is unselected
    expect(tabClient.id).toBe("tab-client");
    expect(tabClient).toHaveAttribute("aria-selected", "false");
    expect(tabClient.textContent).not.toContain("(Active)");

    // Switch to client tab
    fireEvent.click(tabClient);

    // Client tab is now selected
    expect(tabClient).toHaveAttribute("aria-selected", "true");
    expect(tabClient.textContent).toContain("(Active)");

    // Dereference aria-controls to client tabpanel and aria-labelledby back to client tab
    const clientControlsId = tabClient.getAttribute("aria-controls");
    expect(clientControlsId).toBe("section-client");
    const clientPanel = document.getElementById(clientControlsId!);
    expect(clientPanel).toBeTruthy();
    expect(clientPanel).toHaveAttribute("role", "tabpanel");
    expect(clientPanel).toHaveAttribute("aria-labelledby", "tab-client");

    // Appearance tab is now unselected
    expect(tabAppearance).toHaveAttribute("aria-selected", "false");
    expect(tabAppearance.textContent).not.toContain("(Active)");
  });

  it("renders client configuration and write-only credentials (FR-UI-CONFIGURE_CLIENT)", async () => {
    renderWithProvider();

    await waitFor(() => {
      expect(screen.getByTestId("tab-client")).toBeTruthy();
    });

    fireEvent.click(screen.getByTestId("tab-client"));

    expect(screen.getByTestId("section-client")).toBeTruthy();

    const tzSelect = screen.getByTestId("timezone-select") as HTMLSelectElement;
    expect(tzSelect.value).toBe("UTC");
    fireEvent.change(tzSelect, { target: { value: "UTC+2" } });
    expect(tzSelect.value).toBe("UTC+2");

    const logSelect = screen.getByTestId("loglevel-select") as HTMLSelectElement;
    expect(logSelect.value).toBe("INFO");

    const brokerSelect = screen.getByTestId("broker-select") as HTMLSelectElement;
    expect(brokerSelect.value).toBe("mt5");

    const appNameInput = screen.getByTestId("appname-input") as HTMLInputElement;
    expect(appNameInput.value).toBe("HaruQuantAI");

    // Write-only credentials test
    const mt5Slot = screen.getByTestId("cred-slot-mt5");
    expect(mt5Slot).toBeTruthy();
    expect(screen.getByTestId("cred-status-mt5").textContent).toBe("Configured");

    expect(screen.getByTestId("cred-slot-binance")).toBeTruthy();
    expect(screen.getByTestId("cred-status-binance").textContent).toBe("Not Configured");

    // Fill in new password field
    const apiKeyInput = screen.getByLabelText("Binance API Keys api_key") as HTMLInputElement;
    expect(apiKeyInput.type).toBe("password");
    fireEvent.change(apiKeyInput, { target: { value: "mock-key-123" } });

    fireEvent.click(screen.getByTestId("cred-save-binance"));
    expect(screen.getByTestId("cred-status-binance").textContent).toBe("Configured");
    expect(screen.getByTestId("settings-status-message").textContent).toContain("BINANCE credentials saved securely");
  });

  it("renders license and entitlement details and refreshes (FR-UI-MANAGE_LICENSE)", async () => {
    renderWithProvider();

    await waitFor(() => {
      expect(screen.getByTestId("tab-license")).toBeTruthy();
    });

    fireEvent.click(screen.getByTestId("tab-license"));

    expect(screen.getByTestId("section-license")).toBeTruthy();
    expect(screen.getByTestId("license-edition").textContent).toContain("Community Workstation");
    expect(screen.getByTestId("license-status").textContent).toBe("VALID");

    const refreshBtn = screen.getByTestId("refresh-license-btn");
    fireEvent.click(refreshBtn);

    await waitFor(() => {
      expect(screen.getByTestId("settings-status-message").textContent).toContain("License state refreshed");
    });
  });

  it("renders future de-mock stage placeholders", async () => {
    renderWithProvider();

    await waitFor(() => {
      expect(screen.getByTestId("tab-demock")).toBeTruthy();
    });

    fireEvent.click(screen.getByTestId("tab-demock"));

    expect(screen.getByTestId("section-demock")).toBeTruthy();
    expect(screen.getByTestId("demock-language").textContent).toContain("FR-UI-SET_LANGUAGE");
    expect(screen.getByTestId("demock-updates").textContent).toContain("FR-UI-MANAGE_UPDATES");
    expect(screen.getByTestId("demock-capabilities").textContent).toContain("FR-UI-ADMINISTER_CAPABILITIES");
  });

  it("displays unavailable error state when client throws", async () => {
    const errorClient: IUiPresentationClient = {
      ...mockClient,
      administerSystem: vi.fn().mockRejectedValue(new Error("Network failure")),
    };

    renderWithProvider(errorClient);

    await waitFor(() => {
      expect(screen.getByTestId("settings-unavailable")).toBeTruthy();
    });
    expect(screen.getByText("System Settings Unavailable")).toBeTruthy();
  });
});
