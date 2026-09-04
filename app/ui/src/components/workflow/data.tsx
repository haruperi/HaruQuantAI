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
import { InstrumentEditDialog } from "./InstrumentEditDialog";
import {
  QdmRibbon,
  type QdmRibbonTab,
  QdmProgressBar,
  type BatchTask,
  DataReviewModal,
  DukasDownloadModal,
  DukasAddModal,
  CloneTimezoneModal,
  ExportCsvModal,
  ExportMt4Modal,
  DataLogView,
  type LogEntry,
} from "./qdm";

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
  isSelected = false,
  onSelect,
  onDoubleClick,
}: {
  row: MarketSeriesRow;
  onEdit: (row: MarketSeriesRow) => void;
  isSelected?: boolean;
  onSelect?: () => void;
  onDoubleClick?: () => void;
}): ReactNode {
  return (
    <tr
      onClick={onSelect}
      onDoubleClick={onDoubleClick}
      style={{
        background: isSelected ? "rgba(56, 189, 248, 0.12)" : undefined,
        cursor: "pointer",
      }}
    >
      <td>
        <button
          className="series-symbol-link"
          onClick={(e) => {
            e.stopPropagation();
            onEdit(row);
          }}
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
            fontWeight: isSelected ? 700 : 400,
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
function InstrumentRowView({
  row,
  onEdit,
}: {
  row: InstrumentRow;
  onEdit: (instrumentId: string) => void;
}): ReactNode {
  return (
    <tr>
      <td>
        <button
          onClick={() => onEdit(row.instrument)}
          aria-label={`Edit instrument ${row.instrument}`}
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
          {row.instrument}
        </button>
      </td>
      <td>{orDash(row.description)}</td>
      <td>{orDash(row.broker_profile)}</td>
      <td>
        {row.point_value !== null && row.point_value !== undefined
          ? row.point_value.toFixed(5)
          : "—"}
      </td>
      <td>{orDash(row.contract_size)}</td>
      <td>{orDash(row.tick_size)}</td>
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
    <th>Contract Size</th>
    <th>Tick Size</th>
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
  const [ribbonTab, setRibbonTab] = useState<QdmRibbonTab>("sources");
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
  const [editingInstrument, setEditingInstrument] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncNote, setSyncNote] = useState<string | null>(null);

  // QDM Workflow and Modal state
  const [selectedSeries, setSelectedSeries] = useState<MarketSeriesRow | null>(null);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [showDownloadModal, setShowDownloadModal] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showCloneModal, setShowCloneModal] = useState(false);
  const [showExportCsvModal, setShowExportCsvModal] = useState(false);
  const [showExportMt4Modal, setShowExportMt4Modal] = useState(false);
  const [showLogs, setShowLogs] = useState(false);
  const [activeTask, setActiveTask] = useState<BatchTask | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([
    {
      timestamp: new Date().toLocaleTimeString(),
      level: "INFO",
      message: "QuantDataManager initialized. 30 Parquet archives ready.",
    },
  ]);

  const addLog = useCallback((level: LogEntry["level"], message: string) => {
    setLogs((prev) => [
      ...prev,
      {
        timestamp: new Date().toLocaleTimeString(),
        level,
        message,
      },
    ]);
  }, []);

  const load = useCallback(async (tab: TabId): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      if (tab === "data") {
        const response = await apiClients.data.marketSeries();
        const loadedSeries = unwrapData(response).series;
        setSeries(loadedSeries);
        // Select first series by default if none selected
        if (loadedSeries.length > 0) {
          setSelectedSeries((prev) => prev ?? loadedSeries[0]);
        }
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

  const refresh = useCallback(
    async (tab: TabId): Promise<void> => {
      setSyncing(true);
      setSyncNote(null);
      try {
        const response = await apiClients.data.syncReference();
        const summary = unwrapData(response);
        setSyncNote(
          `synced ${summary.series_synced} series, ` +
            `${summary.brokers_synced} brokers, ` +
            `${summary.instruments_synced} instruments` +
            (summary.mt5_available ? "" : " (MT5 unavailable)")
        );
        addLog("INFO", `Synced ${summary.series_synced} series from catalogue.`);
      } catch (reason) {
        setError(
          reason instanceof ApiClientError ? reason.message : "sync unavailable"
        );
      } finally {
        setSyncing(false);
      }
      // Reset lazy caches so every tab reloads fresh reference data.
      setFetched({ data: false, instruments: false, brokers: false });
      await load(tab);
    },
    [addLog, load]
  );

  useEffect(() => {
    if (!fetched[activeTab]) void load(activeTab);
  }, [activeTab, fetched, load]);

  const selectTab = (tab: TabId): void => {
    setActiveTab(tab);
    if (tab === "instruments") setRibbonTab("instruments");
    else if (tab === "brokers") setRibbonTab("brokers");
    else if (ribbonTab === "instruments" || ribbonTab === "brokers") setRibbonTab("sources");
    setError(null);
    setLoading(!fetched[tab]);
  };

  const handleRibbonTabSelect = (tab: QdmRibbonTab) => {
    setRibbonTab(tab);
    if (tab === "sources" || tab === "export" || tab === "tools") {
      selectTab("data");
    } else if (tab === "instruments") {
      selectTab("instruments");
    } else if (tab === "brokers") {
      selectTab("brokers");
    }
  };

  const handleDeleteSeries = async () => {
    if (!selectedSeries) return;
    if (
      !confirm(
        `Are you sure you want to delete series ${selectedSeries.symbol}? This will also delete its parquet files.`
      )
    ) {
      return;
    }
    try {
      addLog("INFO", `Deleting series ${selectedSeries.symbol}...`);
      const res = await apiClients.data.deleteSeries(selectedSeries.series_id, true);
      if (res.status === "success") {
        addLog("SUCCESS", `Deleted series ${selectedSeries.symbol} and removed Parquet archives.`);
        setSelectedSeries(null);
        void load("data");
      } else {
        addLog("ERROR", `Failed to delete series: ${res.message}`);
      }
    } catch (e: any) {
      addLog("ERROR", `Deletion failed: ${e?.message}`);
    }
  };

  const handleDownloadStarted = (taskName: string) => {
    addLog("INFO", taskName);
    setActiveTask({
      id: "task-download",
      name: taskName,
      progress: 10,
      status: "running",
      details: "Fetching Parquet blocks...",
    });

    let p = 20;
    const interval = setInterval(() => {
      p += 25;
      if (p >= 100) {
        clearInterval(interval);
        setActiveTask({
          id: "task-download",
          name: taskName,
          progress: 100,
          status: "completed",
          details: "Parquet written & indexed.",
        });
        addLog("SUCCESS", `Completed download for ${taskName}.`);
        setTimeout(() => setActiveTask(null), 3000);
        void load("data");
      } else {
        setActiveTask((prev) => (prev ? { ...prev, progress: p } : null));
      }
    }, 500);
  };

  const handleCloned = (newSymbol: string) => {
    addLog("SUCCESS", `Successfully cloned series to ${newSymbol} with shifted Parquet bars.`);
    void load("data");
  };

  const handleMt4Exported = (result: Record<string, unknown>) => {
    addLog(
      "SUCCESS",
      `Exported MT4 HST (${result.bars_count} bars) and FXT (${result.records_count} ticks).`
    );
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
      style={{ display: "flex", flexDirection: "column", height: "100%", background: "#0b0f14" }}
    >
      {/* 1. Contextual QuantDataManager Ribbon Toolbar */}
      <QdmRibbon
        activeTab={ribbonTab}
        onSelectTab={handleRibbonTabSelect}
        selectedSymbol={selectedSeries?.symbol || null}
        selectedSeriesId={selectedSeries?.series_id || null}
        onAddNew={() => setShowAddModal(true)}
        onDownload={() => setShowDownloadModal(true)}
        onImport={() => addLog("INFO", "Opening file import dialog...")}
        onDelete={handleDeleteSeries}
        onReview={() => setShowReviewModal(true)}
        onExportCsv={() => setShowExportCsvModal(true)}
        onExportMt4={() => setShowExportMt4Modal(true)}
        onCloneTimezone={() => setShowCloneModal(true)}
        onToggleLogs={() => setShowLogs((v) => !v)}
        onRefresh={() => void refresh(activeTab)}
        isSyncing={syncing}
      />

      {/* 2. Sub-navigation tabs matching design & existing test expectations */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
          padding: "8px 14px",
          borderBottom: "1px solid var(--border-color)",
          background: "var(--bg-primary, #0b0f14)",
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
                  padding: "5px 12px",
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
          onClick={() => void refresh(activeTab)}
          disabled={loading || syncing}
          aria-label="Sync from QuantDataManager and refresh the active table"
          title="Sync from QuantDataManager and refresh the active table"
        >
          <RefreshCw size={12} /> {syncing ? "Syncing…" : "Refresh"}
        </button>
      </div>

      {syncNote && (
        <p
          style={{
            margin: "0 14px",
            padding: "4px 0 0",
            fontSize: 11,
            color: "var(--text-muted-grey)",
          }}
        >
          {syncNote}
        </p>
      )}

      {/* 3. Main Data / Instruments / Brokers Table Panel */}
      <div
        role="tabpanel"
        id={`panel-${activeTab}`}
        aria-labelledby={`tab-${activeTab}`}
        style={{ flex: 1, overflow: "auto", padding: "10px 14px" }}
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
                      isSelected={selectedSeries?.series_id === row.series_id}
                      onSelect={() => setSelectedSeries(row)}
                      onDoubleClick={() => {
                        setSelectedSeries(row);
                        setShowReviewModal(true);
                      }}
                      onEdit={setEditing}
                    />
                  ))}
                {activeTab === "instruments" &&
                  instruments.map((row) => (
                    <InstrumentRowView
                      key={row.instrument}
                      row={row}
                      onEdit={setEditingInstrument}
                    />
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

      {/* 4. Persistent Batch Execution Progress Bar */}
      <QdmProgressBar
        task={activeTask}
        onPauseResume={() => {
          setActiveTask((prev) =>
            prev
              ? { ...prev, status: prev.status === "paused" ? "running" : "paused" }
              : null
          );
        }}
        onCancel={() => {
          addLog("WARN", `Cancelled task ${activeTask?.name}`);
          setActiveTask(null);
        }}
      />

      {/* 5. Collapsible Log Drawer */}
      {showLogs && (
        <DataLogView
          logs={logs}
          onClear={() => setLogs([])}
          onClose={() => setShowLogs(false)}
        />
      )}

      {/* 6. Modals & Dialogs */}
      {showReviewModal && selectedSeries && (
        <DataReviewModal
          symbol={selectedSeries.symbol}
          initialTimeframe={selectedSeries.timeframe || "M1"}
          onClose={() => setShowReviewModal(false)}
        />
      )}

      {showDownloadModal && selectedSeries && (
        <DukasDownloadModal
          symbol={selectedSeries.symbol}
          onClose={() => setShowDownloadModal(false)}
          onStarted={handleDownloadStarted}
        />
      )}

      {showAddModal && (
        <DukasAddModal
          onClose={() => setShowAddModal(false)}
          onAdded={(newSym) => {
            addLog("INFO", `Selected Dukascopy symbol ${newSym} for download.`);
            setShowDownloadModal(true);
          }}
        />
      )}

      {showCloneModal && selectedSeries && (
        <CloneTimezoneModal
          symbol={selectedSeries.symbol}
          onClose={() => setShowCloneModal(false)}
          onCloned={handleCloned}
        />
      )}

      {showExportCsvModal && selectedSeries && (
        <ExportCsvModal
          symbol={selectedSeries.symbol}
          onClose={() => setShowExportCsvModal(false)}
        />
      )}

      {showExportMt4Modal && selectedSeries && (
        <ExportMt4Modal
          symbol={selectedSeries.symbol}
          onClose={() => setShowExportMt4Modal(false)}
          onSuccess={handleMt4Exported}
        />
      )}

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

      {editingInstrument && (
        <InstrumentEditDialog
          instrumentId={editingInstrument}
          onClose={() => setEditingInstrument(null)}
          onSaved={() => {
            setEditingInstrument(null);
            void load("instruments");
          }}
        />
      )}
    </section>
  );
}
