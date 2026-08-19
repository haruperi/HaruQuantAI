/** Unit tests for SimulatorWidget (FR-UI-234..FR-UI-240). */
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const { strategies, startRun, runRead, cancelRun, openStream } = vi.hoisted(() => ({
  strategies: vi.fn(),
  startRun: vi.fn(),
  runRead: vi.fn(),
  cancelRun: vi.fn(),
  openStream: vi.fn(),
}));

vi.mock("@/clients", () => ({
  ApiClientError: class extends Error {},
  apiClients: {
    simulator: { strategies, startRun, run: runRead, cancelRun },
  },
  openStream,
}));
vi.mock("@/clients/routes", () => ({ simulatorRoutes: { runStream: { id: "stream" } } }));

import { SimulatorWidget } from "./SimulatorWidget";

const runnable = {
  strategy_id: "naive-ma-trend",
  strategy_version: "1.0.0",
  evaluator_name: "naive_ma_trend_incremental",
  label: "Naive MA Trend (incremental)",
  runnable: true,
  unavailable_reason: null,
  required_indicators: [],
  supports_exits: true,
  parameters: [
    {
      name: "fast_ma_period",
      label: "Fast MA period",
      kind: "integer" as const,
      default: "20",
      minimum: "2",
      maximum: null,
    },
  ],
};

const blocked = {
  ...runnable,
  strategy_id: "white-fairy",
  label: "White Fairy (RSI reversal)",
  runnable: false,
  unavailable_reason: "This evaluator consumes Indicators-owned series.",
  required_indicators: ["rsi"],
  supports_exits: false,
  parameters: [],
};

const run = (overrides: Record<string, unknown> = {}) => ({
  job_id: "btr-1",
  status: "queued",
  stage: null,
  submitted_at: "2026-08-17T00:00:00Z",
  started_at: null,
  finished_at: null,
  symbol: "EURUSD",
  timeframe: "H1",
  strategy_id: "naive-ma-trend",
  events: [],
  result: null,
  error: null,
  ...overrides,
});

/** Build an async iterable yielding the given stream events. */
function stream(events: unknown[]): AsyncIterable<unknown> {
  return {
    async *[Symbol.asyncIterator]() {
      for (const event of events) yield event;
    },
  };
}

