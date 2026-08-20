/** Tests for the tabbed Data reference workspace. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiClients } from "@/clients";

import { DataWorkspace } from "./data";

vi.mock("@/clients", async () => {
  const actual = await vi.importActual<typeof import("@/clients")>("@/clients");
  return {
    ...actual,
    apiClients: {
      ...actual.apiClients,
      data: {
        ...actual.apiClients.data,
        capabilities: vi.fn(),
        marketSeries: vi.fn(),
        instruments: vi.fn(),
        brokers: vi.fn(),
        instrument: vi.fn(),
        updateSeries: vi.fn(),
        updateInstrument: vi.fn(),
        syncReference: vi.fn(),
      },
    },
  };
});

const METADATA = {
  contract_version: "v1" as const,
  schema_id: "api.metadata.v1" as const,
  request_id: "req-test",
  route: "/api/v1/data/series",
  operation: "api.data.series",
  side_effect: "read" as const,
  timestamp: "2026-08-10T00:00:00Z",
  stale: false,
  idempotency_replayed: false,
};

function mockSeries(series: readonly unknown[]): void {
  vi.mocked(apiClients.data.marketSeries).mockResolvedValue({
    status: "success",
    message: "ok",
    data: { series } as never,
    error: null,
    metadata: METADATA,
  });
}

function mockInstruments(instruments: readonly unknown[]): void {
  vi.mocked(apiClients.data.instruments).mockResolvedValue({
    status: "success",
    message: "ok",
    data: { instruments } as never,
    error: null,
    metadata: METADATA,
  });
}

function mockBrokers(brokers: readonly unknown[]): void {
  vi.mocked(apiClients.data.brokers).mockResolvedValue({
    status: "success",
    message: "ok",
    data: { brokers } as never,
    error: null,
    metadata: METADATA,
  });
}

const SERIES_ROW = {
  series_id: 7,
  symbol: "EURJPY_M1",
  instrument: "EURJPY",
  document: "EURJPY_M1.csv",
  broker_id: 1,
  usymbol: null,
  timeframe: "M1",
  timezone: "UTC",
  date_from: 1609459200,
  date_to: 1640908800,
  total_days: 364,
  row_count: 250000,
  decimals: 3,
  source: 2,
  bar_type: "start_of_bar",
  data_type: 1,
  show: 1,
  remove_weekends: 0,
};

function mockInstrumentSpec(): void {
  vi.mocked(apiClients.data.instrument).mockResolvedValue({
    status: "success",
    message: "ok",
    data: {
      instrument: "EURJPY",
      description: "Euro vs Japanese Yen",
      broker_profile: "MetaTrader 5 Demo",
      point_value: 0.001,
      contract_size: 100000,
      tick_size: 0.001,
      tick_step: 0.001,
      default_spread: 0.002,
      default_slippage: 1,
      data_type: 1,
      order_size_multiplier: 1,
      order_size_step: 0,
      min_distance: 0,
      swap: null,
    } as never,
    error: null,
    metadata: METADATA,
  });
}

describe("DataWorkspace", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSeries([]);
    mockInstruments([]);
    mockBrokers([]);
  });

  it("renders the three reference tabs with the Data tab active", async () => {
    render(<DataWorkspace />);

    const dataTab = screen.getByRole("tab", { name: "Data" });
    expect(dataTab).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tab", { name: "Instruments" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Broker Profiles" })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("Symbol Name")).toBeInTheDocument());
  });

  it("renders market series rows with the catalogue columns", async () => {
    mockSeries([SERIES_ROW]);
    render(<DataWorkspace />);

    await waitFor(() => expect(screen.getByText("EURJPY_M1")).toBeInTheDocument());
    expect(screen.getByText("Instrument")).toBeInTheDocument();
    expect(screen.getByText("Total Days")).toBeInTheDocument();
    expect(screen.getByText("Bar type")).toBeInTheDocument();
    expect(screen.getByText("Start of Bar")).toBeInTheDocument();
    expect(screen.getByText("2021-01-01")).toBeInTheDocument();
  });

  it("opens the edit dialog prepopulated when the symbol is clicked", async () => {
    mockSeries([SERIES_ROW]);
    mockInstrumentSpec();
    render(<DataWorkspace />);

    await waitFor(() => expect(screen.getByText("EURJPY_M1")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Edit series EURJPY_M1" }));

    const dialog = await screen.findByRole("dialog");
    expect(dialog).toHaveAttribute("aria-label", "Edit series EURJPY_M1");
    expect((screen.getByLabelText("Symbol name") as HTMLInputElement).value).toBe(
      "EURJPY_M1"
    );
    await waitFor(() =>
      expect((screen.getByLabelText("Description") as HTMLInputElement).value).toBe(
        "Euro vs Japanese Yen"
      )
    );
    expect(
      (screen.getByLabelText("Bar type") as HTMLInputElement).value
    ).toBe("Start of Bar");
    expect(screen.getByLabelText("Hide")).not.toBeChecked();
    expect(screen.getByText("Remove weekends")).toBeInTheDocument();
  });

  it("saves the edited series and refetches the tab", async () => {
    mockSeries([SERIES_ROW]);
    mockInstrumentSpec();
    vi.mocked(apiClients.data.updateSeries).mockResolvedValue({
      status: "success",
      message: "ok",
      data: {
        series_id: 7,
        symbol: "EDITED_M1",
        instrument: "EURJPY",
        bar_type: "start_of_bar",
      } as never,
      error: null,
      metadata: METADATA,
    });
    render(<DataWorkspace />);

    await waitFor(() => expect(screen.getByText("EURJPY_M1")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Edit series EURJPY_M1" }));
    const symbolInput = await screen.findByLabelText("Symbol name");
    fireEvent.change(symbolInput, { target: { value: "EDITED_M1" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() =>
      expect(apiClients.data.updateSeries).toHaveBeenCalledWith(
        7,
        expect.objectContaining({ symbol: "EDITED_M1", show: 1 })
      )
    );
    await waitFor(() =>
      expect(apiClients.data.marketSeries).toHaveBeenCalledTimes(2)
    );
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("discards edits when Cancel closes the dialog", async () => {
    mockSeries([SERIES_ROW]);
    mockInstrumentSpec();
    render(<DataWorkspace />);

    await waitFor(() => expect(screen.getByText("EURJPY_M1")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Edit series EURJPY_M1" }));
    const symbolInput = await screen.findByLabelText("Symbol name");
    fireEvent.change(symbolInput, { target: { value: "EDITED_M1" } });
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(apiClients.data.updateSeries).not.toHaveBeenCalled();
  });

  it("switches to the Instruments tab and renders its columns", async () => {
    mockInstruments([
      {
        instrument: "EURJPY",
        description: "Euro vs Japanese Yen",
        broker_profile: "MetaTrader 5 Demo",
        point_value: 0.00001,
        contract_size: 100000,
        tick_size: 0.00001,
        default_spread: 12,
        default_slippage: 1,
        data_type: "FOREX",
        order_size_multiplier: 1,
        order_size_step: 0,
      },
    ]);
    render(<DataWorkspace />);

    fireEvent.click(screen.getByRole("tab", { name: "Instruments" }));

    await waitFor(() => expect(screen.getByText("EURJPY")).toBeInTheDocument());
    expect(screen.getByText("Point value")).toBeInTheDocument();
    expect(screen.getByText("Contract Size")).toBeInTheDocument();
    expect(screen.getByText("Tick Size")).toBeInTheDocument();
    expect(screen.getByText("Default spread")).toBeInTheDocument();
    expect(screen.getByText("Default slippage")).toBeInTheDocument();
    expect(screen.getByText("Data type")).toBeInTheDocument();
    expect(screen.getByText("Order size mult.")).toBeInTheDocument();
    expect(screen.getByText("MetaTrader 5 Demo")).toBeInTheDocument();
    expect(screen.getAllByText("0.00001")).toHaveLength(2);
    expect(screen.getByText("100000")).toBeInTheDocument();
    expect(screen.getByText("FOREX")).toBeInTheDocument();
  });

  it("opens the instrument edit dialog prepopulated when an instrument is clicked", async () => {
    mockInstruments([
      {
        instrument: "EURJPY",
        description: null,
        broker_profile: "MetaTrader 5 Demo",
        point_value: 0.001,
        contract_size: 100000,
        tick_size: 0.001,
        default_spread: 0.002,
        default_slippage: 1,
        data_type: "FOREX",
        order_size_multiplier: 1,
        order_size_step: 0,
      },
    ]);
    mockInstrumentSpec();
    render(<DataWorkspace />);

    fireEvent.click(screen.getByRole("tab", { name: "Instruments" }));
    await waitFor(() => expect(screen.getByText("EURJPY")).toBeInTheDocument());
    fireEvent.click(
      screen.getByRole("button", { name: "Edit instrument EURJPY" })
    );

    const dialog = await screen.findByRole("dialog");
    expect(dialog).toHaveAttribute("aria-label", "Edit instrument EURJPY");
    expect((screen.getByLabelText("Instrument") as HTMLInputElement).value).toBe(
      "EURJPY"
    );
    await waitFor(() =>
      expect((screen.getByLabelText("Description") as HTMLInputElement).value).toBe(
        "Euro vs Japanese Yen"
      )
    );
    expect(
      (screen.getByLabelText("Pip/Tick size") as HTMLInputElement).value
    ).toBe("0.001");
  });

  it("saves the edited instrument and refetches the tab", async () => {
    mockInstruments([
      {
        instrument: "EURJPY",
        description: null,
        broker_profile: "MetaTrader 5 Demo",
        point_value: 0.001,
        contract_size: 100000,
        tick_size: 0.001,
        default_spread: 0.002,
        default_slippage: 1,
        data_type: "FOREX",
        order_size_multiplier: 1,
        order_size_step: 0,
      },
    ]);
    mockInstrumentSpec();
    vi.mocked(apiClients.data.updateInstrument).mockResolvedValue({
      status: "success",
      message: "ok",
      data: {
        instrument: "EURJPY",
        description: "Edited",
        broker_profile: "MetaTrader 5 Demo",
        point_value: 0.001,
        contract_size: 100000,
        tick_size: 0.005,
        tick_step: 0.001,
        default_spread: 0.002,
        default_slippage: 1,
        data_type: 1,
        order_size_multiplier: 1,
        order_size_step: 0,
        min_distance: 0,
        swap: null,
      } as never,
      error: null,
      metadata: METADATA,
    });
    render(<DataWorkspace />);

    fireEvent.click(screen.getByRole("tab", { name: "Instruments" }));
    await waitFor(() => expect(screen.getByText("EURJPY")).toBeInTheDocument());
    fireEvent.click(
      screen.getByRole("button", { name: "Edit instrument EURJPY" })
    );
    const tickSizeInput = await screen.findByLabelText("Pip/Tick size");
    await waitFor(() => expect(tickSizeInput).toHaveValue("0.001"));
    fireEvent.change(tickSizeInput, { target: { value: "0.005" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() =>
      expect(apiClients.data.updateInstrument).toHaveBeenCalledWith(
        "EURJPY",
        expect.objectContaining({ tick_size: 0.005 })
      )
    );
    await waitFor(() =>
      expect(apiClients.data.instruments).toHaveBeenCalledTimes(2)
    );
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("discards instrument edits when Cancel closes the dialog", async () => {
    mockInstruments([
      {
        instrument: "EURJPY",
        description: null,
        broker_profile: "MetaTrader 5 Demo",
        point_value: 0.001,
        contract_size: 100000,
        tick_size: 0.001,
        default_spread: 0.002,
        default_slippage: 1,
        data_type: "FOREX",
        order_size_multiplier: 1,
        order_size_step: 0,
      },
    ]);
    mockInstrumentSpec();
    render(<DataWorkspace />);

    fireEvent.click(screen.getByRole("tab", { name: "Instruments" }));
    await waitFor(() => expect(screen.getByText("EURJPY")).toBeInTheDocument());
    fireEvent.click(
      screen.getByRole("button", { name: "Edit instrument EURJPY" })
    );
    await screen.findByRole("dialog");
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(apiClients.data.updateInstrument).not.toHaveBeenCalled();
  });

  it("switches to the Broker Profiles tab and renders its columns", async () => {
    mockBrokers([
      {
        broker_id: 1,
        name: "MetaTrader 5",
        description: "Default MT5 broker",
        postfix: "_r",
        timezone: "EET",
        customized_instruments: 30,
      },
    ]);
    render(<DataWorkspace />);

    fireEvent.click(screen.getByRole("tab", { name: "Broker Profiles" }));

    await waitFor(() => expect(screen.getByText("MetaTrader 5")).toBeInTheDocument());
    expect(screen.getByText("Postfix")).toBeInTheDocument();
    expect(screen.getByText("Timezone")).toBeInTheDocument();
    expect(screen.getByText("Customized instruments")).toBeInTheDocument();
    expect(screen.getByText("30")).toBeInTheDocument();
  });

  it("shows the header row even when the active table is empty", async () => {
    render(<DataWorkspace />);

    await waitFor(() => expect(screen.getByText("Symbol Name")).toBeInTheDocument());
    expect(screen.queryByText("EURJPY_M1")).not.toBeInTheDocument();
  });

  it("syncs from QuantDataManager and refetches when Refresh is clicked", async () => {
    vi.mocked(apiClients.data.syncReference).mockResolvedValue({
      status: "success",
      message: "ok",
      data: {
        series_synced: 60,
        brokers_synced: 9,
        instruments_synced: 30,
        instruments_failed: [],
        mt5_available: true,
      } as never,
      error: null,
      metadata: METADATA,
    });
    render(<DataWorkspace />);
    await waitFor(() => expect(screen.getByText("Symbol Name")).toBeInTheDocument());
    expect(apiClients.data.marketSeries).toHaveBeenCalledTimes(1);

    fireEvent.click(
      screen.getByRole("button", {
        name: "Sync from QuantDataManager and refresh the active table",
      })
    );

    await waitFor(() =>
      expect(apiClients.data.syncReference).toHaveBeenCalledTimes(1)
    );
    await waitFor(() =>
      expect(screen.getByText(/synced 60 series/)).toBeInTheDocument()
    );
    await waitFor(() =>
      expect(apiClients.data.marketSeries).toHaveBeenCalledTimes(2)
    );
  });

  it("surfaces an error without inventing rows", async () => {
    vi.mocked(apiClients.data.marketSeries).mockRejectedValue(
      new Error("series unavailable")
    );
    render(<DataWorkspace />);

    await waitFor(() => expect(screen.getByText("unavailable")).toBeInTheDocument());
    expect(screen.queryByText("Start of Bar")).not.toBeInTheDocument();
  });
});
