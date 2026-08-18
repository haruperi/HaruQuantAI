/**
 * Intelligence panel (FEAT-UI-28, plan §10.14).
 *
 * A V2-only view over the point-in-time fundamental, sentiment, and
 * applicability evidence Research owns. When no asset class was declared for
 * the run, the panel says exactly that rather than guessing one from a symbol
 * string.
 */

"use client";

import { useState, type ReactNode } from "react";

import {
  Badge,
  EvidenceTable,
  KeyValues,
  RecordTable,
  Section,
  TabPanel,
  TabStrip,
  WarningList,
} from "../evidence";
import {
  asText,
  evidenceArray,
  evidenceRecord,
  formatNumber,
} from "../research-selectors";
import type { PanelProps } from "./OverviewPanel";

const STATUS_TONES: Record<string, "positive" | "warning" | "unknown"> = {
  applicable: "positive",
  not_applicable: "warning",
};

/** Fundamental, sentiment, and applicability evidence. */
export function IntelligencePanel({ view }: PanelProps): ReactNode {
  const [tab, setTab] = useState("applicability");
  const intelligence = evidenceRecord(
    view.evidence as Record<string, unknown>,
    "intelligence"
  );
  const applicability = evidenceArray(intelligence, "applicability") as Array<
    Record<string, unknown>
  >;
  const fundamental = evidenceRecord(intelligence, "fundamental");
  const sentiment = evidenceRecord(intelligence, "sentiment");

  return (
    <div className="research-panel">
      <TabStrip
        label="Intelligence evidence"
        active={tab}
        onSelect={setTab}
        tabs={[
          { id: "applicability", label: "Applicability" },
          { id: "fundamental", label: "Fundamental" },
          { id: "sentiment", label: "Sentiment" },
          { id: "coverage", label: "Source coverage" },
        ]}
      />

      <TabPanel id="applicability" active={tab}>
        <Section
          title="Model applicability"
          description="Whether each evidence model applies to this instrument's asset class. This is a deterministic Research decision."
        >
          {intelligence?.available ? (
            <EvidenceTable
              columns={["Model", "Asset class", "Status", "Reason"]}
              rows={applicability.map((row) => [
                <code key={asText(row.model) ?? ""}>{asText(row.model)}</code>,
                asText(row.asset_class) ?? "—",
                <Badge
                  key={`${asText(row.model)}-s`}
                  tone={STATUS_TONES[asText(row.status) ?? ""] ?? "unknown"}
                >
                  {asText(row.status) ?? "unknown"}
                </Badge>,
                asText(row.reason) ?? "—",
              ])}
            />
          ) : (
            <div className="research-empty" role="status">
              <Badge tone="unknown">Unavailable</Badge>
              <p>
                {asText(intelligence?.reason) === "ASSET_CLASS_NOT_DECLARED"
                  ? "No asset class was declared for this run, so Research cannot decide which evidence models apply. Declare one in the run builder to enable this view."
                  : "Research reported no applicability evidence for this run."}
              </p>
              <code className="research-empty__reason">
                {asText(intelligence?.reason) ?? "NO_EVIDENCE"}
              </code>
            </div>
          )}
        </Section>
      </TabPanel>

      <TabPanel id="fundamental" active={tab}>
        <Section
          title="Point-in-time fundamental evidence"
          description="Source identity, availability, and normalized evidence. Nothing is shown that Research did not publish."
        >
          <RecordTable
            record={fundamental}
            emptyLabel="No fundamental source evidence is registered for this run. Research requires eligible point-in-time sources before it will publish any."
          />
        </Section>
      </TabPanel>

      <TabPanel id="sentiment" active={tab}>
        <Section
          title="Deterministic sentiment evidence"
          description="Measurement method and version are Research-owned; no sentiment is inferred here."
        >
          <RecordTable
            record={sentiment}
            emptyLabel="No sentiment source evidence is registered for this run."
          />
        </Section>
      </TabPanel>

      <TabPanel id="coverage" active={tab}>
        <Section
          title="Source coverage and missingness"
          description="Coverage and quality of the sources behind the evidence above."
        >
          <div className="research-two-up">
            <RecordTable
              record={evidenceRecord(fundamental, "coverage")}
              emptyLabel="No fundamental coverage evidence."
            />
            <RecordTable
              record={evidenceRecord(sentiment, "coverage")}
              emptyLabel="No sentiment coverage evidence."
            />
          </div>
          <KeyValues
            columns={3}
            items={[
              [
                "Fundamental references",
                formatNumber(
                  (evidenceArray(fundamental, "document_references") as unknown[])
                    .length,
                  0
                ),
              ],
              [
                "Sentiment references",
                formatNumber(
                  (evidenceArray(sentiment, "document_references") as unknown[]).length,
                  0
                ),
              ],
              [
                "Evidence available",
                <Badge
                  key="a"
                  tone={intelligence?.available ? "positive" : "unknown"}
                >
                  {intelligence?.available ? "yes" : "no"}
                </Badge>,
              ],
            ]}
          />
        </Section>
      </TabPanel>

      <Section title="Warnings" description="Warnings attached to intelligence evidence.">
        <WarningList warnings={view.warnings} />
      </Section>
    </div>
  );
}
