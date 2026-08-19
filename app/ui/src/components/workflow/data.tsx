/** Tabbed presentation of the market-data reference catalogues. */

"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";
import { RefreshCw } from "lucide-react";

import {
  ApiClientError,
  apiClients,
  unwrapData,
  type BrokerRow,
  type InstrumentRow,
  type MarketSeriesRow,
} from "@/clients";

import { DataEditDialog } from "./DataEditDialog";

/** Render an epoch-seconds timestamp as a UTC date, or an em dash. */
function formatDate(seconds: number | null): string {
  if (seconds === null || seconds <= 0) return "—";
  return new Date(seconds * 1000).toISOString().slice(0, 10);
}

/** Render a nullable value as an em dash. */
function orDash(value: string | number | null): string {
  return value === null || value === undefined || value === "" ? "—"
    : String(value);
}

/** One market-data series table row. */
function SeriesRow({
  row,
  onEdit,
}: {
  row: MarketSeriesRow;
  onEdit: (row: MarketSeriesRow) => void;
}): ReactNode {
  return (
    <tr>
      <td>
        <button
          className="series-symbol-link"
          onClick={() => onEdit(row)}
          aria-label={`Edit series ${row.symbol}`}
          style={{
            background: "none",
            border: "none",
            padding: 0,
            color: "var(--cme-blue-bright)",
            cursor: "pointer",
            font: "inherit",
            textDecoration: "underline",
            textUnderlineOffset: 2,
          }}
        >
          {row.symbol}
        </button>
      </td>
      <td>{orDash(row.instrument)}</td>
      <td>{orDash(row.document)}</td>
      <td>{orDash(row.broker_id)}</td>
      <td>{orDash(row.usymbol)}</td>
      <td>{orDash(row.timeframe)}</td>
      <td>{orDash(row.timezone)}</td>
      <td>{formatDate(row.date_from)}</td>
      <td>{formatDate(row.date_to)}</td>
      <td>{orDash(row.total_days)}</td>
      <td>{orDash(row.row_count)}</td>
      <td>{orDash(row.source)}</td>
      {/* Invariant: every stored series uses bar-open timestamps. */}
      <td>Start of Bar</td>
      <td>{orDash(row.data_type)}</td>
      <td>{row.show === 0 ? "hidden" : "visible"}</td>
    </tr>
  );
}

/** One instrument specification table row. */
function InstrumentRowView({ row }: { row: InstrumentRow }): ReactNode {
  return (
    <tr>
      <td>{row.instrument}</td>
      <td>{orDash(row.description)}</td>
      <td>{orDash(row.broker_id)}</td>
      <td>{orDash(row.point_value)}</td>
      <td>{orDash(row.tick_size)}</td>
      <td>{orDash(row.tick_step)}</td>
      <td>{orDash(row.default_spread)}</td>
      <td>{orDash(row.default_slippage)}</td>
      <td>{orDash(row.data_type)}</td>
      <td>{orDash(row.order_size_multiplier)}</td>
      <td>{orDash(row.order_size_step)}</td>
    </tr>
  );
}

/** One broker profile table row. */
function BrokerRowView({ row }: { row: BrokerRow }): ReactNode {
  return (
    <tr>
      <td>{orDash(row.broker_id)}</td>
      <td>{orDash(row.name)}</td>
      <td>{orDash(row.description)}</td>
      <td>{orDash(row.postfix)}</td>
      <td>{orDash(row.timezone)}</td>
      <td>{orDash(row.customized_instruments)}</td>
    </tr>
  );
}

/** Shared loading, empty, and error state rendering for one tab panel. */
function TabStates({
  loading,
  error,
  empty,
}: {
  loading: boolean;
  error: string | null;
  empty: boolean;
}) {
  return (
    <>
      {loading && (
        <p style={{ color: "var(--text-muted-grey)", padding: "16px 2px" }}>
          loading…
        </p>
      )}
      {error && (
        <p role="alert" style={{ color: "var(--cme-sell-red)", padding: "16px 2px" }}>
          {error}
        </p>
      )}
      {!loading && !error && empty && (
        <p
          style={{
            color: "var(--text-muted-grey)",
            padding: "18px 2px 12px",
            fontSize: 12,
          }}
        >
          No rows yet — import data to populate this table.
        </p>
      )}
    </>
  );
}

const SERIES_HEADERS = (
  <>
    <th>Symbol Name</th>
    <th>Instrument</th>
    <th>Broker profile</th>
    <th>Underlying Symbol</th>
    <th>Timeframe</th>
    <th>Timezone</th>
    <th>Date from</th>
    <th>Date to</th>
    <th>Total Days</th>
    <th>Total Records</th>
    <th>Source</th>
    <th>Bar type</th>
    <th>Data type</th>
    <th>Hide</th>
  </>
);

const INSTRUMENT_HEADERS = (
  <>
    <th>Instrument</th>
    <th>Description</th>
    <th>Broker profile</th>
    <th>Point value</th>
    <th>Pip/Tick size</th>
    <th>Pip/Tick step</th>
    <th>Default spread</th>
    <th>Default slippage</th>
    <th>Data type</th>
    <th>Order size mult.</th>
    <th>Order size step</th>
  </>
);

