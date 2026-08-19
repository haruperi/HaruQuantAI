import { beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useWorkspaceStore } from "../workspaces";
import { useTradingStore } from "../../store/useTradingStore";

const { constraints, quotes, catalogue, accountProfile, preflight, submit } = vi.hoisted(() => ({ constraints: vi.fn(), quotes: vi.fn(), catalogue: vi.fn(), accountProfile: vi.fn(), preflight: vi.fn(), submit: vi.fn() }));
vi.mock("../../clients", async () => ({ ApiClientError: class extends Error { retryable = false; }, apiClients: { data: { quotes }, strategies: { catalogue }, trading: { accountProfile, instrumentConstraints: constraints, preflightOrder: preflight, submitOrder: submit } } }));
vi.mock("../watchlists/symbolUniverse", () => ({
  loadSymbolUniverse: () => Promise.resolve(["EURUSD", "EURJPY", "XAUUSD"]),
  filterSymbols: (values: string[], term: string) => values.filter((value) => value.includes(term.toUpperCase())),
  resolveSourceSymbol: (values: string[], term: string) => values.find((value) => value.toUpperCase() === term.trim().toUpperCase()) ?? null,
}));
import { OrderTicket } from "./OrderTicket";

beforeEach(() => {
  cleanup(); vi.clearAllMocks();
  constraints.mockResolvedValue({ status: "success", data: { contract_version: "v1", schema_id: "api.trading.instrument_constraints.v1", symbol: "EURUSD", source_id: "mt5", quantity_unit: "lots", min_quantity: "0.01", max_quantity: "10", quantity_step: "0.01", price_tick: "0.00001", digits: 5, pip_size: "0.0001", trade_tick_size: "0.00001", trade_tick_value_profit: "1", trade_tick_value_loss: "1", trade_contract_size: "100000", profit_currency: "USD", supported_order_types: ["MARKET", "LIMIT", "STOP", "STOP_LIMIT"], supported_time_in_force: ["IOC"], supports_stop_loss: true, supports_take_profit: true, retrieved_at: "2026-08-17T12:00:00Z" } });
  accountProfile.mockResolvedValue({ status: "success", data: { contract_version: "v1", schema_id: "api.trading.account_profile.v1", account_name: "Demo", session_name: "Test", trade_mode: "DEMO", selected_mode: "demo", mode_compatible: true, environment_label: "Demo", source: "mt5", currency: "USD", balance: "10000", equity: "10000", profit: "0", margin: "0", free_margin: "10000", margin_level: null, leverage: "100", retrieved_at: "2026-08-17T12:00:00Z" } });
  quotes.mockResolvedValue({ status: "success", data: { rows: [{ symbol: "EURUSD", bid: 1.1, ask: 1.2 }], generated_at: "2026-08-17T12:00:00Z" } });
  catalogue.mockResolvedValue({ status: "success", data: [
    { lifecycle_status: "APPROVED", manifest: { strategy_id: "alpha", strategy_version: "v2" } },
    { lifecycle_status: "APPROVED", manifest: { strategy_id: "alpha", strategy_version: "v3" } },
    { lifecycle_status: "APPROVED", manifest: { strategy_id: "beta", strategy_version: "1.0.0" } },
  ] });
  preflight.mockResolvedValue({ status: "success", data: { state: "APPROVED", risk_decision_id: "risk-1", action_policy_verdict_id: "verdict-1", approval_token_ref: "token-1", reasons: [], expires_at: "2026-08-17T12:05:00Z" } });
  submit.mockResolvedValue({ status: "success", data: {} });
  useWorkspaceStore.setState({ accountMode: "demo", tradingModeCompatible: true, orderConfirmationRequired: true });
  useTradingStore.setState({ isOrderTicketOpen: true, orderTicketProps: { symbol: "EURUSD", side: "BUY", type: "Market", defaultTab: "futures" } });
});

