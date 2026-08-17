import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useWorkspaceStore } from "@/features/workspaces";

const { listExecutionSessions } = vi.hoisted(() => ({ listExecutionSessions: vi.fn() }));
vi.mock("@/clients", () => ({ ApiClientError: class extends Error {}, apiClients: { trading: { listExecutionSessions } } }));
vi.mock("@/features/price-ladder", () => ({ PriceLadderWidget: ({ accountId, route, symbol, variant }: { accountId?: string; route?: string; symbol?: string; variant?: string }) => <div data-testid="ladder">{variant}|{accountId}|{route}|{symbol}</div> }));
vi.mock("./OrderTicket", () => ({ OrderTicket: ({ accountId, onSymbolChange }: { accountId?: string; onSymbolChange?: (symbol: string) => void }) => <div data-testid="ticket">{accountId}<button type="button" onClick={() => onSymbolChange?.("EURJPY")}>Select EURJPY</button></div> }));
import { TradingWidget } from "./TradingWidget";

const session = (overrides: Record<string, unknown> = {}) => ({ mode: "demo", name: "MT5 Demo", provider_account_ref: "acct-42", is_active: true, is_default: true, ...overrides });

describe("TradingWidget — FR-UI-147/208/225/226", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useWorkspaceStore.setState({ accountMode: "demo", platformAccountMode: "demo", tradingModeCompatible: true });
    listExecutionSessions.mockResolvedValue({ status: "success", data: [session()] });
  });

  it("derives route and account from the active matching session", async () => {
    render(<TradingWidget />);
    expect(await screen.findByTestId("ticket")).toHaveTextContent("acct-42");
    expect(screen.getByTestId("ladder")).toHaveTextContent("trading|acct-42|demo|EURUSD");
    expect(screen.getByText("DEMO · MT5 Demo")).toBeTruthy();
    expect(screen.queryByLabelText("Route")).toBeNull();
    expect(screen.queryByLabelText("Account ID")).toBeNull();
    expect(screen.queryByText("Authority evidence")).toBeNull();
    expect(screen.queryByText("Broker targets")).toBeNull();
  });

  it("synchronizes an exact ticket symbol with the embedded ladder", async () => {
    render(<TradingWidget />);
    await screen.findByTestId("ladder");
    fireEvent.click(screen.getByRole("button", { name: "Select EURJPY" }));
    await waitFor(() => expect(screen.getByTestId("ladder")).toHaveTextContent("EURJPY"));
  });

  it("uses a default matching session when none is active", async () => {
    listExecutionSessions.mockResolvedValue({ status: "success", data: [session({ is_active: false, is_default: true, provider_account_ref: "default-7" })] });
    render(<TradingWidget />);
    expect(await screen.findByTestId("ticket")).toHaveTextContent("default-7");
  });

  it("fails closed when no matching execution session exists", async () => {
    listExecutionSessions.mockResolvedValue({ status: "success", data: [session({ mode: "live" })] });
    render(<TradingWidget />);
    expect(await screen.findByRole("alert")).toHaveTextContent("No active or default DEMO execution session");
    expect(screen.queryByTestId("ticket")).toBeNull();
    expect(screen.queryByTestId("ladder")).toBeNull();
  });

  it("shows execution-session read failures", async () => {
    listExecutionSessions.mockRejectedValue(new Error("registry offline"));
    render(<TradingWidget />);
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("registry offline"));
  });
});
