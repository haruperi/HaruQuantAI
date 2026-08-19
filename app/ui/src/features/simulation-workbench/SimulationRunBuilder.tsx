/**
 * Staged canonical run builder (FEAT-UI-31).
 *
 * Implements the eight configuration stages of the Simulation Workbench run
 * builder. The builder owns operator choices only: every derived value, metric,
 * status, and identity remains server-authoritative, and no internal request,
 * config, data, or risk hash is ever offered as an editable input or submitted.
 */

"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  ApiClientError,
  apiClients,
  type BacktestStrategy,
} from "@/clients";

/** Ordered builder stages exactly as specified for the workbench. */
export const BUILDER_STAGES = [
  "mode",
  "strategy",
  "market",
  "execution",
  "risk",
  "scenario",
  "metadata",
  "review",
] as const;

/** One builder stage identifier. */
export type BuilderStage = (typeof BUILDER_STAGES)[number];

/** Human labels for each ordered builder stage. */
const STAGE_LABELS: Readonly<Record<BuilderStage, string>> = {
  mode: "Mode",
  strategy: "Strategy",
  market: "Market",
  execution: "Execution and costs",
  risk: "Risk and governance",
  scenario: "Scenario and mission",
  metadata: "Metadata",
  review: "Review",
};

/** Run modes offered by the builder. */
export const BUILDER_MODES = [
  "canonical_backtest",
  "visual_practice",
  "manual_practice",
  "batch",
  "replay",
  "scenario_mission",
  "portfolio",
] as const;

/** One selectable builder run mode. */
export type BuilderMode = (typeof BUILDER_MODES)[number];

const MODE_LABELS: Readonly<Record<BuilderMode, string>> = {
  canonical_backtest: "Canonical Backtest",
  visual_practice: "Visual Practice",
  manual_practice: "Manual Practice",
  batch: "Batch",
  replay: "Replay",
  scenario_mission: "Scenario/Mission",
  portfolio: "Portfolio Simulation",
};

/** Modes this builder can submit today; the rest stay explicitly unavailable. */
const SUBMITTABLE_MODES: ReadonlySet<BuilderMode> = new Set<BuilderMode>([
  "canonical_backtest",
  "batch",
]);

/** Exact message rendered for a mode with no submission destination yet. */
const MODE_UNAVAILABLE =
  "This mode has no submission destination in the current workbench build.";

/** Canonical Data timeframes offered for a run. */
const TIMEFRAMES = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"] as const;

/** Frozen batch bounds mirroring the server contract. */
const MAX_BATCH_ITEMS = 100;
const MAX_BATCH_CONCURRENCY = 8;
const MAX_TAGS = 16;
const MAX_TAG_LENGTH = 64;

/** Exact canonical request defaults shared with the canonical simulator. */
export const RUN_DEFAULTS = {
  symbol: "EURUSD",
  timeframe: "H1",
  initial_balance: "10000.00",
  account_currency: "USD",
  volume: "0.1",
  commission_per_lot_per_side: "7",
  spread_points: "10",
  slippage_points: "1",
} as const;

/** Default measurement window: the previous full calendar year. */
function defaultWindow(): { start: string; end: string } {
  const year = new Date().getUTCFullYear() - 1;
  return { start: `${year}-01-01`, end: `${year}-12-31` };
}

/** Resolve a failure message without inventing a successful outcome. */
function failureMessage(cause: unknown): string {
  if (cause instanceof ApiClientError || cause instanceof Error) {
    return cause.message;
  }
  return "The simulator service is unavailable.";
}

