/**
 * Canonical backtest simulator (FEAT-UI-27).
 *
 * Presents the run configuration a human actually chooses, starts the run as a
 * background job, follows its ordered progress, and renders the Analytics-owned
 * performance report. The widget calculates nothing: every metric shown is a
 * figure the backend already reported as `calculated`, and a metric the report
 * omits stays explicitly unavailable rather than rendering as zero.
 */
"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import Link from "next/link";
import {
  AlertTriangle,
  CircleCheck,
  CircleSlash,
  FlaskConical,
  LoaderCircle,
  Play,
  Square,
} from "lucide-react";

import {
  ApiClientError,
  apiClients,
  openStream,
  type BacktestRun,
  type BacktestStrategy,
} from "@/clients";
import { simulatorRoutes } from "@/clients/routes";

/** Ordered metric rows, mirroring the backend's reported metric manifest. */
const METRIC_ROWS: readonly (readonly [string, string])[] = [
  ["starting_equity", "Equity Start"],
  ["ending_equity", "Equity Final"],
  ["net_pnl", "Net PnL"],
  ["cagr", "CAGR"],
  ["volatility", "Volatility (Ann.)"],
  ["sharpe_ratio", "Sharpe Ratio"],
  ["sortino_ratio", "Sortino Ratio"],
  ["calmar_ratio", "Calmar Ratio"],
  ["max_drawdown", "Max. Drawdown"],
  ["max_drawdown_duration", "Max. Drawdown Duration"],
  ["trade_count", "# Trades"],
  ["win_rate", "Win Rate"],
  ["profit_factor", "Profit Factor"],
  ["payoff_ratio", "Payoff Ratio"],
  ["expectancy", "Expectancy"],
  ["average_trade_duration", "Avg. Trade Duration"],
  ["total_commission", "Commission"],
  ["total_swap", "Swap"],
  ["total_cost_drag", "Total Cost Drag"],
  ["benchmark_alpha", "Alpha"],
  ["benchmark_beta", "Beta"],
  ["benchmark_correlation", "Benchmark Correlation"],
  ["tracking_error", "Tracking Error"],
  ["information_ratio", "Information Ratio"],
];

/** Canonical Data timeframes offered for a run. */
const TIMEFRAMES = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"] as const;

/** Ordered pipeline stages the backend reports. */
const STAGES: readonly (readonly [string, string])[] = [
  ["market_retrieval", "Market data"],
  ["tick_generation", "Tick generation"],
  ["simulation", "Simulation"],
  ["analytics", "Analytics"],
];

const ACTIVE_STATUSES = new Set(["queued", "running"]);

/** Poll budget used to settle a run whose progress stream ended early. */
const SETTLE_ATTEMPTS = 240;
const SETTLE_INTERVAL_MS = 3000;

/** Props accepted by `SimulatorWidget`. */
export interface SimulatorWidgetProps {
  className?: string;
}

/** Format an ISO date for a `date` input. */
function toDateInput(value: Date): string {
  return value.toISOString().slice(0, 10);
}

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
  return "The backtest service is unavailable.";
}

