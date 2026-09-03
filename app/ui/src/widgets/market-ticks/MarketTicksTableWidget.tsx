"use client";

import { useMemo } from "react";

import styles from "./market-ticks.module.css";
import type { MarketSnapshotView, SnapshotStatus } from "./useMarketSnapshots";

/** Presentation props owned by the FEAT-UI-25 feature adapter. */
export interface MarketTicksPresentationProps {
  readonly snapshot: MarketSnapshotView | null;
  readonly status: SnapshotStatus;
  readonly error: string | null;
  readonly staleRowAfterSeconds: number;
}

function formatAge(ageMs: number): string {
  if (ageMs < 0) return `${Math.abs(ageMs)} ms future`;
  if (ageMs < 1_000) return `${ageMs} ms`;
  return `${(ageMs / 1_000).toFixed(1)} s`;
}

/** Render one wire value exactly as served; never invent a price. */
function formatWireValue(value: unknown): string {
  return typeof value === "string" && value.length > 0 ? value : "—";
}

/** Decimal places of one wire price string. */
function decimalScale(value: unknown): number {
  if (typeof value !== "string") return 0;
  const match = /\.(\d+)$/.exec(value);
  return match === null ? 0 : match[1].length;
}

/** Spread derived arithmetically from the served bid/ask pair. */
function formatSpread(bid: unknown, ask: unknown): string {
  if (typeof bid !== "string" || typeof ask !== "string") return "—";
  const bidNumber = Number(bid);
  const askNumber = Number(ask);
  if (!Number.isFinite(bidNumber) || !Number.isFinite(askNumber)) return "—";
  return (askNumber - bidNumber).toFixed(
    Math.max(decimalScale(bid), decimalScale(ask)),
  );
}

/** Focused presentation of the latest market tick observations. */
export function MarketTicksTableWidget({
  snapshot,
  status,
  error,
  staleRowAfterSeconds,
}: MarketTicksPresentationProps): React.JSX.Element {
  const rows = useMemo(
    () =>
      (snapshot?.quotes ?? []).map((quote) => {
        const timestamp = String(quote.timestamp ?? "");
        const tickTime = new Date(timestamp);
        const ageMs = Number.isNaN(tickTime.getTime())
          ? 0
          : Date.now() - tickTime.getTime();
        return {
          symbol: String(quote.symbol ?? ""),
          bid: quote.bid,
          ask: quote.ask,
          spread: formatSpread(quote.bid, quote.ask),
          tickTime,
          ageMs,
        };
      }),
    [snapshot],
  );

  return (
    <section className={styles.panel} aria-live="polite">
      <div className={styles.toolbar}>
        <div>
          <h2>Latest quotes</h2>
          <p>One latest MT5 quote per configured symbol, refreshed once per second.</p>
        </div>
        <span className={`${styles.badge} ${styles[status]}`}>{status}</span>
      </div>

      {error ? <p className={styles.error} role="alert">{error}</p> : null}

      {snapshot ? (
        <div className={styles.sourceSummary}>
          <article className={styles.sourceCard}>
            <div>
              <strong>{snapshot.sourceId}</strong>
              <span className={`${styles.state} ${snapshot.stale ? styles.stale : styles.live}`}>
                {snapshot.stale ? "stale" : "live"}
              </span>
            </div>
            <small>sequence {snapshot.sequence} · gaps {snapshot.gap}</small>
          </article>
        </div>
      ) : null}

      <div className={styles.tableScroll}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Source</th><th>Symbol</th><th>Bid</th><th>Ask</th>
              <th>Spread</th><th>Broker tick time</th>
              <th>Age</th><th>Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const future = row.ageMs < 0;
              const stale =
                snapshot?.stale === true ||
                row.ageMs > staleRowAfterSeconds * 1_000;
              return (
                <tr key={`${snapshot?.sourceId}:${row.symbol}`}>
                  <td>{snapshot?.sourceId}</td>
                  <td className={styles.symbol}>{row.symbol}</td>
                  <td className={styles.number}>{formatWireValue(row.bid)}</td>
                  <td className={styles.number}>{formatWireValue(row.ask)}</td>
                  <td className={styles.number}>{row.spread}</td>
                  <td><time dateTime={row.tickTime.toISOString()}>{row.tickTime.toLocaleTimeString()}</time></td>
                  <td>{formatAge(row.ageMs)}</td>
                  <td>
                    <span className={`${styles.state} ${stale || future ? styles.stale : styles.live}`}>
                      {future ? "clock skew" : stale ? "stale" : "live"}
                    </span>
                  </td>
                </tr>
              );
            })}
            {rows.length === 0 ? (
              <tr><td className={styles.empty} colSpan={8}>No MT5 snapshots received yet. Start or attach the EA.</td></tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </section>
  );
}
