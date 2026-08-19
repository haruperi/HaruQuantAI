/**
 * Analytics time-series chart primitive (FEAT-UI-32).
 *
 * Plots one Analytics-owned series exactly as the owner supplied it. The chart
 * performs no smoothing, resampling, interpolation, or metric derivation: it
 * maps supplied points to pixels and nothing else. Every chart declares its
 * source payload, unit, sample count, truncation, and unavailable reason, and
 * offers the same evidence as a table.
 */

"use client";

import { useId, useMemo, type ReactNode } from "react";

import type { AnalyticsWorkbenchSection } from "@/clients";
import { EVIDENCE_UNAVAILABLE_TEXT } from "./AnalyticsEvidenceState";

/** Fixed drawing box; the chart scales responsively through its viewBox. */
const VIEW_WIDTH = 720;
const VIEW_HEIGHT = 220;
const PADDING = 8;

/** One plotted point resolved from an owner item. */
interface SeriesPoint {
  label: string;
  value: number;
}

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

/**
 * Resolve owner items into plottable points.
 *
 * An item whose value is not a finite number is skipped rather than coerced to
 * zero, so a gap in owner evidence never renders as a real observation.
 */
export function toSeriesPoints(
  items: readonly Record<string, unknown>[],
  valueKey: string,
  labelKey: string,
): SeriesPoint[] {
  const points: SeriesPoint[] = [];
  for (const item of items) {
    const value = numeric(item[valueKey]);
    if (value === null) continue;
    points.push({ label: String(item[labelKey] ?? ""), value });
  }
  return points;
}

/** Props accepted by `TimeSeriesChart`. */
export interface TimeSeriesChartProps {
  section: AnalyticsWorkbenchSection | null | undefined;
  title: string;
  valueKey?: string;
  labelKey?: string;
  className?: string;
}

/** Single-series line chart over an Analytics workbench section. */
export function TimeSeriesChart({
  section,
  title,
  valueKey = "value",
  labelKey = "timestamp",
  className = "",
}: TimeSeriesChartProps): ReactNode {
  const titleId = useId();

  const points = useMemo(
    () =>
      section && section.status === "completed"
        ? toSeriesPoints(section.items, valueKey, labelKey)
        : [],
    [section, valueKey, labelKey],
  );

  const path = useMemo(() => {
    if (points.length < 2) return "";
    const values = points.map((point) => point.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const span = max - min || 1;
    const step = (VIEW_WIDTH - PADDING * 2) / (points.length - 1);
    return points
      .map((point, index) => {
        const x = PADDING + index * step;
        const y =
          VIEW_HEIGHT -
          PADDING -
          ((point.value - min) / span) * (VIEW_HEIGHT - PADDING * 2);
        return `${index === 0 ? "M" : "L"}${x.toFixed(2)} ${y.toFixed(2)}`;
      })
      .join(" ");
  }, [points]);

  if (!section || section.status === "unavailable") {
    return (
      <figure className={`analytics-chart ${className}`.trim()}>
        <figcaption>{title}</figcaption>
        <p className="analytics-evidence__unavailable">
          {section?.reason ?? EVIDENCE_UNAVAILABLE_TEXT}
        </p>
      </figure>
    );
  }

  return (
    <figure className={`analytics-chart ${className}`.trim()}>
      <figcaption id={titleId}>{title}</figcaption>
      <p className="analytics-chart__declaration">
        Source: {section.key} · Unit: {section.unit ?? "unspecified"} · Samples:{" "}
        {section.sample_count}
        {section.truncated
          ? ` · Truncated to ${section.items.length} of ${section.total_count}`
          : " · Not truncated"}
      </p>

      {path ? (
        <svg
          viewBox={`0 0 ${VIEW_WIDTH} ${VIEW_HEIGHT}`}
          role="img"
          aria-labelledby={titleId}
          preserveAspectRatio="none"
          className="analytics-chart__svg"
        >
          <path d={path} fill="none" stroke="currentColor" strokeWidth="1.5" />
        </svg>
      ) : (
        <p>Fewer than two plottable points were supplied.</p>
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
            {section.items.map((item, index) => (
              <tr key={`${String(item[labelKey] ?? index)}`}>
                <td>{String(item[labelKey] ?? "—")}</td>
                <td>{String(item[valueKey] ?? "—")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  );
}
