/**
 * Seasonality panel (FEAT-UI-28, plan §10.10).
 *
 * Full V1 parity across six tabs — intraday bias, hour × day heatmaps,
 * calendar, sessions, opportunity windows, and the evidence table — drawn
 * entirely from the seasonality evidence Research published. The heatmaps are
 * CSS grids and the bias line is inline SVG: no second charting stack is added.
 */

"use client";

import { useMemo, useState, type ReactNode } from "react";

import {
  Badge,
  EvidenceTable,
  Heatmap,
  KeyValues,
  Section,
  TabPanel,
  TabStrip,
  WarningList,
} from "../evidence";
import {
  asNumber,
  asText,
  evidenceArray,
  evidenceBranch,
  evidenceRecord,
  formatNumber,
} from "../research-selectors";
import type { PanelProps } from "./OverviewPanel";

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const HEATMAP_MEASURES = [
  { id: "mean_return", label: "Mean return" },
  { id: "mean_range", label: "Range" },
  { id: "mean_volume", label: "Activity / volume" },
  { id: "win_rate", label: "Win rate" },
  { id: "mean_spread", label: "Spread" },
] as const;

/** A compact SVG line of the intraday bias by hour. */
function BiasLine({
  rows,
  measure,
}: {
  rows: ReadonlyArray<Record<string, unknown>>;
  measure: string;
}): ReactNode {
  const points = rows
    .map((row) => ({ hour: asNumber(row.hour), value: asNumber(row[measure]) }))
    .filter(
      (row): row is { hour: number; value: number } =>
        row.hour !== null && row.value !== null
    )
    .sort((a, b) => a.hour - b.hour);
  if (points.length < 2) {
    return <p className="research-note">Not enough hourly buckets to plot a bias line.</p>;
  }
  const values = points.map((point) => point.value);
  const min = Math.min(...values, 0);
  const max = Math.max(...values, 0);
  const span = max - min || 1;
  const width = 720;
  const height = 160;
  const step = width / (points.length - 1);
  const path = points
    .map((point, index) => {
      const x = index * step;
      const y = height - ((point.value - min) / span) * height;
      return `${index === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  const zeroY = height - ((0 - min) / span) * height;

  return (
    <figure className="research-chart">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={`Intraday ${measure} by hour`}
        preserveAspectRatio="none"
      >
        <line
          x1={0}
          x2={width}
          y1={zeroY}
          y2={zeroY}
          className="research-chart__zero"
        />
        <path d={path} className="research-chart__line" />
      </svg>
      <figcaption>
        Hours {points[0].hour}–{points[points.length - 1].hour} ·{" "}
        {formatNumber(min, 6)} to {formatNumber(max, 6)}
      </figcaption>
    </figure>
  );
}

/** Session-aware seasonality evidence. */
export function SeasonalityPanel({ view }: PanelProps): ReactNode {
  const [tab, setTab] = useState("intraday");
  const [measure, setMeasure] = useState<string>("mean_return");
  const stage = evidenceBranch(view, "seasonality");
  const sessions = evidenceArray(stage, "sessions") as Array<Record<string, unknown>>;
  const hours = evidenceArray(stage, "hours") as Array<Record<string, unknown>>;
  const matrix = evidenceArray(stage, "hour_by_weekday") as Array<
    Record<string, unknown>
  >;
  const calendar = evidenceRecord(stage, "calendar");
  const extremes = evidenceRecord(stage, "extremes");
  const dailyExtremes = evidenceRecord(stage, "daily_extremes");
  const opportunity = evidenceRecord(stage, "opportunity");

  const heatmap = useMemo(() => {
    const hourLabels = [...new Set(matrix.map((row) => asNumber(row.hour) ?? -1))]
      .filter((hour) => hour >= 0)
      .sort((a, b) => a - b);
    const weekdayIndices = [
      ...new Set(matrix.map((row) => asNumber(row.weekday) ?? -1)),
    ]
      .filter((day) => day >= 0)
      .sort((a, b) => a - b);
    const values = weekdayIndices.map((weekday) =>
      hourLabels.map((hour) => {
        const cell = matrix.find(
          (row) =>
            asNumber(row.weekday) === weekday && asNumber(row.hour) === hour
        );
        return cell ? asNumber(cell[measure]) : null;
      })
    );
    return {
      rowLabels: weekdayIndices.map((day) => WEEKDAYS[day] ?? `d${day}`),
      columnLabels: hourLabels.map((hour) => String(hour).padStart(2, "0")),
      values,
    };
  }, [matrix, measure]);

  if (stage === null) {
    return (
      <p className="research-note">
        The seasonality stage did not run for this run, so no seasonal evidence
        exists.
      </p>
    );
  }

  const calendarTable = (key: string, label: string): ReactNode => (
    <EvidenceTable
      caption={label}
      columns={[label, "Samples", "Mean return", "Win rate"]}
      emptyLabel={`No ${label.toLowerCase()} buckets were published.`}
      rows={(evidenceArray(calendar, key) as Array<Record<string, unknown>>).map(
        (row) => [
          formatNumber(row[key], 0),
          formatNumber(row.sample_count, 0),
          formatNumber(row.mean_return, 6),
          formatNumber(row.win_rate, 3),
        ]
      )}
    />
  );

  return (
    <div className="research-panel">
      <TabStrip
        label="Seasonality"
        active={tab}
        onSelect={setTab}
        tabs={[
          { id: "intraday", label: "Intraday bias" },
          { id: "heatmaps", label: "Hour × day" },
          { id: "calendar", label: "Calendar" },
          { id: "sessions", label: "Sessions" },
          { id: "opportunity", label: "Opportunity" },
          { id: "evidence", label: "Evidence table" },
        ]}
      />

      <TabPanel id="intraday" active={tab}>
        <Section
          title="Intraday bias"
          description="Per-hour buckets exactly as Research aggregated them."
          actions={
            <label className="research-inline-field">
              Measure
              <select
                value={measure}
                onChange={(event) => setMeasure(event.target.value)}
              >
                {HEATMAP_MEASURES.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>
          }
        >
          <BiasLine rows={hours} measure={measure} />
          <EvidenceTable
            columns={[
              "Hour",
              "Samples",
              "Mean return",
              "Win rate",
              "Range",
              "Volume",
              "Spread",
            ]}
            emptyLabel="No hourly buckets were published."
            rows={hours.map((row) => [
              String(asNumber(row.hour) ?? "—").padStart(2, "0"),
              formatNumber(row.sample_count, 0),
              formatNumber(row.mean_return, 6),
              formatNumber(row.win_rate, 3),
              formatNumber(row.mean_range, 5),
              formatNumber(row.mean_volume, 2),
              formatNumber(row.mean_spread, 5),
            ])}
          />
        </Section>
      </TabPanel>

      <TabPanel id="heatmaps" active={tab}>
        <Section
          title="Hour × day heatmap"
          description="One cell per weekday and hour. Empty cells are marked, not filled with zero."
          actions={
            <label className="research-inline-field">
              Measure
              <select
                value={measure}
                onChange={(event) => setMeasure(event.target.value)}
              >
                {HEATMAP_MEASURES.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>
          }
        >
          <Heatmap
            caption={
              HEATMAP_MEASURES.find((item) => item.id === measure)?.label ?? measure
            }
            rowLabels={heatmap.rowLabels}
            columnLabels={heatmap.columnLabels}
            values={heatmap.values}
            format={(value) => formatNumber(value, 4)}
          />
        </Section>
      </TabPanel>

      <TabPanel id="calendar" active={tab}>
        <Section
          title="Calendar seasonality"
          description="Year, month, day-of-month, and day-of-week buckets."
        >
          <div className="research-two-up">
            {calendarTable("year", "Year")}
            {calendarTable("month", "Month")}
          </div>
          <div className="research-two-up">
            {calendarTable("day_of_month", "Day of month")}
            {calendarTable("day_of_week", "Day of week")}
          </div>
        </Section>
      </TabPanel>

      <TabPanel id="sessions" active={tab}>
        <Section
          title="Session summary"
          description="Per-session movement and dispersion, plus daily high/low ownership."
        >
          <EvidenceTable
            columns={["Session", "Samples", "Mean return", "Win rate", "Std return"]}
            emptyLabel="No session buckets were published."
            rows={sessions.map((row) => [
              asText(row.session) ?? "—",
              formatNumber(row.sample_count, 0),
              formatNumber(row.mean_return, 6),
              formatNumber(row.win_rate, 3),
              formatNumber(row.std_return, 6),
            ])}
          />
          <div className="research-two-up">
            <EvidenceTable
              caption={`Daily high ownership (${formatNumber(dailyExtremes?.day_count, 0)} days)`}
              columns={["Session", "Days"]}
              emptyLabel="No high ownership evidence."
              rows={(
                evidenceArray(dailyExtremes, "high_ownership") as Array<
                  Record<string, unknown>
                >
              ).map((row) => [asText(row.session) ?? "—", formatNumber(row.days, 0)])}
            />
            <EvidenceTable
              caption="Daily low ownership"
              columns={["Session", "Days"]}
              emptyLabel="No low ownership evidence."
              rows={(
                evidenceArray(dailyExtremes, "low_ownership") as Array<
                  Record<string, unknown>
                >
              ).map((row) => [asText(row.session) ?? "—", formatNumber(row.days, 0)])}
            />
          </div>
        </Section>
      </TabPanel>

      <TabPanel id="opportunity" active={tab}>
        <Section
          title="Opportunity windows"
          description="The best and dead windows Research identified, and the observed extremes."
        >
          <KeyValues
            columns={4}
            items={[
              [
                "Best session",
                <Badge key="bs" tone="positive">
                  {asText(opportunity?.session) ?? "—"}
                </Badge>,
              ],
              [
                "Best session mean return",
                formatNumber(opportunity?.mean_return, 6),
              ],
              [
                "Dead session",
                <Badge key="ds" tone="warning">
                  {asText(opportunity?.dead_session) ?? "—"}
                </Badge>,
              ],
              [
                "Dead session mean return",
                formatNumber(opportunity?.dead_session_mean_return, 6),
              ],
              ["Best hour", formatNumber(opportunity?.best_hour, 0)],
              [
                "Best hour mean return",
                formatNumber(opportunity?.best_hour_mean_return, 6),
              ],
              ["Dead hour", formatNumber(opportunity?.dead_hour, 0)],
              [
                "Dead hour mean return",
                formatNumber(opportunity?.dead_hour_mean_return, 6),
              ],
              ["Max observed return", formatNumber(extremes?.max_return, 6)],
              ["Min observed return", formatNumber(extremes?.min_return, 6)],
              ["ADR period", formatNumber(stage.adr_period, 0)],
              ["Rows analysed", formatNumber(stage.row_count, 0)],
            ]}
          />
        </Section>
      </TabPanel>

      <TabPanel id="evidence" active={tab}>
        <Section
          title="Evidence table"
          description="The hour × weekday cells behind the heatmap, bounded to what the server returned."
        >
          <EvidenceTable
            columns={[
              "Weekday",
              "Hour",
              "Samples",
              "Mean return",
              "Win rate",
              "Range",
              "Volume",
              "Spread",
            ]}
            emptyLabel="No matrix cells were published."
            rows={matrix.map((row) => [
              WEEKDAYS[asNumber(row.weekday) ?? -1] ?? "—",
              String(asNumber(row.hour) ?? "—").padStart(2, "0"),
              formatNumber(row.sample_count, 0),
              formatNumber(row.mean_return, 6),
              formatNumber(row.win_rate, 3),
              formatNumber(row.mean_range, 5),
              formatNumber(row.mean_volume, 2),
              formatNumber(row.mean_spread, 5),
            ])}
          />
        </Section>
      </TabPanel>

      <Section title="Warnings" description="Sparse-bucket and tagging warnings.">
        <WarningList warnings={view.warnings} />
      </Section>
    </div>
  );
}
