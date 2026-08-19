/**
 * Modeling panel (FEAT-UI-28, plan §10.12).
 *
 * Realizes the V1 "Unsupervised Structure" intent under V2 ownership: the
 * preprocessing, PCA variance and loadings, cluster sizes, and risk-factor
 * interpretation Research produced under an explicit seed. Cluster scatter is
 * drawn only from the component scores the report actually publishes.
 */

"use client";

import { useMemo, type ReactNode } from "react";

import {
  Badge,
  ContributionBar,
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
} from "../research-selectors";
import type { PanelProps } from "./OverviewPanel";

/** Scatter of the first two PCA components, coloured by cluster label. */
function ClusterScatter({
  scores,
  labels,
}: {
  scores: number[][];
  labels: number[];
}): ReactNode {
  const points = useMemo(
    () =>
      scores
        .map((row, index) => ({
          x: asNumber(row?.[0]),
          y: asNumber(row?.[1]),
          label: labels[index] ?? 0,
        }))
        .filter(
          (point): point is { x: number; y: number; label: number } =>
            point.x !== null && point.y !== null
        )
        .slice(0, 1500),
    [scores, labels]
  );
  if (points.length === 0) {
    return (
      <p className="research-note">
        The report publishes no component scores, so no scatter is drawn.
      </p>
    );
  }
  const xs = points.map((point) => point.x);
  const ys = points.map((point) => point.y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const spanX = maxX - minX || 1;
  const spanY = maxY - minY || 1;
  const size = 260;

  return (
    <figure className="research-chart">
      <svg
        viewBox={`0 0 ${size} ${size}`}
        role="img"
        aria-label="First two principal components coloured by cluster"
      >
        {points.map((point, index) => (
          <circle
            key={index}
            cx={((point.x - minX) / spanX) * size}
            cy={size - ((point.y - minY) / spanY) * size}
            r={1.6}
            className={`research-scatter research-scatter--c${point.label % 6}`}
          />
        ))}
      </svg>
      <figcaption>
        {points.length} observations · PC1 {formatNumber(minX, 2)}–
        {formatNumber(maxX, 2)} · PC2 {formatNumber(minY, 2)}–{formatNumber(maxY, 2)}
      </figcaption>
    </figure>
  );
}

/** Deterministic unsupervised evidence. */
export function ModelingPanel({ view }: PanelProps): ReactNode {
  const stage = evidenceBranch(view, "modeling");
  const pca = evidenceRecord(stage, "pca");
  const clusters = evidenceRecord(stage, "clusters");
  const insights = evidenceRecord(stage, "insights");
  const preprocessing = evidenceRecord(stage, "preprocessing");

  if (stage === null) {
    return (
      <p className="research-note">
        The modeling stage did not run for this run, so no unsupervised evidence
        exists.
      </p>
    );
  }

  const variance = evidenceArray(pca, "explained_variance") as number[];
  const loadings = evidenceArray(pca, "loadings") as number[][];
  const features = evidenceArray(pca, "feature_columns") as string[];
  const labels = evidenceArray(clusters, "labels") as number[];
  const scores = evidenceArray(pca, "scores") as number[][];
  const factors = evidenceArray(insights, "factors") as Array<
    Record<string, unknown>
  >;
  const clusterSizes = new Map<number, number>();
  for (const label of labels) {
    clusterSizes.set(label, (clusterSizes.get(label) ?? 0) + 1);
  }
  const maxVariance = Math.max(0.0001, ...variance.map((value) => Math.abs(value)));

  return (
    <div className="research-panel">
      <Section
        title="Preprocessing"
        description="What Research scaled and selected before fitting."
      >
        <KeyValues
          columns={4}
          items={[
            ["Rows", formatNumber(preprocessing?.row_count, 0)],
            ["Columns", formatNumber(preprocessing?.column_count, 0)],
            [
              "Numeric columns",
              formatNumber(preprocessing?.numeric_column_count, 0),
            ],
            ["Duplicate rows", formatNumber(preprocessing?.duplicate_rows, 0)],
            ["Scaled", clusters?.scale ? "yes" : "no"],
            ["Seed", formatNumber(stage.seed, 0)],
            ["Selected features", features.join(", ") || "—"],
            [
              "Advisory only",
              <Badge key="a" tone="warning">
                yes
              </Badge>,
            ],
          ]}
        />
      </Section>

      <Section
        title="PCA"
        description="Explained variance and component loadings, as fitted."
      >
        <div className="research-bars">
          {variance.map((value, index) => (
            <ContributionBar
              key={index}
              label={`PC${index + 1}`}
              value={value}
              maximum={maxVariance}
              display={`${formatNumber(value * 100, 1)}%`}
            />
          ))}
        </div>
        <EvidenceTable
          caption="Component loadings"
          columns={["Component", ...features]}
          emptyLabel="No loadings were published."
          rows={loadings.map((row, index) => [
            `PC${index + 1}`,
            ...features.map((_, column) => formatNumber(row?.[column], 4)),
          ])}
        />
      </Section>

      <Section
        title="Clusters"
        description="Cluster sizes and centres from the seeded fit."
      >
        <KeyValues
          columns={3}
          items={[
            ["Clusters", formatNumber(clusters?.n_clusters, 0)],
            [
              "Samples",
              formatNumber(
                evidenceRecord(clusters, "diagnostics")?.sample_count,
                0
              ),
            ],
            [
              "Inertia",
              formatNumber(evidenceRecord(clusters, "diagnostics")?.inertia, 4),
            ],
          ]}
        />
        <div className="research-two-up">
          <EvidenceTable
            caption="Cluster sizes"
            columns={["Cluster", "Observations", "Share"]}
            emptyLabel="No cluster labels were published."
            rows={[...clusterSizes.entries()]
              .sort((a, b) => a[0] - b[0])
              .map(([label, count]) => [
                `C${label}`,
                formatNumber(count, 0),
                `${formatNumber((count / Math.max(1, labels.length)) * 100, 1)}%`,
              ])}
          />
          <ClusterScatter scores={scores} labels={labels} />
        </div>
      </Section>

      <Section
        title="Risk factors"
        description="The factor interpretation Research derived from the loadings."
      >
        <EvidenceTable
          columns={["Component", "Feature", "Sign", "Magnitude"]}
          emptyLabel="No factor interpretation was published."
          rows={factors.map((factor, index) => [
            `PC${(asNumber(factor.component) ?? index) + 1}`,
            asText(factor.feature) ?? "—",
            <Badge
              key={index}
              tone={asText(factor.sign) === "positive" ? "positive" : "negative"}
            >
              {asText(factor.sign) ?? "—"}
            </Badge>,
            formatNumber(factor.magnitude, 4),
          ])}
        />
        <KeyValues
          columns={2}
          items={[
            [
              "Signal adaptation",
              <Badge key="sa" tone="unknown">
                {asText(insights?.signal_adaptation) ?? "—"}
              </Badge>,
            ],
            [
              "Minimum-sample status",
              (asNumber(evidenceRecord(clusters, "diagnostics")?.sample_count) ?? 0) > 0
                ? "met"
                : "not reported",
            ],
          ]}
        />
      </Section>

      <Section
        title="Descriptive summary"
        description="The descriptive frame Research summarised before modeling."
      >
        <RecordTable
          record={evidenceRecord(insights, "descriptive")}
          emptyLabel="No descriptive summary was published."
        />
      </Section>

      <Section title="Warnings" description="Warnings raised while modeling.">
        <WarningList warnings={view.warnings} />
      </Section>
    </div>
  );
}
