/**
 * Component tests for the header profile section (FEAT-UI-01, FR-UI-011/013/
 * FR-UI-016/017/203/204/205): digital clock segments, the 1-Click confirmation
 * switch, the colour-coded account-mode badge, and the profile dropdown opened
 * from the `<` chevron. Every dropdown action is asserted against the real
 * store/client mechanism it drives.
 */
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";

import { Header } from "./Header";
import { useTradingStore } from "../../store/useTradingStore";
import { useWorkspaceStore } from "../../features/workspaces";

const { readSystem, updateSystem, accountProfile, listExecutionSessions, actOnExecutionSession, logout } = vi.hoisted(() => ({
  readSystem: vi.fn(),
  updateSystem: vi.fn(),
  accountProfile: vi.fn(),
  listExecutionSessions: vi.fn(),
  actOnExecutionSession: vi.fn(),
  logout: vi.fn(),
}));

vi.mock("@/clients", () => ({
  apiClients: {
    settings: { readSystem, updateSystem },
    trading: { accountProfile, listExecutionSessions, actOnExecutionSession },
  },
  unwrapData: (response: { data: unknown }) => response.data,
}));

vi.mock("@/context", () => ({
  useAuth: () => ({ logout, state: "authenticated", principal: null, error: null }),
}));

const initialState = useWorkspaceStore.getState();

/** One stored system-settings document, as the backend returns it. */
const systemSettingsResponse = (accountMode: string, version = 7) => ({
  data: {
    settings: { TIMEZONE: "UTC", LOG_LEVEL: "INFO", ACCOUNT_MODE: accountMode },
    version,
  },
});

beforeEach(() => {
  vi.clearAllMocks();
  readSystem.mockResolvedValue(systemSettingsResponse("sim"));
  listExecutionSessions.mockResolvedValue({ data: [] });
  actOnExecutionSession.mockResolvedValue({ data: {} });
  accountProfile.mockResolvedValue({
    data: {
      contract_version: "v1",
      schema_id: "api.trading.account_profile.v1",
      account_name: "haruquantai",
      session_name: "Research SIM",
      trade_mode: "SIMULATION",
      selected_mode: "sim",
      mode_compatible: true,
      environment_label: "Simulation Environment",
      source: "simulator",
      currency: null,
      balance: null,
      equity: null,
      profit: null,
      margin: null,
      free_margin: null,
      margin_level: null,
      leverage: null,
      retrieved_at: "2026-08-17T00:00:00Z",
    },
  });
  updateSystem.mockImplementation((settings: Record<string, string>) =>
    Promise.resolve({ data: { settings, version: 8 } }),
  );
  logout.mockResolvedValue(undefined);
  useWorkspaceStore.setState(initialState, true);
  useWorkspaceStore.setState({ accountMode: "sim", accountModeVersion: 7 });
  useTradingStore.setState({
    practiceBalance: 100000,
    netPL: 0,
    margin: 0,
    available: 100000,
    mode: "practice",
    isSettingsOpen: false,
  });
});

const openMenu = async () => {
  fireEvent.click(screen.getByRole("button", { name: "Open profile menu" }));
  await screen.findByRole("menu", { name: "Profile menu" });
};

