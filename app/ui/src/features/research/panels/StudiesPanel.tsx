/**
 * Edge Studies panel (FEAT-UI-28, plan §10.9).
 *
 * One tab per approved study plus a null-evidence tab. Every classification,
 * statistic, and null summary is a Research field; the browser never decides
 * whether an edge is confirmed.
 */

"use client";

import { useState, type ReactNode } from "react";

import {
  Badge,
  DistributionStrip,
  EvidenceTable,
  KeyValues,
  RecordTable,
  Section,
  TabPanel,
  TabStrip,
  WarningList,
} from "../evidence";
import {
  CLASSIFICATION_TONES,
  asNumber,
  asText,
  evidenceArray,
  evidenceBranch,
  evidenceRecord,
  formatNumber,
} from "../research-selectors";
import type { PanelProps } from "./OverviewPanel";
import type { ResearchWarning } from "@/clients";

const STUDY_LABELS: Record<string, string> = {
  mean_reversion: "Mean reversion",
  trend_persistence: "Trend persistence",
  session: "Session edge",
};

/** One study card. */
function StudyCard({ study }: { study: Record<string, unknown> }): ReactNode {
  const statistics = evidenceRecord(study, "statistics");
  const nullEvidence = evidenceRecord(study, "null_evidence");
  const classification = asText(study.classification) ?? "inconclusive";
  const settings = evidenceRecord(statistics, "settings");
  const warnings = (evidenceArray(study, "warnings") ??
    []) as unknown as ResearchWarning[];

  return (
    <div className="research-study">
      <header className="research-study__head">
        <h4>{STUDY_LABELS[asText(study.study) ?? ""] ?? asText(study.study)}</h4>
        <Badge tone={CLASSIFICATION_TONES[classification] ?? "unknown"}>
          {classification}
        </Badge>
      </header>

      <KeyValues
        columns={4}
        items={[
          ["Seed", formatNumber(study.seed, 0)],
          [
            "Observed samples",
            formatNumber(statistics?.observed_samples, 0),
          ],
          [
            "Required samples",
            formatNumber(statistics?.required_samples, 0),
          ],
          [
            "Advisory only",
            <Badge key="a" tone="warning">
              {study.advisory_only === false ? "no" : "yes"}
            </Badge>,
          ],
          [
            "Statistic",
            <span key="st" className="is-mono">
              {formatNumber(statistics?.statistic, 6)}
            </span>,
          ],
          [
            "p-value",
            <span key="p" className="is-mono">
              {formatNumber(statistics?.p_value, 6)}
            </span>,
          ],
          [
            "Adjusted p-value",
            <span key="ap" className="is-mono">
              {formatNumber(statistics?.adjusted_p_value, 6)}
            </span>,
          ],
          [
            "Null percentile",
            <span key="np" className="is-mono">
              {formatNumber(nullEvidence?.percentile, 4)}
            </span>,
          ],
        ]}
      />

      <DistributionStrip
        label="Null distribution"
        minimum={asNumber(nullEvidence?.minimum)}
        maximum={asNumber(nullEvidence?.maximum)}
        observed={asNumber(statistics?.statistic)}
        percentile={asNumber(nullEvidence?.percentile)}
      />

      <div className="research-two-up">
        <RecordTable record={settings} emptyLabel="No study settings were published." />
        <RecordTable
          record={nullEvidence}
          emptyLabel="No null evidence was published."
        />
      </div>

      <WarningList warnings={warnings} emptyLabel="No study warnings." />
    </div>
  );
}

/** Edge study evidence. */
export function StudiesPanel({ view }: PanelProps): ReactNode {
  const stage = evidenceBranch(view, "studies");
  const results = evidenceArray(stage, "results") as Array<Record<string, unknown>>;
  const [tab, setTab] = useState(
    results.length > 0 ? (asText(results[0].study) ?? "null") : "null"
  );

  if (stage === null) {
    return (
      <p className="research-note">
        The studies stage did not run for this run, so no edge evidence exists.
      </p>
    );
  }

  const tabs = [
    ...results.map((study, index) => ({
      id: asText(study.study) ?? `study-${index}`,
      label: STUDY_LABELS[asText(study.study) ?? ""] ?? `Study ${index + 1}`,
    })),
    { id: "null", label: "Null evidence" },
  ];

  return (
    <div className="research-panel">
      <Section
        title="Edge studies"
        description="Each study carries its own classification. Contradicted and inconclusive outcomes stay visible."
      >
        <EvidenceTable
          columns={["Study", "Classification", "Samples", "Seed"]}
          emptyLabel="Research published no study results."
          rows={results.map((study) => [
            STUDY_LABELS[asText(study.study) ?? ""] ?? asText(study.study),
            <Badge
              key={`${asText(study.study)}-c`}
              tone={
                CLASSIFICATION_TONES[asText(study.classification) ?? ""] ?? "unknown"
              }
            >
              {asText(study.classification) ?? "—"}
            </Badge>,
            formatNumber(
              evidenceRecord(study, "statistics")?.observed_samples,
              0
            ),
            formatNumber(study.seed, 0),
          ])}
        />
      </Section>

      <TabStrip label="Edge studies" active={tab} onSelect={setTab} tabs={tabs} />

      {results.map((study, index) => (
        <TabPanel
          key={asText(study.study) ?? index}
          id={asText(study.study) ?? `study-${index}`}
          active={tab}
        >
          <StudyCard study={study} />
        </TabPanel>
      ))}

      <TabPanel id="null" active={tab}>
        <Section
          title="Null baseline"
          description="The baseline each study is compared against, and the threshold policy Research applied."
        >
          <EvidenceTable
            columns={["Study", "Null policy", "Percentile", "Threshold decision"]}
            emptyLabel="No null evidence was published."
            rows={results.map((study) => {
              const nullEvidence = evidenceRecord(study, "null_evidence");
              return [
                STUDY_LABELS[asText(study.study) ?? ""] ?? asText(study.study),
                asText(nullEvidence?.policy_version) ??
                  asText(nullEvidence?.method) ??
                  "—",
                formatNumber(nullEvidence?.percentile, 4),
                asText(nullEvidence?.exceeds_threshold) ??
                  asText(study.classification) ??
                  "—",
              ];
            })}
          />
          <p className="research-note">
            The threshold decision above is Research&apos;s. This page compares
            nothing against a null of its own.
          </p>
        </Section>
      </TabPanel>

      <Section title="Warnings" description="Warnings raised while running the studies.">
        <WarningList warnings={view.warnings} />
      </Section>
    </div>
  );
}
