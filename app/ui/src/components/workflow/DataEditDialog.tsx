/** Governed edit dialog for one market series and its instrument spec. */

"use client";

import {
  useEffect,
  useMemo,
  useState,
  type ChangeEvent,
  type ReactNode,
} from "react";

import {
  ApiClientError,
  apiClients,
  unwrapData,
  type InstrumentSpec,
  type MarketSeriesRow,
  type SeriesUpdateBody,
} from "@/clients";

/** One labelled text input inside the edit dialog. */
function Field({
  label,
  value,
  onChange,
  type = "text",
  disabled = false,
  readOnly = false,
  width = 180,
}: {
  label: string;
  value: string;
  onChange?: (value: string) => void;
  type?: string;
  disabled?: boolean;
  readOnly?: boolean;
  width?: number;
}): ReactNode {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <span style={{ fontSize: 11, color: "var(--text-muted-grey)" }}>{label}</span>
      <input
        type={type}
        value={value}
        disabled={disabled}
        readOnly={readOnly}
        onChange={
          onChange
            ? (event: ChangeEvent<HTMLInputElement>) => onChange(event.target.value)
            : undefined
        }
        style={{
          width,
          padding: "6px 8px",
          borderRadius: 6,
          border: "1px solid var(--border-color)",
          background: "var(--cme-navy-dark)",
          color: "var(--text-light-grey)",
          fontSize: 12,
        }}
      />
    </label>
  );
}

function toDateInput(seconds: number | null): string {
  if (seconds === null || seconds <= 0) return "";
  return new Date(seconds * 1000).toISOString().slice(0, 10);
}

function fromDateInput(value: string): number | null {
  if (!value) return null;
  const parsed = Date.parse(`${value}T00:00:00Z`);
  return Number.isNaN(parsed) ? null : Math.floor(parsed / 1000);
}

