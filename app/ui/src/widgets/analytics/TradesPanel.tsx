/**
 * Analytics trade ledger panel (FEAT-UI-32).
 *
 * Pages and filters the canonical Simulation trade ledger entirely on the
 * server. The panel sorts, filters, and counts nothing locally: the page it
 * renders is exactly the page the owner returned.
 */

"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";
import Link from "next/link";

import {
  ApiClientError,
  apiClients,
  type TradePage,
  type TradeSide,
  type TradeSort,
} from "@/clients";

/** Default server page size for the trade ledger. */
export const TRADES_PAGE_SIZE = 50;

/** Resolve a failure message without implying a successful read. */
function failureMessage(cause: unknown): string {
  if (cause instanceof ApiClientError || cause instanceof Error) {
    return cause.message;
  }
  return "The canonical trade ledger is unavailable.";
}

/** Render one optional owner value, or a dash. */
function cell(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  return String(value);
}

/** Props accepted by `TradesPanel`. */
export interface TradesPanelProps {
  runId: string;
  className?: string;
}

/** Server-paginated canonical trade ledger for one run. */
export function TradesPanel({
  runId,
  className = "",
}: TradesPanelProps): ReactNode {
  const [page, setPage] = useState(1);
  const [side, setSide] = useState<TradeSide>("all");
  const [sort, setSort] = useState<TradeSort>("exit_time_desc");
  const [symbol, setSymbol] = useState("");
  const [data, setData] = useState<TradePage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClients.analyticsWorkbench.getTrades(runId, {
        page,
        page_size: TRADES_PAGE_SIZE,
        sort,
        side,
        ...(symbol.trim() ? { symbol: symbol.trim() } : {}),
      });
      if (response.status === "error") {
        setError(response.error.message);
        return;
      }
      setData(response.data);
    } catch (cause) {
      setError(failureMessage(cause));
    } finally {
      setLoading(false);
    }
  }, [runId, page, sort, side, symbol]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <section
      className={`analytics-trades ${className}`.trim()}
      aria-label="Canonical trade ledger"
    >
      <div className="analytics-trades__filters">
        <label htmlFor="trades-side">Direction</label>
        <select
          id="trades-side"
          value={side}
          onChange={(event) => {
            setSide(event.target.value as TradeSide);
            setPage(1);
          }}
        >
          <option value="all">All</option>
          <option value="buy">Long</option>
          <option value="sell">Short</option>
        </select>

        <label htmlFor="trades-sort">Sort</label>
        <select
          id="trades-sort"
          value={sort}
          onChange={(event) => {
            setSort(event.target.value as TradeSort);
            setPage(1);
          }}
        >
          <option value="exit_time_desc">Exit time, newest first</option>
          <option value="exit_time_asc">Exit time, oldest first</option>
        </select>

        <label htmlFor="trades-symbol">Symbol</label>
        <input
          id="trades-symbol"
          value={symbol}
          onChange={(event) => {
            setSymbol(event.target.value);
            setPage(1);
          }}
        />
      </div>

      {error ? <p role="alert">{error}</p> : null}
      {loading ? <p role="status">Loading trade ledger…</p> : null}

      {data ? (
        <>
          <p className="analytics-trades__count">
            {data.total_trades} closed trades · page {data.page} of{" "}
            {data.total_pages}
          </p>

          <table className="analytics-trades__table">
            <caption className="sr-only">Canonical closed trades</caption>
            <thead>
              <tr>
                <th scope="col">Ticket</th>
                <th scope="col">Symbol</th>
                <th scope="col">Side</th>
                <th scope="col">Volume</th>
                <th scope="col">Entry time</th>
                <th scope="col">Entry price</th>
                <th scope="col">Exit time</th>
                <th scope="col">Exit price</th>
                <th scope="col">Commission</th>
                <th scope="col">Swap</th>
                <th scope="col">PnL</th>
                <th scope="col">MAE</th>
                <th scope="col">MFE</th>
                <th scope="col">Bars held</th>
                <th scope="col">Reason</th>
              </tr>
            </thead>
            <tbody>
              {data.trades.map((trade) => (
                <tr key={trade.ticket}>
                  <td>
                    <Link
                      href={`/workstation/analytics/${encodeURIComponent(runId)}/trades/${encodeURIComponent(trade.ticket)}`}
                    >
                      {trade.ticket}
                    </Link>
                  </td>
                  <td>{cell(trade.symbol)}</td>
                  <td>{cell(trade.side)}</td>
                  <td>{cell(trade.volume)}</td>
                  <td>{cell(trade.entry_time)}</td>
                  <td>{cell(trade.entry_price)}</td>
                  <td>{cell(trade.exit_time)}</td>
                  <td>{cell(trade.exit_price)}</td>
                  <td>{cell(trade.commission)}</td>
                  <td>{cell(trade.swap)}</td>
                  <td>{cell(trade.pnl)}</td>
                  <td>{cell(trade.mae)}</td>
                  <td>{cell(trade.mfe)}</td>
                  <td>{cell(trade.bars_held)}</td>
                  <td>{cell(trade.reason)}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <nav className="analytics-trades__pager" aria-label="Trade ledger pages">
            <button
              type="button"
              onClick={() => setPage((current) => Math.max(1, current - 1))}
              disabled={data.page <= 1 || loading}
            >
              Previous page
            </button>
            <span>
              Page {data.page} of {data.total_pages}
            </span>
            <button
              type="button"
              onClick={() => setPage((current) => current + 1)}
              disabled={data.page >= data.total_pages || loading}
            >
              Next page
            </button>
          </nav>
        </>
      ) : null}
    </section>
  );
}
