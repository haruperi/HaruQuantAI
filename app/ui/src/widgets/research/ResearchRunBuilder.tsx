/**
 * New experiment / run builder (FEAT-UI-28, plan §10.2).
 *
 * Six sections: hypothesis, dataset, stages, preset and approved overrides,
 * validation settings, and review. The builder submits a safe request — a
 * symbol, a window, a preset, and a bounded override set. It never constructs
 * an owner-domain contract, and it never chooses an artifact root or a
 * resource ceiling.
 */

"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState, type ReactNode } from "react";

import { ApiClientError, apiClients } from "@/clients";
import type { ResearchRunCreateInput } from "@/clients";

import { Badge, EvidenceTable, KeyValues, Section } from "./evidence";
import { EvidenceGate } from "./ResearchRunStatus";
import { useResearchStore } from "./research-store";
import { usePresets, useExperiments } from "./use-research";

const TIMEFRAMES = ["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"];

/** Parse a comma-separated integer list into a bounded array. */
function parseIntegers(value: string): number[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item.length > 0)
    .map(Number)
    .filter((item) => Number.isFinite(item));
}

/** Parse a `name=window` list into an override mapping. */
function parseWindows(value: string): Record<string, number> {
  const result: Record<string, number> = {};
  for (const part of value.split(",")) {
    const [name, size] = part.split("=").map((item) => item.trim());
    if (!name || !size) continue;
    const parsed = Number(size);
    if (Number.isFinite(parsed)) result[name] = parsed;
  }
  return result;
}

/** Props accepted by `ResearchRunBuilder`. */
export interface ResearchRunBuilderProps {
  initialExperimentId?: string;
  initialSymbol?: string;
  initialTimeframe?: string;
  initialPreset?: string;
}