/** Canonical backtest configuration, execution, and reporting surface. */
export function SimulatorWidget({
  className,
}: SimulatorWidgetProps = {}): ReactNode {
  const [strategies, setStrategies] = useState<BacktestStrategy[]>([]);
  const [strategyId, setStrategyId] = useState("");
  const [parameters, setParameters] = useState<Record<string, string>>({});
  const [symbol, setSymbol] = useState("EURUSD");
  const [timeframe, setTimeframe] = useState<string>("H1");
  const [window, setWindow] = useState(defaultWindow);
  const [initialBalance, setInitialBalance] = useState("10000.00");
  const [volume, setVolume] = useState("0.1");
  const [commission, setCommission] = useState("7");
  const [spreadPoints, setSpreadPoints] = useState("10");
  const [slippagePoints, setSlippagePoints] = useState("1");

  const [catalogueError, setCatalogueError] = useState<string | null>(null);
  const [loadingCatalogue, setLoadingCatalogue] = useState(true);
  const [run, setRun] = useState<BacktestRun | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const strategy = useMemo(
    () => strategies.find((item) => item.strategy_id === strategyId) ?? null,
    [strategies, strategyId]
  );

  // Load the registered strategy catalogue once.
  useEffect(() => {
    let cancelled = false;
    setLoadingCatalogue(true);
    setCatalogueError(null);
    void apiClients.simulator
      .strategies()
      .then((response) => {
        if (cancelled) return;
        if (response.status === "error") throw new Error(response.error.message);
        setStrategies(response.data.strategies);
        const first = response.data.strategies.find((item) => item.runnable);
        if (first) setStrategyId(first.strategy_id);
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

  // Reset parameter overrides to the selected strategy's declared defaults.
  useEffect(() => {
    if (!strategy) return;
    setParameters(
      Object.fromEntries(
        strategy.parameters.map((item) => [item.name, item.default])
      )
    );
  }, [strategy]);

  // Abort any in-flight stream when the widget unmounts.
  useEffect(() => () => abortRef.current?.abort(), []);

  /**
   * Poll the run until it reports a terminal status.
   *
   * The progress stream can end early — a proxy timeout, a dropped connection,
   * a server-side frame failure — none of which mean the run stopped. The run
   * read is the authority, so the widget never reports a finished run as still
   * running.
   */
  const settle = useCallback(
    async (runId: string, controller: AbortController): Promise<boolean> => {
      for (let attempt = 0; attempt < SETTLE_ATTEMPTS; attempt += 1) {
        if (controller.signal.aborted) return true;
        const response = await apiClients.simulator.run(runId).catch(() => null);
        if (response && response.status === "success") {
          setRun(response.data);
          if (!ACTIVE_STATUSES.has(response.data.status)) return true;
        }
        await new Promise((resolve) => setTimeout(resolve, SETTLE_INTERVAL_MS));
      }
      return false;
    },
    []
  );

  const follow = useCallback(async (runId: string) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    try {
      for await (const event of openStream(simulatorRoutes.runStream, {
        pathParams: { run_id: runId },
        signal: controller.signal,
      })) {
        if (event.event_type === "heartbeat") continue;
        const payload = event.payload as Record<string, unknown>;
        if (typeof payload.status === "string") {
          // Terminal frame carries the complete run projection.
          setRun(payload as unknown as BacktestRun);
          return;
        }
        setRun((current) =>
          current
            ? {
                ...current,
                status: "running",
                stage: String(payload.stage ?? current.stage ?? ""),
                events: [
                  ...current.events,
                  {
                    sequence: Number(payload.sequence ?? 0),
                    at: String(payload.at ?? ""),
                    stage: String(payload.stage ?? ""),
                    detail: String(payload.detail ?? ""),
                  },
                ],
              }
            : current
        );
      }
      // The stream ended without a terminal frame. That is not proof the run
      // ended, so settle it against the authoritative read rather than leaving
      // the widget claiming it is still running.
      await settle(runId, controller);
    } catch (cause) {
      if (controller.signal.aborted) return;
      // The stream is only a progress convenience; the run itself is
      // authoritative and may well have succeeded.
      const settled = await settle(runId, controller);
      if (!settled) setRunError(failureMessage(cause));
    }
  }, [settle]);

  async function start(): Promise<void> {
    if (!strategy?.runnable) return;
    setStarting(true);
    setRunError(null);
    try {
      const response = await apiClients.simulator.startRun({
        symbol: symbol.trim().toUpperCase(),
        timeframe,
        start: new Date(`${window.start}T00:00:00Z`).toISOString(),
        end: new Date(`${window.end}T23:59:59Z`).toISOString(),
        strategy_id: strategy.strategy_id,
        parameters,
        initial_balance: initialBalance,
        volume,
        commission_per_lot_per_side: commission,
        spread_points: spreadPoints,
        slippage_points: slippagePoints,
      });
      if (response.status === "error") {
        setRunError(response.error.message);
        return;
      }
      setRun(response.data);
      void follow(response.data.job_id);
    } catch (cause) {
      setRunError(failureMessage(cause));
    } finally {
      setStarting(false);
    }
  }

  async function cancel(): Promise<void> {
    if (!run) return;
    abortRef.current?.abort();
    try {
      const response = await apiClients.simulator.cancelRun(run.job_id);
      if (response.status === "success") setRun(response.data);
    } catch (cause) {
      setRunError(failureMessage(cause));
    }
  }

  const active = run !== null && ACTIVE_STATUSES.has(run.status);
  const report = run?.result ?? null;
  // A blocked strategy's option is disabled and therefore unselectable, so its
  // reason has to be surfaced separately or the catalogue would look arbitrary.
  const blocked = useMemo(
    () => strategies.filter((item) => !item.runnable),
    [strategies]
  );

  return (
    <section
      className={`workflow-simulator ${className ?? ""}`.trim()}
      role="region"
      aria-label="Backtest simulator"
    >
      <header className="workflow-simulator__hero">
        <div>
          <span className="workflow-simulator__eyebrow">
            <FlaskConical size={14} /> Canonical simulation
          </span>
          <h2>Backtest simulator</h2>
          <p>
            Runs a registered strategy over genuine provider bars through
            Simulation authority, then reports Analytics-owned performance.
          </p>
        </div>
        <span
          className={`workflow-simulator__status workflow-simulator__status--${
            run?.status ?? "idle"
          }`}
        >
          {run ? run.status.toUpperCase() : "IDLE"}
        </span>
      </header>

      {catalogueError && (
        <div className="workflow-simulator__alert" role="alert">
          <AlertTriangle size={18} />
          <div>
            <strong>Strategy catalogue unavailable</strong>
            <span>{catalogueError}</span>
          </div>
        </div>
      )}

      <div className="workflow-simulator__grid">
        <form
          className="workflow-simulator__config"
          onSubmit={(submitEvent) => {
            submitEvent.preventDefault();
            void start();
          }}
        >
          <fieldset disabled={active || starting}>
            <legend>Strategy</legend>
            <label>
              Strategy
              <select
                value={strategyId}
                onChange={(changeEvent) => setStrategyId(changeEvent.target.value)}
              >
                {loadingCatalogue && <option value="">Loading…</option>}
                {strategies.map((item) => (
                  <option
                    key={item.strategy_id}
                    value={item.strategy_id}
                    disabled={!item.runnable}
                  >
                    {item.label}
                    {item.runnable ? "" : " — unavailable"}
                  </option>
                ))}
              </select>
            </label>
            {blocked.length > 0 && (
              <details className="workflow-simulator__blocked">
                <summary>
                  {blocked.length} strateg{blocked.length === 1 ? "y" : "ies"}{" "}
                  unavailable
                </summary>
                <ul>
                  {blocked.map((item) => (
                    <li key={item.strategy_id}>
                      <strong>{item.label}</strong>
                      {item.unavailable_reason}
                    </li>
                  ))}
                </ul>
              </details>
            )}
            {strategy?.parameters.map((item) => (
              <label key={item.name}>
                {item.label}
                <input
                  type="number"
                  value={parameters[item.name] ?? item.default}
                  min={item.minimum ?? undefined}
                  max={item.maximum ?? undefined}
                  step={item.kind === "integer" ? 1 : "any"}
                  onChange={(changeEvent) =>
                    setParameters((current) => ({
                      ...current,
                      [item.name]: changeEvent.target.value,
                    }))
                  }
                />
              </label>
            ))}
          </fieldset>

          <fieldset disabled={active || starting}>
            <legend>Market</legend>
            <label>
              Symbol
              <input
                value={symbol}
                onChange={(changeEvent) => setSymbol(changeEvent.target.value)}
              />
            </label>
            <label>
              Timeframe
              <select
                value={timeframe}
                onChange={(changeEvent) => setTimeframe(changeEvent.target.value)}
              >
                {TIMEFRAMES.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Start
              <input
                type="date"
                value={window.start}
                max={window.end}
                onChange={(changeEvent) =>
                  setWindow((current) => ({
                    ...current,
                    start: changeEvent.target.value,
                  }))
                }
              />
            </label>
            <label>
              End
              <input
                type="date"
                value={window.end}
                min={window.start}
                max={toDateInput(new Date())}
                onChange={(changeEvent) =>
                  setWindow((current) => ({
                    ...current,
                    end: changeEvent.target.value,
                  }))
                }
              />
            </label>
          </fieldset>

          <fieldset disabled={active || starting}>
            <legend>Execution</legend>
            <label>
              Initial balance
              <input
                type="number"
                min="0"
                step="any"
                value={initialBalance}
                onChange={(changeEvent) =>
                  setInitialBalance(changeEvent.target.value)
                }
              />
            </label>
            <label>
              Volume (lots)
              <input
                type="number"
                min="0"
                step="any"
                value={volume}
                onChange={(changeEvent) => setVolume(changeEvent.target.value)}
              />
            </label>
            <label>
              Commission / lot / side
              <input
                type="number"
                min="0"
                step="any"
                value={commission}
                onChange={(changeEvent) => setCommission(changeEvent.target.value)}
              />
            </label>
            <label>
              Spread (points)
              <input
                type="number"
                min="0"
                step="any"
                value={spreadPoints}
                onChange={(changeEvent) =>
                  setSpreadPoints(changeEvent.target.value)
                }
              />
            </label>
            <label>
              Slippage (points)
              <input
                type="number"
                min="0"
                step="any"
                value={slippagePoints}
                onChange={(changeEvent) =>
                  setSlippagePoints(changeEvent.target.value)
                }
              />
            </label>
          </fieldset>

          <div className="workflow-simulator__commands">
            <button
              type="submit"
              disabled={active || starting || !strategy?.runnable}
            >
              {starting ? (
                <LoaderCircle className="is-spinning" size={15} />
              ) : (
                <Play size={15} />
              )}
              Run backtest
            </button>
            <button type="button" onClick={() => void cancel()} disabled={!active}>
              <Square size={15} /> Cancel
            </button>
          </div>
          {runError && (
            <div className="workflow-simulator__alert" role="alert">
              <AlertTriangle size={18} />
              <div>
                <strong>Run rejected</strong>
                <span>{runError}</span>
              </div>
            </div>
          )}
        </form>

        <div className="workflow-simulator__output">
          {run && (
            <ol className="workflow-simulator__stages">
              {STAGES.map(([key, label]) => {
                const reached = run.events.some((item) => item.stage === key);
                const current = run.stage === key && active;
                return (
                  <li
                    key={key}
                    className={
                      current
                        ? "is-current"
                        : reached
                          ? "is-complete"
                          : "is-pending"
                    }
                  >
                    {current ? (
                      <LoaderCircle className="is-spinning" size={13} />
                    ) : reached ? (
                      <CircleCheck size={13} />
                    ) : (
                      <CircleSlash size={13} />
                    )}
                    {label}
                  </li>
                );
              })}
            </ol>
          )}

          {run && run.events.length > 0 && (
            <ul className="workflow-simulator__log" aria-label="Run progress" aria-live="polite">
              {run.events.slice(-12).map((item) => (
                <li key={item.sequence}>
                  <span>{item.stage}</span>
                  {item.detail}
                </li>
              ))}
            </ul>
          )}

          {run?.status === "failed" && (
            <div className="workflow-simulator__alert" role="alert">
              <AlertTriangle size={18} />
              <div>
                <strong>Backtest failed</strong>
                <span>{run.error ?? "The run reported no reason."}</span>
              </div>
            </div>
          )}

          {run?.status === "cancelled" && (
            <div className="workflow-simulator__warning" role="status">
              <CircleSlash size={18} />
              <div>
                <strong>Backtest cancelled</strong>
                <span>{run.error ?? "Cancelled by operator."}</span>
              </div>
            </div>
          )}

          {report && (
            <div className="workflow-simulator__report">
              <h3>Performance report</h3>
              <dl className="workflow-simulator__summary">
                <div>
                  <dt>Strategy</dt>
                  <dd>{report.strategy_label}</dd>
                </div>
                <div>
                  <dt>Instrument</dt>
                  <dd>
                    {report.symbol} {report.timeframe}
                  </dd>
                </div>
                <div>
                  <dt>Bars measured</dt>
                  <dd>{report.bar_count.toLocaleString()}</dd>
                </div>
                <div>
                  <dt>Warm-up bars</dt>
                  <dd>{report.warmup_bars.toLocaleString()}</dd>
                </div>
                <div>
                  <dt>Closed trades</dt>
                  <dd>{report.closed_trade_count.toLocaleString()}</dd>
                </div>
                <div>
                  <dt>Run ID</dt>
                  <dd className="is-mono">{report.run_id}</dd>
                </div>
              </dl>

              <table className="workflow-simulator__metrics">
                <caption>
                  Analytics-owned metrics. A metric the report did not calculate
                  is shown as unavailable.
                </caption>
                <tbody>
                  {METRIC_ROWS.map(([key, label]) => (
                    <tr key={key}>
                      <th scope="row">{label}</th>
                      <td>{report.metrics[key] ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {report.quality_flags.length > 0 && (
                <p className="workflow-simulator__note">
                  Quality flags: {report.quality_flags.join(", ")}
                </p>
              )}
              {report.caveats.length > 0 && (
                <p className="workflow-simulator__note">
                  Caveats: {report.caveats.join(", ")}
                </p>
              )}

              <div className="workflow-simulator__handoff mt-4 flex items-center justify-between p-3 rounded bg-slate-800/90 border border-slate-700">
                <div className="text-xs text-slate-400">
                  <span>Comprehensive 18-section breakdown available</span>
                </div>
                <Link
                  href={`/workstation/analytics/${encodeURIComponent(report.run_id)}/overview`}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded bg-teal-600 hover:bg-teal-500 text-white shadow"
                  aria-label="Inspect in Analytics Workspace"
                >
                  <FlaskConical size={14} aria-hidden="true" />
                  <span>Inspect in Analytics</span>
                </Link>
              </div>
            </div>
          )}

          {!run && !loadingCatalogue && (
            <p className="workflow-simulator__empty">
              Configure a strategy and window, then run a backtest.
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
