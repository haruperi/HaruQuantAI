/**
 * Data & Quality panel (FEAT-UI-28, plan §10.5).
 *
 * Covers the V1 Data page under V2 ownership: the dataset identity, quality
 * decision, checks, cleaning actions, and provenance are Data- and
 * Research-owned fields. The preview renders the exact bounded rows the server
 * returned for this run's window — it never refetches a live series and calls
 * it the run's data. The owned Chart widget is available on demand for live
 * exploration and is labelled as live.
 */

"use client";

import { useState, type ReactNode } from "react";

import { ChartWidget } from "@/features/chart/ChartWidget";

import {
  Badge,
  EvidenceTable,
  KeyValues,
  RecordTable,
  Section,
  WarningList,
} from "../evidence";
import {
  asNumber,
  asText,
  evidenceArray,
  evidenceBranch,
  evidenceRecord,
  formatNumber,
  formatTimestamp,
  hashPrefix,
} from "../research-selectors";
import type { PanelProps } from "./OverviewPanel";

/** Bounded candlestick preview drawn from the server-supplied rows. */
function CandlePreview({
  rows,
}: {
  rows: ReadonlyArray<Record<string, unknown>>;
}): ReactNode {
  if (rows.length === 0) {
    return <p className="research-note">No preview rows were returned.</p>;
  }
  const parsed = rows
    .map((row) => ({
      timestamp: asText(row.timestamp) ?? "",
      open: asNumber(row.open),
      high: asNumber(row.high),
      low: asNumber(row.low),
      close: asNumber(row.close),
    }))
    .filter(
      (row): row is {
        timestamp: string;
        open: number;
        high: number;
        low: number;
        close: number;
      } =>
        row.open !== null &&
        row.high !== null &&
        row.low !== null &&
        row.close !== null
    );
  if (parsed.length === 0) {
    return <p className="research-note">Preview rows carried no usable prices.</p>;
  }
  const highest = Math.max(...parsed.map((row) => row.high));
  const lowest = Math.min(...parsed.map((row) => row.low));
  const span = highest - lowest || 1;
  const width = Math.max(320, parsed.length * 4);
  const height = 180;
  const step = width / parsed.length;
  const y = (value: number): number => height - ((value - lowest) / span) * height;

  return (
    <figure className="research-chart">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={`Price preview of ${parsed.length} bars from the analysed dataset`}
        preserveAspectRatio="none"
      >
        {parsed.map((row, index) => {
          const x = index * step + step / 2;
          const rising = row.close >= row.open;
          return (
            <g key={`${row.timestamp}-${index}`}>
              <line
                x1={x}
                x2={x}
                y1={y(row.high)}
                y2={y(row.low)}
                className="research-chart__wick"
              />
              <rect
                x={x - Math.max(1, step * 0.3)}
                width={Math.max(1.5, step * 0.6)}
                y={y(Math.max(row.open, row.close))}
                height={Math.max(1, Math.abs(y(row.open) - y(row.close)))}
                className={
                  rising ? "research-chart__up" : "research-chart__down"
                }
              />
            </g>
          );
        })}
      </svg>
      <figcaption>
        {parsed.length} bars from the analysed window · {formatNumber(lowest, 5)} –{" "}
        {formatNumber(highest, 5)}
      </figcaption>
    </figure>
  );
}

