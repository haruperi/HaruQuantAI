/**
 * Research automation (FEAT-UI-28, plan §10.18).
 *
 * Covers V1's single and batch automation controls, and adds the V2
 * improvements: queued background jobs, per-symbol status, partial-failure
 * visibility, retry of failed symbols, and server-side rejection reporting.
 */

"use client";

import Link from "next/link";
import { useState, type ReactNode } from "react";

import { ApiClientError, apiClients } from "@/clients";

import { Badge, EvidenceTable, KeyValues, Section, StateBadge } from "./evidence";
import { EvidenceGate } from "./ResearchRunStatus";
import { formatNumber, formatScore, formatTimestamp } from "./research-selectors";
import { useAutomationBatch, useExperiments, usePresets } from "./use-research";

const TIMEFRAMES = ["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"];

/** Batch research automation. */
export function ResearchAutomation(): ReactNode {
  const experiments = useExperiments();
  const presets = usePresets();
  const [experimentId, setExperimentId] = useState("");
  const [symbols, setSymbols] = useState("");
  const [timeframe, setTimeframe] = useState("H1");
  const [preset, setPreset] = useState("standard_edge");
  const [stages, setStages] = useState<string[]>([]);
  const [barLimit, setBarLimit] = useState(5000);
  const [sourceId, setSourceId] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [useCache, setUseCache] = useState(true);
  const [forceRerun, setForceRerun] = useState(false);
  const [saveArtifacts, setSaveArtifacts] = useState(true);
  const [trigger, setTrigger] = useState<"manual" | "scheduled">("manual");
  const [reason, setReason] = useState("");
  const [batchId, setBatchId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const batch = useAutomationBatch(batchId);
  const parsedSymbols = symbols
    .split(/[,\s]+/)
    .map((symbol) => symbol.trim().toUpperCase())
    .filter((symbol) => symbol.length > 0);

  async function submit(retrySymbols?: string[]): Promise<void> {
    const universe = retrySymbols ?? parsedSymbols;
    if (universe.length === 0 || !experimentId) return;
    setSubmitting(true);
    setError(null);
    try {
      const response = await apiClients.research.createAutomationBatch({
        experiment_id: experimentId,
        symbols: universe,
        timeframe,
        source_id: sourceId.trim() || null,
        start: start ? new Date(start).toISOString() : null,
        end: end ? new Date(end).toISOString() : null,
        bar_limit: barLimit,
        preset,
        selected_stages: stages,
        use_cache: useCache,
        force_rerun: forceRerun,
        save_artifacts: saveArtifacts,
        trigger,
        reason: reason.trim() || null,
      });
      if (response.status === "error") {
        setError(response.error.message);
        return;
      }
      setBatchId(response.data.batch_id);
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

  const failedSymbols = (batch.data?.runs ?? [])
    .filter((run) => run.status === "failed")
    .map((run) => run.symbol);

  return (
    <div className="research-page">
      <header className="research-page__head">
        <p className="research-eyebrow">Research workbench</p>
        <h1>Automation</h1>
        <p>
          Queue one run per symbol as background jobs. A rejected symbol is
          recorded and does not stop the rest of the batch.
        </p>
        <div className="research-links">
          <Link className="research-button" href="/workstation/research">
            Back to ledger
          </Link>
        </div>
      </header>

      <EvidenceGate
        loading={presets.loading}
        error={presets.error}
        reload={presets.reload}
        ready={presets.data !== null}
        loadingLabel="Loading server-owned presets…"
      >
        <Section
          title="Batch configuration"
          description="Universe, window, stages, and cache policy. Resource ceilings stay server-owned."
        >
          <div className="research-form-grid">
            <label>
              Experiment
              <select
                value={experimentId}
                onChange={(event) => setExperimentId(event.target.value)}
              >
                <option value="">Select an experiment</option>
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
            <label className="research-form-grid__wide">
              Symbols / watchlist
              <textarea
                rows={2}
                value={symbols}
                onChange={(event) => setSymbols(event.target.value)}
                placeholder="EURUSD, GBPUSD, USDJPY"
              />
            </label>
            <label>
              Timeframe
              <select
                value={timeframe}
                onChange={(event) => setTimeframe(event.target.value)}
              >
                {TIMEFRAMES.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Preset
              <select value={preset} onChange={(event) => setPreset(event.target.value)}>
                {(presets.data?.presets ?? []).map((item) => (
                  <option key={item.preset_id} value={item.preset_id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Dataset source
              <input
                value={sourceId}
                onChange={(event) => setSourceId(event.target.value)}
                placeholder="server default"
              />
            </label>
            <label>
              Bar limit
              <input
                type="number"
                min={1}
                value={barLimit}
                onChange={(event) => setBarLimit(Number(event.target.value) || 1)}
              />
            </label>
            <label>
              Start
              <input
                type="datetime-local"
                value={start}
                onChange={(event) => setStart(event.target.value)}
              />
            </label>
            <label>
              End
              <input
                type="datetime-local"
                value={end}
                onChange={(event) => setEnd(event.target.value)}
              />
            </label>
            <label>
              Trigger
              <select
                value={trigger}
                onChange={(event) =>
                  setTrigger(event.target.value === "scheduled" ? "scheduled" : "manual")
                }
              >
                <option value="manual">manual</option>
                <option value="scheduled">scheduled</option>
              </select>
            </label>
            <label>
              Run reason
              <input value={reason} onChange={(event) => setReason(event.target.value)} />
            </label>
            <label>
              Use cache
              <input
                type="checkbox"
                checked={useCache}
                onChange={(event) => setUseCache(event.target.checked)}
              />
            </label>
            <label>
              Force rerun
              <input
                type="checkbox"
                checked={forceRerun}
                onChange={(event) => setForceRerun(event.target.checked)}
              />
            </label>
            <label>
              Save artifacts
              <input
                type="checkbox"
                checked={saveArtifacts}
                onChange={(event) => setSaveArtifacts(event.target.checked)}
              />
            </label>
          </div>

          <h4>Selected stages</h4>
          <div className="research-chips">
            {(presets.data?.stages ?? []).map((stage) => {
              const checked = stages.includes(stage);
              return (
                <label key={stage} className="research-check">
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() =>
                      setStages(
                        checked
                          ? stages.filter((item) => item !== stage)
                          : [...stages, stage]
                      )
                    }
                  />
                  {stage}
                </label>
              );
            })}
          </div>

          {error ? (
            <p className="research-error" role="alert">
              {error}
            </p>
          ) : null}
          <button
            type="button"
            className="research-button research-button--primary"
            disabled={submitting || parsedSymbols.length === 0 || !experimentId}
            onClick={() => void submit()}
          >
            {submitting
              ? "Queueing batch…"
              : `Queue ${parsedSymbols.length || 0} symbol run(s)`}
          </button>
        </Section>
      </EvidenceGate>

      {batchId ? (
        <EvidenceGate
          loading={batch.loading}
          error={batch.error}
          reload={batch.reload}
          ready={batch.data !== null}
          loadingLabel="Loading batch progress…"
        >
          {batch.data ? (
            <>
              <Section
                title="Batch progress"
                description="Per-symbol status, including partial failure and server-side rejections."
                actions={
                  failedSymbols.length > 0 ? (
                    <button
                      type="button"
                      className="research-button"
                      onClick={() => void submit(failedSymbols)}
                    >
                      Retry {failedSymbols.length} failed
                    </button>
                  ) : null
                }
              >
                <KeyValues
                  columns={4}
                  items={[
                    ["Batch", batch.data.batch_id],
                    [
                      "Status",
                      <StateBadge key="s" state={batch.data.status} />,
                    ],
                    ["Trigger", batch.data.trigger],
                    ["Created", formatTimestamp(batch.data.created_at)],
                    ["Total", formatNumber(batch.data.counts.total, 0)],
                    ["Completed", formatNumber(batch.data.counts.completed, 0)],
                    ["Failed", formatNumber(batch.data.counts.failed, 0)],
                    ["Pending", formatNumber(batch.data.counts.pending, 0)],
                    ["Cancelled", formatNumber(batch.data.counts.cancelled, 0)],
                    ["Rejected", formatNumber(batch.data.counts.rejected, 0)],
                  ]}
                />
                <EvidenceTable
                  columns={[
                    "Symbol",
                    "Run",
                    "Status",
                    "Readiness",
                    "Score",
                    "Warnings",
                    "Error",
                  ]}
                  emptyLabel="No runs were queued for this batch."
                  rows={batch.data.runs.map((run) => [
                    run.symbol,
                    <Link
                      key={run.run_id}
                      href={`/workstation/research/experiments/${run.experiment_id}/runs/${run.run_id}/overview`}
                    >
                      {run.run_id.slice(0, 12)}…
                    </Link>,
                    <StateBadge key={`${run.run_id}-s`} state={run.status} />,
                    run.readiness ?? "—",
                    formatScore(run.score),
                    formatNumber(run.warning_count, 0),
                    run.error ? `${run.error.code}: ${run.error.message}` : "—",
                  ])}
                />
              </Section>

              <Section
                title="Rejections"
                description="Symbols the server refused to queue, with the reason it gave."
              >
                <EvidenceTable
                  columns={["Symbol", "Code", "Detail"]}
                  emptyLabel="No symbols were rejected."
                  rows={batch.data.rejections.map((rejection, index) => [
                    rejection.symbol,
                    <Badge key={index} tone="negative">
                      {rejection.code}
                    </Badge>,
                    rejection.detail,
                  ])}
                />
              </Section>
            </>
          ) : null}
        </EvidenceGate>
      ) : null}
    </div>
  );
}