/** Experiment and run builder. */
export function ResearchRunBuilder({
  initialExperimentId,
  initialSymbol,
  initialTimeframe,
  initialPreset,
}: ResearchRunBuilderProps): ReactNode {
  const router = useRouter();
  const presets = usePresets();
  const experiments = useExperiments();
  const draft = useResearchStore((state) => state.draft);
  const setDraft = useResearchStore((state) => state.setDraft);
  const resetDraft = useResearchStore((state) => state.resetDraft);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [advanced, setAdvanced] = useState(false);

  useEffect(() => {
    const patch: Record<string, string> = {};
    if (initialExperimentId) patch.experimentId = initialExperimentId;
    if (initialSymbol) patch.symbol = initialSymbol;
    if (initialTimeframe) patch.timeframe = initialTimeframe;
    if (initialPreset) patch.preset = initialPreset;
    if (Object.keys(patch).length > 0) setDraft(patch);
  }, [initialExperimentId, initialSymbol, initialTimeframe, initialPreset, setDraft]);

  const selectedPreset = useMemo(
    () =>
      presets.data?.presets.find((preset) => preset.preset_id === draft.preset) ??
      null,
    [presets.data, draft.preset]
  );

  const stageOptions = presets.data?.stages ?? [];
  const effectiveStages =
    draft.selectedStages.length > 0
      ? draft.selectedStages
      : (selectedPreset?.selected_stages ?? []);

  const overrides = useMemo(() => {
    const result: Record<string, unknown> = {};
    if (draft.bootstrapSamples) result.bootstrap_samples = Number(draft.bootstrapSamples);
    if (draft.permutationSamples)
      result.permutation_samples = Number(draft.permutationSamples);
    if (draft.nullSamples) result.null_samples = Number(draft.nullSamples);
    if (draft.correction) result.correction = draft.correction;
    if (draft.featureWindows)
      result.feature_windows = parseWindows(draft.featureWindows);
    if (draft.forwardHorizons)
      result.forward_horizons = parseIntegers(draft.forwardHorizons);
    if (draft.enableMarketStructureQuality !== null)
      result.enable_market_structure_quality = draft.enableMarketStructureQuality;
    if (draft.modelingClusters) result.modeling_clusters = Number(draft.modelingClusters);
    if (draft.modelingPcaComponents)
      result.modeling_pca_components = Number(draft.modelingPcaComponents);
    if (draft.continueOnStudyError !== null)
      result.continue_on_study_error = draft.continueOnStudyError;
    if (draft.sessionTimezone) result.session_timezone = draft.sessionTimezone;
    return result;
  }, [draft]);

  const canSubmit =
    draft.symbol.trim().length > 0 &&
    (draft.experimentId !== null || draft.experimentName.trim().length > 0) &&
    (draft.experimentId !== null || draft.hypothesis.trim().length > 0);

  async function submit(): Promise<void> {
    setSubmitting(true);
    setError(null);
    try {
      let experimentId = draft.experimentId;
      if (!experimentId) {
        const created = await apiClients.research.createExperiment({
          name: draft.experimentName.trim(),
          hypothesis: draft.hypothesis.trim(),
          notes: draft.notes.trim() || null,
          tags: draft.tags
            .split(",")
            .map((tag) => tag.trim())
            .filter((tag) => tag.length > 0),
        });
        if (created.status === "error") {
          setError(created.error.message);
          return;
        }
        experimentId = created.data.experiment_id;
      }

      const input: ResearchRunCreateInput = {
        dataset: {
          symbol: draft.symbol.trim(),
          timeframe: draft.timeframe,
          source_id: draft.sourceId.trim() || null,
          start: draft.start ? new Date(draft.start).toISOString() : null,
          end: draft.end ? new Date(draft.end).toISOString() : null,
          bar_limit: draft.barLimit,
          asset_class: draft.assetClass.trim() || null,
        },
        preset: draft.preset,
        selected_stages: draft.selectedStages,
        approved_overrides: overrides,
        seed: draft.seed ? Number(draft.seed) : null,
        reason: draft.reason.trim() || null,
        force_rerun: draft.forceRerun,
        save_artifacts: draft.saveArtifacts,
        hypothesis: draft.hypothesis.trim() || null,
      };
      const response = await apiClients.research.createRun(experimentId, input);
      if (response.status === "error") {
        setError(response.error.message);
        return;
      }
      resetDraft();
      router.push(
        `/workstation/research/experiments/${experimentId}/runs/${response.data.run_id}/overview`
      );
    } catch (cause) {
      setError(
        cause instanceof ApiClientError
          ? `${cause.code}: ${cause.message}`
          : "unavailable"
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="research-page">
      <header className="research-page__head">
        <p className="research-eyebrow">Research workbench</p>
        <h1>New run</h1>
        <p>
          The server resolves the dataset, artifact root, resource limits, and
          effective preset. This form only carries the choices a researcher makes.
        </p>
      </header>

      <EvidenceGate
        loading={presets.loading}
        error={presets.error}
        reload={presets.reload}
        ready={presets.data !== null}
        loadingLabel="Loading server-owned presets…"
      >
        <Section
          title="1 · Hypothesis"
          description="Every run records the explicit question it tests."
        >
          <div className="research-form-grid">
            <label>
              Existing experiment
              <select
                value={draft.experimentId ?? ""}
                onChange={(event) =>
                  setDraft({ experimentId: event.target.value || null })
                }
              >
                <option value="">Create a new experiment</option>
                {(experiments.data?.experiments ?? []).map((experiment) => (
                  <option
                    key={experiment.experiment_id}
                    value={experiment.experiment_id}
                  >
                    {experiment.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Experiment name
              <input
                value={draft.experimentName}
                disabled={draft.experimentId !== null}
                onChange={(event) => setDraft({ experimentName: event.target.value })}
              />
            </label>
            <label className="research-form-grid__wide">
              Hypothesis
              <textarea
                value={draft.hypothesis}
                rows={2}
                onChange={(event) => setDraft({ hypothesis: event.target.value })}
                placeholder="e.g. Returns mean-revert over one research bar in the London session."
              />
            </label>
            <label className="research-form-grid__wide">
              Notes
              <textarea
                value={draft.notes}
                rows={2}
                onChange={(event) => setDraft({ notes: event.target.value })}
              />
            </label>
            <label>
              Tags
              <input
                value={draft.tags}
                onChange={(event) => setDraft({ tags: event.target.value })}
                placeholder="fx, intraday"
              />
            </label>
            <label>
              Run reason
              <input
                value={draft.reason}
                onChange={(event) => setDraft({ reason: event.target.value })}
              />
            </label>
          </div>
        </Section>

        <Section
          title="2 · Dataset"
          description="Named, not uploaded. The server resolves the canonical dataset through Data."
        >
          <div className="research-form-grid">
            <label>
              Symbol
              <input
                value={draft.symbol}
                onChange={(event) => setDraft({ symbol: event.target.value })}
                placeholder="EURUSD"
                required
              />
            </label>
            <label>
              Timeframe
              <select
                value={draft.timeframe}
                onChange={(event) => setDraft({ timeframe: event.target.value })}
              >
                {TIMEFRAMES.map((timeframe) => (
                  <option key={timeframe} value={timeframe}>
                    {timeframe}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Source (optional)
              <input
                value={draft.sourceId}
                onChange={(event) => setDraft({ sourceId: event.target.value })}
                placeholder="server default"
              />
            </label>
            <label>
              Bar limit
              <input
                type="number"
                min={1}
                value={draft.barLimit}
                onChange={(event) =>
                  setDraft({ barLimit: Number(event.target.value) || 1 })
                }
              />
            </label>
            <label>
              Start (optional)
              <input
                type="datetime-local"
                value={draft.start}
                onChange={(event) => setDraft({ start: event.target.value })}
              />
            </label>
            <label>
              End (optional)
              <input
                type="datetime-local"
                value={draft.end}
                onChange={(event) => setDraft({ end: event.target.value })}
              />
            </label>
            <label>
              Asset class (enables intelligence applicability)
              <input
                value={draft.assetClass}
                onChange={(event) => setDraft({ assetClass: event.target.value })}
                placeholder="fx, equity, commodity…"
              />
            </label>
          </div>
        </Section>

        <Section
          title="3 · Stages"
          description="Leave every box clear to run the preset's own selection. Dependencies are completed server-side."
        >
          <div className="research-chips">
            {stageOptions.map((stage) => {
              const checked = draft.selectedStages.includes(stage);
              return (
                <label key={stage} className="research-check">
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() =>
                      setDraft({
                        selectedStages: checked
                          ? draft.selectedStages.filter((item) => item !== stage)
                          : [...draft.selectedStages, stage],
                      })
                    }
                  />
                  {stage}
                </label>
              );
            })}
          </div>
        </Section>

        <Section
          title="4 · Preset"
          description="Presets are server-owned. Their sample counts and thresholds are policy, not browser input."
        >
          <div className="research-cards">
            {(presets.data?.presets ?? []).map((preset) => (
              <label
                key={preset.preset_id}
                className={`research-card research-card--select${
                  draft.preset === preset.preset_id ? " research-card--active" : ""
                }`}
              >
                <input
                  type="radio"
                  name="preset"
                  value={preset.preset_id}
                  checked={draft.preset === preset.preset_id}
                  onChange={() => setDraft({ preset: preset.preset_id })}
                />
                <h4>{preset.name}</h4>
                <p>{preset.description}</p>
                <p className="research-card__meta">
                  {preset.selected_stages.length} stages ·{" "}
                  {preset.statistics.bootstrap_samples} bootstrap ·{" "}
                  {preset.statistics.correction ?? "no correction"}
                </p>
              </label>
            ))}
          </div>
        </Section>

        <Section
          title="5 · Validation settings"
          description="Approved overrides only. The server rejects anything outside this set or outside its bounds."
          actions={
            <button
              type="button"
              className="research-button"
              onClick={() => setAdvanced((value) => !value)}
            >
              {advanced ? "Hide advanced" : "Show advanced"}
            </button>
          }
        >
          <div className="research-form-grid">
            <label>
              Seed
              <input
                value={draft.seed}
                onChange={(event) => setDraft({ seed: event.target.value })}
                placeholder={String(selectedPreset?.statistics.seed ?? "")}
              />
            </label>
            <label>
              Correction
              <select
                value={draft.correction}
                onChange={(event) => setDraft({ correction: event.target.value })}
              >
                <option value="">preset default</option>
                <option value="benjamini_hochberg">benjamini_hochberg</option>
              </select>
            </label>
            <label>
              Force rerun
              <input
                type="checkbox"
                checked={draft.forceRerun}
                onChange={(event) => setDraft({ forceRerun: event.target.checked })}
              />
            </label>
            <label>
              Save artifacts
              <input
                type="checkbox"
                checked={draft.saveArtifacts}
                onChange={(event) => setDraft({ saveArtifacts: event.target.checked })}
              />
            </label>
          </div>
          {advanced ? (
            <div className="research-form-grid">
              <label>
                Bootstrap samples
                <input
                  value={draft.bootstrapSamples}
                  onChange={(event) =>
                    setDraft({ bootstrapSamples: event.target.value })
                  }
                  placeholder={String(
                    selectedPreset?.statistics.bootstrap_samples ?? ""
                  )}
                />
              </label>
              <label>
                Permutation samples
                <input
                  value={draft.permutationSamples}
                  onChange={(event) =>
                    setDraft({ permutationSamples: event.target.value })
                  }
                  placeholder={String(
                    selectedPreset?.statistics.permutation_samples ?? ""
                  )}
                />
              </label>
              <label>
                Null samples
                <input
                  value={draft.nullSamples}
                  onChange={(event) => setDraft({ nullSamples: event.target.value })}
                  placeholder={String(selectedPreset?.statistics.null_samples ?? "")}
                />
              </label>
              <label>
                Feature windows
                <input
                  value={draft.featureWindows}
                  onChange={(event) =>
                    setDraft({ featureWindows: event.target.value })
                  }
                  placeholder="sma=20, atr=14"
                />
              </label>
              <label>
                Forward horizons
                <input
                  value={draft.forwardHorizons}
                  onChange={(event) =>
                    setDraft({ forwardHorizons: event.target.value })
                  }
                  placeholder="1, 5"
                />
              </label>
              <label>
                Session timezone
                <input
                  value={draft.sessionTimezone}
                  onChange={(event) =>
                    setDraft({ sessionTimezone: event.target.value })
                  }
                  placeholder="UTC"
                />
              </label>
              <label>
                Modeling clusters
                <input
                  value={draft.modelingClusters}
                  onChange={(event) =>
                    setDraft({ modelingClusters: event.target.value })
                  }
                  placeholder={String(selectedPreset?.modeling_clusters ?? "")}
                />
              </label>
              <label>
                PCA components
                <input
                  value={draft.modelingPcaComponents}
                  onChange={(event) =>
                    setDraft({ modelingPcaComponents: event.target.value })
                  }
                  placeholder={String(selectedPreset?.modeling_pca_components ?? "")}
                />
              </label>
              <label>
                Market-structure quality
                <select
                  value={
                    draft.enableMarketStructureQuality === null
                      ? ""
                      : String(draft.enableMarketStructureQuality)
                  }
                  onChange={(event) =>
                    setDraft({
                      enableMarketStructureQuality:
                        event.target.value === ""
                          ? null
                          : event.target.value === "true",
                    })
                  }
                >
                  <option value="">preset default</option>
                  <option value="true">enabled</option>
                  <option value="false">disabled</option>
                </select>
              </label>
              <label>
                Continue on study error
                <select
                  value={
                    draft.continueOnStudyError === null
                      ? ""
                      : String(draft.continueOnStudyError)
                  }
                  onChange={(event) =>
                    setDraft({
                      continueOnStudyError:
                        event.target.value === ""
                          ? null
                          : event.target.value === "true",
                    })
                  }
                >
                  <option value="">preset default</option>
                  <option value="true">continue</option>
                  <option value="false">stop</option>
                </select>
              </label>
            </div>
          ) : null}
        </Section>

        <Section
          title="6 · Review and submit"
          description="Exactly what will be sent. Server-owned settings are absent because the browser never chooses them."
        >
          <KeyValues
            columns={4}
            items={[
              ["Symbol", draft.symbol || "—"],
              ["Timeframe", draft.timeframe],
              ["Preset", draft.preset],
              ["Bar limit", String(draft.barLimit)],
              ["Stages", effectiveStages.join(", ") || "preset default"],
              [
                "Overrides",
                Object.keys(overrides).length > 0
                  ? Object.keys(overrides).join(", ")
                  : "none",
              ],
              ["Save artifacts", draft.saveArtifacts ? "yes" : "no"],
              [
                "Advisory only",
                <Badge key="a" tone="warning">
                  yes
                </Badge>,
              ],
            ]}
          />
          <EvidenceTable
            caption="Approved override keys accepted by the server"
            columns={["Key"]}
            emptyLabel="No override keys were published."
            rows={(selectedPreset?.approved_override_keys ?? []).map((key) => [
              <code key={key}>{key}</code>,
            ])}
          />
          {error ? (
            <p className="research-error" role="alert">
              {error}
            </p>
          ) : null}
          <button
            type="button"
            className="research-button research-button--primary"
            disabled={!canSubmit || submitting}
            onClick={() => void submit()}
          >
            {submitting ? "Queueing run…" : "Queue run"}
          </button>
        </Section>
      </EvidenceGate>
    </div>
  );
}