/** Data & Quality stage. */
export function DataQualityPanel({ detail, view }: PanelProps): ReactNode {
  const [liveChart, setLiveChart] = useState(false);
  const stage = evidenceBranch(view, "data");
  const dataset = evidenceRecord(view.evidence as Record<string, unknown>, "dataset")
    ?? (detail.dataset as unknown as Record<string, unknown> | null);
  const preview = evidenceArray(
    view.evidence as Record<string, unknown>,
    "preview"
  ) as Array<Record<string, unknown>>;
  const quality = evidenceRecord(dataset, "quality");
  const cleaning = evidenceArray(stage, "cleaning_actions") as Array<
    Record<string, unknown>
  >;
  const fatal = evidenceArray(stage, "fatal_issues") as Array<
    Record<string, unknown>
  >;
  const checks = evidenceArray(stage, "checks") as string[];
  const config = evidenceRecord(
    view.evidence as Record<string, unknown>,
    "effective_configuration"
  );

  return (
    <div className="research-panel">
      <Section
        title="Dataset identity"
        description="Resolved by the server through Data. The browser never submits market rows."
      >
        <KeyValues
          columns={4}
          items={[
            ["Symbol", asText(dataset?.symbol) ?? detail.symbol],
            ["Timeframe", asText(dataset?.timeframe) ?? detail.timeframe],
            ["Data kind", asText(dataset?.data_kind) ?? "—"],
            ["Records", formatNumber(dataset?.record_count, 0)],
            ["Range start", formatTimestamp(asText(dataset?.start))],
            ["Range end", formatTimestamp(asText(dataset?.end))],
            ["Available at", formatTimestamp(asText(dataset?.available_at))],
            ["Cache status", asText(dataset?.cache_status) ?? "—"],
            [
              "Normalization",
              asText(dataset?.normalization_version) ?? "—",
            ],
            ["Precision policy", asText(dataset?.precision_policy) ?? "—"],
            [
              "Dataset hash",
              <span key="h" className="is-mono" title={detail.dataset_hash ?? ""}>
                {hashPrefix(detail.dataset_hash)}
              </span>,
            ],
            [
              "Session basis",
              asText(config?.session_timezone) ?? "—",
            ],
          ]}
        />
      </Section>

      <Section
        title="Quality decision"
        description="Data-owned quality verdict. Research did not recompute it, and neither did this page."
      >
        {quality ? (
          <KeyValues
            columns={3}
            items={[
              [
                "Status",
                <Badge key="s" tone="neutral">
                  {asText(quality.status) ?? "—"}
                </Badge>,
              ],
              [
                "Decision",
                <Badge
                  key="d"
                  tone={
                    asText(quality.decision) === "accepted" ? "positive" : "warning"
                  }
                >
                  {asText(quality.decision) ?? "—"}
                </Badge>,
              ],
              ["Score", asText(quality.score) ?? "—"],
              ["Records", formatNumber(quality.record_count, 0)],
              ["Checked", formatNumber(quality.checked_count, 0)],
              ["Truncated", quality.truncated ? "yes" : "no"],
            ]}
          />
        ) : (
          <p className="research-note">
            No Data-owned quality report accompanied this dataset.
          </p>
        )}
        <h4>Research checks</h4>
        <div className="research-chips">
          {checks.length === 0 ? (
            <span className="research-note">No checks were published.</span>
          ) : (
            checks.map((check) => (
              <Badge key={check} tone="positive">
                {check}
              </Badge>
            ))
          )}
        </div>
      </Section>

      <Section
        title="Cleaning and fatal issues"
        description="Explicit actions Research applied, and any issue that stopped preparation."
      >
        <EvidenceTable
          columns={["Action", "Detail"]}
          emptyLabel="Research applied no cleaning actions."
          rows={cleaning.map((action, index) => [
            <code key={`a-${index}`}>{asText(action.action) ?? "action"}</code>,
            <RecordTable key={`d-${index}`} record={action} />,
          ])}
        />
        {fatal.length > 0 ? (
          <EvidenceTable
            caption="Fatal issues"
            columns={["Code", "Detail"]}
            rows={fatal.map((issue, index) => [
              <code key={`c-${index}`}>{asText(issue.code) ?? "—"}</code>,
              <RecordTable key={`i-${index}`} record={issue} />,
            ])}
          />
        ) : (
          <p className="research-note">No fatal issues were reported.</p>
        )}
      </Section>

      <Section
        title="Source and license"
        description="Provenance carried by the Data-owned dataset."
      >
        <div className="research-two-up">
          <RecordTable
            record={evidenceRecord(dataset, "source_metadata")}
            emptyLabel="No source metadata."
          />
          <RecordTable
            record={evidenceRecord(dataset, "license_metadata")}
            emptyLabel="No license metadata."
          />
        </div>
      </Section>

      <Section
        title="Analysed window preview"
        description="Bounded rows from the exact dataset this run analysed, returned by the server."
        actions={
          <button
            type="button"
            className="research-button"
            onClick={() => setLiveChart((value) => !value)}
          >
            {liveChart ? "Hide live chart" : "Open live Chart widget"}
          </button>
        }
      >
        <CandlePreview rows={preview} />
        <EvidenceTable
          caption={`First rows of the analysed window (${preview.length} returned)`}
          columns={["Timestamp", "Open", "High", "Low", "Close", "Volume", "Spread"]}
          emptyLabel="No preview rows were returned."
          rows={preview.slice(0, 25).map((row) => [
            formatTimestamp(asText(row.timestamp)),
            asText(row.open) ?? "—",
            asText(row.high) ?? "—",
            asText(row.low) ?? "—",
            asText(row.close) ?? "—",
            asText(row.volume) ?? "—",
            asText(row.spread) ?? "—",
          ])}
        />
        {liveChart ? (
          <div className="research-chart-embed">
            <p className="research-note">
              The Chart widget below shows the <strong>live</strong> series for{" "}
              {detail.symbol}, not the historical window this run analysed.
            </p>
            <ChartWidget symbol={detail.symbol} />
          </div>
        ) : null}
      </Section>

      <Section title="Warnings" description="Warnings raised while preparing the dataset.">
        <WarningList warnings={view.warnings} />
      </Section>
    </div>
  );
}
