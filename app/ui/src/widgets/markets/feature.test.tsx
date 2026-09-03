/**
 * FEAT-UI-02 feature adapter lifecycle tests (D-UI §4.8).
 */
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiClientError } from "../../clients";
import { WidgetContentHost } from "../../components/layout/WidgetContentHost";
import type { Widget } from "../workspaces";

import { MarketsFeature } from "./feature";

const {
  marketsMock,
  quotesMock,
  snapshotStreamMock,
  listMock,
  openOrderTicketMock,
  submitOrderMock,
  addWidgetToWorkspaceMock,
  setWidgetSymbolMock,
} = vi.hoisted(() => ({
  marketsMock: vi.fn(),
  quotesMock: vi.fn(),
  snapshotStreamMock: vi.fn(),
  listMock: vi.fn(),
  openOrderTicketMock: vi.fn(),
  submitOrderMock: vi.fn(),
  addWidgetToWorkspaceMock: vi.fn(),
  setWidgetSymbolMock: vi.fn(),
}));

vi.mock("../../store/useTradingStore", () => ({
  useTradingStore: () => ({
    openOrderTicket: openOrderTicketMock,
    submitOrder: submitOrderMock,
  }),
}));

vi.mock("../workspaces", () => ({
  useWorkspaceStore: () => ({
    orderConfirmationRequired: true,
    workspaces: [],
    activeWorkspaceId: 1,
    addWidgetToWorkspace: addWidgetToWorkspaceMock,
    setWidgetSymbol: setWidgetSymbolMock,
  }),
}));

vi.mock("@/clients", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../clients")>();
  return {
    ...actual,
    apiClients: {
      data: { markets: marketsMock, quotes: quotesMock, snapshotStream: snapshotStreamMock },
      watchlists: { list: listMock },
    },
    unwrapData: (response: { data: unknown }) => response.data,
  };
});

function directoryRow(symbol: string) {
  return {
    symbol,
    name: `${symbol} name`,
    asset_class: "Forex",
    source_id: "catalogue.catalog-instruments@1",
    digits: 5,
    last: null,
    bid: null,
    ask: null,
    spread: null,
    volume: null,
    open: null,
    high: null,
    low: null,
    close: null,
    change: null,
    change_percent: null,
  };
}

function noWatchlists() {
  listMock.mockResolvedValue({ data: [] });
}

function marketsPage(rows: unknown[], nextCursor: string | null = null) {
  marketsMock.mockResolvedValue({
    data: {
      source_id: "catalogue.catalog-instruments@1",
      rows,
      limit: 50,
      next_cursor: nextCursor,
      revision: "rev-1",
      generated_at: "2026-09-03T12:00:00.000000Z",
      request_id: "req-1",
    },
  });
}

function gatewayUnavailable(): never {
  throw new ApiClientError({
    message: "HTTP 503 opening route",
    status: 503,
    code: "UPSTREAM_UNAVAILABLE",
  });
}

function marketsWidget(): Widget {
  return { id: "widget-1", type: "markets", title: "Markets" };
}

describe("FEAT-UI-02 feature adapter — D-UI §4.8 lifecycle", () => {
  beforeEach(() => {
    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      value: "visible",
    });
    marketsMock.mockReset();
    quotesMock.mockReset();
    snapshotStreamMock.mockReset();
    listMock.mockReset();
    noWatchlists();
  });

  it("applies validated configuration to the directory load", async () => {
    marketsPage([directoryRow("EURUSD")]);

    render(
      <MarketsFeature config={{ pageSize: 25, maxPages: 2, streamSettlingSeconds: 1 }} />,
    );

    await waitFor(() => expect(marketsMock).toHaveBeenCalled());
    expect(marketsMock).toHaveBeenCalledWith(
      expect.objectContaining({ limit: 25 }),
    );
    expect(screen.getByText("EURUSD")).toBeInTheDocument();
  });

  it("renders the explicit unavailable state on catalogue 503", async () => {
    marketsMock.mockImplementation(() => {
      gatewayUnavailable();
    });

    render(<MarketsFeature />);

    await waitFor(() =>
      expect(
        screen.getByText(/The market catalogue gateway is unavailable/),
      ).toBeInTheDocument(),
    );
    expect(screen.queryByText("EURUSD")).not.toBeInTheDocument();
  });

  it("renders the transient error state for non-503 failures", async () => {
    marketsMock.mockRejectedValue(new Error("network down"));

    render(<MarketsFeature />);

    await waitFor(() =>
      expect(
        screen.getByText("Unable to load the market directory."),
      ).toBeInTheDocument(),
    );
  });

  it("rejects invalid configuration explicitly without transport activity", () => {
    render(<MarketsFeature config={{ pageSize: 50, extra: true }} />);

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.queryByText("Loading market directory")).not.toBeInTheDocument();
    expect(marketsMock).not.toHaveBeenCalled();
  });

  it("registers through the workspace content host", async () => {
    marketsPage([directoryRow("EURUSD")]);

    render(<WidgetContentHost widget={marketsWidget()} />);

    await waitFor(() =>
      expect(screen.getByText("EURUSD")).toBeInTheDocument(),
    );
  });
});
