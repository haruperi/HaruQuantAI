/**
 * Analytics distribution chart primitive (FEAT-UI-32).
 *
 * Renders an Analytics-owned histogram or distribution section as bars. Bucket
 * boundaries and counts come from the owner: this component never bins, never
 * normalises, and never estimates a density of its own.
 */

"use client";

import { useId, useMemo, type ReactNode } from "react";

import type { AnalyticsWorkbenchSection } from "@/clients";
import { EVIDENCE_UNAVAILABLE_TEXT } from "./AnalyticsEvidenceState";

const VIEW_WIDTH = 720;
const VIEW_HEIGHT = 200;
const PADDING = 8;

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

/** Props accepted by `DistributionChart`. */
export interface DistributionChartProps {
  section: AnalyticsWorkbenchSection | null | undefined;
  title: string;
  bucketKey?: string;
  countKey?: string;
  className?: string;
}

/** Owner-supplied bucket counts rendered as a bar chart. */
export function DistributionChart({
  section,
  title,
  bucketKey = "bucket",
  countKey = "count",
  className = "",
}: DistributionChartProps): ReactNode {
  const titleId = useId();

  const bars = useMemo(() => {
    if (!section || section.status !== "completed") return [];
    return section.items
      .map((item, index) => ({
        key: `${String(item[bucketKey] ?? index)}`,
        label: String(item[bucketKey] ?? ""),
        count: numeric(item[countKey]),
      }))
      .filter((bar) => bar.count !== null) as {
      key: string;
      label: string;
      count: number;
    }[];
  }, [section, bucketKey, countKey]);

  const maxCount = useMemo(
    () => (bars.length > 0 ? Math.max(...bars.map((bar) => bar.count)) : 0),
    [bars],
  );

  if (!section || section.status === "unavailable") {
    return (
      <figure className={`analytics-distribution ${className}`.trim()}>
        <figcaption>{title}</figcaption>
        <p className="analytics-evidence__unavailable">
          {section?.reason ?? EVIDENCE_UNAVAILABLE_TEXT}
        </p>
      </figure>
    );
  }

  return (
    <figure className={`analytics-distribution ${className}`.trim()}>
      <figcaption id={titleId}>{title}</figcaption>
      <p className="analytics-chart__declaration">
        Source: {section.key} · Unit: {section.unit ?? "unspecified"} · Samples:{" "}
        {section.sample_count}
        {section.truncated
          ? ` · Truncated to ${section.items.length} of ${section.total_count}`
          : " · Not truncated"}
      </p>

      {bars.length > 0 && maxCount > 0 ? (
        <svg
          viewBox={`0 0 ${VIEW_WIDTH} ${VIEW_HEIGHT}`}
          role="img"
          aria-labelledby={titleId}
          preserveAspectRatio="none"
          className="analytics-chart__svg"
        >
          {bars.map((bar, index) => {
            const width = (VIEW_WIDTH - PADDING * 2) / bars.length;
            const height =
              (bar.count / maxCount) * (VIEW_HEIGHT - PADDING * 2);
            return (
              <rect
                key={bar.key}
                x={PADDING + index * width}
                y={VIEW_HEIGHT - PADDING - height}
                width={Math.max(1, width - 1)}
                height={height}
                fill="currentColor"
              />
            );
          })}
        </svg>
      ) : (
        <p>No bucket count was supplied.</p>
      )}

      <details className="analytics-chart__table">
        <summary>Show {title} as a table</summary>
        <table>
          <thead>
            <tr>
              <th scope="col">{bucketKey}</th>
              <th scope="col">{countKey}</th>
            </tr>
          </thead>
          <tbody>
            {section.items.map((item, index) => (
              <tr key={`${String(item[bucketKey] ?? index)}`}>
                <td>{String(item[bucketKey] ?? "—")}</td>
                <td>{String(item[countKey] ?? "—")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  );
}
