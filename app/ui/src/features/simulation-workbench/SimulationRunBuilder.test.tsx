/**
 * Staged run builder tests (FEAT-UI-31, P2-T01).
 *
 * Covers mode selection, generated strategy parameters, blocking validation,
 * exact request defaults, and single-identity idempotency on submission.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { strategies, startRun, createBatch } = vi.hoisted(() => ({
  strategies: vi.fn(),
  startRun: vi.fn(),
  createBatch: vi.fn(),
}));

vi.mock("@/clients", () => ({
  ApiClientError: class extends Error {},
  apiClients: {
    simulator: { strategies, startRun },
    simulationWorkbench: { createBatch },
  },
}));

import { SimulationRunBuilder } from "./SimulationRunBuilder";

const CATALOGUE = {
  strategies: [
    {
      strategy_id: "trend",
      strategy_version: "1.2.0",
      evaluator_name: "TrendEvaluator",
      label: "Trend Following",
      runnable: true,
      unavailable_reason: null,
      required_indicators: ["ema"],
      supports_exits: true,
      parameters: [
        {
          name: "fast_period",
          label: "Fast period",
          kind: "integer" as const,
          default: "12",
          minimum: "2",
          maximum: "200",
        },
      ],
    },
    {
      strategy_id: "grid",
      strategy_version: "0.4.0",
      evaluator_name: "GridEvaluator",
      label: "Grid",
      runnable: false,
      unavailable_reason: "Grid execution is not certified for canonical runs.",
      required_indicators: [],
      supports_exits: false,
      parameters: [],
    },
  ],
};

/** Move the builder to one named stage. */
function goToStage(label: RegExp): void {
  fireEvent.click(screen.getByRole("button", { name: label }));
}

