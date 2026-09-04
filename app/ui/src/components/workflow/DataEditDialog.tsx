/**
 * Governed "Edit symbol" dialog for market series and linked instrument specifications.
 * Faithfully matches StrategyQuant QuantDataManager's Edit Symbol dialog.
 */

"use client";

import React, {
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import { X, PlusCircle, HelpCircle } from "lucide-react";

import {
  ApiClientError,
  apiClients,
  unwrapData,
  type MarketSeriesRow,
  type SeriesUpdateBody,
} from "@/clients";

function adjustValue(
  valStr: string,
  delta: number,
  step: number = 1,
  min?: number,
  max?: number
): string {
  const current = Number(valStr);
  const num = Number.isFinite(current) ? current : 0;
  let next = num + delta;
  if (min !== undefined && next < min) next = min;
  if (max !== undefined && next > max) next = max;

  const stepStr = String(step);
  const decimals = stepStr.includes(".") ? stepStr.split(".")[1].length : 0;
  return next.toFixed(decimals);
}

function adjustHour(hourStr: string, delta: number): string {
  const [hStr, mStr] = (hourStr || "23:00").split(":");
  let h = Number(hStr);
  if (!Number.isFinite(h)) h = 23;
  h = (h + delta + 24) % 24;
  const m = Number(mStr) || 0;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

function numberOrNull(value: string): number | null {
  if (!value || value.trim() === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

/** Number Stepper with inline [-] and [+] decrement/increment buttons. */
function StepperInput({
  id,
  ariaLabel,
  value,
  onChange,
  step = 1,
  min,
  max,
  suffix,
  width = "100%",
  disabled = false,
}: {
  id?: string;
  ariaLabel?: string;
  value: string;
  onChange: (val: string) => void;
  step?: number;
  min?: number;
  max?: number;
  suffix?: string;
  width?: number | string;
  disabled?: boolean;
}) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          width,
          height: 26,
          background: disabled ? "#f8fafc" : "#ffffff",
          border: "1px solid #cbd5e1",
          borderRadius: 2,
          overflow: "hidden",
          opacity: disabled ? 0.7 : 1,
        }}
      >
        <input
          id={id}
          aria-label={ariaLabel}
          type="text"
          value={value}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
          style={{
            flex: 1,
            height: "100%",
            border: "none",
            outline: "none",
            padding: "0 6px",
            fontSize: 12,
            fontFamily: "inherit",
            color: "#1e293b",
            background: "transparent",
            minWidth: 0,
          }}
        />
        <button
          type="button"
          disabled={disabled}
          onClick={() => onChange(adjustValue(value, -step, step, min, max))}
          style={{
            width: 18,
            height: "100%",
            border: "none",
            borderLeft: "1px solid #cbd5e1",
            background: "#f1f5f9",
            color: "#475569",
            fontSize: 13,
            fontWeight: 600,
            cursor: disabled ? "not-allowed" : "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            userSelect: "none",
          }}
        >
          −
        </button>
        <button
          type="button"
          disabled={disabled}
          onClick={() => onChange(adjustValue(value, step, step, min, max))}
          style={{
            width: 18,
            height: "100%",
            border: "none",
            borderLeft: "1px solid #cbd5e1",
            background: "#f1f5f9",
            color: "#475569",
            fontSize: 13,
            fontWeight: 600,
            cursor: disabled ? "not-allowed" : "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            userSelect: "none",
          }}
        >
          +
        </button>
      </div>
      {suffix && (
        <span style={{ fontSize: 11, color: "#475569", whiteSpace: "nowrap" }}>
          {suffix}
        </span>
      )}
    </div>
  );
}

