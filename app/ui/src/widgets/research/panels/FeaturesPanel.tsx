/**
 * Features panel (FEAT-UI-28, plan §10.6).
 *
 * A V2-only view. It renders the feature-frame shape, the declared windows and
 * forward horizons, and the no-lookahead classification Research published —
 * it derives no feature and recomputes no lineage.
 */

"use client";

import type { ReactNode } from "react";

import { Badge, EvidenceTable, KeyValues, Section, WarningList } from "../evidence";
import {
  asNumber,
  asText,
  evidenceArray,
  evidenceBranch,
  evidenceRecord,
  formatNumber,
  hashPrefix,
} from "../research-selectors";
import type { PanelProps } from "./OverviewPanel";

/** Research feature frame evidence. */
export function FeaturesPanel({ view }: PanelProps): ReactNode {
  const stage = evidenceBranch(view, "features");
  const metadata = evidenceRecord(stage, "metadata");
  const config = evidenceRecord(
    view.evidence as Record<string, unknown>,
    "effective_configuration"
  );
  const training = evidenceArray(metadata, "training_feature_columns") as string[];
  const forward = evidenceArray(
    metadata,
    "research_only_forward_columns"
  ) as string[];
  const lineage = evidenceArray(metadata, "indicator_lineage") as Array<
    Record<string, unknown>
  >;
  const windows = evidenceRecord(config, "feature_windows") ?? {};
  const horizons = evidenceArray(config, "forward_horizons") as number[];
  const rowCount = asNumber(stage?.row_count);
  const declaredRows = asNumber(
    evidenceRecord(view.evidence as Record<string, unknown>, "data")?.record_count
  );
  const warmupLoss =
    rowCount !== null && declaredRows !== null ? declaredRows - rowCount : null;

  return (
    <div className="research-panel">
      <Section
        title="Feature frame"
        description="Shape of the frame Research built, and the policy it applied."
      >
        <KeyValues
          columns={4}
          items={[
            ["Rows", formatNumber(stage?.row_count, 0)],
            ["Columns", formatNumber(stage?.column_count, 0)],
            [
              "Warmup loss",
              warmupLoss === null ? "—" : `${warmupLoss} rows`,
            ],
            ["NaN policy", asText(metadata?.nan_policy) ?? "—"],
            [
              "Input mutated",
              <Badge
                key="m"
                tone={metadata?.input_mutated ? "negative" : "positive"}
              >
                {metadata?.input_mutated ? "yes" : "no"}
              </Badge>,
            ],
            ["Schema", asText(metadata?.schema_version) ?? "—"],
            [
              "Dataset hash",
              <span key="d" className="is-mono">
                {hashPrefix(asText(metadata?.dataset_hash))}
              </span>,
            ],
            [
              "Config hash",
              <span key="c" className="is-mono">
                {hashPrefix(asText(metadata?.configuration_hash))}
              </span>,
            ],
          ]}
        />
      </Section>

      <Section
        title="Windows and horizons"
        description="The effective configuration the server resolved for this run."
      >
        <div className="research-two-up">
          <EvidenceTable
            caption="Feature windows"
            columns={["Feature", "Window"]}
            emptyLabel="No feature windows were declared."
            rows={Object.entries(windows).map(([name, value]) => [
              <code key={name}>{name}</code>,
              formatNumber(value, 0),
            ])}
          />
          <EvidenceTable
            caption="Forward horizons"
            columns={["Horizon"]}
            emptyLabel="No forward horizons were declared."
            rows={horizons.map((horizon) => [formatNumber(horizon, 0)])}
          />
        </div>
      </Section>

      <Section
        title="Column classification"
        description="Source-derived training columns and the forward columns Research keeps out of training."
      >
        <div className="research-two-up">
          <EvidenceTable
            caption="Training feature columns (no-lookahead eligible)"
            columns={["Column", "Eligibility"]}
            emptyLabel="No training columns were published."
            rows={training.map((column) => [
              <code key={column}>{column}</code>,
              <Badge key={`${column}-b`} tone="positive">
                training-eligible
              </Badge>,
            ])}
          />
          <EvidenceTable
            caption="Research-only forward columns"
            columns={["Column", "Eligibility"]}
            emptyLabel="No forward columns were declared."
            rows={forward.map((column) => [
              <code key={column}>{column}</code>,
              <Badge key={`${column}-b`} tone="warning">
                research-only
              </Badge>,
            ])}
          />
        </div>
      </Section>

      <Section
        title="Indicator lineage"
        description="Indicator provenance Research recorded for the derived columns."
      >
        <EvidenceTable
          columns={["Entry"]}
          emptyLabel="No indicator lineage was recorded for this run."
          rows={lineage.map((entry, index) => [
            <code key={index}>{JSON.stringify(entry)}</code>,
          ])}
        />
      </Section>

      <Section title="Warnings" description="Warnings raised while building features.">
        <WarningList warnings={view.warnings} />
      </Section>
    </div>
  );
}
