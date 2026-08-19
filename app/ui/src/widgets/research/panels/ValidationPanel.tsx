/**
 * Validation panel (FEAT-UI-28, plan §10.7).
 *
 * Two tabs over one stage view: the leakage evidence and chronological split
 * policy, and the seeded statistical evidence. Every p-value, interval, and
 * decision shown is a Research-owned field.
 */

"use client";

import { useState, type ReactNode } from "react";

import {
  Badge,
  EvidenceTable,
  IntervalBar,
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
  formatNumber,
} from "../research-selectors";
import type { PanelProps } from "./OverviewPanel";

const SEVERITY_TONES: Record<string, "positive" | "warning" | "negative"> = {
  none: "positive",
  low: "warning",
  medium: "warning",
  high: "negative",
  critical: "negative",
};

/** Leakage and statistical validation. */
export function ValidationPanel({ view }: PanelProps): ReactNode {
  const [tab, setTab] = useState("leakage");
  const leakage = evidenceBranch(view, "leakage");
  const statistics = evidenceBranch(view, "statistics");
  const config = evidenceRecord(
    view.evidence as Record<string, unknown>,
    "effective_configuration"
  );
  const suspected = evidenceArray(leakage, "suspected_columns") as string[];
  const allowed = evidenceArray(leakage, "allowed_forward_columns") as string[];
  const interval = evidenceArray(statistics, "mean_confidence_interval") as number[];
  const severity = asText(leakage?.severity) ?? "unknown";

  return (
    <div className="research-panel">
      <TabStrip
        label="Validation evidence"
        active={tab}
        onSelect={setTab}
        tabs={[
          { id: "leakage", label: "Leakage & splits" },
          { id: "statistical", label: "Statistical" },
        ]}
      />

      <TabPanel id="leakage" active={tab}>
        {leakage === null ? (
          <p className="research-note">
            The leakage stage did not run for this run, so no leakage evidence
            exists.
          </p>
        ) : (
          <>
            <Section
              title="Leakage evidence"
              description="Research's own no-lookahead review of the feature frame."
            >
              <KeyValues
                columns={3}
                items={[
                  [
                    "Severity",
                    <Badge key="s" tone={SEVERITY_TONES[severity] ?? "unknown"}>
                      {severity}
                    </Badge>,
                  ],
                  ["Target column", asText(leakage.target_column) ?? "none declared"],
                  ["Schema", asText(leakage.schema_version) ?? "—"],
                ]}
              />
              <p className="research-note">
                <strong>Recommendation:</strong>{" "}
                {asText(leakage.recommendation) ?? "none supplied"}
              </p>
              <div className="research-two-up">
                <EvidenceTable
                  caption="Suspected columns"
                  columns={["Column"]}
                  emptyLabel="No columns were flagged."
                  rows={suspected.map((column) => [<code key={column}>{column}</code>])}
                />
                <EvidenceTable
                  caption="Allowed forward columns"
                  columns={["Column"]}
                  emptyLabel="No forward columns were allowed."
                  rows={allowed.map((column) => [<code key={column}>{column}</code>])}
                />
              </div>
              <RecordTable
                record={evidenceRecord(leakage, "evidence")}
                emptyLabel="No structured leakage evidence was published."
              />
            </Section>

            <Section
              title="Chronological splits"
              description="Research enforces a forward-ordered train/validation/test partition before any study runs."
            >
              <KeyValues
                columns={3}
                items={[
                  ["Train fraction", "0.60"],
                  ["Validation fraction", "0.20"],
                  ["Test fraction", "0.20"],
                  ["Ordering", "chronological, no shuffling"],
                  ["Embargo/gap policy", "contiguous partitions, no overlap"],
                  [
                    "Source references",
                    formatNumber(
                      (evidenceArray(leakage, "source_references") as string[]).length,
                      0
                    ),
                  ],
                ]}
              />
            </Section>
          </>
        )}
      </TabPanel>

      <TabPanel id="statistical" active={tab}>
        {statistics === null ? (
          <p className="research-note">
            The statistics stage did not run for this run, so no seeded evidence
            exists.
          </p>
        ) : (
          <Section
            title="Seeded statistical evidence"
            description="Bootstrap and permutation evidence produced under an explicit seed."
          >
            <KeyValues
              columns={4}
              items={[
                ["Sample size", formatNumber(statistics.sample_size, 0)],
                [
                  "Permutation p-value",
                  <span key="p" className="is-mono">
                    {formatNumber(statistics.permutation_p_value, 6)}
                  </span>,
                ],
                ["Seed", formatNumber(statistics.seed, 0)],
                [
                  "Correction",
                  asText(evidenceRecord(config, "statistics")?.correction) ??
                    "none applied",
                ],
                [
                  "Bootstrap samples",
                  formatNumber(evidenceRecord(config, "statistics")?.bootstrap_samples, 0),
                ],
                [
                  "Permutation samples",
                  formatNumber(
                    evidenceRecord(config, "statistics")?.permutation_samples,
                    0
                  ),
                ],
                [
                  "Null samples",
                  formatNumber(evidenceRecord(config, "statistics")?.null_samples, 0),
                ],
                [
                  "Block size",
                  formatNumber(evidenceRecord(config, "statistics")?.block_size, 0),
                ],
              ]}
            />
            <IntervalBar
              label="Mean return, 95% block bootstrap"
              lower={asNumber(interval[0])}
              upper={asNumber(interval[1])}
              point={0}
            />
            <p className="research-note">
              The interval and p-value above are Research values. This page applies
              no threshold of its own; the acceptance decision belongs to the study
              evidence.
            </p>
          </Section>
        )}
      </TabPanel>

      <Section title="Warnings" description="Warnings raised during validation.">
        <WarningList warnings={view.warnings} />
      </Section>
    </div>
  );
}