const BROKER_HEADERS = (
  <>
    <th>ID</th>
    <th>Name</th>
    <th>Description</th>
    <th>Postfix</th>
    <th>Timezone</th>
    <th>Customized instruments</th>
  </>
);

type TabId = "data" | "instruments" | "brokers";

const TABS: readonly { id: TabId; label: string }[] = [
  { id: "data", label: "Data" },
  { id: "instruments", label: "Instruments" },
  { id: "brokers", label: "Broker Profiles" },
];

/** Tabbed workspace over the Data, Instruments, and Broker Profiles tables. */
export function DataWorkspace(): ReactNode {
  const [activeTab, setActiveTab] = useState<TabId>("data");
  const [series, setSeries] = useState<readonly MarketSeriesRow[]>([]);
  const [instruments, setInstruments] = useState<readonly InstrumentRow[]>([]);
  const [brokers, setBrokers] = useState<readonly BrokerRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetched, setFetched] = useState<Record<TabId, boolean>>({
    data: false,
    instruments: false,
    brokers: false,
  });
  const [editing, setEditing] = useState<MarketSeriesRow | null>(null);

  const load = useCallback(async (tab: TabId): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      if (tab === "data") {
        const response = await apiClients.data.marketSeries();
        setSeries(unwrapData(response).series);
      } else if (tab === "instruments") {
        const response = await apiClients.data.instruments();
        setInstruments(unwrapData(response).instruments);
      } else {
        const response = await apiClients.data.brokers();
        setBrokers(unwrapData(response).brokers);
      }
      setFetched((previous) => ({ ...previous, [tab]: true }));
    } catch (reason) {
      setError(
        reason instanceof ApiClientError ? reason.message : "unavailable"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!fetched[activeTab]) void load(activeTab);
  }, [activeTab, fetched, load]);

  const selectTab = (tab: TabId): void => {
    setActiveTab(tab);
    setError(null);
    setLoading(!fetched[tab]);
  };

  const empty =
    activeTab === "data"
      ? series.length === 0
      : activeTab === "instruments"
        ? instruments.length === 0
        : brokers.length === 0;

  const showTable = !loading && !error;

  return (
    <section
      aria-label="Data reference catalogues"
      aria-live="polite"
      style={{ display: "flex", flexDirection: "column", height: "100%" }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
          padding: "10px 14px",
          borderBottom: "1px solid var(--border-color)",
        }}
      >
        <div
          role="tablist"
          aria-label="Data reference tabs"
          style={{
            display: "inline-flex",
            gap: 2,
            padding: 3,
            borderRadius: 8,
            background: "var(--cme-navy-dark)",
            border: "1px solid var(--border-color)",
          }}
        >
          {TABS.map((tab) => {
            const selected = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                role="tab"
                aria-selected={selected}
                aria-controls={`panel-${tab.id}`}
                id={`tab-${tab.id}`}
                onClick={() => selectTab(tab.id)}
                style={{
                  border: "none",
                  borderRadius: 6,
                  padding: "6px 14px",
                  fontSize: 12,
                  fontWeight: 600,
                  letterSpacing: 0.2,
                  cursor: "pointer",
                  transition: "background 120ms ease, color 120ms ease",
                  background: selected ? "var(--cme-blue-primary)" : "transparent",
                  color: selected ? "#fff" : "var(--text-muted-grey)",
                }}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
        <button
          className="btn-cme btn-outline btn-sm"
          onClick={() => void load(activeTab)}
          disabled={loading}
          aria-label="Refresh the active table"
          title="Refresh the active table"
        >
          <RefreshCw size={12} /> Refresh
        </button>
      </div>
      <div
        role="tabpanel"
        id={`panel-${activeTab}`}
        aria-labelledby={`tab-${activeTab}`}
        style={{ flex: 1, overflow: "auto", padding: "12px 14px" }}
      >
        <TabStates loading={loading} error={error} empty={empty} />
        {showTable && (
          <div
            style={{
              borderRadius: 8,
              border: "1px solid var(--border-color)",
              overflow: "hidden",
            }}
          >
            <table className="cme-table">
              <thead>
                <tr>
                  {activeTab === "data" && SERIES_HEADERS}
                  {activeTab === "instruments" && INSTRUMENT_HEADERS}
                  {activeTab === "brokers" && BROKER_HEADERS}
                </tr>
              </thead>
              <tbody>
                {activeTab === "data" &&
                  series.map((row, index) => (
                    <SeriesRow
                      key={`${row.symbol}-${row.timeframe ?? index}`}
                      row={row}
                      onEdit={setEditing}
                    />
                  ))}
                {activeTab === "instruments" &&
                  instruments.map((row) => (
                    <InstrumentRowView key={row.instrument} row={row} />
                  ))}
                {activeTab === "brokers" &&
                  brokers.map((row, index) => (
                    <BrokerRowView
                      key={`${row.broker_id ?? index}-${row.name ?? index}`}
                      row={row}
                    />
                  ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      {editing && (
        <DataEditDialog
          row={editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            void load("data");
          }}
        />
      )}
    </section>
  );
}
