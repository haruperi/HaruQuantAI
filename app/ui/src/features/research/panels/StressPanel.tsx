/**
 * Stress panel (FEAT-UI-28, plan §10.15).
 *
 * A V2-only view over the stress-scenario evidence Research persists. A shock
 * is only shown when it cites a basis Research validated; the panel invents no
 * magnitude and applies no shock of its own.
 */

"use client";

import { useEffect, useState, type ReactNode } from "react";

import { ApiClientError, apiClients } from "@/clients";

import {
  Badge,
  EvidenceTable,
  KeyValues,
  RecordTable,
  Section,
  WarningList,
} from "../evidence";
import {
  asText,
  evidenceArray,
  evidenceRecord,
  formatNumber,
  formatTimestamp,
} from "../research-selectors";
import type { PanelProps } from "./OverviewPanel";

/** Props accepted by `StressPanel`. */
export interface StressPanelProps extends PanelProps {
  scenarioId: string;
  onScenarioChange: (value: string) => void;
}

const BASIS_TONES: Record<string, "positive" | "warning"> = {
  historical: "positive",
  reasoned: "warning",
};

/** Stress-scenario evidence. */
export function StressPanel({
  view,
  scenarioId,
  onScenarioChange,
}: StressPanelProps): ReactNode {
  const [draft, setDraft] = useState(scenarioId);
  const [catalog, setCatalog] = useState<
    Array<{ scenario_key: string; name: string; rationale: string }>
  >([]);
  const [scenarioKey, setScenarioKey] = useState("broad_market_dislocation");
  const [hypothesis, setHypothesis] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createMessage, setCreateMessage] = useState<string | null>(null);
  const stress = evidenceRecord(
    view.evidence as Record<string, unknown>,
    "stress",
  );
  const evidence = evidenceRecord(stress, "evidence");
  const shocks = evidenceArray(evidence, "shocks") as Array<
    Record<string, unknown>
  >;
  const expectancy = evidenceRecord(
    view.evidence as Record<string, unknown>,
    "expectancy",
  );

  useEffect(() => {
    void apiClients.research.listPresets().then((response) => {
      if (response.status === "success")
        setCatalog(response.data.stress_scenarios);
    });
  }, []);

  async function createScenario(): Promise<void> {
    setCreating(true);
    setCreateError(null);
    setCreateMessage(null);
    try {
      const response = await apiClients.research.createStressScenario({
        scenario_key: scenarioKey as
          | "broad_market_dislocation"
          | "severe_fx_repricing"
          | "liquidity_withdrawal"
          | "venue_connectivity_disruption"
          | "extreme_combined_tail",
        hypothesis: hypothesis.trim(),
      });
      if (response.status === "error") {
        setCreateError(response.error.message);
        return;
      }
      const createdId = asText(response.data.evidence.scenario_id);
      if (createdId) {
        setDraft(createdId);
        onScenarioChange(createdId);
      }
      setCreateMessage(`Scenario ${createdId ?? "created"}.`);
    } catch (cause) {
      setCreateError(
        cause instanceof ApiClientError
          ? cause.message
          : "Scenario creation unavailable",
      );
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="research-panel">
      {stress?.creation_permitted === true ? (
        <Section
          title="Create reasoned scenario"
          description="Instantiate one immutable Research-owned approved assumption set. This records advisory evidence and applies no shock."
        >
          <form
            className="research-inline-form"
            onSubmit={(event) => {
              event.preventDefault();
              void createScenario();
            }}
          >
            <label className="research-inline-field">
              Approved scenario
              <select
                value={scenarioKey}
                onChange={(event) => setScenarioKey(event.target.value)}
              >
                {catalog.map((item) => (
                  <option key={item.scenario_key} value={item.scenario_key}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="research-inline-field">
              Stress objective
              <input
                required
                maxLength={500}
                value={hypothesis}
                onChange={(event) => setHypothesis(event.target.value)}
              />
            </label>
            <button
              type="submit"
              className="research-button"
              disabled={creating}
            >
              {creating ? "Creating…" : "Create scenario"}
            </button>
          </form>
          <p className="research-note">
            {catalog.find((item) => item.scenario_key === scenarioKey)
              ?.rationale ?? "Loading approved scenarios…"}
          </p>
          {createError ? (
            <p role="alert" className="research-error">
              {createError}
            </p>
          ) : null}
          {createMessage ? (
            <p role="status" className="research-note">
              {createMessage}
            </p>
          ) : null}
        </Section>
      ) : null}

      <Section
        title="Scenario selection"
        description="Stress evidence is keyed by the Research-owned scenario identity. Nothing is loaded until one is named."
        actions={
          <form
            className="research-inline-form"
            onSubmit={(event) => {
              event.preventDefault();
              onScenarioChange(draft.trim());
            }}
          >
            <label className="research-inline-field">
              Scenario id
              <input
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                placeholder="scn-…"
              />
            </label>
            <button type="submit" className="research-button">
              Load
            </button>
          </form>
        }
      >
        {stress?.available ? (
          <KeyValues
            columns={4}
            items={[
              ["Scenario", asText(evidence?.scenario_id) ?? scenarioId],
              ["Hypothesis", asText(evidence?.hypothesis) ?? "—"],
              [
                "Generated",
                formatTimestamp(asText(evidence?.generated_at_utc)),
              ],
              ["Contract", asText(evidence?.contract_version) ?? "—"],
            ]}
          />
        ) : (
          <div className="research-empty" role="status">
            <Badge tone="unknown">Unavailable</Badge>
            <p>
              {asText(stress?.reason) === "SCENARIO_NOT_SELECTED"
                ? "Name a stress scenario to load the evidence Research persisted for it."
                : "Research has recorded no stress evidence for the named scenario."}
            </p>
            <code className="research-empty__reason">
              {asText(stress?.reason) ?? "NO_EVIDENCE"}
            </code>
          </div>
        )}
      </Section>

      <Section
        title="Shocks and basis validation"
        description="Every shock cites either a historical event or an explicitly reasoned assumption. Both are labelled."
      >
        <EvidenceTable
          columns={[
            "Shock",
            "Magnitude",
            "Unit",
            "Basis",
            "Reference",
            "Rationale",
          ]}
          emptyLabel="No shocks were published for this scenario."
          rows={shocks.map((shock, index) => [
            <code key={index}>{asText(shock.shock_type) ?? "—"}</code>,
            <span key={`${index}-m`} className="is-mono">
              {formatNumber(shock.magnitude, 4)}
            </span>,
            asText(shock.unit) ?? "—",
            <Badge
              key={`${index}-b`}
              tone={BASIS_TONES[asText(shock.basis_kind) ?? ""] ?? "unknown"}
            >
              {asText(shock.basis_kind) ?? "—"}
            </Badge>,
            asText(shock.basis_ref) ?? "—",
            asText(shock.rationale) ?? "—",
          ])}
        />
      </Section>

      <Section
        title="Scenario outcome"
        description="Outcome evidence and any calibration reference the scenario carries."
      >
        <RecordTable
          record={evidence}
          emptyLabel="No scenario outcome evidence was published."
        />
      </Section>

      <Section
        title="Expectancy reference"
        description="The approved expectancy profile a stress result would be read against. Read-only here."
      >
        {expectancy?.available ? (
          <RecordTable record={evidenceRecord(expectancy, "profile")} />
        ) : (
          <p className="research-note">
            No expectancy profile is attached (
            {asText(expectancy?.reason) ?? "none"}).
          </p>
        )}
      </Section>

      <Section
        title="Warnings"
        description="Warnings attached to stress evidence."
      >
        <WarningList warnings={view.warnings} />
      </Section>
    </div>
  );
}