describe("header profile section rendering", () => {
  it("shows the selected mode and active session name together", async () => {
    render(<Header />);
    expect(await screen.findByRole("status")).toHaveTextContent("SIM : Research SIM");
  });

  it("automatically starts the session named Default on initial load when no session is running", async () => {
    listExecutionSessions.mockResolvedValueOnce({
      data: [
        {
          session_id: "sess-default-1",
          name: "Default",
          mode: "sim",
          is_active: false,
          is_default: true,
          lifecycle_state: "stopped",
        },
      ],
    });
    render(<Header />);
    await waitFor(() => {
      expect(actOnExecutionSession).toHaveBeenCalledWith(
        "start",
        expect.objectContaining({ name: "Default", mode: "sim" }),
      );
    });
  });

  it("shows an explicit no-session state", async () => {
    const current = await accountProfile();
    accountProfile.mockResolvedValueOnce({
      data: { ...current.data, session_name: null },
    });
    render(<Header />);
    expect(await screen.findByRole("status")).toHaveTextContent("SIM : NO SESSION");
  });

  it("renders the digital clock as segmented digit groups with a zone suffix", async () => {
    render(<Header />);
    const clock = await screen.findByLabelText(/:\d\d (am|pm) UTC \d\d\/\d\d\/\d{4}/);
    expect(clock.className).toContain("digital-time");
    expect(clock.querySelectorAll(".dt-seg")).toHaveLength(3);
    expect(clock.querySelectorAll(".dt-colon")).toHaveLength(2);
    expect(clock.querySelector(".dt-suffix")?.textContent).toMatch(/ (am|pm) UTC /);
    expect(clock).toHaveAttribute("aria-haspopup", "dialog");
  });

  it("opens a correction dialog and persists the selected timezone", async () => {
    render(<Header />);
    const clock = await screen.findByLabelText(/:\d\d (am|pm) UTC \d\d\/\d\d\/\d{4}/);
    fireEvent.click(clock);
    expect(screen.getByRole("dialog", { name: "Correct display time" })).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Time zone"), { target: { value: "UTC+2" } });
    fireEvent.click(screen.getByRole("button", { name: "Apply" }));

    await waitFor(() => expect(updateSystem).toHaveBeenCalledWith(
      { TIMEZONE: "UTC+2", LOG_LEVEL: "INFO", ACCOUNT_MODE: "sim" },
      7,
    ));
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
  });

  it("opens the clock correction dialog from the keyboard", async () => {
    render(<Header />);
    const clock = await screen.findByLabelText(/:\d\d (am|pm) UTC \d\d\/\d\d\/\d{4}/);
    clock.focus();
    fireEvent.keyDown(clock, { key: "Enter" });
    expect(screen.getByRole("dialog", { name: "Correct display time" })).toBeInTheDocument();
  });

  it("renders the 1-Click switch reflecting the confirmation mode", () => {
    render(<Header />);
    // Confirmation required by default, so 1-click trading is off.
    expect(
      screen.getByRole("switch", { name: "1-Click trading" }),
    ).toHaveAttribute("aria-checked", "false");
    expect(screen.getByText("1-Click")).toBeInTheDocument();
  });

  it("toggles the confirmation mode from the switch", () => {
    render(<Header />);
    fireEvent.click(screen.getByRole("switch", { name: "1-Click trading" }));
    expect(useWorkspaceStore.getState().orderConfirmationRequired).toBe(false);
    expect(
      screen.getByRole("switch", { name: "1-Click trading" }),
    ).toHaveAttribute("aria-checked", "true");
  });

  it("presents the account mode as a colour-coded badge", async () => {
    render(<Header />);
    const badge = await screen.findByRole("status");
    expect(badge).toHaveTextContent("SIM");
    // Colour is carried by the mode attribute the stylesheet keys on, so the
    // badge and the dropdown can never disagree about a mode's colour.
    expect(badge).toHaveAttribute("data-mode", "sim");
    expect(badge.className).toContain("account-mode-badge");
    expect(badge.getAttribute("title")).toContain("virtually");
  });

  it("presents an unresolved mode as unknown rather than guessing", () => {
    useWorkspaceStore.setState({ accountMode: "unknown", accountModeVersion: -1 });
    render(<Header />);
    const badge = screen.getByRole("status");
    expect(badge).toHaveTextContent("MODE UNKNOWN");
    expect(badge).toHaveAttribute("data-mode", "unknown");
  });

  it("shows the provider account name, environment, and chevron", async () => {
    render(<Header />);
    expect(await screen.findByText("haruquantai")).toBeInTheDocument();
    expect(screen.getByText("Simulation Environment")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Open profile menu" }),
    ).toHaveAttribute("aria-expanded", "false");
  });

  it("renders MT5 account name and trade mode instead of app identity", async () => {
    useWorkspaceStore.setState({ accountMode: "demo", accountModeVersion: 7 });
    readSystem.mockResolvedValue(systemSettingsResponse("demo"));
    accountProfile.mockResolvedValue({
      data: {
        contract_version: "v1",
        schema_id: "api.trading.account_profile.v1",
        account_name: "Rufaro MT5",
        trade_mode: "DEMO",
        selected_mode: "demo",
        mode_compatible: true,
        environment_label: "Demo Environment",
        source: "mt5",
        currency: "USD",
        balance: "100000.00",
        equity: "100125.50",
        profit: "125.50",
        margin: "1000.00",
        free_margin: "99125.50",
        margin_level: "10012.55",
        leverage: "100",
        retrieved_at: "2026-08-17T00:00:00Z",
      },
    });
    render(<Header />);
    expect(await screen.findByText("Rufaro MT5")).toBeInTheDocument();
    expect(screen.getByText("Demo Environment")).toBeInTheDocument();
    expect(screen.getByText("BALANCE")).toBeInTheDocument();
    expect(screen.getByText("$100,000.00")).toBeInTheDocument();
    expect(screen.getByText("PROFIT")).toBeInTheDocument();
    expect(screen.getByText("FREE MARGIN")).toBeInTheDocument();
    expect(screen.getByText("MARGIN LEVEL")).toBeInTheDocument();
    expect(screen.getByText("1:100")).toBeInTheDocument();
    expect(screen.getByText("EQUITY")).toBeInTheDocument();
    expect(screen.queryByText("Trader")).toBeNull();
  });

  it("switches Profit between Money and internally calculated Percent", async () => {
    useWorkspaceStore.setState({ accountMode: "demo", accountModeVersion: 7 });
    readSystem.mockResolvedValue(systemSettingsResponse("demo"));
    accountProfile.mockResolvedValue({
      data: {
        contract_version: "v1",
        schema_id: "api.trading.account_profile.v1",
        account_name: "Rufaro MT5",
        trade_mode: "DEMO",
        selected_mode: "demo",
        mode_compatible: true,
        environment_label: "Demo Environment",
        source: "mt5",
        currency: "USD",
        balance: "100000.00",
        equity: "100250.00",
        profit: "250.00",
        margin: "0",
        free_margin: "100250.00",
        margin_level: null,
        leverage: "100",
        retrieved_at: "2026-08-17T00:00:00Z",
      },
    });
    render(<Header />);
    expect(await screen.findByText("$250.00")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Account metric settings" }));
    const menu = screen.getByRole("menu", { name: "Account metric settings" });
    expect(within(menu).getByRole("radio", { name: "Money" })).toBeChecked();
    fireEvent.click(within(menu).getByRole("radio", { name: "Percent" }));
    expect(screen.getByText("0.25%")).toBeInTheDocument();
    expect(within(menu).getByRole("spinbutton", { name: "Leverage" })).toBeDisabled();
  });

  it("shows unavailable percentage when account balance is zero", async () => {
    accountProfile.mockResolvedValue({
      data: {
        contract_version: "v1",
        schema_id: "api.trading.account_profile.v1",
        account_name: "haruquantai",
        trade_mode: "SIMULATION",
        selected_mode: "sim",
        mode_compatible: true,
        environment_label: "Simulation Environment",
        source: "simulator",
        currency: "USD",
        balance: "0",
        equity: "5",
        profit: "5",
        margin: "0",
        free_margin: "5",
        margin_level: null,
        leverage: null,
        retrieved_at: "2026-08-17T00:00:00Z",
      },
    });
    render(<Header />);
    await waitFor(() => expect(screen.getAllByText("$5.00")).not.toHaveLength(0));
    fireEvent.click(screen.getByRole("button", { name: "Account metric settings" }));
    fireEvent.click(screen.getByRole("radio", { name: "Percent" }));
    const profitMetric = screen.getByText("PROFIT").closest('.metric-item');
    expect(profitMetric).toHaveTextContent("—");
  });

  it("disables trading globally when selected and platform modes differ", async () => {
    useWorkspaceStore.setState({ accountMode: "live", accountModeVersion: 7 });
    readSystem.mockResolvedValue(systemSettingsResponse("live"));
    accountProfile.mockResolvedValue({
      data: {
        contract_version: "v1",
        schema_id: "api.trading.account_profile.v1",
        account_name: "Demo Account",
        trade_mode: "DEMO",
        selected_mode: "live",
        mode_compatible: false,
        environment_label: "Demo Environment",
        source: "mt5",
        retrieved_at: "2026-08-17T00:00:00Z",
      },
    });
    render(<Header />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Trading disabled: selected LIVE, platform DEMO",
    );
    expect(useWorkspaceStore.getState().tradingModeCompatible).toBe(false);
  });

  it("shows explicit unavailable identity when the provider read fails", async () => {
    accountProfile.mockRejectedValue(new Error("unavailable"));
    render(<Header />);
    expect(await screen.findByText("Account unavailable")).toBeInTheDocument();
    expect(screen.getByText("Environment unavailable")).toBeInTheDocument();
  });
});

describe("profile dropdown interactions", () => {
  it("opens from the chevron and closes on Escape", async () => {
    render(<Header />);
    await openMenu();
    expect(
      screen.getByRole("button", { name: "Close profile menu" }),
    ).toHaveAttribute("aria-expanded", "true");

    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("menu", { name: "Profile menu" })).toBeNull();
  });

  it("lists the simulator menu groups: account mode, settings, logout", async () => {
    render(<Header />);
    await openMenu();
    expect(screen.getByText("Account Mode:")).toBeInTheDocument();
    const group = screen.getByRole("radiogroup", { name: "Account mode" });
    for (const mode of ["SIM", "DEMO", "LIVE"]) {
      expect(within(group).getByRole("radio", { name: mode })).toBeInTheDocument();
    }
    expect(screen.queryByText("Reset")).toBeNull();
    expect(screen.queryByText("Practice Account:")).toBeNull();
    expect(screen.getByRole("menuitem", { name: /Settings/ })).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: /Logout/ })).toBeInTheDocument();
  });

  it("selects exactly one account mode and persists it as the app context", async () => {
    render(<Header />);
    await openMenu();

    expect(screen.getByRole("radio", { name: "SIM" })).toHaveAttribute("aria-checked", "true");
    expect(screen.getByRole("radio", { name: "DEMO" })).toHaveAttribute("aria-checked", "false");

    fireEvent.click(screen.getByRole("radio", { name: "LIVE" }));

    // The complete settings document is written back, not just the one key:
    // a partial write would erase every other system setting.
    await waitFor(() =>
      expect(updateSystem).toHaveBeenCalledWith(
        { TIMEZONE: "UTC", LOG_LEVEL: "INFO", ACCOUNT_MODE: "live" },
        7,
      ),
    );
    await waitFor(() => expect(useWorkspaceStore.getState().accountMode).toBe("live"));
    // The new record version is adopted so the next write locks correctly.
    expect(useWorkspaceStore.getState().accountModeVersion).toBe(8);
    expect(screen.getByRole("radio", { name: "LIVE" })).toHaveAttribute("aria-checked", "true");
    expect(screen.getByRole("radio", { name: "SIM" })).toHaveAttribute("aria-checked", "false");
    expect(screen.getByRole("radio", { name: "DEMO" })).toHaveAttribute("aria-checked", "false");
  });

  it("reverts the selection when the backend refuses the mode change", async () => {
    updateSystem.mockRejectedValue(new Error("SETTINGS_VERSION_CONFLICT"));
    render(<Header />);
    await openMenu();

    fireEvent.click(screen.getByRole("radio", { name: "LIVE" }));

    // The shell must never present a mode the backend is not routing to.
    await waitFor(() => expect(useWorkspaceStore.getState().accountMode).toBe("sim"));
    expect(screen.getByRole("radio", { name: "SIM" })).toHaveAttribute("aria-checked", "true");
    expect(await screen.findByText("Account mode change refused")).toBeInTheDocument();
  });

  it("hydrates the stored account mode from system settings on mount", async () => {
    useWorkspaceStore.setState({ accountMode: "unknown", accountModeVersion: -1 });
    readSystem.mockResolvedValue(systemSettingsResponse("demo", 3));
    render(<Header />);

    await waitFor(() => expect(useWorkspaceStore.getState().accountMode).toBe("demo"));
    expect(useWorkspaceStore.getState().accountModeVersion).toBe(3);
  });

  it("records the settings version even before any mode has been stored", async () => {
    // The very first selection has nothing stored to hydrate from, but it
    // still needs a version to lock its write against, or it can never be made.
    useWorkspaceStore.setState({ accountMode: "sim", accountModeVersion: -1 });
    readSystem.mockResolvedValue({
      data: { settings: { TIMEZONE: "UTC", LOG_LEVEL: "INFO" }, version: 6 },
    });
    render(<Header />);

    await waitFor(() => expect(useWorkspaceStore.getState().accountModeVersion).toBe(6));
    // The session-reported mode stands until the operator chooses.
    expect(useWorkspaceStore.getState().accountMode).toBe("sim");

    await openMenu();
    fireEvent.click(screen.getByRole("radio", { name: "LIVE" }));
    await waitFor(() =>
      expect(updateSystem).toHaveBeenCalledWith(
        { TIMEZONE: "UTC", LOG_LEVEL: "INFO", ACCOUNT_MODE: "live" },
        6,
      ),
    );
  });

  it("closes when clicking outside the panel", async () => {
    render(<Header />);
    await openMenu();
    fireEvent.mouseDown(document.body);
    expect(screen.queryByRole("menu", { name: "Profile menu" })).toBeNull();
  });

  it("opens System Settings from the Settings item", async () => {
    render(<Header />);
    await openMenu();

    fireEvent.click(screen.getByRole("menuitem", { name: /Settings/ }));
    expect(useTradingStore.getState().isSettingsOpen).toBe(true);
    expect(screen.queryByRole("menu", { name: "Profile menu" })).toBeNull();
  });

  it("signs the session out from the Logout item", async () => {
    render(<Header />);
    await openMenu();

    fireEvent.click(screen.getByRole("menuitem", { name: /Logout/ }));
    await waitFor(() => expect(logout).toHaveBeenCalledTimes(1));
    expect(screen.queryByRole("menu", { name: "Profile menu" })).toBeNull();
  });
});
