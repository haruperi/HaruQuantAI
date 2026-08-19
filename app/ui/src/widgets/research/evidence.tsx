/**
 * Shared presentation primitives for Research evidence (FEAT-UI-28).
 *
 * These components render values the backend already decided. They add no
 * calculation beyond layout arithmetic (bar widths, cell scaling), and every
 * status carries a text label as well as a colour so colour is never the only
 * cue.
 */

"use client";

import type { ReactNode } from "react";

import type { ResearchWarning } from "@/clients";

import {
  type EvidenceTone,
  STATE_LABELS,
  STATE_TONES,
  asNumber,
  asText,
  formatNumber,
  groupWarnings,
  severityTone,
} from "./research-selectors";

/** A titled section with optional description and actions. */
export function Section({
  title,
  description,
  actions,
  children,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
}): ReactNode {
  return (
    <section className="research-section">
      <header className="research-section__head">
        <div>
          <h3>{title}</h3>
          {description ? <p>{description}</p> : null}
        </div>
        {actions ? <div className="research-section__actions">{actions}</div> : null}
      </header>
      {children}
    </section>
  );
}

/** A small labelled status badge. The label always carries the meaning. */
export function Badge({
  tone,
  children,
  title,
}: {
  tone: EvidenceTone;
  children: ReactNode;
  title?: string;
}): ReactNode {
  return (
    <span className={`research-badge research-badge--${tone}`} title={title}>
      {children}
    </span>
  );
}

/** Badge rendering one explicit stage or run state. */
export function StateBadge({ state }: { state: string }): ReactNode {
  return (
    <Badge tone={STATE_TONES[state] ?? "neutral"}>
      {STATE_LABELS[state] ?? state}
    </Badge>
  );
}

/**
 * Explicit non-success evidence state.
 *
 * Each state reads differently on purpose: a stage the caller did not select
 * is not the same as one the run has not reached, and neither is the same as
 * one Research could not produce.
 */
export function EvidenceState({
  state,
  reason,
  stageLabel,
}: {
  state: string;
  reason?: string | null;
  stageLabel?: string;
}): ReactNode {
  const messages: Record<string, string> = {
    queued: "This run is queued. Evidence appears once the stage runs.",
    running: "This stage is still running.",
    not_selected: "This stage was not selected for this run.",
    unavailable: "Research produced no evidence for this stage.",
    partial: "Only part of this stage's evidence is available.",
    failed: "This run failed before the stage produced evidence.",
    cancelled: "This run was cancelled before the stage completed.",
    stale: "This evidence is stale relative to the current run.",
  };
  return (
    <div className="research-empty" role="status">
      <StateBadge state={state} />
      <p>{messages[state] ?? "No evidence is available for this stage."}</p>
      {stageLabel ? <p className="research-empty__hint">{stageLabel}</p> : null}
      {reason ? <code className="research-empty__reason">{reason}</code> : null}
    </div>
  );
}

/** A definition grid of label/value pairs. */
export function KeyValues({
  items,
  columns = 3,
}: {
  items: ReadonlyArray<readonly [string, ReactNode]>;
  columns?: number;
}): ReactNode {
  return (
    <dl
      className="research-kv"
      style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}
    >
      {items.map(([label, value]) => (
        <div key={label} className="research-kv__item">
          <dt>{label}</dt>
          <dd>{value ?? "—"}</dd>
        </div>
      ))}
    </dl>
  );
}

