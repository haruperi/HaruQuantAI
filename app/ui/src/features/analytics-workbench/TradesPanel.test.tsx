/**
 * Analytics trade analysis tests (FEAT-UI-32, P3-T02).
 *
 * Covers server-side pagination and filtering, the trade detail evidence, the
 * exact encoded replay return context, and the artifact drawer.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { getTrades, getTrade, getArtifacts, getReplayAnchors } = vi.hoisted(() => ({
  getTrades: vi.fn(),
  getTrade: vi.fn(),
  getArtifacts: vi.fn(),
  getReplayAnchors: vi.fn(),
}));

vi.mock("@/clients", () => ({
  ApiClientError: class extends Error {},
  apiClients: {
    analyticsWorkbench: { getTrades, getTrade, getArtifacts, getReplayAnchors },
  },
}));

import { TradesPanel, TRADES_PAGE_SIZE } from "./TradesPanel";
import { TradeDetailPanel, buildReplayHref } from "./TradeDetailPanel";
import { AnalyticsArtifactDrawer } from "./AnalyticsArtifactDrawer";

const TRADE = {
  ticket: "1001",
  symbol: "EURUSD",
  side: "buy",
  volume: "0.10",
  entry_time: "2025-03-04T08:00:00Z",
  entry_price: "1.08500",
  exit_time: "2025-03-04T14:00:00Z",
  exit_price: "1.08750",
  pnl: "25.00",
  commission: "0.70",
  swap: "0.00",
  reason: "take_profit",
  mae: "-4.20",
  mfe: "31.10",
  bars_held: 6,
  duration_seconds: 21600,
};

const PAGE = {
  run_id: "canonical-1",
  page: 1,
  page_size: TRADES_PAGE_SIZE,
  total_trades: 120,
  total_pages: 3,
  trades: [TRADE],
};

describe("TradesPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getTrades.mockResolvedValue({ status: "success", data: PAGE });
  });

  it("requests the first page with the server defaults", async () => {
    render(<TradesPanel runId="canonical-1" />);
    await screen.findByText("1001");
    expect(getTrades).toHaveBeenCalledWith("canonical-1", {
      page: 1,
      page_size: TRADES_PAGE_SIZE,
      sort: "exit_time_desc",
      side: "all",
    });
  });

  it("delegates filtering to the server and resets to page one", async () => {
    render(<TradesPanel runId="canonical-1" />);
    await screen.findByText("1001");

    fireEvent.click(screen.getByRole("button", { name: /next page/i }));
    await waitFor(() =>
      expect(getTrades).toHaveBeenLastCalledWith(
        "canonical-1",
        expect.objectContaining({ page: 2 }),
      ),
    );

    fireEvent.change(screen.getByLabelText("Direction"), {
      target: { value: "sell" },
    });
    await waitFor(() =>
      expect(getTrades).toHaveBeenLastCalledWith(
        "canonical-1",
        expect.objectContaining({ page: 1, side: "sell" }),
      ),
    );
  });

  it("renders the server page counters rather than deriving them", async () => {
    render(<TradesPanel runId="canonical-1" />);
    expect(
      await screen.findByText("120 closed trades · page 1 of 3"),
    ).toBeInTheDocument();
  });

  it("surfaces a ledger read failure", async () => {
    getTrades.mockResolvedValue({
      status: "error",
      error: { message: "trade ledger unavailable" },
    });
    render(<TradesPanel runId="canonical-1" />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "trade ledger unavailable",
    );
  });
});

describe("TradeDetailPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getTrade.mockResolvedValue({ status: "success", data: TRADE });
  });

  it("renders complete owner trade evidence", async () => {
    render(<TradeDetailPanel runId="canonical-1" ticket="1001" />);
    expect(await screen.findByText("take_profit")).toBeInTheDocument();
    expect(screen.getByText("-4.20")).toBeInTheDocument();
    expect(screen.getByText("31.10")).toBeInTheDocument();
    expect(screen.getByText("0.70")).toBeInTheDocument();
  });

  it("marks an evidence field the owner omitted as unavailable", async () => {
    getTrade.mockResolvedValue({
      status: "success",
      data: { ...TRADE, mae: null, mfe: null },
    });
    render(<TradeDetailPanel runId="canonical-1" ticket="1001" />);
    await screen.findByText("take_profit");
    expect(screen.getAllByText("Unavailable").length).toBeGreaterThan(0);
  });

  it("carries the exact encoded return context on the replay link", async () => {
    render(<TradeDetailPanel runId="run/1" ticket="10 01" />);
    const link = await screen.findByRole("link", { name: /replay this trade/i });
    expect(link).toHaveAttribute("href", buildReplayHref("run/1", "10 01"));
    expect(link.getAttribute("href")).toBe(
      "/workstation/simulator/replay/run%2F1?ticket=10%2001&return=" +
        encodeURIComponent("/workstation/analytics/run%2F1/trades/10%2001"),
    );
  });
});

describe("AnalyticsArtifactDrawer", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getArtifacts.mockResolvedValue({
      status: "success",
      data: {
        run_id: "canonical-1",
        artifacts: [
          { kind: "analytics-report", ref: "artifacts/analytics-report.json" },
          { kind: "journal", ref: "artifacts/journal.ndjson" },
        ],
      },
    });
    getReplayAnchors.mockResolvedValue({
      status: "success",
      data: {
        run_id: "canonical-1",
        anchors: [{ ticket: "1001", exit_time: "2025-03-04T14:00:00Z" }],
      },
    });
  });

  it("lists immutable artifact references without a delete action", async () => {
    render(<AnalyticsArtifactDrawer runId="canonical-1" />);
    expect(
      await screen.findByText("artifacts/analytics-report.json"),
    ).toBeInTheDocument();
    expect(screen.getByText("artifacts/journal.ndjson")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /delete/i })).toBeNull();
  });

  it("links each replay anchor to immutable playback", async () => {
    render(<AnalyticsArtifactDrawer runId="canonical-1" />);
    const link = await screen.findByRole("link", { name: /ticket 1001/i });
    expect(link).toHaveAttribute("href", buildReplayHref("canonical-1", "1001"));
  });
});