/** Time Stepper for rollout hour (e.g. 23:00) with [-] and [+] */
function TimeStepperInput({
  id,
  ariaLabel,
  value,
  onChange,
  width = 160,
  disabled = false,
}: {
  id?: string;
  ariaLabel?: string;
  value: string;
  onChange: (val: string) => void;
  width?: number | string;
  disabled?: boolean;
}) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        width,
        height: 26,
        background: disabled ? "#f8fafc" : "#ffffff",
        border: "1px solid #cbd5e1",
        borderRadius: 2,
        overflow: "hidden",
        opacity: disabled ? 0.7 : 1,
      }}
    >
      <input
        id={id}
        aria-label={ariaLabel}
        type="text"
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        style={{
          flex: 1,
          height: "100%",
          border: "none",
          outline: "none",
          padding: "0 6px",
          fontSize: 12,
          fontFamily: "inherit",
          color: "#1e293b",
          background: "transparent",
        }}
      />
      <button
        type="button"
        disabled={disabled}
        onClick={() => onChange(adjustHour(value, -1))}
        style={{
          width: 18,
          height: "100%",
          border: "none",
          borderLeft: "1px solid #cbd5e1",
          background: "#f1f5f9",
          color: "#475569",
          fontSize: 13,
          fontWeight: 600,
          cursor: disabled ? "not-allowed" : "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          userSelect: "none",
        }}
      >
        −
      </button>
      <button
        type="button"
        disabled={disabled}
        onClick={() => onChange(adjustHour(value, 1))}
        style={{
          width: 18,
          height: "100%",
          border: "none",
          borderLeft: "1px solid #cbd5e1",
          background: "#f1f5f9",
          color: "#475569",
          fontSize: 13,
          fontWeight: 600,
          cursor: disabled ? "not-allowed" : "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          userSelect: "none",
        }}
      >
        +
      </button>
    </div>
  );
}