describe("SimulatorWidget", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    strategies.mockResolvedValue({
      status: "success",
      data: { strategies: [runnable, blocked] },
    });
    startRun.mockResolvedValue({ status: "success", data: run() });
    runRead.mockResolvedValue({ status: "success", data: run() });
    openStream.mockReturnValue(stream([]));
  });

  it("selects the first runnable strategy and shows its declared parameters", async () => {
    render(<SimulatorWidget />);
    expect(await screen.findByLabelText("Fast MA period")).toHaveValue(20);
    const picker = screen.getByLabelText("Strategy") as HTMLSelectElement;
    expect(picker.value).toBe("naive-ma-trend");
  });

  it("keeps a blocked strategy listed, disabled, and explained", async () => {
    render(<SimulatorWidget />);
    await screen.findByLabelText("Fast MA period");
    const option = screen.getByRole("option", {
      name: /White Fairy .* unavailable/,
    }) as HTMLOptionElement;
    expect(option.disabled).toBe(true);
    // The option cannot be selected, so its reason must be reachable elsewhere.
    expect(screen.getByText("1 strategy unavailable")).toBeTruthy();
    expect(
      screen.getByText("This evaluator consumes Indicators-owned series.")
    ).toBeTruthy();
  });

  it("submits the operator's configuration to the backend once", async () => {
    render(<SimulatorWidget />);
    await screen.findByLabelText("Fast MA period");
    fireEvent.change(screen.getByLabelText("Symbol"), {
      target: { value: "gbpusd" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Run backtest/ }));
    await waitFor(() => expect(startRun).toHaveBeenCalledTimes(1));
    const payload = startRun.mock.calls[0][0];
    expect(payload.symbol).toBe("GBPUSD");
    expect(payload.strategy_id).toBe("naive-ma-trend");
    expect(payload.parameters).toEqual({ fast_ma_period: "20" });
    expect(payload.volume).toBe("0.1");
  });

  it("renders a rejected run without inventing a result", async () => {
    startRun.mockResolvedValue({
      status: "error",
      error: { message: "insufficient EURUSD H1 history" },
    });
    render(<SimulatorWidget />);
    await screen.findByLabelText("Fast MA period");
    fireEvent.click(screen.getByRole("button", { name: /Run backtest/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "insufficient EURUSD H1 history"
    );
  });

  it("renders only calculated metrics and marks the rest unavailable", async () => {
    openStream.mockReturnValue(
      stream([
        {
          event_type: "payload",
          payload: run({
            status: "succeeded",
            result: {
              run_id: "sim-9",
              engine_version: "1",
              config_hash: "abc",
              strategy_id: "naive-ma-trend",
              strategy_version: "1.0.0",
              strategy_label: "Naive MA Trend (incremental)",
              parameters: { fast_ma_period: "20" },
              symbol: "EURUSD",
              timeframe: "H1",
              start: "2025-01-01T00:00:00Z",
              end: "2025-12-31T23:59:59Z",
              initial_balance: "10000.00",
              account_currency: "USD",
              bar_count: 6200,
              warmup_bars: 201,
              closed_trade_count: 42,
              metrics: { net_pnl: "1234.56", sharpe_ratio: "0.87" },
              quality: {},
              quality_flags: [],
              caveats: [],
            },
          }),
        },
      ])
    );
    const onOpen = vi.fn();
    render(<SimulatorWidget onOpenAnalytics={onOpen} />);
    await screen.findByLabelText("Fast MA period");
    fireEvent.click(screen.getByRole("button", { name: /Run backtest/ }));
    expect(await screen.findByText("Performance report")).toBeTruthy();
    expect(screen.getByRole("row", { name: /Net PnL/ })).toHaveTextContent("1234.56");
    expect(screen.getByRole("row", { name: /Sharpe Ratio/ })).toHaveTextContent("0.87");
    // CAGR was not calculated and must not render as a number.
    expect(screen.getByRole("row", { name: /CAGR/ })).toHaveTextContent("—");
    expect(screen.getByText("42")).toBeTruthy();
    const btn = screen.getByRole("button", { name: /inspect in analytics workspace/i });
    expect(btn).toBeInTheDocument();
    fireEvent.click(btn);
    expect(onOpen).toHaveBeenCalledWith("sim-9");
  });

  it("surfaces a failed run's reason", async () => {
    openStream.mockReturnValue(
      stream([
        {
          event_type: "payload",
          payload: run({ status: "failed", error: "provider connection failed" }),
        },
      ])
    );
    render(<SimulatorWidget />);
    await screen.findByLabelText("Fast MA period");
    fireEvent.click(screen.getByRole("button", { name: /Run backtest/ }));
    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(
        "provider connection failed"
      )
    );
  });

  it("settles from the authoritative read when the stream ends early", async () => {
    // The progress stream ending is not proof the run stopped: a proxy timeout
    // or dropped connection once left the widget claiming RUNNING forever while
    // the backend had already succeeded.
    openStream.mockReturnValue(stream([]));
    runRead.mockResolvedValue({
      status: "success",
      data: run({ status: "succeeded", result: null, error: null }),
    });
    render(<SimulatorWidget />);
    await screen.findByLabelText("Fast MA period");
    fireEvent.click(screen.getByRole("button", { name: /Run backtest/ }));
    await waitFor(() => expect(runRead).toHaveBeenCalled());
    await waitFor(() =>
      expect(screen.getByText("SUCCEEDED")).toBeTruthy()
    );
  });

  it("reports an unavailable strategy catalogue", async () => {
    strategies.mockRejectedValue(new Error("gateway offline"));
    render(<SimulatorWidget />);
    expect(await screen.findByRole("alert")).toHaveTextContent("gateway offline");
  });
});
