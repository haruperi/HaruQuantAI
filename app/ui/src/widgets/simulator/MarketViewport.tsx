/**
 * Backwards-only market viewport (FEAT-UI-31).
 *
 * Renders the bars the server returned for one live session. The viewport is
 * strictly historical: the server never sends a row past the cursor, and this
 * component never extrapolates, forecasts, or pads one. A row the server did
 * not send is simply absent.
 */

"use client";

import { useId, useMemo, type ReactNode } from "react";

import type { MarketViewport as MarketViewportPayload } from "@/clients";

const VIEW_WIDTH = 900;
const VIEW_HEIGHT = 260;
const PADDING = 6;

/** Resolve one owner value as a finite number, or null when unusable. */
function numeric(value: unknown): number | null {
  if (value === null || value === undefined || value === "") return null;
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

/** Props accepted by `MarketViewport`. */
export interface MarketViewportProps {
  viewport: MarketViewportPayload | null;
  loading?: boolean;
  error?: string | null;
  className?: string;
}

/** Historical bar viewport for one interactive session. */
export function MarketViewport({
  viewport,
  loading = false,
  error = null,
  className = "",
}: MarketViewportProps): ReactNode {
  const titleId = useId();

  const closes = useMemo(
    () =>
      (viewport?.rows ?? [])
        .map((row) => numeric(row.close))
        .filter((value): value is number => value !== null),
    [viewport],
  );

  const path = useMemo(() => {
    if (closes.length < 2) return "";
    const min = Math.min(...closes);
    const max = Math.max(...closes);
    const span = max - min || 1;
    const step = (VIEW_WIDTH - PADDING * 2) / (closes.length - 1);
    return closes
      .map((value, index) => {
        const x = PADDING + index * step;
        const y =
          VIEW_HEIGHT -
          PADDING -
          ((value - min) / span) * (VIEW_HEIGHT - PADDING * 2);
        return `${index === 0 ? "M" : "L"}${x.toFixed(2)} ${y.toFixed(2)}`;
      })
      .join(" ");
  }, [closes]);

  return (
    <section
      className={`simulation-viewport ${className}`.trim()}
      aria-label="Market viewport"
    >
      <h4 id={titleId}>Market viewport</h4>

      {loading ? <p role="status">Loading viewport…</p> : null}
      {error ? <p role="alert">{error}</p> : null}

      {viewport ? (
        <>
          <p className="simulation-viewport__declaration">
            {viewport.rows.length} bars ending at cursor {viewport.cursor} ·
            forward rows requested: {viewport.after}
          </p>

          {path ? (
            <svg
              viewBox={`0 0 ${VIEW_WIDTH} ${VIEW_HEIGHT}`}
              role="img"
              aria-labelledby={titleId}
              preserveAspectRatio="none"
              className="simulation-viewport__svg"
            >
              <path
                d={path}
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
              />
            </svg>
          ) : (
            <p>The session has not advanced far enough to plot a series.</p>
          )}

          <details className="simulation-viewport__table">
            <summary>Show viewport rows as a table</summary>
            <table>
              <thead>
                <tr>
                  <th scope="col">Timestamp</th>
                  <th scope="col">Open</th>
                  <th scope="col">High</th>
                  <th scope="col">Low</th>
                  <th scope="col">Close</th>
                  <th scope="col">Volume</th>
                  <th scope="col">Forming</th>
                  <th scope="col">Markers</th>
                </tr>
              </thead>
              <tbody>
                {viewport.rows.map((row) => (
                  <tr key={row.timestamp}>
                    <td>{row.timestamp}</td>
                    <td>{String(row.open)}</td>
                    <td>{String(row.high)}</td>
                    <td>{String(row.low)}</td>
                    <td>{String(row.close)}</td>
                    <td>{String(row.volume)}</td>
                    <td>{row.forming ? "yes" : "no"}</td>
                    <td>{row.markers.length}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </details>
        </>
      ) : null}
    </section>
  );
}
