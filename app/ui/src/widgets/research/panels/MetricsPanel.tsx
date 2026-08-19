/**
 * Metrics panel (FEAT-UI-28, plan §10.8).
 *
 * Covers V1 Core Metric with the seven canonical V2 metric families. Values,
 * units, sample sizes, and validity all come from Research; the browser sorts
 * and formats, and computes no metric.
 */

"use client";

import { useMemo, useState, type ReactNode } from "react";

import { Badge, EvidenceTable, Section, WarningList } from "../evidence";
import {
  asNumber,
  asText,
  evidenceBranch,
  evidenceRecord,
  formatNumber,
} from "../research-selectors";
import type { PanelProps } from "./OverviewPanel";

/** The seven canonical metric families, in their registered order. */
const FAMILIES = [
  "returns",
  "roc",
  "candles",
  "ranges",
  "volatility",
  "spread",
  "activity",
] as const;

const FAMILY_LABELS: Record<string, string> = {
  returns: "Returns",
  roc: "Rate of change",
  candles: "Candles",
  ranges: "Ranges",
  volatility: "Volatility",
  spread: "Spread",
  activity: "Activity",
};

type SortKey = "family" | "value" | "sample";

/** Core metric families. */
export function MetricsPanel({ view }: PanelProps): ReactNode {
  const [sort, setSort] = useState<SortKey>("family");
  const stage = evidenceBranch(view, "metrics");
  const metrics = useMemo(
    () => evidenceRecord(stage, "metrics") ?? {},
    [stage]
  );

  const rows = useMemo(() => {
    const names = new Set([...FAMILIES, ...Object.keys(metrics)]);
    const items = [...names].map((name) => {
      const entry = evidenceRecord(metrics, name);
      return {
        family: name,
        value: asNumber(entry?.value),
        unit: asText(entry?.unit),
        sample: asNumber(entry?.sample_size),
        undefinedReason: asText(entry?.undefined_reason),
        present: entry !== null,
      };
    });
    if (sort === "value") {
      return [...items].sort((a, b) => (b.value ?? -Infinity) - (a.value ?? -Infinity));
    }
    if (sort === "sample") {
      return [...items].sort((a, b) => (b.sample ?? -Infinity) - (a.sample ?? -Infinity));
    }
    return items;
  }, [metrics, sort]);

  if (stage === null) {
    return (
      <p className="research-note">
        The metrics stage did not run for this run, so no metric families exist.
      </p>
    );
  }

  return (
    <div className="research-panel">
      <Section
        title="Metric families"
        description="Each card is one canonical family exactly as Research reported it. A family with no value is shown as unavailable, never as zero."
      >
        <div className="research-cards">
          {rows.map((row) => (
            <article key={row.family} className="research-card">
              <header>
                <h4>{FAMILY_LABELS[row.family] ?? row.family}</h4>
                <Badge
                  tone={
                    !row.present
                      ? "unknown"
                      : row.undefinedReason
                        ? "warning"
                        : "positive"
                  }
                >
                  {!row.present
                    ? "not reported"
                    : row.undefinedReason
                      ? "warning"
                      : "valid"}
                </Badge>
              </header>
              <p className="research-card__value is-mono">
                {row.value === null ? "—" : formatNumber(row.value, 6)}
              </p>
              <p className="research-card__meta">
                {row.unit ?? "unit unreported"} ·{" "}
                {row.sample === null ? "no sample count" : `n=${row.sample}`}
              </p>
              {row.undefinedReason ? (
                <p className="research-card__reason">{row.undefinedReason}</p>
              ) : null}
            </article>
          ))}
        </div>
      </Section>

      <Section
        title="Metric table"
        description="The same values in tabular form."
        actions={
          <label className="research-inline-field">
            Sort
            <select
              value={sort}
              onChange={(event) => setSort(event.target.value as SortKey)}
            >
              <option value="family">Family order</option>
              <option value="value">Value</option>
              <option value="sample">Sample size</option>
            </select>
          </label>
        }
      >
        <EvidenceTable
          columns={["Family", "Value", "Unit", "Samples", "Status"]}
          rows={rows.map((row) => [
            FAMILY_LABELS[row.family] ?? row.family,
            <span key={`${row.family}-v`} className="is-mono">
              {row.value === null ? "—" : formatNumber(row.value, 6)}
            </span>,
            row.unit ?? "—",
            row.sample === null ? "—" : formatNumber(row.sample, 0),
            row.undefinedReason ?? (row.present ? "valid" : "not reported"),
          ])}
        />
      </Section>

      <Section title="Warnings" description="Warnings raised while computing metrics.">
        <WarningList warnings={view.warnings} />
      </Section>
    </div>
  );
}