describe("OrderTicket — FR-UI-063 through FR-UI-072 and FR-UI-226 through FR-UI-232", () => {
  it("shows cTrader-style types, authoritative quotes, strategy, and no manual governance fields", async () => {
    render(<OrderTicket accountId="account-1" />);
    expect(await screen.findByText("1.1")).toBeTruthy();
    expect(screen.getByRole("button", { name: "market order" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "stop-limit order" })).toBeTruthy();
    expect(screen.getByRole("option", { name: "alpha · v2" })).toBeTruthy();
    expect(screen.getByRole("option", { name: "alpha · v3" })).toBeTruthy();
    expect(screen.getByRole("option", { name: "beta · 1.0.0" })).toBeTruthy();
    expect(screen.queryByLabelText("Strategy version")).toBeNull();
    expect(screen.queryByLabelText("Intent ID")).toBeNull();
  });

  it("switches order-type fields and resolves provider symbols", async () => {
    const onSymbolChange = vi.fn();
    render(<OrderTicket accountId="account-1" onSymbolChange={onSymbolChange} />); await screen.findByText("1.1");
    await waitFor(() => expect(onSymbolChange).toHaveBeenCalledWith("EURUSD"));
    expect(screen.queryByLabelText("Limit price")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "stop-limit order" }));
    expect(screen.getByLabelText("Limit price")).toBeTruthy(); expect(screen.getByLabelText("Stop price")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Symbol"), { target: { value: "EURJPY" } });
    await waitFor(() => expect(constraints).toHaveBeenCalledWith("EURJPY"));
    expect(onSymbolChange).toHaveBeenLastCalledWith("EURJPY");
    fireEvent.change(screen.getByLabelText("Symbol"), { target: { value: "EUR" } });
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Choose an exact provider symbol"));
    expect(onSymbolChange).not.toHaveBeenCalledWith("EUR");
  });

  it("predicts provider symbols and selects them with keyboard navigation", async () => {
    const onSymbolChange = vi.fn();
    render(<OrderTicket accountId="account-1" onSymbolChange={onSymbolChange} />);
    await screen.findByText("1.1");
    const input = screen.getByRole("combobox", { name: "Symbol" });
    fireEvent.change(input, { target: { value: "EUR" } });
    const listbox = await screen.findByRole("listbox", { name: "Symbol suggestions" });
    expect(listbox).toBeTruthy();
    expect(screen.getByRole("option", { name: "EURUSD" })).toBeTruthy();
    expect(screen.getByRole("option", { name: "EURJPY" })).toBeTruthy();
    const constraintCalls = constraints.mock.calls.length;
    expect(onSymbolChange).not.toHaveBeenCalledWith("EUR");
    expect(constraints).toHaveBeenCalledTimes(constraintCalls);
    fireEvent.keyDown(input, { key: "ArrowDown" });
    expect(screen.getByRole("option", { name: "EURUSD" })).toHaveAttribute("aria-selected", "true");
    fireEvent.keyDown(input, { key: "ArrowDown" });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(input).toHaveValue("EURJPY");
    expect(screen.queryByRole("listbox", { name: "Symbol suggestions" })).toBeNull();
    await waitFor(() => expect(onSymbolChange).toHaveBeenLastCalledWith("EURJPY"));
  });

  it("supports mouse selection and dismisses suggestions with Escape", async () => {
    render(<OrderTicket accountId="account-1" />);
    await screen.findByText("1.1");
    const input = screen.getByRole("combobox", { name: "Symbol" });
    fireEvent.change(input, { target: { value: "XAU" } });
    fireEvent.mouseDown(await screen.findByRole("option", { name: "XAUUSD" }));
    expect(input).toHaveValue("XAUUSD");
    fireEvent.focus(input);
    expect(await screen.findByRole("listbox", { name: "Symbol suggestions" })).toBeTruthy();
    fireEvent.keyDown(input, { key: "Escape" });
    expect(screen.queryByRole("listbox", { name: "Symbol suggestions" })).toBeNull();
  });

  it("keeps symbol autocomplete available when the strategy catalogue fails", async () => {
    catalogue.mockResolvedValue({ status: "error", error: { message: "Strategy catalogue contract failed" } });
    render(<OrderTicket accountId="account-1" />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Strategy catalogue contract failed");

    const input = screen.getByRole("combobox", { name: "Symbol" });
    fireEvent.change(input, { target: { value: "EUR" } });
    expect(await screen.findByRole("option", { name: "EURUSD" })).toBeTruthy();
    expect(screen.getByText("Place order")).toBeDisabled();
  });

  it("preflights then submits the selected registered strategy exactly once", async () => {
    render(<OrderTicket accountId="account-1" />); await screen.findByText("1.1");
    fireEvent.change(screen.getByLabelText("Strategy"), { target: { value: "alpha@v3" } });
    fireEvent.click(screen.getByText("Buy")); fireEvent.change(screen.getByLabelText("Ticket quantity"), { target: { value: "0.02" } });
    fireEvent.click(screen.getByText("Place order")); fireEvent.click(screen.getByText("Confirm and submit"));
    await waitFor(() => expect(submit).toHaveBeenCalledTimes(1)); expect(preflight).toHaveBeenCalledTimes(1);
    expect(submit.mock.calls[0][0]).toMatchObject({ strategy_id: "alpha", strategy_version: "v3", account_id: "account-1" });
  });

  it("presents contract-aware cTrader market controls and submits enabled protection", async () => {
    render(<OrderTicket accountId="account-1" />);
    await screen.findByText("1.1");
    fireEvent.change(screen.getByLabelText("Strategy"), { target: { value: "alpha@v3" } });
    expect(screen.getByLabelText("Market range value")).toBeDisabled();
    expect(screen.getByLabelText("Comment")).toBeDisabled();
    expect(screen.getByText("Trailing stop").closest("label")?.querySelector("input")).toBeDisabled();
    expect(screen.getByRole("textbox", { name: "Stop loss price" })).toBeDisabled();
    const protectionLabels = Array.from(screen.getByLabelText("Protection controls").querySelectorAll(".order-ticket__protection-label"), (element) => element.textContent);
    expect(protectionLabels).toEqual(["Pips", "Price", "Balance", "Profit"]);
    fireEvent.click(screen.getByText("Buy"));
    fireEvent.change(screen.getByLabelText("Ticket quantity"), { target: { value: "0.02" } });
    fireEvent.click(screen.getByLabelText("Enable stop loss"));
    fireEvent.change(screen.getByRole("textbox", { name: "Stop loss price" }), { target: { value: "1.05" } });
    fireEvent.click(screen.getByText("Place order"));
    fireEvent.click(screen.getByText("Confirm and submit"));
    await waitFor(() => expect(submit).toHaveBeenCalledTimes(1));
    expect(submit.mock.calls[0][0]).toMatchObject({ stop_loss: "1.05", take_profit: null });
  });

  it("gives limit orders the connected protection calculator based on limit price", async () => {
    render(<OrderTicket accountId="account-1" />);
    await screen.findByText("1.1");
    fireEvent.click(screen.getByRole("button", { name: "limit order" }));
    fireEvent.click(screen.getByText("Buy"));
    expect(screen.getByLabelText("Enable stop loss")).toBeDisabled();
    expect(screen.getByLabelText("Stop loss price")).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Limit price"), { target: { value: "1.15" } });
    fireEvent.change(screen.getByLabelText("Ticket quantity"), { target: { value: "0.1" } });
    expect(screen.queryByLabelText("Market range value")).toBeNull();
    fireEvent.click(screen.getByLabelText("Enable stop loss"));
    fireEvent.change(screen.getByLabelText("Stop loss pips"), { target: { value: "10" } });
    expect(screen.getByLabelText("Stop loss price")).toHaveValue("1.149");
    expect(screen.getByLabelText("Stop loss profit")).toHaveValue("-10");
    fireEvent.change(screen.getByLabelText("Limit price"), { target: { value: "1.16" } });
    await waitFor(() => expect(screen.getByLabelText("Stop loss pips")).toHaveValue("110"));
    expect(screen.getByLabelText("Stop loss price")).toHaveValue("1.149");
  });

  it("gives stop orders the connected protection calculator based on stop price", async () => {
    render(<OrderTicket accountId="account-1" />);
    await screen.findByText("1.1");
    fireEvent.click(screen.getByRole("button", { name: "stop order" }));
    fireEvent.click(screen.getByText("Sell"));
    fireEvent.change(screen.getByLabelText("Stop price"), { target: { value: "1.25" } });
    fireEvent.change(screen.getByLabelText("Ticket quantity"), { target: { value: "0.1" } });
    fireEvent.click(screen.getByLabelText("Enable take profit"));
    fireEvent.change(screen.getByLabelText("Take profit pips"), { target: { value: "10" } });
    expect(screen.getByLabelText("Take profit price")).toHaveValue("1.249");
    expect(screen.getByLabelText("Take profit balance")).toHaveValue("10010");
  });

  it("uses the limit fill target rather than the stop trigger for stop-limit protection", async () => {
    render(<OrderTicket accountId="account-1" />);
    await screen.findByText("1.1");
    fireEvent.change(screen.getByLabelText("Strategy"), { target: { value: "alpha@v3" } });
    fireEvent.click(screen.getByRole("button", { name: "stop-limit order" }));
    fireEvent.click(screen.getByText("Buy"));
    fireEvent.change(screen.getByLabelText("Stop price"), { target: { value: "1.3" } });
    fireEvent.change(screen.getByLabelText("Limit price"), { target: { value: "1.25" } });
    fireEvent.change(screen.getByLabelText("Ticket quantity"), { target: { value: "0.1" } });
    fireEvent.click(screen.getByLabelText("Enable take profit"));
    fireEvent.change(screen.getByLabelText("Take profit profit"), { target: { value: "10" } });
    expect(screen.getByLabelText("Take profit price")).toHaveValue("1.251");
    expect(screen.getByLabelText("Take profit pips")).toHaveValue("10");
    fireEvent.click(screen.getByText("Place order"));
    fireEvent.click(screen.getByText("Confirm and submit"));
    await waitFor(() => expect(submit).toHaveBeenCalledTimes(1));
    expect(submit.mock.calls[0][0]).toMatchObject({ price: "1.25", stop_price: "1.3", take_profit: "1.251" });
  });

  it("keeps every protection column field bidirectionally connected", async () => {
    render(<OrderTicket accountId="account-1" />);
    await screen.findByText("1.1");
    fireEvent.click(screen.getByText("Buy"));
    fireEvent.change(screen.getByLabelText("Ticket quantity"), { target: { value: "0.1" } });
    fireEvent.click(screen.getByLabelText("Enable stop loss"));
    fireEvent.click(screen.getByLabelText("Enable take profit"));

    fireEvent.change(screen.getByLabelText("Stop loss pips"), { target: { value: "10" } });
    expect(screen.getByLabelText("Stop loss price")).toHaveValue("1.199");
    expect(screen.getByLabelText("Stop loss balance")).toHaveValue("9990");
    expect(screen.getByLabelText("Stop loss profit")).toHaveValue("-10");
    fireEvent.change(screen.getByLabelText("Stop loss price"), { target: { value: "1.198" } });
    expect(screen.getByLabelText("Stop loss pips")).toHaveValue("20");
    fireEvent.change(screen.getByLabelText("Stop loss balance"), { target: { value: "9995" } });
    expect(screen.getByLabelText("Stop loss profit")).toHaveValue("-5");
    fireEvent.change(screen.getByLabelText("Stop loss profit"), { target: { value: "-15" } });
    expect(screen.getByLabelText("Stop loss price")).toHaveValue("1.1985");

    fireEvent.change(screen.getByLabelText("Take profit pips"), { target: { value: "10" } });
    expect(screen.getByLabelText("Take profit price")).toHaveValue("1.201");
    expect(screen.getByLabelText("Take profit balance")).toHaveValue("10010");
    expect(screen.getByLabelText("Take profit profit")).toHaveValue("10");
    fireEvent.change(screen.getByLabelText("Take profit price"), { target: { value: "1.202" } });
    expect(screen.getByLabelText("Take profit pips")).toHaveValue("20");
    fireEvent.change(screen.getByLabelText("Take profit balance"), { target: { value: "10005" } });
    expect(screen.getByLabelText("Take profit profit")).toHaveValue("5");
    fireEvent.change(screen.getByLabelText("Take profit profit"), { target: { value: "15" } });
    expect(screen.getByLabelText("Take profit price")).toHaveValue("1.2015");

    fireEvent.click(screen.getByLabelText("Enable take profit"));
    for (const name of ["Take profit pips", "Take profit price", "Take profit balance", "Take profit profit"]) expect(screen.getByLabelText(name)).toBeDisabled();
  });

  it("fails closed when calculator evidence is incomplete", async () => {
    const completeConstraints = await constraints();
    constraints.mockResolvedValueOnce({ status: "success", data: { ...completeConstraints.data, pip_size: null } });
    render(<OrderTicket accountId="account-1" />);
    expect(await screen.findByText(/Protection calculator unavailable/)).toBeTruthy();
    expect(screen.getByLabelText("Enable stop loss")).toBeDisabled();
    expect(screen.getByLabelText("Enable take profit")).toBeDisabled();
  });

  it("fails closed when the strategy catalogue is empty", async () => {
    catalogue.mockResolvedValue({ status: "success", data: [] }); render(<OrderTicket accountId="account-1" />);
    await screen.findByText("1.1"); expect(screen.getByRole("status")).toHaveTextContent("Choose a registered strategy"); expect(screen.getByText("Place order")).toBeDisabled();
  });
});
