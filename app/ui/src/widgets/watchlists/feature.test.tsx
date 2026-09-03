/**
 * FEAT-UI-03 feature adapter lifecycle tests (D-UI §4.8).
 */
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiClientError } from "../../clients";
import { WidgetContentHost } from "../../components/layout/WidgetContentHost";
import type { Widget } from "../workspaces";

import { WatchlistsFeature } from "./feature";

const {
  listMock,
  createMock,
  updateMock,
  removeMock,
  quotesMock,
  symbolsMock,
} = vi.hoisted(() => ({
  listMock: vi.fn(),
  createMock: vi.fn(),
  updateMock: vi.fn(),
  removeMock: vi.fn(),
  quotesMock: vi.fn(),
  symbolsMock: vi.fn(),
}));

vi.mock("../../store/useTradingStore", () => ({
  useTradingStore: () => ({
    openOrderTicket: vi.fn(),
    submitOrder: vi.fn(),
  }),
}));

vi.mock("../workspaces", () => ({
  useWorkspaceStore: () => ({
    orderConfirmationRequired: true,
    addWidgetToWorkspace: vi.fn(),
  }),
}));

vi.mock("@/clients", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../clients")>();
  return {
    ...actual,
    apiClients: {
      watchlists: {
        create: createMock,
        list: listMock,
        remove: removeMock,
        update: updateMock,
      },
      data: { quotes: quotesMock, symbols: symbolsMock },
    },
    unwrapData: (response: { data: unknown }) => response.data,
  };
});

const DEFAULT_LIST = {
  watchlist_id: "wl-default",
  account_id: "acct-1",
  name: "Default",
  is_default: true,
  sort_order: 0,
  items: [
    { source_id: "mt5", symbol: "EURUSD", sort_order: 0, asset_class: "Forex" },
  ],
  created_at: "2026-09-03T12:00:00Z",
  updated_at: "2026-09-03T12:00:00Z",
};

function watchlistWidget(): Widget {
  return { id: "widget-1", type: "watchlist", title: "Watchlists" };
}

describe("FEAT-UI-03 feature adapter — D-UI §4.8 lifecycle", () => {
  beforeEach(() => {
    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      value: "visible",
    });
    listMock.mockReset();
    createMock.mockReset();
    updateMock.mockReset();
    removeMock.mockReset();
    quotesMock.mockReset();
    symbolsMock.mockReset();
  });

  it("is active when the gateway is present", async () => {
    listMock.mockResolvedValue({ data: [DEFAULT_LIST] });

    render(<WatchlistsFeature />);

    await waitFor(() =>
      expect(screen.getByText("EURUSD")).toBeInTheDocument(),
    );
  });

  it("renders the explicit unavailable state on gateway 503", async () => {
    listMock.mockImplementation(() =>
      Promise.reject(
        new ApiClientError({
          message: "HTTP 503 opening route",
          status: 503,
          code: "UPSTREAM_UNAVAILABLE",
        }),
      ),
    );

    render(<WatchlistsFeature />);

    await waitFor(() =>
      expect(
        screen.getAllByText(/The watchlist gateway is unavailable/).length,
      ).toBeGreaterThan(0),
    );
    expect(screen.queryByText("EURUSD")).not.toBeInTheDocument();
    expect(screen.queryByText("EURUSD")).not.toBeInTheDocument();
  });

  it("renders the transient error state for non-503 failures", async () => {
    listMock.mockRejectedValue(new Error("network down"));

    render(<WatchlistsFeature />);

    await waitFor(() =>
      expect(document.body.textContent).toContain(
        "Unable to load watchlists.",
      ),
    );
  });

  it("rejects invalid configuration explicitly without transport activity", () => {
    render(<WatchlistsFeature config={{ refreshSeconds: 30, extra: true }} />);

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(listMock).not.toHaveBeenCalled();
  });

  it("registers through the workspace content host", async () => {
    listMock.mockResolvedValue({ data: [DEFAULT_LIST] });

    render(<WidgetContentHost widget={watchlistWidget()} />);

    await waitFor(() =>
      expect(screen.getByText("EURUSD")).toBeInTheDocument(),
    );
  });
});