function numberOrUndefined(value: string): number | null {
  if (value.trim() === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

/** Modal editor prepopulated from the series row and linked instrument spec. */
export function DataEditDialog({
  row,
  onClose,
  onSaved,
}: {
  row: MarketSeriesRow;
  onClose: () => void;
  onSaved: () => void;
}): ReactNode {
  const [spec, setSpec] = useState<InstrumentSpec | null>(null);
  const [specError, setSpecError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const [symbol, setSymbol] = useState(row.symbol);
  const [instrument, setInstrument] = useState(row.instrument ?? "");
  const [brokerId, setBrokerId] = useState(
    row.broker_id === null ? "" : String(row.broker_id)
  );
  const [timeframe, setTimeframe] = useState(row.timeframe ?? "");
  const [timezone, setTimezone] = useState(row.timezone ?? "");
  const [dateFrom, setDateFrom] = useState(toDateInput(row.date_from));
  const [dateTo, setDateTo] = useState(toDateInput(row.date_to));
  const [dataType, setDataType] = useState(
    row.data_type === null ? "" : String(row.data_type)
  );
  const [decimals, setDecimals] = useState(
    row.decimals === null ? "" : String(row.decimals)
  );
  const [source, setSource] = useState(
    row.source === null ? "" : String(row.source)
  );
  const [rowCount, setRowCount] = useState(
    row.row_count === null ? "" : String(row.row_count)
  );
  const [removeWeekends, setRemoveWeekends] = useState(row.remove_weekends === 1);
  const [hidden, setHidden] = useState(row.show === 0);

  const [description, setDescription] = useState("");
  const [pointValue, setPointValue] = useState("");
  const [tickSize, setTickSize] = useState("");
  const [tickStep, setTickStep] = useState("");
  const [defaultSpread, setDefaultSpread] = useState("");
  const [defaultSlippage, setDefaultSlippage] = useState("");
  const [minDistance, setMinDistance] = useState("");
  const [orderSizeMultiplier, setOrderSizeMultiplier] = useState("");
  const [orderSizeStep, setOrderSizeStep] = useState("");

  useEffect(() => {
    let cancelled = false;
    const identity = row.instrument ?? "";
    if (!identity) return;
    async function load(): Promise<void> {
      try {
        const response = await apiClients.data.instrument(identity);
        if (!cancelled) setSpec(unwrapData(response));
      } catch (reason) {
        if (!cancelled) {
          setSpecError(
            reason instanceof ApiClientError ? reason.message : "unavailable"
          );
        }
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [row.instrument]);

  useEffect(() => {
    if (!spec) return;
    setDescription(spec.description ?? "");
    setPointValue(spec.point_value === null ? "" : String(spec.point_value));
    setTickSize(spec.tick_size === null ? "" : String(spec.tick_size));
    setTickStep(spec.tick_step === null ? "" : String(spec.tick_step));
    setDefaultSpread(
      spec.default_spread === null ? "" : String(spec.default_spread)
    );
    setDefaultSlippage(
      spec.default_slippage === null ? "" : String(spec.default_slippage)
    );
    setMinDistance(spec.min_distance === null ? "" : String(spec.min_distance));
    setOrderSizeMultiplier(
      spec.order_size_multiplier === null
        ? ""
        : String(spec.order_size_multiplier)
    );
    setOrderSizeStep(
      spec.order_size_step === null ? "" : String(spec.order_size_step)
    );
  }, [spec]);

  const body: SeriesUpdateBody = useMemo(
    () => ({
      symbol,
      instrument,
      broker_id: numberOrUndefined(brokerId),
      timeframe: timeframe || null,
      timezone: timezone || null,
      date_from: fromDateInput(dateFrom),
      date_to: fromDateInput(dateTo),
      data_type: numberOrUndefined(dataType),
      decimals: numberOrUndefined(decimals),
      source: numberOrUndefined(source),
      row_count: numberOrUndefined(rowCount),
      remove_weekends: removeWeekends ? 1 : 0,
      show: hidden ? 0 : 1,
      description: description || null,
      point_value: numberOrUndefined(pointValue),
      tick_size: numberOrUndefined(tickSize),
      tick_step: numberOrUndefined(tickStep),
      default_spread: numberOrUndefined(defaultSpread),
      default_slippage: numberOrUndefined(defaultSlippage),
      min_distance: numberOrUndefined(minDistance),
      order_size_multiplier: numberOrUndefined(orderSizeMultiplier),
      order_size_step: numberOrUndefined(orderSizeStep),
    }),
    [
      symbol,
      instrument,
      brokerId,
      timeframe,
      timezone,
      dateFrom,
      dateTo,
      dataType,
      decimals,
      source,
      rowCount,
      removeWeekends,
      hidden,
      description,
      pointValue,
      tickSize,
      tickStep,
      defaultSpread,
      defaultSlippage,
      minDistance,
      orderSizeMultiplier,
      orderSizeStep,
    ]
  );

  const save = async (): Promise<void> => {
    setSaving(true);
    setSaveError(null);
    try {
      await apiClients.data.updateSeries(row.series_id, body);
      onSaved();
    } catch (reason) {
      setSaveError(
        reason instanceof ApiClientError ? reason.message : "unavailable"
      );
      setSaving(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={`Edit series ${row.symbol}`}
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0, 0, 0, 0.55)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
      }}
    >
      <div
        onClick={(event) => event.stopPropagation()}
        style={{
          width: 620,
          maxHeight: "85vh",
          overflow: "auto",
          borderRadius: 10,
          border: "1px solid var(--border-color)",
          background: "var(--cme-navy-panel)",
          padding: 20,
          display: "flex",
          flexDirection: "column",
          gap: 16,
        }}
      >
        <h2 style={{ margin: 0, fontSize: 16 }}>Edit series</h2>

        <fieldset style={{ border: "none", padding: 0, margin: 0 }}>
          <legend style={{ fontSize: 11, color: "var(--text-muted-grey)" }}>
            Series
          </legend>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: 12,
              marginTop: 8,
            }}
          >
            <Field label="Symbol name" value={symbol} onChange={setSymbol} />
            <Field label="Instrument" value={instrument} onChange={setInstrument} />
            <Field label="Broker profile" value={brokerId} onChange={setBrokerId} />
            <Field label="Timeframe" value={timeframe} onChange={setTimeframe} />
            <Field label="Timezone" value={timezone} onChange={setTimezone} />
            <Field
              label="Bar type"
              value="Start of Bar"
              readOnly
            />
            <Field
              label="Date from"
              type="date"
              value={dateFrom}
              onChange={setDateFrom}
            />
            <Field label="Date to" type="date" value={dateTo} onChange={setDateTo} />
            <Field label="Data type" value={dataType} onChange={setDataType} />
            <Field label="Decimals" value={decimals} onChange={setDecimals} />
            <Field label="Source" value={source} onChange={setSource} />
            <Field
              label="Total records"
              value={rowCount}
              onChange={setRowCount}
            />
          </div>
          <div
            style={{
              display: "flex",
              gap: 20,
              marginTop: 12,
              fontSize: 12,
              color: "var(--text-light-grey)",
            }}
          >
            <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <input
                type="checkbox"
                checked={removeWeekends}
                onChange={(event) => setRemoveWeekends(event.target.checked)}
              />
              Remove weekends
            </label>
            <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <input
                type="checkbox"
                checked={hidden}
                onChange={(event) => setHidden(event.target.checked)}
              />
              Hide
            </label>
          </div>
        </fieldset>

        <fieldset style={{ border: "none", padding: 0, margin: 0 }}>
          <legend style={{ fontSize: 11, color: "var(--text-muted-grey)" }}>
            Instrument specification
          </legend>
          {specError && (
            <p role="alert" style={{ color: "var(--cme-sell-red)", fontSize: 12 }}>
              {specError}
            </p>
          )}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: 12,
              marginTop: 8,
            }}
          >
            <Field label="Description" value={description} onChange={setDescription} />
            <Field label="Point value" value={pointValue} onChange={setPointValue} />
            <Field label="Pip/Tick size" value={tickSize} onChange={setTickSize} />
            <Field label="Pip/Tick step" value={tickStep} onChange={setTickStep} />
            <Field
              label="Default spread"
              value={defaultSpread}
              onChange={setDefaultSpread}
            />
            <Field
              label="Default slippage"
              value={defaultSlippage}
              onChange={setDefaultSlippage}
            />
            <Field
              label="Min distance"
              value={minDistance}
              onChange={setMinDistance}
            />
            <Field
              label="Order size mult."
              value={orderSizeMultiplier}
              onChange={setOrderSizeMultiplier}
            />
            <Field
              label="Order size step"
              value={orderSizeStep}
              onChange={setOrderSizeStep}
            />
          </div>
          <p style={{ fontSize: 11, color: "var(--text-muted-grey)", margin: "8px 0 0" }}>
            Swap rules: {spec?.swap ? "configured" : "none"} (read-only)
          </p>
        </fieldset>

        {saveError && (
          <p role="alert" style={{ color: "var(--cme-sell-red)", fontSize: 12 }}>
            {saveError}
          </p>
        )}

        <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
          <button className="btn-cme btn-outline btn-sm" onClick={onClose}>
            Cancel
          </button>
          <button
            className="btn-cme btn-sm"
            onClick={() => void save()}
            disabled={saving}
          >
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}
