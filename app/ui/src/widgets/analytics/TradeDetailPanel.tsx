/**
 * Analytics trade detail panel (FEAT-UI-32).
 *
 * Renders the complete owner-supplied evidence for one canonical trade and the
 * replay handoff. The replay URL carries the exact encoded return context so a
 * reviewer lands back on the trade they left.
 */

"use client";

import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import Link from "next/link";

import {
  ApiClientError,
  apiClients,
  type ClosedTradeRecord,
} from "@/clients";
import { EvidenceValue } from "./AnalyticsEvidenceState";

/** Resolve a failure message without implying a successful read. */
function failureMessage(cause: unknown): string {
  if (cause instanceof ApiClientError || cause instanceof Error) {
    return cause.message;
  }
  return "The canonical trade record is unavailable.";
}

/**
 * Build the immutable playback URL for one trade.
 *
 * The `return` parameter is the exact encoded Analytics destination the
 * reviewer came from, so playback can restore it without guessing.
 */
export function buildReplayHref(runId: string, ticket: string): string {
  const returnTo = `/workstation/analytics/${encodeURIComponent(runId)}/trades/${encodeURIComponent(ticket)}`;
  return (
    `/workstation/simulator/replay/${encodeURIComponent(runId)}` +
    `?ticket=${encodeURIComponent(ticket)}&return=${encodeURIComponent(returnTo)}`
  );
}

/** Props accepted by `TradeDetailPanel`. */
export interface TradeDetailPanelProps {
  runId: string;
  ticket: string;
  className?: string;
}

/** Complete evidence for one canonical closed trade. */
export function TradeDetailPanel({
  runId,
  ticket,
  className = "",
}: TradeDetailPanelProps): ReactNode {
  const [trade, setTrade] = useState<ClosedTradeRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClients.analyticsWorkbench.getTrade(
        runId,
        ticket,
      );
      if (response.status === "error") {
        setError(response.error.message);
        return;
      }
      setTrade(response.data);
    } catch (cause) {
      setError(failureMessage(cause));
    } finally {
      setLoading(false);
    }
  }, [runId, ticket]);

  useEffect(() => {
    void load();
  }, [load]);

  const replayHref = useMemo(
    () => buildReplayHref(runId, ticket),
    [runId, ticket],
  );

  return (
    <section
      className={`analytics-trade-detail ${className}`.trim()}
      aria-label="Trade detail"
    >
      <header>
        <h3>Trade {ticket}</h3>
        <Link href={replayHref} className="analytics-trade-detail__replay">
          Replay this trade
        </Link>
      </header>

      {loading ? <p role="status">Loading trade evidence…</p> : null}
      {error ? <p role="alert">{error}</p> : null}

      {trade ? (
        <>
          <section aria-labelledby="trade-detail-identity">
            <h4 id="trade-detail-identity">Trade evidence</h4>
            <dl className="analytics-trade-detail__grid">
              <dt>Ticket</dt>
              <dd className="font-mono">{trade.ticket}</dd>
              <dt>Symbol</dt>
              <dd>
                <EvidenceValue value={trade.symbol} />
              </dd>
              <dt>Side</dt>
              <dd>{trade.side}</dd>
              <dt>Volume</dt>
              <dd>
                <EvidenceValue value={trade.volume} />
              </dd>
              <dt>Entry</dt>
              <dd>
                {trade.entry_time} @ {String(trade.entry_price)}
              </dd>
              <dt>Exit</dt>
              <dd>
                {trade.exit_time} @ {String(trade.exit_price)}
              </dd>
              <dt>Close reason</dt>
              <dd>
                <EvidenceValue value={trade.reason} />
              </dd>
            </dl>
          </section>

          <section aria-labelledby="trade-detail-costs">
            <h4 id="trade-detail-costs">Cost breakdown</h4>
            <dl className="analytics-trade-detail__grid">
              <dt>Gross PnL</dt>
              <dd>
                <EvidenceValue value={trade.pnl} />
              </dd>
              <dt>Return</dt>
              <dd>
                <EvidenceValue value={trade.return_pct ?? trade.pnl_percent} />
              </dd>
              <dt>Commission</dt>
              <dd>
                <EvidenceValue value={trade.commission} />
              </dd>
              <dt>Swap</dt>
              <dd>
                <EvidenceValue value={trade.swap} />
              </dd>
            </dl>
          </section>

          <section aria-labelledby="trade-detail-excursions">
            <h4 id="trade-detail-excursions">Excursions and duration</h4>
            <dl className="analytics-trade-detail__grid">
              <dt>MAE</dt>
              <dd>
                <EvidenceValue value={trade.mae} />
              </dd>
              <dt>MFE</dt>
              <dd>
                <EvidenceValue value={trade.mfe} />
              </dd>
              <dt>Bars held</dt>
              <dd>
                <EvidenceValue value={trade.bars_held} />
              </dd>
              <dt>Duration (seconds)</dt>
              <dd>
                <EvidenceValue value={trade.duration_seconds} />
              </dd>
            </dl>
          </section>

          <section aria-labelledby="trade-detail-provenance">
            <h4 id="trade-detail-provenance">Provenance</h4>
            <p className="font-mono">Run: {runId}</p>
            <p>
              This trade is read from the immutable canonical Simulation result;
              the Analytics workbench derives none of its values.
            </p>
          </section>
        </>
      ) : null}
    </section>
  );
}
