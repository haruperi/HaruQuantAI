import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MarketTicksTableWidget } from "./MarketTicksTableWidget";

const { snapshotHookMock } = vi.hoisted(() => ({ snapshotHookMock: vi.fn() }));

vi.mock("./useMarketSnapshots", () => ({
  useMarketSnapshots: snapshotHookMock,
}));

describe("MarketTicksTableWidget — FR-UI-186 through FR-UI-191", () => {
  beforeEach(() => {
    snapshotHookMock.mockReturnValue({
      snapshot: null,
      status: "connecting",
      error: null,
    });
  });

  it("presents the explicit connecting and empty states", () => {
    render(<MarketTicksTableWidget />);

    expect(screen.getByText("connecting")).toBeInTheDocument();
    expect(screen.getByText(/No MT5 snapshots received yet/)).toBeInTheDocument();
  });

  it("renders the playground-equivalent quote and source evidence", () => {
    snapshotHookMock.mockReturnValue({
      status: "connected",
      error: null,
      snapshot: {
        sequence: 42,
        sourceId: "pepperstone-demo",
        gap: 2,
        stale: false,
        quotes: [{
          symbol: "EURUSD",
          bid: "1.12345",
          ask: "1.12355",
          last: null,
          spread: "0.00010",
          digits: 5,
          time: new Date().toISOString(),
        }],
      },
    });

    render(<MarketTicksTableWidget />);

    expect(screen.getAllByText("pepperstone-demo")).toHaveLength(2);
    expect(screen.getByText("sequence 42 · gaps 2")).toBeInTheDocument();
    expect(screen.getByText("EURUSD")).toBeInTheDocument();
    expect(screen.getByText("1.12345")).toBeInTheDocument();
    expect(screen.getByText("1.12355")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
  });

  it("presents configuration or transport failure without inventing rows", () => {
    snapshotHookMock.mockReturnValue({
      snapshot: null,
      status: "unavailable",
      error: "MT5 snapshot symbols are not configured.",
    });

    render(<MarketTicksTableWidget />);

    expect(screen.getByRole("alert")).toHaveTextContent("not configured");
    expect(screen.getByText("unavailable")).toBeInTheDocument();
    expect(screen.queryByText("EURUSD")).not.toBeInTheDocument();
  });
});
