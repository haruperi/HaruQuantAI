/**
 * Market Structure panel (FEAT-UI-28, plan §10.11).
 *
 * Replaces the V1 mega-page with focused tabs over the market-structure
 * evidence Research published: score inputs, geometry parameters,
 * distribution, breakout and excursion evidence, regimes, advisory strategy
 * fit, quality, forward validation, and calibration. The score and verdict are
 * rendered, never recomputed.
 */

"use client";

import { useState, type ReactNode } from "react";

import {
  Badge,
  ContributionBar,
  EvidenceTable,
  KeyValues,
  RecordTable,
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
  formatDuration,
  formatNumber,
  formatScore,
} from "../research-selectors";
import type { PanelProps } from "./OverviewPanel";

const VERDICT_TONES: Record<string, "positive" | "warning" | "neutral"> = {
  trending: "positive",
  ranging: "neutral",
  mixed: "warning",
};

const GEOMETRY_FIELDS = new Set([
  "swing_points",
  "trend_legs",
  "geometry_point_limit",
  "geometry_total_points",
  "geometry_truncated",
]);

/** Explicit note for evidence the report does not publish. */
function NotPublished({ what }: { what: string }): ReactNode {
  return (
    <p className="research-note">
      The registered report does not publish {what} for this run. Nothing is
      inferred here in its place.
    </p>
  );
}