/** Toggle switch for Swap Use */
function ToggleSwitch({
  id,
  ariaLabel,
  checked,
  onChange,
  label,
}: {
  id?: string;
  ariaLabel?: string;
  checked: boolean;
  onChange: (val: boolean) => void;
  label?: string;
}) {
  return (
    <label style={{ display: "inline-flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
      <input
        id={id}
        aria-label={ariaLabel || label}
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        style={{ position: "absolute", opacity: 0, pointerEvents: "none", width: 0, height: 0 }}
      />
      <div
        onClick={() => onChange(!checked)}
        style={{
          width: 36,
          height: 18,
          borderRadius: 9,
          background: checked ? "#2563eb" : "#cbd5e1",
          position: "relative",
          transition: "background 0.15s ease",
        }}
      >
        <div
          style={{
            width: 14,
            height: 14,
            borderRadius: "50%",
            background: "#ffffff",
            position: "absolute",
            top: 2,
            left: 2,
            transform: checked ? "translateX(18px)" : "none",
            transition: "transform 0.15s ease",
            boxShadow: "0 1px 2px rgba(0,0,0,0.2)",
          }}
        />
      </div>
      {label && <span style={{ fontSize: 12, color: "#334155", fontWeight: 500 }}>{label}</span>}
    </label>
  );
}

export interface DataEditDialogProps {
  row: MarketSeriesRow;
  onClose: () => void;
  onSaved: () => void;
}

export function DataEditDialog({
  row,
  onClose,
  onSaved,
}: DataEditDialogProps): ReactNode {
  // Available instrument specifications
  const [availableInstruments, setAvailableInstruments] = useState<string[]>([]);
  const [specError, setSpecError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Section 1: Data Settings
  const [symbol, setSymbol] = useState(row.symbol);
  const [timezone, setTimezone] = useState(
    row.timezone || "(UTC) Coordinated Universal Time, DST: No"
  );

  // Section 2: Choose Instrument
  const [instrument, setInstrument] = useState(row.instrument ?? "EURUSD");
  const [brokerProfileFilter, setBrokerProfileFilter] = useState("All broker profiles");
  const [isAddingInstrument, setIsAddingInstrument] = useState(false);
  const [newInstrumentName, setNewInstrumentName] = useState("");

  // Section 3: Instrument Details
  const [brokerProfile, setBrokerProfile] = useState("SQ default");
  const [dataType, setDataType] = useState("Forex");
  const [description, setDescription] = useState("");
  const [tickSize, setTickSize] = useState("0.0001");
  const [pointValue, setPointValue] = useState("100000");
  const [tickStep, setTickStep] = useState("0.00001");
  const [defaultSpread, setDefaultSpread] = useState("2");
  const [defaultSlippage, setDefaultSlippage] = useState("0");
  const [minDistance, setMinDistance] = useState("0");
  const [orderSizeMultiplier, setOrderSizeMultiplier] = useState("1");
  const [orderSizeStep, setOrderSizeStep] = useState("0");

  // Section 4: Swap
  const [useSwap, setUseSwap] = useState(false);
  const [swapType, setSwapType] = useState<"money" | "points" | "percentage">("money");
  const [swapLong, setSwapLong] = useState("0");
  const [swapShort, setSwapShort] = useState("0");
  const [tripleSwapOn, setTripleSwapOn] = useState("WEDNESDAY");
  const [rolloutHour, setRolloutHour] = useState("23:00");

  // Load available instruments list from database
  useEffect(() => {
    let cancelled = false;
    async function loadInstruments() {
      try {
        const res = await apiClients.data.instruments();
        const list = unwrapData(res).instruments.map((i) => i.instrument);
        if (!cancelled && list.length > 0) {
          setAvailableInstruments(list);
          if (!list.includes(instrument)) {
            setAvailableInstruments((prev) => [instrument, ...prev]);
          }
        }
      } catch {
        // Fallback
        if (!cancelled && !availableInstruments.includes(instrument)) {
          setAvailableInstruments([instrument]);
        }
      }
    }
    void loadInstruments();
    return () => {
      cancelled = true;
    };
  }, [instrument]);

  // Load specific instrument spec from database
  const loadSpec = useCallback(async (targetInstrument: string) => {
    if (!targetInstrument) return;
    try {
      setSpecError(null);
      const res = await apiClients.data.instrument(targetInstrument);
      const loaded = unwrapData(res);

      setDescription(loaded.description ?? targetInstrument);
      setBrokerProfile(loaded.broker_profile || "SQ default");
      setDataType(loaded.data_type ? String(loaded.data_type) : "Forex");
      setTickSize(loaded.tick_size !== null && loaded.tick_size !== undefined ? String(loaded.tick_size) : "0.0001");
      setPointValue(loaded.point_value !== null && loaded.point_value !== undefined ? String(loaded.point_value) : "100000");
      setTickStep(loaded.tick_step !== null && loaded.tick_step !== undefined ? String(loaded.tick_step) : "0.00001");
      setDefaultSpread(loaded.default_spread !== null && loaded.default_spread !== undefined ? String(loaded.default_spread) : "2");
      setDefaultSlippage(loaded.default_slippage !== null && loaded.default_slippage !== undefined ? String(loaded.default_slippage) : "0");
      setMinDistance(loaded.min_distance !== null && loaded.min_distance !== undefined ? String(loaded.min_distance) : "0");
      setOrderSizeMultiplier(loaded.order_size_multiplier !== null && loaded.order_size_multiplier !== undefined ? String(loaded.order_size_multiplier) : "1");
      setOrderSizeStep(loaded.order_size_step !== null && loaded.order_size_step !== undefined ? String(loaded.order_size_step) : "0");

      // Swap fields
      const hasSwap = (loaded.swap_mode ?? 0) > 0;
      setUseSwap(hasSwap);
      setSwapType(loaded.swap_mode === 1 ? "points" : "money");
      setSwapLong(loaded.swap_long !== null && loaded.swap_long !== undefined ? String(loaded.swap_long) : "0");
      setSwapShort(loaded.swap_short !== null && loaded.swap_short !== undefined ? String(loaded.swap_short) : "0");
      setTripleSwapOn(
        loaded.swap_rollover3days === 1 ? "MONDAY"
        : loaded.swap_rollover3days === 2 ? "TUESDAY"
        : loaded.swap_rollover3days === 4 ? "THURSDAY"
        : loaded.swap_rollover3days === 5 ? "FRIDAY"
        : "WEDNESDAY"
      );
    } catch (reason) {
      setSpecError(reason instanceof ApiClientError ? reason.message : "Instrument details unavailable");
    }
  }, []);

  useEffect(() => {
    void loadSpec(instrument);
  }, [instrument, loadSpec]);

  const handleAddNewInstrument = () => {
    if (!newInstrumentName.trim()) return;
    const name = newInstrumentName.trim().toUpperCase();
    if (!availableInstruments.includes(name)) {
      setAvailableInstruments((prev) => [name, ...prev]);
    }
    setInstrument(name);
    setIsAddingInstrument(false);
    setNewInstrumentName("");
  };

  const handleSave = async (): Promise<void> => {
    setSaving(true);
    setSaveError(null);
    try {
      const rolloverDay =
        tripleSwapOn === "MONDAY" ? 1
        : tripleSwapOn === "TUESDAY" ? 2
        : tripleSwapOn === "WEDNESDAY" ? 3
        : tripleSwapOn === "THURSDAY" ? 4
        : 5;

      const body: SeriesUpdateBody = {
        symbol: symbol.trim(),
        instrument: instrument.trim(),
        broker_id: row.broker_id,
        timeframe: row.timeframe,
        timezone: timezone || row.timezone,
        date_from: row.date_from,
        date_to: row.date_to,
        data_type: dataType || "Forex",
        decimals: row.decimals,
        source: row.source,
        row_count: row.row_count,
        remove_weekends: row.remove_weekends ?? 0,
        show: row.show ?? 1,
        // Linked instrument specifications
        description: description.trim() || null,
        point_value: numberOrNull(pointValue),
        tick_size: numberOrNull(tickSize),
        tick_step: numberOrNull(tickStep),
        default_spread: numberOrNull(defaultSpread),
        default_slippage: numberOrNull(defaultSlippage),
        min_distance: numberOrNull(minDistance),
        order_size_multiplier: numberOrNull(orderSizeMultiplier),
        order_size_step: numberOrNull(orderSizeStep),
        // Swap specification
        swap_mode: useSwap ? (swapType === "money" ? 2 : 1) : 0,
        swap_long: numberOrNull(swapLong),
        swap_short: numberOrNull(swapShort),
        swap_rollover3days: rolloverDay,
      };

      await apiClients.data.updateSeries(row.series_id, body);
      onSaved();
    } catch (reason) {
      setSaveError(
        reason instanceof ApiClientError ? reason.message : "Failed to save symbol"
      );
      setSaving(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Edit symbol"
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0, 0, 0, 0.6)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: 620,
          maxHeight: "92vh",
          display: "flex",
          flexDirection: "column",
          borderRadius: 6,
          boxShadow: "0 10px 30px rgba(0, 0, 0, 0.4)",
          background: "#eef2f6",
          overflow: "hidden",
          border: "1px solid #cbd5e1",
        }}
      >
        {/* Top Header Bar */}
        <div
          style={{
            background: "#2563eb",
            padding: "8px 14px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            color: "#ffffff",
          }}
        >
          <div style={{ fontSize: 14, fontWeight: 600 }}>Edit symbol</div>
          <button
            onClick={onClose}
            aria-label="Close dialog"
            style={{
              background: "transparent",
              border: "none",
              color: "#ffffff",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: 2,
              borderRadius: 4,
            }}
          >
            <X size={16} />
          </button>
        </div>

        {/* Scrollable Form Body */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: 14,
            display: "flex",
            flexDirection: "column",
            gap: 12,
          }}
        >
          {saveError && (
            <div
              style={{
                padding: "8px 12px",
                background: "#fef2f2",
                border: "1px solid #fecaca",
                borderRadius: 4,
                color: "#dc2626",
                fontSize: 12,
              }}
            >
              {saveError}
            </div>
          )}

          {/* Section 1: Data settings */}
          <div
            style={{
              background: "#ffffff",
              border: "1px solid #dcdfe4",
              borderRadius: 4,
              padding: "12px 16px",
            }}
          >
            <div style={{ fontSize: 13, fontWeight: 700, color: "#334155", marginBottom: 10 }}>
              Data settings
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {/* Row 1: Data symbol name */}
              <div style={{ display: "flex", alignItems: "center" }}>
                <label
                  htmlFor="edit-data-symbol-name"
                  style={{ width: 140, fontSize: 12, color: "#334155" }}
                >
                  Data symbol name
                </label>
                <input
                  id="edit-data-symbol-name"
                  aria-label="Data symbol name"
                  type="text"
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  style={{
                    width: 220,
                    height: 26,
                    padding: "0 8px",
                    background: "#ffffff",
                    border: "1px solid #cbd5e1",
                    borderRadius: 2,
                    fontSize: 12,
                    color: "#1e293b",
                  }}
                />
              </div>

              {/* Row 2: Bar type */}
              <div style={{ display: "flex", alignItems: "center" }}>
                <label
                  htmlFor="edit-bar-type"
                  style={{ width: 140, fontSize: 12, color: "#334155" }}
                >
                  Bar type
                </label>
                <input
                  id="edit-bar-type"
                  aria-label="Bar type"
                  type="text"
                  readOnly
                  disabled
                  value="Timestamp represents start of bar time (MetaTrader, Dukascopy, forex data)"
                  style={{
                    flex: 1,
                    height: 26,
                    padding: "0 8px",
                    background: "#f8fafc",
                    border: "1px solid #e2e8f0",
                    borderRadius: 2,
                    fontSize: 11,
                    color: "#64748b",
                  }}
                />
              </div>

              {/* Row 3: Timezone */}
              <div style={{ display: "flex", alignItems: "center" }}>
                <label
                  htmlFor="edit-timezone"
                  style={{ width: 140, fontSize: 12, color: "#334155" }}
                >
                  Timezone
                </label>
                <input
                  id="edit-timezone"
                  aria-label="Timezone"
                  type="text"
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                  style={{
                    flex: 1,
                    height: 26,
                    padding: "0 8px",
                    background: "#f8fafc",
                    border: "1px solid #e2e8f0",
                    borderRadius: 2,
                    fontSize: 11,
                    color: "#475569",
                  }}
                />
              </div>
            </div>
          </div>

          {/* Section 2: Choose instrument */}
          <div
            style={{
              background: "#ffffff",
              border: "1px solid #dcdfe4",
              borderRadius: 4,
              padding: "12px 16px",
            }}
          >
            <div style={{ fontSize: 13, fontWeight: 700, color: "#334155", marginBottom: 2 }}>
              Choose instrument
            </div>
            <div
              style={{
                fontSize: 11,
                fontStyle: "italic",
                color: "#64748b",
                lineHeight: 1.4,
                marginBottom: 10,
              }}
            >
              Instrument is a specification of this symbol - it contains tick size, point value etc.
              <br />
              You can have mutiple data imported - for example EURUSD_1, EURUSD_2, EURUSD_3, but they
              share the same instrument specification for EURUSD.
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
              <label
                htmlFor="edit-choose-instrument"
                style={{ fontSize: 12, color: "#334155", fontWeight: 500 }}
              >
                Instrument *
              </label>
              <select
                id="edit-broker-filter"
                aria-label="Filter broker profiles"
                value={brokerProfileFilter}
                onChange={(e) => setBrokerProfileFilter(e.target.value)}
                style={{
                  height: 26,
                  padding: "0 8px",
                  background: "#ffffff",
                  border: "1px solid #cbd5e1",
                  borderRadius: 2,
                  fontSize: 12,
                  color: "#1e293b",
                }}
              >
                <option value="All broker profiles">All broker profiles</option>
                <option value="SQ default">SQ default</option>
                <option value="Pepperstone">Pepperstone</option>
                <option value="ICMarkets">ICMarkets</option>
              </select>

              <select
                id="edit-choose-instrument"
                aria-label="Choose instrument"
                value={instrument}
                onChange={(e) => setInstrument(e.target.value)}
                style={{
                  minWidth: 140,
                  height: 26,
                  padding: "0 8px",
                  background: "#ffffff",
                  border: "1px solid #cbd5e1",
                  borderRadius: 2,
                  fontSize: 12,
                  color: "#1e293b",
                }}
              >
                {availableInstruments.map((inst) => (
                  <option key={inst} value={inst}>
                    {inst}
                  </option>
                ))}
              </select>

              {isAddingInstrument ? (
                <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                  <input
                    type="text"
                    aria-label="New instrument name"
                    placeholder="NEW_INSTRUMENT"
                    value={newInstrumentName}
                    onChange={(e) => setNewInstrumentName(e.target.value)}
                    style={{
                      height: 24,
                      width: 120,
                      padding: "0 6px",
                      fontSize: 11,
                      border: "1px solid #cbd5e1",
                      borderRadius: 2,
                    }}
                  />
                  <button
                    type="button"
                    onClick={handleAddNewInstrument}
                    style={{
                      height: 24,
                      padding: "0 8px",
                      background: "#2563eb",
                      color: "#fff",
                      border: "none",
                      borderRadius: 2,
                      fontSize: 11,
                      cursor: "pointer",
                    }}
                  >
                    Add
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsAddingInstrument(false)}
                    style={{
                      height: 24,
                      padding: "0 6px",
                      background: "transparent",
                      color: "#64748b",
                      border: "none",
                      fontSize: 11,
                      cursor: "pointer",
                    }}
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => setIsAddingInstrument(true)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 4,
                    background: "none",
                    border: "none",
                    color: "#2563eb",
                    fontSize: 12,
                    cursor: "pointer",
                    textDecoration: "underline",
                    textUnderlineOffset: 2,
                    padding: 0,
                  }}
                >
                  <PlusCircle size={14} /> Add new instrument
                </button>
              )}
            </div>
          </div>

          {/* Section 3: Instrument Details */}
          <div
            style={{
              background: "#ffffff",
              border: "1px solid #dcdfe4",
              borderRadius: 4,
              padding: "14px 16px",
              display: "flex",
              flexDirection: "column",
              gap: 10,
            }}
          >
            {specError && (
              <div style={{ fontSize: 11, color: "#dc2626" }}>{specError}</div>
            )}

            {/* Row 1: Broker profile & Instrument */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <div>
                <label
                  htmlFor="edit-broker-profile"
                  style={{ display: "block", fontSize: 12, color: "#334155", marginBottom: 3 }}
                >
                  Broker profile *
                </label>
                <input
                  id="edit-broker-profile"
                  aria-label="Broker profile"
                  type="text"
                  disabled
                  value={brokerProfile}
                  style={{
                    width: "100%",
                    height: 26,
                    background: "#f8fafc",
                    border: "1px solid #cbd5e1",
                    borderRadius: 2,
                    padding: "0 8px",
                    fontSize: 12,
                    color: "#64748b",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              <div>
                <label
                  htmlFor="edit-instrument-name"
                  style={{ display: "block", fontSize: 12, color: "#334155", marginBottom: 3 }}
                >
                  Instrument *
                </label>
                <input
                  id="edit-instrument-name"
                  aria-label="Instrument"
                  type="text"
                  disabled
                  value={instrument}
                  style={{
                    width: "100%",
                    height: 26,
                    background: "#f8fafc",
                    border: "1px solid #cbd5e1",
                    borderRadius: 2,
                    padding: "0 8px",
                    fontSize: 12,
                    color: "#64748b",
                    boxSizing: "border-box",
                  }}
                />
              </div>
            </div>

            {/* Row 2: Data type & Description */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <div>
                <label
                  htmlFor="edit-data-type"
                  style={{ display: "block", fontSize: 12, color: "#334155", marginBottom: 3 }}
                >
                  Data type *
                </label>
                <input
                  id="edit-data-type"
                  aria-label="Data type"
                  type="text"
                  value={dataType}
                  onChange={(e) => setDataType(e.target.value)}
                  style={{
                    width: "100%",
                    height: 26,
                    background: "#ffffff",
                    border: "1px solid #cbd5e1",
                    borderRadius: 2,
                    padding: "0 8px",
                    fontSize: 12,
                    color: "#1e293b",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              <div>
                <label
                  htmlFor="edit-description"
                  style={{ display: "block", fontSize: 12, color: "#334155", marginBottom: 3 }}
                >
                  Description
                </label>
                <input
                  id="edit-description"
                  aria-label="Description"
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  style={{
                    width: "100%",
                    height: 26,
                    background: "#ffffff",
                    border: "1px solid #cbd5e1",
                    borderRadius: 2,
                    padding: "0 8px",
                    fontSize: 12,
                    color: "#1e293b",
                    boxSizing: "border-box",
                  }}
                />
              </div>
            </div>

            {/* Row 3: Pip/Tick size, Point value in $, Pip/Tick step */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
              <div>
                <label
                  htmlFor="edit-tick-size"
                  style={{ display: "block", fontSize: 12, color: "#334155", marginBottom: 3 }}
                >
                  Pip/Tick size *
                </label>
                <StepperInput
                  id="edit-tick-size"
                  ariaLabel="Pip/Tick size"
                  value={tickSize}
                  onChange={setTickSize}
                  step={0.0001}
                  min={0.000001}
                />
              </div>

              <div>
                <label
                  htmlFor="edit-point-value"
                  style={{ display: "block", fontSize: 12, color: "#334155", marginBottom: 3 }}
                >
                  Point value in $ *
                </label>
                <StepperInput
                  id="edit-point-value"
                  ariaLabel="Point value in $"
                  value={pointValue}
                  onChange={setPointValue}
                  step={1000}
                  min={1}
                />
              </div>

              <div>
                <label
                  htmlFor="edit-tick-step"
                  style={{ display: "block", fontSize: 12, color: "#334155", marginBottom: 3 }}
                >
                  Pip/Tick step *
                </label>
                <StepperInput
                  id="edit-tick-step"
                  ariaLabel="Pip/Tick step"
                  value={tickStep}
                  onChange={setTickStep}
                  step={0.00001}
                  min={0.000001}
                />
              </div>
            </div>

            {/* Row 4: Default spread, Default slippage, Min distance */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
              <div>
                <label
                  htmlFor="edit-default-spread"
                  style={{ display: "block", fontSize: 12, color: "#334155", marginBottom: 3 }}
                >
                  Default spread * pips
                </label>
                <StepperInput
                  id="edit-default-spread"
                  ariaLabel="Default spread"
                  value={defaultSpread}
                  onChange={setDefaultSpread}
                  step={1}
                  min={0}
                />
              </div>

              <div>
                <label
                  htmlFor="edit-default-slippage"
                  style={{ display: "block", fontSize: 12, color: "#334155", marginBottom: 3 }}
                >
                  Default slippage * pips
                </label>
                <StepperInput
                  id="edit-default-slippage"
                  ariaLabel="Default slippage"
                  value={defaultSlippage}
                  onChange={setDefaultSlippage}
                  step={1}
                  min={0}
                />
              </div>

              <div>
                <label
                  htmlFor="edit-min-distance"
                  style={{ display: "block", fontSize: 12, color: "#334155", marginBottom: 3 }}
                >
                  Min distance
                </label>
                <StepperInput
                  id="edit-min-distance"
                  ariaLabel="Min distance"
                  value={minDistance}
                  onChange={setMinDistance}
                  step={1}
                  min={0}
                />
              </div>
            </div>

            {/* Row 5: Order size multiplier & Order size step */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <div>
                <label
                  htmlFor="edit-order-multiplier"
                  style={{ display: "block", fontSize: 12, color: "#334155", marginBottom: 3 }}
                >
                  Order size multiplier
                </label>
                <StepperInput
                  id="edit-order-multiplier"
                  ariaLabel="Order size multiplier"
                  value={orderSizeMultiplier}
                  onChange={setOrderSizeMultiplier}
                  step={1}
                  min={0.01}
                />
              </div>

              <div>
                <label
                  htmlFor="edit-order-step"
                  style={{ display: "block", fontSize: 12, color: "#334155", marginBottom: 3 }}
                >
                  Order size step
                </label>
                <StepperInput
                  id="edit-order-step"
                  ariaLabel="Order size step"
                  value={orderSizeStep}
                  onChange={setOrderSizeStep}
                  step={0.01}
                  min={0}
                />
              </div>
            </div>
          </div>

          {/* Section 4: Swap */}
          <div
            style={{
              background: "#ffffff",
              border: "1px solid #dcdfe4",
              borderRadius: 4,
              padding: "12px 16px",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: 10,
              }}
            >
              <div style={{ fontSize: 13, fontWeight: 700, color: "#334155" }}>Swap</div>
              <button
                type="button"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 4,
                  background: "#f8fafc",
                  border: "1px solid #cbd5e1",
                  borderRadius: 4,
                  padding: "2px 8px",
                  fontSize: 11,
                  color: "#334155",
                  cursor: "pointer",
                }}
              >
                <HelpCircle size={14} color="#2563eb" /> Help
              </button>
            </div>

            {/* Toggle Switch */}
            <div style={{ marginBottom: 12 }}>
              <ToggleSwitch
                id="edit-swap-use"
                ariaLabel="Use swap"
                checked={useSwap}
                onChange={setUseSwap}
                label="Use"
              />
            </div>

            {/* Swap Form Grid */}
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {/* Swap type */}
              <div style={{ display: "flex", alignItems: "center" }}>
                <label
                  htmlFor="edit-swap-type"
                  style={{ width: 130, fontSize: 12, color: "#334155" }}
                >
                  Swap type
                </label>
                <select
                  id="edit-swap-type"
                  aria-label="Swap type"
                  disabled={!useSwap}
                  value={swapType}
                  onChange={(e) => setSwapType(e.target.value as "money" | "points" | "percentage")}
                  style={{
                    width: 160,
                    height: 26,
                    padding: "0 8px",
                    background: useSwap ? "#ffffff" : "#f8fafc",
                    border: "1px solid #cbd5e1",
                    borderRadius: 2,
                    fontSize: 12,
                    color: useSwap ? "#1e293b" : "#94a3b8",
                  }}
                >
                  <option value="money">money</option>
                  <option value="points">points</option>
                  <option value="percentage">percentage</option>
                </select>
              </div>

              {/* Long */}
              <div style={{ display: "flex", alignItems: "center" }}>
                <label
                  htmlFor="edit-swap-long"
                  style={{ width: 130, fontSize: 12, color: "#334155" }}
                >
                  Long
                </label>
                <StepperInput
                  id="edit-swap-long"
                  ariaLabel="Swap Long"
                  disabled={!useSwap}
                  value={swapLong}
                  onChange={setSwapLong}
                  step={0.1}
                  width={160}
                  suffix="$ per day"
                />
              </div>

              {/* Short */}
              <div style={{ display: "flex", alignItems: "center" }}>
                <label
                  htmlFor="edit-swap-short"
                  style={{ width: 130, fontSize: 12, color: "#334155" }}
                >
                  Short
                </label>
                <StepperInput
                  id="edit-swap-short"
                  ariaLabel="Swap Short"
                  disabled={!useSwap}
                  value={swapShort}
                  onChange={setSwapShort}
                  step={0.1}
                  width={160}
                  suffix="$ per day"
                />
              </div>

              {/* Triple swap on */}
              <div style={{ display: "flex", alignItems: "center" }}>
                <label
                  htmlFor="edit-triple-swap"
                  style={{ width: 130, fontSize: 12, color: "#334155" }}
                >
                  Triple swap on
                </label>
                <select
                  id="edit-triple-swap"
                  aria-label="Triple swap on"
                  disabled={!useSwap}
                  value={tripleSwapOn}
                  onChange={(e) => setTripleSwapOn(e.target.value)}
                  style={{
                    width: 160,
                    height: 26,
                    padding: "0 8px",
                    background: useSwap ? "#ffffff" : "#f8fafc",
                    border: "1px solid #cbd5e1",
                    borderRadius: 2,
                    fontSize: 12,
                    color: useSwap ? "#1e293b" : "#94a3b8",
                  }}
                >
                  <option value="MONDAY">MONDAY</option>
                  <option value="TUESDAY">TUESDAY</option>
                  <option value="WEDNESDAY">WEDNESDAY</option>
                  <option value="THURSDAY">THURSDAY</option>
                  <option value="FRIDAY">FRIDAY</option>
                </select>
              </div>

              {/* Rollout hour */}
              <div style={{ display: "flex", alignItems: "center" }}>
                <label
                  htmlFor="edit-rollout-hour"
                  style={{ width: 130, fontSize: 12, color: "#334155" }}
                >
                  Rollout hour
                </label>
                <TimeStepperInput
                  id="edit-rollout-hour"
                  ariaLabel="Rollout hour"
                  disabled={!useSwap}
                  value={rolloutHour}
                  onChange={setRolloutHour}
                  width={160}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div
          style={{
            padding: "10px 16px",
            background: "#eef2f6",
            borderTop: "1px solid #dcdfe4",
            display: "flex",
            alignItems: "center",
            justifyContent: "flex-end",
            gap: 16,
          }}
        >
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            style={{
              background: "transparent",
              border: "none",
              color: "#2563eb",
              fontSize: 12,
              cursor: "pointer",
              padding: "6px 10px",
              textDecoration: "underline",
              textUnderlineOffset: 2,
            }}
          >
            Close
          </button>
          <button
            type="button"
            disabled={saving}
            onClick={handleSave}
            aria-label="Save"
            style={{
              background: "#2563eb",
              color: "#ffffff",
              border: "none",
              borderRadius: 4,
              padding: "6px 20px",
              fontSize: 12,
              fontWeight: 600,
              cursor: saving ? "not-allowed" : "pointer",
              boxShadow: "0 1px 2px rgba(0,0,0,0.1)",
              opacity: saving ? 0.7 : 1,
            }}
          >
            {saving ? "Saving..." : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}
