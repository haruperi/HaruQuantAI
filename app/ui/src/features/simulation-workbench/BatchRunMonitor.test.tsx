/**
 * Unit tests for batch monitor behavior (FEAT-UI-31, P2-T02).
 *
 * Covers partial failure presentation, cancellation, retry-failed, the compare
 * handoff for successful runs only, and the rule that batch membership never
 * implies an aggregate portfolio result.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { getBatch, cancelBatch, retryFailedBatch } = vi.hoisted(() => ({
  getBatch: vi.fn(),
  cancelBatch: vi.fn(),
  retryFailedBatch: vi.fn(),
}));

vi.mock("@/clients", () => ({
  ApiClientError: class extends Error {},
  apiClients: {
    simulationWorkbench: {
      getBatch,
      cancelBatch,
      retryFailedBatch,
    },
  },
}));

vi.mock("@/context/streams", () => ({
  consumeStream: () => ({
    async *[Symbol.asyncIterator]() {
      // Intentionally empty stream; reconciliation should still update by read.
    },
  }),
}));
vi.mock("@/clients/routes", () => ({
  simulationWorkbenchRoutes: {
    batchStream: { id: "api.simulation.batch_stream" },
  },
}));

import { BatchRunMonitor } from "./BatchRunMonitor";

/** Batch with one running, one completed, and one failed item. */
const PROJECTION = {
  batch_id: "batch-abc",
  principal_id: "user-1",
  status: "running",
  concurrency: 2,
  total_items: 3,
  completed_items: 1,
  failed_items: 1,
  cancelled_items: 0,
  created_at: "2026-08-18T12:00:00Z",
  completed_at: null,
  items: [
    {
      item_id: "item-1",
      batch_id: "batch-abc",
      job_id: "job-1",
      symbol: "EURUSD",
      timeframe: "H1",
      strategy_id: "trend",
      parameters: {},
      status: "running",
      run_id: null,
      error: null,
    },
    {
      item_id: "item-2",
      batch_id: "batch-abc",
      job_id: "job-2",
      symbol: "GBPUSD",
      timeframe: "H1",
      strategy_id: "trend",
      parameters: {},
      status: "completed",
      run_id: "canonical-2",
      error: null,
    },
    {
      item_id: "item-3",
      batch_id: "batch-abc",
      job_id: "job-3",
      symbol: "USDJPY",
      timeframe: "H1",
      strategy_id: "trend",
      parameters: {},
      status: "failed",
      run_id: null,
      error: "market data gap",
    },
  ],
};

/** Same batch after both remaining runs completed. */
const TWO_COMPLETED = {
  ...PROJECTION,
  status: "completed",
  completed_items: 2,
  failed_items: 1,
  items: [
    { ...PROJECTION.items[0], status: "completed", run_id: "canonical-1" },
    PROJECTION.items[1],
    PROJECTION.items[2],
  ],
};

describe("BatchRunMonitor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getBatch.mockResolvedValue({ status: "success", data: PROJECTION });
    cancelBatch.mockResolvedValue({ status: "success", data: PROJECTION });
    retryFailedBatch.mockResolvedValue({ status: "success", data: PROJECTION });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders batch status and dispatches cancel", async () => {
    render(<BatchRunMonitor batchId="batch-abc" />);
    expect(await screen.findByText(/status:/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /cancel remaining/i })).toBeEnabled();

    fireEvent.click(screen.getByRole("button", { name: /cancel remaining/i }));
    await waitFor(() => expect(cancelBatch).toHaveBeenCalledWith("batch-abc"));
  });

  it("dispatches retry when failed items exist", async () => {
    render(<BatchRunMonitor batchId="batch-abc" />);
    await screen.findByText(/completed:/i);
    fireEvent.click(screen.getByRole("button", { name: /retry failed/i }));
    await waitFor(() => expect(retryFailedBatch).toHaveBeenCalledWith("batch-abc"));
  });

  it("shows per-item partial failure without failing the whole batch", async () => {
    render(<BatchRunMonitor batchId="batch-abc" />);
    await screen.findByText(/completed:/i);

    expect(screen.getByText("market data gap")).toBeInTheDocument();
    expect(screen.getByText(/Failed: 1/)).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /open analytics/i }),
    ).toHaveAttribute("href", "/workstation/analytics/canonical-2/overview");
  });

  it("keeps retry disabled when no item failed", async () => {
    getBatch.mockResolvedValue({
      status: "success",
      data: { ...PROJECTION, failed_items: 0 },
    });
    render(<BatchRunMonitor batchId="batch-abc" />);
    await screen.findByText(/completed:/i);
    expect(screen.getByRole("button", { name: /retry failed/i })).toBeDisabled();
  });

  it("offers comparison only once two runs succeeded", async () => {
    render(<BatchRunMonitor batchId="batch-abc" />);
    await screen.findByText(/completed:/i);
    expect(
      screen.getByText(/Compare successful runs needs at least two completed runs\./),
    ).toBeInTheDocument();
  });

  it("compares successful runs by identity and infers no portfolio", async () => {
    getBatch.mockResolvedValue({ status: "success", data: TWO_COMPLETED });
    render(<BatchRunMonitor batchId="batch-abc" />);
    await screen.findByText(/completed:/i);

    const compare = await screen.findByRole("link", {
      name: /compare successful runs/i,
    });
    expect(compare).toHaveAttribute(
      "href",
      "/workstation/analytics/compare?runs=canonical-1,canonical-2",
    );
    expect(screen.queryByText(/portfolio/i)).toBeNull();
  });
});
