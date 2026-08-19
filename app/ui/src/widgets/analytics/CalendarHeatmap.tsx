/**
 * Analytics calendar heatmap primitive (FEAT-UI-32).
 *
 * Renders one Analytics-owned calendar section as a grid of cells. Cell colour
 * is a presentation of the owner's own value; the component computes no
 * aggregate, average, or ranking of its own.
 */

"use client";

import { useMemo, type ReactNode } from "react";

import type { AnalyticsWorkbenchSection } from "@/clients";
import { EVIDENCE_UNAVAILABLE_TEXT } from "./AnalyticsEvidenceState";

/**
 * Resolve one owner value as a finite number.
 *
 * Null, undefined, empty, and booleans return null rather than coercing to
 * zero, so absent owner evidence is never plotted as a real observation.
 */
function numeric(value: unknown): number | null {
  if (value === null || value === undefined || value === "") return null;
  if (typeof value === "boolean") return null;
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

/** Props accepted by `CalendarHeatmap`. */
export interface CalendarHeatmapProps {
  section: AnalyticsWorkbenchSection | null | undefined;
  title: string;
  labelKey?: string;
  valueKey?: string;
  className?: string;
}

/** Owner-supplied calendar activity rendered as a bounded cell grid. */
export function CalendarHeatmap({
  section,
  title,
  labelKey = "date",
  valueKey = "value",
  className = "",
}: CalendarHeatmapProps): ReactNode {
  const cells = useMemo(() => {
    if (!section || section.status !== "completed") return [];
    return section.items.map((item, index) => ({
      key: `${String(item[labelKey] ?? index)}`,
      label: String(item[labelKey] ?? ""),
      value: numeric(item[valueKey]),
    }));
  }, [section, labelKey, valueKey]);

  const extent = useMemo(() => {
    const values = cells
      .map((cell) => cell.value)
      .filter((value): value is number => value !== null);
    if (values.length === 0) return null;
    return { min: Math.min(...values), max: Math.max(...values) };
  }, [cells]);

  if (!section || section.status === "unavailable") {
    return (
      <figure className={`analytics-heatmap ${className}`.trim()}>
        <figcaption>{title}</figcaption>
        <p className="analytics-evidence__unavailable">
          {section?.reason ?? EVIDENCE_UNAVAILABLE_TEXT}
        </p>
      </figure>
    );
  }

  return (
    <figure className={`analytics-heatmap ${className}`.trim()}>
      <figcaption>{title}</figcaption>
      <p className="analytics-chart__declaration">
        Source: {section.key} · Unit: {section.unit ?? "unspecified"} · Samples:{" "}
        {section.sample_count}
        {section.truncated
          ? ` · Truncated to ${section.items.length} of ${section.total_count}`
          : " · Not truncated"}
      </p>

      {cells.length > 0 ? (
        <ul className="analytics-heatmap__grid">
          {cells.map((cell) => {
            const intensity =
              cell.value !== null && extent && extent.max !== extent.min
                ? (cell.value - extent.min) / (extent.max - extent.min)
                : null;
            return (
              <li
                key={cell.key}
                className={
                  cell.value === null
                    ? "analytics-heatmap__cell is-unavailable"
                    : "analytics-heatmap__cell"
                }
                style={
                  intensity === null
                    ? undefined
                    : { opacity: 0.25 + intensity * 0.75 }
                }
                title={`${cell.label}: ${cell.value ?? "unavailable"}`}
              >
                <span className="sr-only">
                  {cell.label}: {cell.value ?? "unavailable"}
                </span>
              </li>
            );
          })}
        </ul>
      ) : (
        <p>No calendar cell was supplied.</p>
      )}

      <details className="analytics-chart__table">
        <summary>Show {title} as a table</summary>
        <table>
          <thead>
            <tr>
              <th scope="col">{labelKey}</th>
              <th scope="col">{valueKey}</th>
            </tr>
          </thead>
          <tbody>
            {cells.map((cell) => (
              <tr key={cell.key}>
                <td>{cell.label || "—"}</td>
                <td>{cell.value === null ? "Unavailable" : String(cell.value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  );
}