/** Market-structure evidence. */
export function MarketStructurePanel({ view }: PanelProps): ReactNode {
  const [tab, setTab] = useState("overview");
  const stage = evidenceBranch(view, "market_structure");
  const structure = evidenceRecord(stage, "structure");
  const strategyFit = evidenceRecord(stage, "strategy_fit");
  const quality = evidenceRecord(stage, "quality");
  const calibration = evidenceRecord(stage, "calibration");
  const validation = evidenceRecord(stage, "validation");
  const realized = evidenceRecord(validation, "realized");
  const summary = evidenceRecord(validation, "summary");
  const verdict = asText(stage?.verdict) ?? "—";
  const score = asNumber(stage?.score);

  if (stage === null) {
    return (
      <p className="research-note">
        The market-structure stage did not run for this run, so no structure
        evidence exists.
      </p>
    );
  }

  const structureRows = Object.entries(structure ?? {}).filter(
    ([key]) => !GEOMETRY_FIELDS.has(key),
  );
  const swingPoints = evidenceArray(structure, "swing_points") as Array<
    Record<string, unknown>
  >;
  const trendLegs = evidenceArray(structure, "trend_legs") as Array<
    Record<string, unknown>
  >;
  const geometryPublished =
    structure !== null &&
    Array.isArray(structure.swing_points) &&
    Array.isArray(structure.trend_legs);

  return (
    <div className="research-panel">
      <TabStrip
        label="Market structure"
        active={tab}
        onSelect={setTab}
        tabs={[
          { id: "overview", label: "Overview" },
          { id: "score", label: "Score inputs" },
          { id: "geometry", label: "Geometry" },
          { id: "distribution", label: "Distribution" },
          { id: "breakout", label: "Breakout & excursions" },
          { id: "regimes", label: "Regimes" },
          { id: "fit", label: "Strategy fit" },
          { id: "quality", label: "Quality" },
          { id: "validation", label: "Validation" },
          { id: "calibration", label: "Calibration" },
        ]}
      />

      <TabPanel id="overview" active={tab}>
        <Section
          title="Structure verdict"
          description="The canonical score and verdict Research published."
        >
          <KeyValues
            columns={4}
            items={[
              [
                "Verdict",
                <Badge key="v" tone={VERDICT_TONES[verdict] ?? "unknown"}>
                  {verdict}
                </Badge>,
              ],
              [
                "Score",
                <span key="s" className="is-mono">
                  {formatScore(score)}
                </span>,
              ],
              ["Schema", asText(stage.schema_version) ?? "—"],
              [
                "Efficiency ratio",
                formatNumber(structure?.efficiency_ratio, 4),
              ],
            ]}
          />
          <ContributionBar
            label="Structure score (0–100)"
            value={score}
            maximum={100}
            tone={
              VERDICT_TONES[verdict] === "positive" ? "positive" : "neutral"
            }
          />
        </Section>
      </TabPanel>

      <TabPanel id="score" active={tab}>
        <Section
          title="Score inputs"
          description="Every input Research used to reach the canonical score."
        >
          <EvidenceTable
            columns={["Input", "Value"]}
            emptyLabel="No score inputs were published."
            rows={structureRows.map(([key, value]) => [
              <code key={key}>{key}</code>,
              <span key={`${key}-v`} className="is-mono">
                {formatNumber(value, 6)}
              </span>,
            ])}
          />
        </Section>
      </TabPanel>

      <TabPanel id="geometry" active={tab}>
        <Section
          title="Geometry parameters"
          description="The swing and ATR policy the profile was computed under."
        >
          <KeyValues
            columns={3}
            items={[
              ["Swing window", formatNumber(structure?.swing_window, 0)],
              ["ATR period", formatNumber(structure?.atr_period, 0)],
              ["ATR", formatNumber(structure?.atr, 6)],
              ["Trend threshold", formatNumber(structure?.trend_threshold, 4)],
              ["Range threshold", formatNumber(structure?.range_threshold, 4)],
              [
                "Reversal ATR multiple",
                formatNumber(structure?.reversal_atr_multiple, 4),
              ],
            ]}
          />
          {geometryPublished ? (
            <>
              <KeyValues
                columns={3}
                items={[
                  ["Published swings", formatNumber(swingPoints.length, 0)],
                  [
                    "Detected swings",
                    formatNumber(structure.geometry_total_points, 0),
                  ],
                  [
                    "Series status",
                    <Badge
                      key="geometry-status"
                      tone={
                        structure.geometry_truncated ? "warning" : "positive"
                      }
                    >
                      {structure.geometry_truncated ? "truncated" : "complete"}
                    </Badge>,
                  ],
                ]}
              />
              <div className="research-two-up">
                <EvidenceTable
                  caption="Confirmed swing points"
                  columns={["Position", "Timestamp", "Kind", "Price"]}
                  emptyLabel="Research published no confirmed swings for this window."
                  rows={swingPoints.map((point) => [
                    formatNumber(point.position, 0),
                    asText(point.timestamp) ?? "â€”",
                    <Badge key={`${point.position}-kind`} tone="neutral">
                      {asText(point.kind) ?? "unknown"}
                    </Badge>,
                    formatNumber(point.price, 6),
                  ])}
                />
                <EvidenceTable
                  caption="Directional trend legs"
                  columns={[
                    "From",
                    "To",
                    "Direction",
                    "Bars",
                    "Change",
                    "ATR multiple",
                  ]}
                  emptyLabel="Research published no directional legs for this window."
                  rows={trendLegs.map((leg) => [
                    formatNumber(leg.start_position, 0),
                    formatNumber(leg.end_position, 0),
                    <Badge
                      key={`${leg.start_position}-${leg.end_position}`}
                      tone="neutral"
                    >
                      {asText(leg.direction) ?? "unknown"}
                    </Badge>,
                    formatNumber(leg.bar_count, 0),
                    formatNumber(leg.price_change, 6),
                    formatNumber(leg.atr_multiple, 4),
                  ])}
                />
              </div>
            </>
          ) : (
            <NotPublished what="per-swing points or trend-leg series" />
          )}
        </Section>
      </TabPanel>

      <TabPanel id="distribution" active={tab}>
        <Section
          title="Distribution and tails"
          description="Distribution evidence the profile carries."
        >
          <RecordTable
            record={evidenceRecord(stage, "distribution")}
            emptyLabel="The report publishes no separate distribution branch for this run."
          />
        </Section>
      </TabPanel>

      <TabPanel id="breakout" active={tab}>
        <Section
          title="Breakout and excursions"
          description="Follow-through, failure, retest, and MFE/MAE evidence."
        >
          <RecordTable
            record={evidenceRecord(stage, "breakout")}
            emptyLabel="The report publishes no separate breakout branch for this run."
          />
          <RecordTable
            record={evidenceRecord(stage, "excursions")}
            emptyLabel="The report publishes no separate excursion branch for this run."
          />
        </Section>
      </TabPanel>

      <TabPanel id="regimes" active={tab}>
        <Section
          title="Regimes"
          description="Regime evidence and conditioned metrics, where the report publishes them."
        >
          <EvidenceTable
            columns={["Window", "Score"]}
            emptyLabel="No stability windows were published; enable market-structure quality to produce them."
            rows={(
              evidenceArray(
                evidenceRecord(quality, "stability"),
                "windows",
              ) as Array<Record<string, unknown>>
            ).map((row) => [
              formatNumber(row.window, 0),
              formatNumber(row.score, 4),
            ])}
          />
        </Section>
      </TabPanel>

      <TabPanel id="fit" active={tab}>
        <Section
          title="Strategy fit"
          description="Advisory archetype fit. No promotion or trading action is offered here."
        >
          <KeyValues
            columns={3}
            items={[
              [
                "Primary archetype",
                asText(strategyFit?.primary_archetype) ?? "—",
              ],
              ["Fit score", formatNumber(strategyFit?.score, 3)],
              [
                "Advisory only",
                <Badge key="a" tone="warning">
                  yes
                </Badge>,
              ],
            ]}
          />
          <RecordTable
            record={strategyFit}
            emptyLabel="No strategy fit published."
          />
        </Section>
      </TabPanel>

      <TabPanel id="quality" active={tab}>
        <Section
          title="Stability and robustness"
          description="Opt-in quality evidence. When it is disabled, Research says so rather than reporting an empty result as a pass."
        >
          <KeyValues
            columns={3}
            items={[
              [
                "Quality enabled",
                <Badge key="q" tone={quality?.enabled ? "positive" : "unknown"}>
                  {quality?.enabled ? "enabled" : "disabled"}
                </Badge>,
              ],
              ["Duration", formatDuration(asNumber(quality?.duration_ms))],
              [
                "Robustness score std",
                formatNumber(
                  evidenceRecord(quality, "robustness")?.score_std,
                  6,
                ),
              ],
            ]}
          />
          <div className="research-two-up">
            <EvidenceTable
              caption="Stability windows"
              columns={["Window", "Score"]}
              emptyLabel="No stability windows were published."
              rows={(
                evidenceArray(
                  evidenceRecord(quality, "stability"),
                  "windows",
                ) as Array<Record<string, unknown>>
              ).map((row) => [
                formatNumber(row.window, 0),
                formatNumber(row.score, 4),
              ])}
            />
            <RecordTable
              record={evidenceRecord(quality, "robustness")}
              emptyLabel="No robustness evidence."
            />
          </div>
        </Section>
      </TabPanel>

      <TabPanel id="validation" active={tab}>
        <Section
          title="Forward validation"
          description="Realized behaviour over the declared validation horizon, and the aggregate summary."
        >
          <KeyValues
            columns={4}
            items={[
              ["Symbol", asText(realized?.symbol) ?? "—"],
              ["Timeframe", asText(realized?.timeframe) ?? "—"],
              ["Horizon", formatNumber(realized?.horizon, 0)],
              [
                "Realized verdict",
                <Badge key="rv" tone="neutral">
                  {asText(realized?.verdict) ?? "—"}
                </Badge>,
              ],
              ["Samples", formatNumber(realized?.sample_count, 0)],
              [
                "Mean forward return",
                formatNumber(realized?.mean_forward_return, 6),
              ],
              [
                "Median volatility",
                formatNumber(realized?.median_volatility, 6),
              ],
              ["Mean confidence", formatNumber(summary?.mean_confidence, 4)],
            ]}
          />
          <RecordTable
            record={evidenceRecord(summary, "by_verdict")}
            emptyLabel="No verdict counts were published."
          />
        </Section>
      </TabPanel>

      <TabPanel id="calibration" active={tab}>
        <Section
          title="Calibration"
          description="Candidate ranking and the current profile, as Research reported them."
        >
          <RecordTable
            record={calibration}
            emptyLabel="No calibration evidence was published."
          />
        </Section>
      </TabPanel>

      <Section
        title="Warnings"
        description="Warnings raised by market-structure analysis."
      >
        <WarningList warnings={view.warnings} />
      </Section>
    </div>
  );
}
