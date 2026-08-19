/** Governed edit dialog for one instrument specification. */

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
  type InstrumentUpdateBody,
} from "@/clients";

/** One labelled text input inside the edit dialog. */
function Field({
  label,
  value,
  onChange,
  readOnly = false,
}: {
  label: string;
  value: string;
  onChange?: (value: string) => void;
  readOnly?: boolean;
}): ReactNode {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <span style={{ fontSize: 11, color: "var(--text-muted-grey)" }}>{label}</span>
      <input
        value={value}
        readOnly={readOnly}
        onChange={
          onChange
            ? (event: ChangeEvent<HTMLInputElement>) => onChange(event.target.value)
            : undefined
        }
        style={{
          padding: "6px 8px",
          borderRadius: 6,
          border: "1px solid var(--border-color)",
          background: "var(--cme-navy-dark)",
          color: "var(--text-light-grey)",
          fontSize: 12,
          width: "100%",
          boxSizing: "border-box",
        }}
      />
    </label>
  );
}

function numberOrNull(value: string): number | null {
  if (value.trim() === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function textOrNull(value: string): string | null {
  return value.trim() === "" ? null : value;
}

/** Modal editor prepopulated from the instrument specification. */
export function InstrumentEditDialog({
  instrumentId,
  onClose,
  onSaved,
}: {
  instrumentId: string;
  onClose: () => void;
  onSaved: () => void;
}): ReactNode {
  const [spec, setSpec] = useState<InstrumentSpec | null>(null);
  const [specError, setSpecError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

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
    async function load(): Promise<void> {
      try {
        const response = await apiClients.data.instrument(instrumentId);
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
  }, [instrumentId]);

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

  const body: InstrumentUpdateBody = useMemo(
    () => ({
      description: textOrNull(description),
      point_value: numberOrNull(pointValue),
      tick_size: numberOrNull(tickSize),
      tick_step: numberOrNull(tickStep),
      default_spread: numberOrNull(defaultSpread),
      default_slippage: numberOrNull(defaultSlippage),
      min_distance: numberOrNull(minDistance),
      order_size_multiplier: numberOrNull(orderSizeMultiplier),
      order_size_step: numberOrNull(orderSizeStep),
    }),
    [
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
      await apiClients.data.updateInstrument(instrumentId, body);
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
      aria-label={`Edit instrument ${instrumentId}`}
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
          width: 480,
          borderRadius: 10,
          border: "1px solid var(--border-color)",
          background: "var(--cme-navy-panel)",
          padding: 20,
          display: "flex",
          flexDirection: "column",
          gap: 16,
        }}
      >
        <h2 style={{ margin: 0, fontSize: 16 }}>Edit instrument</h2>

        {specError && (
          <p role="alert" style={{ color: "var(--cme-sell-red)", fontSize: 12 }}>
            {specError}
          </p>
        )}

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(2, 1fr)",
            gap: 12,
          }}
        >
          <Field label="Instrument" value={instrumentId} readOnly />
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
        <p style={{ fontSize: 11, color: "var(--text-muted-grey)", margin: 0 }}>
          Swap rules: {spec?.swap ? "configured" : "none"} (read-only)
        </p>

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