/** Generate one idempotency key for a single submission identity. */
function newIdempotencyKey(): string {
  const source = globalThis.crypto;
  if (source && typeof source.randomUUID === "function") {
    return source.randomUUID();
  }
  return `run-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

/** Split a free-text list into bounded, trimmed, non-empty entries. */
function splitList(value: string): string[] {
  return value
    .split(/[\s,]+/)
    .map((entry) => entry.trim())
    .filter((entry) => entry.length > 0);
}

/** Outcome handed to the caller after a successful submission. */
export type RunBuilderSubmission =
  | { kind: "run"; runId: string }
  | { kind: "batch"; batchId: string };

/** Props accepted by `SimulationRunBuilder`. */
export interface SimulationRunBuilderProps {
  initialMode?: BuilderMode;
  onSubmitted?: (submission: RunBuilderSubmission) => void;
  className?: string;
}

/** Staged canonical and batch run builder. */
export function SimulationRunBuilder({
  initialMode = "canonical_backtest",
  onSubmitted,
  className = "",
}: SimulationRunBuilderProps = {}): ReactNode {
  const [stage, setStage] = useState<BuilderStage>("mode");
  const [mode, setMode] = useState<BuilderMode>(initialMode);

  const [strategies, setStrategies] = useState<BacktestStrategy[]>([]);
  const [catalogueError, setCatalogueError] = useState<string | null>(null);
  const [loadingCatalogue, setLoadingCatalogue] = useState(true);
  const [strategyId, setStrategyId] = useState("");
  const [parameters, setParameters] = useState<Record<string, string>>({});

  const [symbol, setSymbol] = useState<string>(RUN_DEFAULTS.symbol);
  const [batchSymbols, setBatchSymbols] = useState<string>(RUN_DEFAULTS.symbol);
  const [timeframe, setTimeframe] = useState<string>(RUN_DEFAULTS.timeframe);
  const [window, setWindow] = useState(defaultWindow);
  const [barLimit, setBarLimit] = useState("");
  const [accountCurrency, setAccountCurrency] = useState<string>(
    RUN_DEFAULTS.account_currency,
  );

  const [initialBalance, setInitialBalance] = useState<string>(
    RUN_DEFAULTS.initial_balance,
  );
  const [volume, setVolume] = useState<string>(RUN_DEFAULTS.volume);
  const [commission, setCommission] = useState<string>(
    RUN_DEFAULTS.commission_per_lot_per_side,
  );
  const [spreadPoints, setSpreadPoints] = useState<string>(
    RUN_DEFAULTS.spread_points,
  );
  const [slippagePoints, setSlippagePoints] = useState<string>(
    RUN_DEFAULTS.slippage_points,
  );

  const [concurrency, setConcurrency] = useState("1");
  const [scenarioId, setScenarioId] = useState("");
  const [missionId, setMissionId] = useState("");
  const [assistanceMode, setAssistanceMode] = useState("none");

  const [name, setName] = useState("");
  const [alias, setAlias] = useState("");
  const [description, setDescription] = useState("");
  const [tagsText, setTagsText] = useState("");
  const [runReason, setRunReason] = useState("");

  const [idempotencyKey, setIdempotencyKey] = useState(newIdempotencyKey);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState<RunBuilderSubmission | null>(null);

  // Load the registered strategy catalogue once.
  useEffect(() => {
    let cancelled = false;
    setLoadingCatalogue(true);
    apiClients.simulator
      .strategies()
      .then((response) => {
        if (cancelled) return;
        if (response.status === "error") {
          setCatalogueError(response.error.message);
          return;
        }
        setStrategies(response.data.strategies);
        const first = response.data.strategies.find((item) => item.runnable);
        if (first) {
          setStrategyId(first.strategy_id);
          setParameters(
            Object.fromEntries(
              first.parameters.map((item) => [item.name, item.default]),
            ),
          );
        }
      })
      .catch((cause: unknown) => {
        if (!cancelled) setCatalogueError(failureMessage(cause));
      })
      .finally(() => {
        if (!cancelled) setLoadingCatalogue(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const strategy = useMemo(
    () => strategies.find((item) => item.strategy_id === strategyId) ?? null,
    [strategies, strategyId],
  );

  const selectStrategy = useCallback(
    (nextId: string) => {
      setStrategyId(nextId);
      const next = strategies.find((item) => item.strategy_id === nextId);
      setParameters(
        next
          ? Object.fromEntries(
              next.parameters.map((item) => [item.name, item.default]),
            )
          : {},
      );
    },
    [strategies],
  );

  const tags = useMemo(() => splitList(tagsText), [tagsText]);
  const symbolUniverse = useMemo(
    () => splitList(batchSymbols),
    [batchSymbols],
  );

  /** Collect every blocking validation problem for the current draft. */
  const problems = useMemo(() => {
    const found: string[] = [];

    if (!SUBMITTABLE_MODES.has(mode)) {
      found.push(MODE_UNAVAILABLE);
      return found;
    }

    if (!strategyId) {
      found.push("Select a strategy before submitting.");
    } else if (strategy && !strategy.runnable) {
      found.push(
        strategy.unavailable_reason ??
          "The selected strategy is not runnable today.",
      );
    }

    if (mode === "batch") {
      if (symbolUniverse.length === 0) {
        found.push("Provide at least one batch symbol.");
      }
      if (symbolUniverse.length > MAX_BATCH_ITEMS) {
        found.push(`A batch accepts at most ${MAX_BATCH_ITEMS} items.`);
      }
      const parsedConcurrency = Number(concurrency);
      if (
        !Number.isInteger(parsedConcurrency) ||
        parsedConcurrency < 1 ||
        parsedConcurrency > MAX_BATCH_CONCURRENCY
      ) {
        found.push(`Concurrency must be between 1 and ${MAX_BATCH_CONCURRENCY}.`);
      }
    } else if (!symbol.trim()) {
      found.push("Provide a symbol.");
    }

    if (!window.start || !window.end) {
      found.push("Provide both a start and an end date.");
    } else if (window.start > window.end) {
      found.push("The start date must not be after the end date.");
    }

    if (barLimit.trim() && !/^\d+$/.test(barLimit.trim())) {
      found.push("The bars limit must be a whole number.");
    }

    if (tags.length > MAX_TAGS) {
      found.push(`At most ${MAX_TAGS} tags are allowed.`);
    }
    if (tags.some((tag) => tag.length > MAX_TAG_LENGTH)) {
      found.push(`Each tag must be at most ${MAX_TAG_LENGTH} characters.`);
    }

    return found;
  }, [
    mode,
    strategyId,
    strategy,
    symbol,
    symbolUniverse,
    concurrency,
    window,
    barLimit,
    tags,
  ]);

  const submit = useCallback(async () => {
    if (problems.length > 0 || submitting) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      if (mode === "batch") {
        const response = await apiClients.simulationWorkbench.createBatch(
          {
            items: symbolUniverse.map((entry) => ({
              symbol: entry,
              timeframe,
              strategy_id: strategyId,
              parameters,
              start: window.start,
              end: window.end,
            })),
            concurrency: Number(concurrency),
            ...(name.trim() ? { name: name.trim() } : {}),
          },
          { idempotencyKey },
        );
        if (response.status === "error") {
          setSubmitError(response.error.message);
          return;
        }
        const outcome: RunBuilderSubmission = {
          kind: "batch",
          batchId: response.data.batch_id,
        };
        setSubmitted(outcome);
        setIdempotencyKey(newIdempotencyKey());
        onSubmitted?.(outcome);
        return;
      }

      const response = await apiClients.simulator.startRun(
        {
          symbol: symbol.trim(),
          timeframe,
          start: window.start,
          end: window.end,
          strategy_id: strategyId,
          parameters,
          initial_balance: initialBalance,
          account_currency: accountCurrency,
          volume,
          commission_per_lot_per_side: commission,
          spread_points: spreadPoints,
          slippage_points: slippagePoints,
          ...(barLimit.trim() ? { bar_limit: Number(barLimit.trim()) } : {}),
        },
        { idempotencyKey },
      );
      if (response.status === "error") {
        setSubmitError(response.error.message);
        return;
      }
      const outcome: RunBuilderSubmission = {
        kind: "run",
        runId: response.data.job_id,
      };
      setSubmitted(outcome);
      setIdempotencyKey(newIdempotencyKey());
      onSubmitted?.(outcome);
    } catch (cause) {
      setSubmitError(failureMessage(cause));
    } finally {
      setSubmitting(false);
    }
  }, [
    problems,
    submitting,
    mode,
    symbolUniverse,
    timeframe,
    strategyId,
    parameters,
    window,
    concurrency,
    name,
    idempotencyKey,
    symbol,
    initialBalance,
    accountCurrency,
    volume,
    commission,
    spreadPoints,
    slippagePoints,
    barLimit,
    onSubmitted,
  ]);

  return (
    <section
      className={`simulation-run-builder ${className}`.trim()}
      aria-label="Simulation run builder"
    >
      <ol className="simulation-run-builder__stages" aria-label="Builder stages">
        {BUILDER_STAGES.map((item, index) => (
          <li key={item}>
            <button
              type="button"
              aria-current={stage === item ? "step" : undefined}
              onClick={() => setStage(item)}
              className="simulation-run-builder__stage-btn"
            >
              {index + 1}. {STAGE_LABELS[item]}
            </button>
          </li>
        ))}
      </ol>

      {stage === "mode" ? (
        <fieldset>
          <legend>Stage 1 — Mode</legend>
          {BUILDER_MODES.map((item) => (
            <label key={item} className="simulation-run-builder__option">
              <input
                type="radio"
                name="builder-mode"
                value={item}
                checked={mode === item}
                onChange={() => setMode(item)}
              />
              <span>{MODE_LABELS[item]}</span>
            </label>
          ))}
          {!SUBMITTABLE_MODES.has(mode) ? (
            <p role="note">{MODE_UNAVAILABLE}</p>
          ) : null}
        </fieldset>
      ) : null}

      {stage === "strategy" ? (
        <fieldset>
          <legend>Stage 2 — Strategy</legend>
          {loadingCatalogue ? <p>Loading strategy catalogue…</p> : null}
          {catalogueError ? (
            <p role="alert">{catalogueError}</p>
          ) : null}
          <label htmlFor="builder-strategy">Strategy</label>
          <select
            id="builder-strategy"
            value={strategyId}
            onChange={(event) => selectStrategy(event.target.value)}
          >
            <option value="">Select a strategy</option>
            {strategies.map((item) => (
              <option key={item.strategy_id} value={item.strategy_id}>
                {item.label} ({item.strategy_version})
                {item.runnable ? "" : " — unavailable"}
              </option>
            ))}
          </select>

          {strategy ? (
            <div className="simulation-run-builder__strategy">
              <p>Version: {strategy.strategy_version}</p>
              <p>Evaluator: {strategy.evaluator_name}</p>
              <p>Runnable: {strategy.runnable ? "yes" : "no"}</p>
              {strategy.unavailable_reason ? (
                <p role="note">{strategy.unavailable_reason}</p>
              ) : null}
              <p>
                Warm-up indicators:{" "}
                {strategy.required_indicators.length > 0
                  ? strategy.required_indicators.join(", ")
                  : "none"}
              </p>
              {strategy.parameters.map((item) => (
                <div key={item.name}>
                  <label htmlFor={`param-${item.name}`}>{item.label}</label>
                  <input
                    id={`param-${item.name}`}
                    value={parameters[item.name] ?? item.default}
                    onChange={(event) =>
                      setParameters((current) => ({
                        ...current,
                        [item.name]: event.target.value,
                      }))
                    }
                  />
                </div>
              ))}
            </div>
          ) : null}
        </fieldset>
      ) : null}

      {stage === "market" ? (
        <fieldset>
          <legend>Stage 3 — Market</legend>
          {mode === "batch" ? (
            <>
              <label htmlFor="builder-batch-symbols">Batch universe</label>
              <input
                id="builder-batch-symbols"
                value={batchSymbols}
                onChange={(event) => setBatchSymbols(event.target.value)}
              />
              <p>
                {symbolUniverse.length} of {MAX_BATCH_ITEMS} batch items
              </p>
              <label htmlFor="builder-concurrency">Concurrency</label>
              <input
                id="builder-concurrency"
                value={concurrency}
                onChange={(event) => setConcurrency(event.target.value)}
              />
            </>
          ) : (
            <>
              <label htmlFor="builder-symbol">Symbol</label>
              <input
                id="builder-symbol"
                value={symbol}
                onChange={(event) => setSymbol(event.target.value)}
              />
            </>
          )}

          <label htmlFor="builder-timeframe">Timeframe</label>
          <select
            id="builder-timeframe"
            value={timeframe}
            onChange={(event) => setTimeframe(event.target.value)}
          >
            {TIMEFRAMES.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>

          <label htmlFor="builder-start">Start</label>
          <input
            id="builder-start"
            type="date"
            value={window.start}
            onChange={(event) =>
              setWindow((current) => ({ ...current, start: event.target.value }))
            }
          />

          <label htmlFor="builder-end">End</label>
          <input
            id="builder-end"
            type="date"
            value={window.end}
            onChange={(event) =>
              setWindow((current) => ({ ...current, end: event.target.value }))
            }
          />

          <label htmlFor="builder-bar-limit">Bars limit</label>
          <input
            id="builder-bar-limit"
            value={barLimit}
            onChange={(event) => setBarLimit(event.target.value)}
          />

          <label htmlFor="builder-currency">Account currency</label>
          <input
            id="builder-currency"
            value={accountCurrency}
            onChange={(event) => setAccountCurrency(event.target.value)}
          />
        </fieldset>
      ) : null}

      {stage === "execution" ? (
        <fieldset>
          <legend>Stage 4 — Execution and costs</legend>
          <label htmlFor="builder-balance">Initial balance</label>
          <input
            id="builder-balance"
            value={initialBalance}
            onChange={(event) => setInitialBalance(event.target.value)}
          />

          <label htmlFor="builder-volume">Volume</label>
          <input
            id="builder-volume"
            value={volume}
            onChange={(event) => setVolume(event.target.value)}
          />

          <label htmlFor="builder-commission">
            Commission per lot per side
          </label>
          <input
            id="builder-commission"
            value={commission}
            onChange={(event) => setCommission(event.target.value)}
          />

          <label htmlFor="builder-spread">Spread points</label>
          <input
            id="builder-spread"
            value={spreadPoints}
            onChange={(event) => setSpreadPoints(event.target.value)}
          />

          <label htmlFor="builder-slippage">Slippage points</label>
          <input
            id="builder-slippage"
            value={slippagePoints}
            onChange={(event) => setSlippagePoints(event.target.value)}
          />

          <p>
            Execution realism preset and leverage evidence are server-derived and
            reported with the run result.
          </p>
        </fieldset>
      ) : null}

      {stage === "risk" ? (
        <fieldset>
          <legend>Stage 5 — Risk and governance</legend>
          <p>
            The registered risk policy, approved practice limits, and
            exposure guardrails are applied by the server. They are shown with
            the resulting run evidence and are not editable here.
          </p>
          <p>
            Evidence declaration:{" "}
            {mode === "canonical_backtest"
              ? "canonical"
              : mode === "batch"
                ? "canonical batch member"
                : "advisory"}
          </p>
        </fieldset>
      ) : null}

      {stage === "scenario" ? (
        <fieldset>
          <legend>Stage 6 — Scenario, mission, and assistance</legend>
          <label htmlFor="builder-scenario">Scenario ID</label>
          <input
            id="builder-scenario"
            value={scenarioId}
            onChange={(event) => setScenarioId(event.target.value)}
          />

          <label htmlFor="builder-mission">Mission</label>
          <input
            id="builder-mission"
            value={missionId}
            onChange={(event) => setMissionId(event.target.value)}
          />

          <label htmlFor="builder-assistance">Assistance mode</label>
          <select
            id="builder-assistance"
            value={assistanceMode}
            onChange={(event) => setAssistanceMode(event.target.value)}
          >
            <option value="none">None</option>
            <option value="guided">Guided</option>
            <option value="coached">Coached</option>
          </select>

          <p>
            Scenario, checklist, fault, and calibration profiles apply to
            practice sessions only and are ignored by a canonical run.
          </p>
        </fieldset>
      ) : null}

      {stage === "metadata" ? (
        <fieldset>
          <legend>Stage 7 — Metadata</legend>
          <label htmlFor="builder-name">Name</label>
          <input
            id="builder-name"
            value={name}
            onChange={(event) => setName(event.target.value)}
          />

          <label htmlFor="builder-alias">Alias</label>
          <input
            id="builder-alias"
            value={alias}
            onChange={(event) => setAlias(event.target.value)}
          />

          <label htmlFor="builder-description">Description</label>
          <textarea
            id="builder-description"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />

          <label htmlFor="builder-tags">Tags</label>
          <input
            id="builder-tags"
            value={tagsText}
            onChange={(event) => setTagsText(event.target.value)}
          />

          <label htmlFor="builder-reason">Run reason</label>
          <input
            id="builder-reason"
            value={runReason}
            onChange={(event) => setRunReason(event.target.value)}
          />
        </fieldset>
      ) : null}

      {stage === "review" ? (
        <fieldset>
          <legend>Stage 8 — Review</legend>
          <dl className="simulation-run-builder__review">
            <dt>Mode</dt>
            <dd>{MODE_LABELS[mode]}</dd>
            <dt>Strategy</dt>
            <dd>{strategy ? `${strategy.label} (${strategy.strategy_version})` : "—"}</dd>
            <dt>Market</dt>
            <dd>
              {mode === "batch" ? symbolUniverse.join(", ") : symbol} · {timeframe}
            </dd>
            <dt>Window</dt>
            <dd>
              {window.start} → {window.end}
            </dd>
            <dt>Initial balance</dt>
            <dd>
              {initialBalance} {accountCurrency}
            </dd>
            <dt>Costs</dt>
            <dd>
              commission {commission} · spread {spreadPoints} · slippage{" "}
              {slippagePoints}
            </dd>
            <dt>Evidence class</dt>
            <dd>{mode === "canonical_backtest" || mode === "batch" ? "Official canonical" : "Advisory"}</dd>
            <dt>Expected stages</dt>
            <dd>Market data → Tick generation → Simulation → Analytics</dd>
            <dt>Permission</dt>
            <dd>simulation:run</dd>
            <dt>Tags</dt>
            <dd>{tags.length > 0 ? tags.join(", ") : "—"}</dd>
            <dt>Run reason</dt>
            <dd>{runReason || "—"}</dd>
          </dl>

          {problems.length > 0 ? (
            <ul role="alert" aria-label="Validation problems">
              {problems.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : null}

          {submitError ? <p role="alert">{submitError}</p> : null}

          {submitted ? (
            <p role="status">
              {submitted.kind === "run"
                ? `Run submitted: ${submitted.runId}`
                : `Batch submitted: ${submitted.batchId}`}
            </p>
          ) : null}

          <button
            type="button"
            onClick={() => void submit()}
            disabled={problems.length > 0 || submitting}
          >
            {submitting ? "Submitting…" : "Submit run"}
          </button>
        </fieldset>
      ) : null}
    </section>
  );
}
