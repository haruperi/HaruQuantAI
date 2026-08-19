"use client";

import { useMemo } from "react";

import styles from "./market-ticks.module.css";
import { useMarketSnapshots } from "./useMarketSnapshots";

function formatAge(ageMs: number): string {
  if (ageMs < 0) return `${Math.abs(ageMs)} ms future`;
  if (ageMs < 1_000) return `${ageMs} ms`;
  return `${(ageMs / 1_000).toFixed(1)} s`;
}

function formatPrice(value: unknown, digits: number): string {
  if (value === null || value === undefined) return "—";
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric.toFixed(digits) : "—";
}

function formatSpreadPoints(value: unknown, digits: number): string {
  const numeric = Number(value);
  if (!Number.isFinite(numeric) || numeric <= 0) return "0";
  return String(Math.round(numeric * 10 ** digits));
}

/** Like-for-like diagnostic view of the one-second MT5 snapshot stream. */
export function MarketTicksTableWidget(): React.JSX.Element {
  const { snapshot, status, error } = useMarketSnapshots();
  const rows = useMemo(
    () =>
      (snapshot?.quotes ?? []).map((quote) => {
        const timestamp = String(quote.time ?? "");
        const tickTime = new Date(timestamp);
        const ageMs = Number.isNaN(tickTime.getTime())
          ? 0
          : Date.now() - tickTime.getTime();
        return {
          symbol: String(quote.symbol ?? ""),
          digits: Number(quote.digits ?? 5),
          bid: quote.bid,
          ask: quote.ask,
          spread: quote.spread,
          last: quote.last,
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
              <th>Spread (pts)</th><th>Last</th><th>Broker tick time</th>
              <th>Age</th><th>Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const future = row.ageMs < 0;
              const stale = snapshot?.stale === true || row.ageMs > 5_000;
              return (
                <tr key={`${snapshot?.sourceId}:${row.symbol}`}>
                  <td>{snapshot?.sourceId}</td>
                  <td className={styles.symbol}>{row.symbol}</td>
                  <td className={styles.number}>{formatPrice(row.bid, row.digits)}</td>
                  <td className={styles.number}>{formatPrice(row.ask, row.digits)}</td>
                  <td className={styles.number}>{formatSpreadPoints(row.spread, row.digits)}</td>
                  <td className={styles.number}>{formatPrice(row.last, row.digits)}</td>
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
              <tr><td className={styles.empty} colSpan={9}>No MT5 snapshots received yet. Start or attach the EA.</td></tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </section>
  );
}