/** A bounded, scrollable evidence table. */
export function EvidenceTable({
  columns,
  rows,
  caption,
  emptyLabel = "No rows",
}: {
  columns: readonly string[];
  rows: ReadonlyArray<ReadonlyArray<ReactNode>>;
  caption?: string;
  emptyLabel?: string;
}): ReactNode {
  if (rows.length === 0) {
    return <p className="research-note">{emptyLabel}</p>;
  }
  return (
    <div className="research-table-wrap">
      <table className="research-table">
        {caption ? <caption>{caption}</caption> : null}
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column} scope="col">
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {row.map((cell, cellIndex) => (
                <td key={cellIndex}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** A horizontal contribution bar with its numeric value alongside. */
export function ContributionBar({
  label,
  value,
  maximum,
  tone = "neutral",
  display,
}: {
  label: string;
  value: number | null;
  maximum: number;
  tone?: EvidenceTone;
  display?: string;
}): ReactNode {
  const safeMax = maximum > 0 ? maximum : 1;
  const width =
    value === null ? 0 : Math.max(0, Math.min(100, (Math.abs(value) / safeMax) * 100));
  return (
    <div className="research-bar">
      <span className="research-bar__label">{label}</span>
      <span className="research-bar__track" aria-hidden="true">
        <span
          className={`research-bar__fill research-bar__fill--${tone}`}
          style={{ width: `${width}%` }}
        />
      </span>
      <span className="research-bar__value">
        {display ?? (value === null ? "—" : formatNumber(value, 2))}
      </span>
    </div>
  );
}

/** A confidence-interval strip showing lower, point, and upper values. */
export function IntervalBar({
  lower,
  upper,
  point,
  label,
}: {
  lower: number | null;
  upper: number | null;
  point?: number | null;
  label: string;
}): ReactNode {
  if (lower === null || upper === null) {
    return (
      <div className="research-interval">
        <span className="research-interval__label">{label}</span>
        <span className="research-interval__value">Interval unavailable</span>
      </div>
    );
  }
  const span = upper - lower || 1;
  const marker = point === null || point === undefined ? null : ((point - lower) / span) * 100;
  const crossesZero = lower <= 0 && upper >= 0;
  return (
    <div className="research-interval">
      <span className="research-interval__label">{label}</span>
      <span className="research-interval__track" aria-hidden="true">
        <span className="research-interval__span" />
        {marker === null ? null : (
          <span
            className="research-interval__marker"
            style={{ left: `${Math.max(0, Math.min(100, marker))}%` }}
          />
        )}
      </span>
      <span className="research-interval__value">
        [{formatNumber(lower)}, {formatNumber(upper)}]
      </span>
      <Badge tone={crossesZero ? "warning" : "positive"}>
        {crossesZero ? "Includes zero" : "Excludes zero"}
      </Badge>
    </div>
  );
}

/** A CSS-grid heatmap over an arbitrary row/column evidence matrix. */
export function Heatmap({
  rowLabels,
  columnLabels,
  values,
  caption,
  format = (value) => formatNumber(value, 2),
}: {
  rowLabels: readonly string[];
  columnLabels: readonly string[];
  values: ReadonlyArray<ReadonlyArray<number | null>>;
  caption?: string;
  format?: (value: number) => string;
}): ReactNode {
  const flat = values.flat().filter((value): value is number => value !== null);
  if (flat.length === 0) {
    return <p className="research-note">No heatmap evidence available.</p>;
  }
  const min = Math.min(...flat);
  const max = Math.max(...flat);
  const span = max - min || 1;
  return (
    <figure className="research-heatmap">
      {caption ? <figcaption>{caption}</figcaption> : null}
      <div
        className="research-heatmap__grid"
        style={{
          gridTemplateColumns: `auto repeat(${columnLabels.length}, minmax(28px, 1fr))`,
        }}
      >
        <span className="research-heatmap__corner" />
        {columnLabels.map((column) => (
          <span key={column} className="research-heatmap__col">
            {column}
          </span>
        ))}
        {rowLabels.map((row, rowIndex) => (
          <FragmentRow
            key={row}
            row={row}
            cells={values[rowIndex] ?? []}
            min={min}
            span={span}
            format={format}
          />
        ))}
      </div>
      <div className="research-heatmap__scale">
        <span>{format(min)}</span>
        <span className="research-heatmap__ramp" aria-hidden="true" />
        <span>{format(max)}</span>
      </div>
    </figure>
  );
}

/** One heatmap row. Split out so each cell keeps a stable key. */
function FragmentRow({
  row,
  cells,
  min,
  span,
  format,
}: {
  row: string;
  cells: ReadonlyArray<number | null>;
  min: number;
  span: number;
  format: (value: number) => string;
}): ReactNode {
  return (
    <>
      <span className="research-heatmap__row">{row}</span>
      {cells.map((cell, index) => (
        <span
          key={`${row}-${index}`}
          className={`research-heatmap__cell${cell === null ? " research-heatmap__cell--empty" : ""}`}
          style={
            cell === null
              ? undefined
              : { opacity: 0.2 + ((cell - min) / span) * 0.8 }
          }
          title={cell === null ? "unavailable" : format(cell)}
        >
          {cell === null ? "·" : format(cell)}
        </span>
      ))}
    </>
  );
}

/** A percentile strip summarising a null distribution. */
export function DistributionStrip({
  minimum,
  maximum,
  observed,
  percentile,
  label,
}: {
  minimum: number | null;
  maximum: number | null;
  observed: number | null;
  percentile: number | null;
  label: string;
}): ReactNode {
  if (minimum === null || maximum === null) {
    return <p className="research-note">{label}: null distribution unavailable.</p>;
  }
  const span = maximum - minimum || 1;
  const marker =
    observed === null ? null : ((observed - minimum) / span) * 100;
  return (
    <div className="research-distribution">
      <span className="research-distribution__label">{label}</span>
      <span className="research-distribution__track" aria-hidden="true">
        {marker === null ? null : (
          <span
            className="research-distribution__marker"
            style={{ left: `${Math.max(0, Math.min(100, marker))}%` }}
          />
        )}
      </span>
      <span className="research-distribution__value">
        observed {formatNumber(observed)} · percentile {formatNumber(percentile, 2)}
      </span>
    </div>
  );
}

/** Warnings grouped by Research-supplied severity. */
export function WarningList({
  warnings,
  emptyLabel = "No warnings reported.",
}: {
  warnings: readonly ResearchWarning[];
  emptyLabel?: string;
}): ReactNode {
  if (warnings.length === 0) {
    return <p className="research-note">{emptyLabel}</p>;
  }
  return (
    <div className="research-warnings">
      {groupWarnings(warnings).map((group) => (
        <div key={group.severity} className="research-warnings__group">
          <Badge tone={severityTone(group.severity)}>
            {group.severity} · {group.items.length}
          </Badge>
          <ul>
            {group.items.map((warning, index) => (
              <li key={`${warning.code}-${index}`}>
                <code>{warning.code}</code> {warning.message}
                {warning.field_path ? (
                  <span className="research-warnings__path"> ({warning.field_path})</span>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

/** Render an arbitrary evidence record as a two-column table. */
export function RecordTable({
  record,
  emptyLabel = "No evidence supplied.",
}: {
  record: Record<string, unknown> | null;
  emptyLabel?: string;
}): ReactNode {
  const entries = Object.entries(record ?? {}).filter(
    ([key]) => key !== "warnings" && key !== "schema_version"
  );
  if (entries.length === 0) {
    return <p className="research-note">{emptyLabel}</p>;
  }
  return (
    <EvidenceTable
      columns={["Field", "Value"]}
      rows={entries.map(([key, value]) => [
        <code key={`${key}-k`}>{key}</code>,
        <EvidenceValue key={`${key}-v`} value={value} />,
      ])}
    />
  );
}

/** Render one unknown evidence value without inventing a shape for it. */
export function EvidenceValue({ value }: { value: unknown }): ReactNode {
  if (value === null || value === undefined) return <span>—</span>;
  const numeric = asNumber(value);
  if (numeric !== null && typeof value !== "string") {
    return <span className="is-mono">{formatNumber(numeric)}</span>;
  }
  const text = asText(value);
  if (text !== null) return <span>{text}</span>;
  if (Array.isArray(value)) {
    return <span className="is-mono">{`[${value.length} items]`}</span>;
  }
  return (
    <details className="research-nested">
      <summary>object</summary>
      <pre>{JSON.stringify(value, null, 2)}</pre>
    </details>
  );
}

/** A simple accessible tab strip driven by caller state. */
export function TabStrip({
  tabs,
  active,
  onSelect,
  label,
}: {
  tabs: ReadonlyArray<{ id: string; label: string }>;
  active: string;
  onSelect: (id: string) => void;
  label: string;
}): ReactNode {
  return (
    <div className="research-tabs" role="tablist" aria-label={label}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          id={`research-tab-${tab.id}`}
          aria-selected={tab.id === active}
          aria-controls={`research-tabpanel-${tab.id}`}
          className={`research-tab${tab.id === active ? " research-tab--active" : ""}`}
          onClick={() => onSelect(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

/** Panel body bound to a tab in `TabStrip`. */
export function TabPanel({
  id,
  active,
  children,
}: {
  id: string;
  active: string;
  children: ReactNode;
}): ReactNode {
  if (id !== active) return null;
  return (
    <div
      role="tabpanel"
      id={`research-tabpanel-${id}`}
      aria-labelledby={`research-tab-${id}`}
      className="research-tabpanel"
    >
      {children}
    </div>
  );
}
