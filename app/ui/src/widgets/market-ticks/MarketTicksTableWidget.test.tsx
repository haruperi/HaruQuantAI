import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MarketTicksTableWidget } from "./MarketTicksTableWidget";
import type { MarketSnapshotView } from "./useMarketSnapshots";

const SNAPSHOT: MarketSnapshotView = {
  sequence: 42,
  sourceId: "data.stream-market-events@1",
  gap: 2,
  stale: false,
  quotes: [
    {
      symbol: "EURUSD",
      timestamp: new Date().toISOString(),
      bid: "1.12345",
      ask: "1.12355",
    },
  ],
};

describe("MarketTicksTableWidget — FR-UI-186 through FR-UI-191", () => {
  it("presents the explicit connecting and empty states", () => {
    render(
      <MarketTicksTableWidget
        snapshot={null}
        status="connecting"
        error={null}
        staleRowAfterSeconds={5}
      />,
    );

    expect(screen.getByText("connecting")).toBeInTheDocument();
    expect(screen.getByText(/No MT5 snapshots received yet/)).toBeInTheDocument();
  });

  it("renders the served wire values exactly, with derived spread", () => {
    render(
      <MarketTicksTableWidget
        snapshot={SNAPSHOT}
        status="connected"
        error={null}
        staleRowAfterSeconds={5}
      />,
    );

    expect(screen.getAllByText("data.stream-market-events@1").length).toBe(2);
    expect(screen.getByText("sequence 42 · gaps 2")).toBeInTheDocument();
    expect(screen.getByText("EURUSD")).toBeInTheDocument();
    // Wire decimal strings render exactly as served — never reformatted.
    expect(screen.getByText("1.12345")).toBeInTheDocument();
    expect(screen.getByText("1.12355")).toBeInTheDocument();
    // Spread is derived arithmetically from the served pair.
    expect(screen.getByText("0.00010")).toBeInTheDocument();
    expect(screen.getAllByText("live").length).toBeGreaterThan(0);
  });

  it("marks rows stale beyond the configured threshold", () => {
    render(
      <MarketTicksTableWidget
        snapshot={{
          ...SNAPSHOT,
          quotes: [
            {
              symbol: "EURUSD",
              timestamp: new Date(Date.now() - 10_000).toISOString(),
              bid: "1.12345",
              ask: "1.12355",
            },
          ],
        }}
        status="connected"
        error={null}
        staleRowAfterSeconds={5}
      />,
    );

    expect(screen.getByText("stale")).toBeInTheDocument();
  });

  it("presents configuration or transport failure without inventing rows", () => {
    render(
      <MarketTicksTableWidget
        snapshot={null}
        status="unavailable"
        error="MT5 snapshot symbols are not configured."
        staleRowAfterSeconds={5}
      />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent("not configured");
    expect(screen.getByText("unavailable")).toBeInTheDocument();
    expect(screen.queryByText("EURUSD")).not.toBeInTheDocument();
  });

  it("marks the whole source card stale from the served stale flag", () => {
    render(
      <MarketTicksTableWidget
        snapshot={{ ...SNAPSHOT, stale: true }}
        status="connected"
        error={null}
        staleRowAfterSeconds={5}
      />,
    );

    expect(screen.getAllByText("stale").length).toBeGreaterThan(0);
  });
});