describe("SimulationRunBuilder", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    strategies.mockResolvedValue({ status: "success", data: CATALOGUE });
    startRun.mockResolvedValue({
      status: "success",
      data: { job_id: "job-77" },
    });
    createBatch.mockResolvedValue({
      status: "success",
      data: { batch_id: "batch-77" },
    });
  });

  it("renders every ordered builder stage", async () => {
    render(<SimulationRunBuilder />);
    await screen.findByRole("button", { name: /1\. Mode/ });
    for (const label of [
      /1\. Mode/,
      /2\. Strategy/,
      /3\. Market/,
      /4\. Execution and costs/,
      /5\. Risk and governance/,
      /6\. Scenario and mission/,
      /7\. Metadata/,
      /8\. Review/,
    ]) {
      expect(screen.getByRole("button", { name: label })).toBeInTheDocument();
    }
  });

  it("offers every run mode and blocks modes with no destination", async () => {
    render(<SimulationRunBuilder />);
    await screen.findByLabelText("Canonical Backtest");
    expect(screen.getByLabelText("Visual Practice")).toBeInTheDocument();
    expect(screen.getByLabelText("Manual Practice")).toBeInTheDocument();
    expect(screen.getByLabelText("Batch")).toBeInTheDocument();
    expect(screen.getByLabelText("Replay")).toBeInTheDocument();
    expect(screen.getByLabelText("Scenario/Mission")).toBeInTheDocument();
    expect(screen.getByLabelText("Portfolio Simulation")).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("Replay"));
    goToStage(/8\. Review/);
    expect(
      screen.getByText(
        "This mode has no submission destination in the current workbench build.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Submit run/ })).toBeDisabled();
  });

  it("generates the strategy parameter form from the catalogue", async () => {
    render(<SimulationRunBuilder />);
    goToStage(/2\. Strategy/);
    const input = await screen.findByLabelText("Fast period");
    expect(input).toHaveValue("12");
  });

  it("blocks submission when the measurement window is inverted", async () => {
    render(<SimulationRunBuilder />);
    await screen.findByLabelText("Canonical Backtest");
    goToStage(/3\. Market/);
    fireEvent.change(screen.getByLabelText("Start"), {
      target: { value: "2025-12-31" },
    });
    fireEvent.change(screen.getByLabelText("End"), {
      target: { value: "2025-01-01" },
    });
    goToStage(/8\. Review/);
    expect(
      screen.getByText("The start date must not be after the end date."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Submit run/ })).toBeDisabled();
    expect(startRun).not.toHaveBeenCalled();
  });

  it("blocks submission for a strategy the recipe cannot run", async () => {
    render(<SimulationRunBuilder />);
    goToStage(/2\. Strategy/);
    const select = await screen.findByLabelText("Strategy");
    fireEvent.change(select, { target: { value: "grid" } });
    goToStage(/8\. Review/);
    expect(
      screen.getByText(
        "Grid execution is not certified for canonical runs.",
        { selector: "li" },
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Submit run/ })).toBeDisabled();
  });

  it("submits exact canonical defaults under one idempotency key", async () => {
    const onSubmitted = vi.fn();
    render(<SimulationRunBuilder onSubmitted={onSubmitted} />);
    await screen.findByLabelText("Canonical Backtest");
    goToStage(/8\. Review/);
    fireEvent.click(screen.getByRole("button", { name: /Submit run/ }));

    await waitFor(() => expect(startRun).toHaveBeenCalledTimes(1));
    const [body, options] = startRun.mock.calls[0];
    expect(body).toMatchObject({
      symbol: "EURUSD",
      timeframe: "H1",
      strategy_id: "trend",
      parameters: { fast_period: "12" },
      initial_balance: "10000.00",
      account_currency: "USD",
      volume: "0.1",
      commission_per_lot_per_side: "7",
      spread_points: "10",
      slippage_points: "1",
    });
    expect(body).not.toHaveProperty("config_hash");
    expect(body).not.toHaveProperty("request_hash");
    expect(body).not.toHaveProperty("data_hash");
    expect(typeof options.idempotencyKey).toBe("string");
    expect(options.idempotencyKey.length).toBeGreaterThan(0);
    expect(onSubmitted).toHaveBeenCalledWith({ kind: "run", runId: "job-77" });
  });

  it("reuses the same idempotency key when a submission fails", async () => {
    startRun.mockResolvedValueOnce({
      status: "error",
      error: { message: "gateway unavailable" },
    });
    render(<SimulationRunBuilder />);
    await screen.findByLabelText("Canonical Backtest");
    goToStage(/8\. Review/);

    fireEvent.click(screen.getByRole("button", { name: /Submit run/ }));
    await screen.findByText("gateway unavailable");
    fireEvent.click(screen.getByRole("button", { name: /Submit run/ }));
    await waitFor(() => expect(startRun).toHaveBeenCalledTimes(2));

    expect(startRun.mock.calls[0][1].idempotencyKey).toBe(
      startRun.mock.calls[1][1].idempotencyKey,
    );
  });

  it("issues a fresh idempotency key after a successful submission", async () => {
    render(<SimulationRunBuilder />);
    await screen.findByLabelText("Canonical Backtest");
    goToStage(/8\. Review/);

    fireEvent.click(screen.getByRole("button", { name: /Submit run/ }));
    await waitFor(() => expect(startRun).toHaveBeenCalledTimes(1));
    fireEvent.click(screen.getByRole("button", { name: /Submit run/ }));
    await waitFor(() => expect(startRun).toHaveBeenCalledTimes(2));

    expect(startRun.mock.calls[0][1].idempotencyKey).not.toBe(
      startRun.mock.calls[1][1].idempotencyKey,
    );
  });

  it("submits batch mode as bounded independent items", async () => {
    const onSubmitted = vi.fn();
    render(<SimulationRunBuilder initialMode="batch" onSubmitted={onSubmitted} />);
    await screen.findByLabelText("Batch");
    goToStage(/3\. Market/);
    fireEvent.change(screen.getByLabelText("Batch universe"), {
      target: { value: "EURUSD, GBPUSD" },
    });
    fireEvent.change(screen.getByLabelText("Concurrency"), {
      target: { value: "2" },
    });
    goToStage(/8\. Review/);
    fireEvent.click(screen.getByRole("button", { name: /Submit run/ }));

    await waitFor(() => expect(createBatch).toHaveBeenCalledTimes(1));
    const [body] = createBatch.mock.calls[0];
    expect(body.items).toHaveLength(2);
    expect(body.items[0].symbol).toBe("EURUSD");
    expect(body.items[1].symbol).toBe("GBPUSD");
    expect(body.concurrency).toBe(2);
    expect(onSubmitted).toHaveBeenCalledWith({
      kind: "batch",
      batchId: "batch-77",
    });
  });

  it("rejects a batch concurrency above the frozen bound", async () => {
    render(<SimulationRunBuilder initialMode="batch" />);
    await screen.findByLabelText("Batch");
    goToStage(/3\. Market/);
    fireEvent.change(screen.getByLabelText("Concurrency"), {
      target: { value: "9" },
    });
    goToStage(/8\. Review/);
    expect(
      screen.getByText("Concurrency must be between 1 and 8."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Submit run/ })).toBeDisabled();
  });
});
