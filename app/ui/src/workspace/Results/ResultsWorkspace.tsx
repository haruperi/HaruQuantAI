import React, { useMemo } from 'react';
import { Check, Copy, Download } from 'lucide-react';
import { DockviewReact, type DockviewReadyEvent } from 'dockview';
import { useAppStore } from '../../app/store';
import { Button, Section, Stat } from '../../components/ui';
import { EquityChart } from '../../components/EquityChart';
import { OptimizationSurface } from '../../plugins/optimization/OptimizationSurface';
import { PortfolioCorrelationView } from './views/PortfolioCorrelationView';

const views = [
  'Overview',
  'Trade list',
  'Equity chart',
  'Drawdown',
  'Trades on chart',
  'Trade analysis',
  'Strategy config',
  'Source code',
  'Robustness',
  'Optimization profile',
  'Parameter permutation',
  'Walk-forward',
  'Sequential optimization',
  'Correlation',
  'Portfolio',
  'Reports',
  'Prop analytics',
  'Prop Monte Carlo',
];

function Overview() {
  const lastExec = useAppStore(x => x.lastExecutionResult);
  const s = useAppStore(x => x.strategies.find(y => y.id === x.selectedStrategyId));

  if (lastExec) {
    const outputs = Object.entries(lastExec.outputs);
    return (
      <div className="results-overview" style={{ padding: 16 }}>
        <div style={{ padding: '10px 14px', background: 'rgba(255, 180, 0, 0.08)', border: '1px solid rgba(255, 180, 0, 0.4)', borderRadius: 6, marginBottom: 16, fontSize: '0.82rem', lineHeight: 1.5 }}>
          <strong>Trading Backtest Metrics Unavailable:</strong> Financial performance metrics (Net Profit, Profit Factor, Max Drawdown, Sharpe Ratio, Trade List) require a trading simulation backtest engine plugin (deferred to S6). Currently displaying algebraic node outputs and execution reproducibility produced by graph evaluation.
        </div>

        <div className="metric-strip" style={{ marginBottom: 16 }}>
          <Stat label="Execution Status" value={lastExec.success ? 'Success' : 'Failed'} tone={lastExec.success ? 'good' : 'bad'} />
          <Stat label="Elapsed Time" value={`${lastExec.elapsed_seconds.toFixed(4)}s`} />
          <Stat label="Output Ports" value={outputs.length} />
          <Stat label="Issues" value={lastExec.issues.length} tone={lastExec.issues.length > 0 ? 'bad' : undefined} />
          <Stat label="Seed" value={lastExec.reproducibility?.seed != null ? String(lastExec.reproducibility.seed) : 'None'} />
        </div>

        <Section title="Execution Reproducibility & Provenance" description="Cryptographic fingerprint and determinism record from backend execution runtime.">
          <dl className="details">
            <dt>Graph Fingerprint</dt>
            <dd style={{ fontFamily: 'monospace', fontSize: '0.8rem', wordBreak: 'break-all' }}>{lastExec.reproducibility?.graph_fingerprint ?? 'N/A'}</dd>
            <dt>Engine Version</dt>
            <dd>{lastExec.reproducibility?.engine_version ?? '1.0.0'}</dd>
            <dt>Elapsed Duration</dt>
            <dd>{lastExec.elapsed_seconds.toFixed(4)} seconds</dd>
          </dl>
        </Section>

        <Section title="Calculated Port Outputs" description="Direct calculation outputs keyed by <node_id>.<port_key>.">
          <div className="plain-table-wrap">
            <table className="plain-table">
              <thead>
                <tr>
                  <th>Port Key (&lt;node_id&gt;.&lt;port_key&gt;)</th>
                  <th>Type</th>
                  <th>Dimension</th>
                  <th>Value / Series Sample</th>
                </tr>
              </thead>
              <tbody>
                {outputs.map(([port, val]) => {
                  const isArr = Array.isArray(val);
                  return (
                    <tr key={port}>
                      <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>{port}</td>
                      <td>{isArr ? 'Float Array' : typeof val}</td>
                      <td>{isArr ? `${val.length} values` : 'Scalar'}</td>
                      <td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                        {isArr
                          ? `[${(val as unknown[]).slice(0, 6).map(v => typeof v === 'number' ? (v as number).toFixed(2) : String(v)).join(', ')}${(val as unknown[]).length > 6 ? ` ... +${(val as unknown[]).length - 6} more` : ''}]`
                          : String(val)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Section>

        {lastExec.issues.length > 0 && (
          <Section title="Execution Issues" description="Diagnostics encountered during graph evaluation.">
            <div className="plain-table-wrap">
              <table className="plain-table">
                <thead>
                  <tr>
                    <th>Path</th>
                    <th>Code</th>
                    <th>Message</th>
                  </tr>
                </thead>
                <tbody>
                  {lastExec.issues.map((iss, idx) => (
                    <tr key={idx}>
                      <td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{iss.path || 'graph'}</td>
                      <td><code>{iss.code}</code></td>
                      <td>{iss.message}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Section>
        )}
      </div>
    );
  }

  if (!s) return <Empty />;
  const wins = s.trades.filter(t => t.pnl > 0);
  return (
    <div className="results-overview">
      <div style={{ padding: '10px 14px', background: 'rgba(100, 100, 100, 0.1)', border: '1px solid var(--border)', borderRadius: 6, margin: '8px 16px 12px', fontSize: '0.82rem' }}>
        <strong>Illustrative Strategy Template Fixtures:</strong> Parities unverified; not produced by execution engine. Run evaluation in <em>Builder</em> or <em>Retester</em> to view real graph evaluation outputs.
      </div>
      <div className="metric-strip">
        <Stat
          label="Net profit (mock)"
          value={`$${s.metrics.netProfit.toLocaleString()}`}
          tone={s.metrics.netProfit > 0 ? 'good' : 'bad'}
        />
        <Stat label="Profit factor (mock)" value={s.metrics.profitFactor} />
        <Stat
          label="Max drawdown (mock)"
          value={`$${s.metrics.maxDrawdown.toLocaleString()}`}
          tone="bad"
        />
        <Stat label="Trades (mock)" value={s.metrics.trades} />
        <Stat label="Sharpe ratio (mock)" value={s.metrics.sharpe} />
        <Stat label="Stability (mock)" value={`${s.metrics.stability}%`} />
      </div>
      <div className="results-columns">
        <Section title="Equity (Illustrative preview)">
          <EquityChart data={s.equity} height={260} />
        </Section>
        <Section title="Performance summary (Template fixture)">
          <dl className="details">
            <dt>Strategy</dt>
            <dd>{s.name}</dd>
            <dt>Revision</dt>
            <dd>{s.revision}</dd>
            <dt>Market</dt>
            <dd>
              {s.symbol} · {s.timeframe}
            </dd>
            <dt>Winning trades</dt>
            <dd>
              {wins.length} ({Math.round((wins.length / s.trades.length) * 100)}%)
            </dd>
            <dt>Average trade</dt>
            <dd>${Math.round(s.metrics.netProfit / s.metrics.trades)}</dd>
            <dt>Direction</dt>
            <dd>{s.direction}</dd>
            <dt>Sample</dt>
            <dd>Full data (IS + OOS)</dd>
          </dl>
        </Section>
      </div>
    </div>
  );
}

function Config() {
  const s = useAppStore(x => x.strategies.find(y => y.id === x.selectedStrategyId));
  if (!s) return <Empty />;
  return (
    <div className="config-view">
      <Section title="Strategy properties">
        <dl className="details">
          {Object.entries(s.parameters).map(([k, v]) => (
            <React.Fragment key={k}>
              <dt>{k}</dt>
              <dd>{v}</dd>
            </React.Fragment>
          ))}
        </dl>
      </Section>
      <Section title="Trading logic">
        <div className="code-block">
          On Bar Open{'\n'}  IF EMA(FastPeriod) crosses above EMA(SlowPeriod){'\n'}  AND
          ATR(ATRPeriod) &gt; 0.0012{'\n'}    Enter Long at Market{'\n'}    Stop Loss =
          StopLoss pips{'\n'}    Profit Target = StopLoss × 2
        </div>
      </Section>
    </div>
  );
}

function Source() {
  const s = useAppStore(x => x.strategies.find(y => y.id === x.selectedStrategyId));
  if (!s) return <Empty />;
  return (
    <div className="source-view">
      <div className="subtoolbar">
        <select className="text-input">
          <option>MetaTrader 5</option>
          <option>MetaTrader 4</option>
          <option>TradeStation EasyLanguage</option>
          <option>JForex</option>
          <option>PseudoCode</option>
        </select>
        <Button>
          <Copy size={14} /> Copy
        </Button>
        <Button>
          <Download size={14} /> Download mock source
        </Button>
        <span className="mock-badge">Illustrative preview — not compiled</span>
      </div>
      <pre className="code-block">{`// ${s.name} — generated frontend preview\ninput int FastPeriod = ${s.parameters.FastPeriod};\ninput int SlowPeriod = ${s.parameters.SlowPeriod};\n\nvoid OnTick() {\n  if (isNewBar() && CrossAbove(EMA(FastPeriod), EMA(SlowPeriod))) {\n    trade.Buy(CalculateSize(), _Symbol, Ask, ${s.parameters.StopLoss}, ${s.parameters.StopLoss * 2});\n  }\n}`}</pre>
    </div>
  );
}

function OptimizationView({ mode }: { mode: string }) {
  const s = useAppStore(x => x.strategies.find(y => y.id === x.selectedStrategyId));
  const trials = useMemo(
    () =>
      Array.from({ length: 18 }, (_, i) => ({
        p: 5 + i * 3,
        profit:
          (s?.metrics.netProfit ?? 5000) *
          (0.65 + Math.sin(i / 3) * 0.22 + i / 45),
        dd: 900 + ((i * 389) % 1800),
      })),
    [s]
  );
  return (
    <div className="optimization-result">
      <Section
        title={`${mode} results`}
        description="Trials use the same deterministic strategy record and parameter sets."
      >
        <div className="profile-chart">
          {trials.map(t => (
            <div key={t.p} title={`${t.p}: $${Math.round(t.profit)}`}>
              <i style={{ height: `${Math.max(12, t.profit / 110)}px` }} />
              <span>{t.p}</span>
            </div>
          ))}
        </div>
      </Section>
      <div className="plain-table-wrap">
        <table className="plain-table">
          <thead>
            <tr>
              <th>Trial</th>
              <th>FastPeriod</th>
              <th>Net profit</th>
              <th>Drawdown</th>
              <th>Return / DD</th>
              <th>Verdict</th>
            </tr>
          </thead>
          <tbody>
            {trials.map((t, i) => (
              <tr key={t.p}>
                <td>#{i + 1}</td>
                <td>{t.p}</td>
                <td>${Math.round(t.profit).toLocaleString()}</td>
                <td>${t.dd.toLocaleString()}</td>
                <td>{(t.profit / t.dd).toFixed(2)}</td>
                <td>
                  <Check size={14} className="positive" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Empty() {
  return (
    <div className="empty-state">
      <strong>No strategy selected</strong>
      <span>Select a strategy in the databank to inspect its linked result set.</span>
    </div>
  );
}

function BacktestUnavailableView({ featureName }: { featureName: string }) {
  return (
    <div className="empty-state" style={{ padding: 32, textAlign: 'center' }}>
      <h3 style={{ marginBottom: 8 }}>Trading Backtest Required ({featureName})</h3>
      <p style={{ color: 'var(--muted)', fontSize: '0.85rem', maxWidth: 460, margin: '0 auto', lineHeight: 1.5 }}>
        Trading simulation, trade execution lists, and financial performance metrics require a dedicated backtesting engine plugin (deferred to S6).
      </p>
      <p style={{ color: 'var(--accent)', fontSize: '0.8rem', marginTop: 12 }}>
        Currently displaying algebraic node outputs and execution reproducibility from graph evaluation.
      </p>
    </div>
  );
}

function ResultPanel() {
  const view = useAppStore(s => s.resultView);
  const selected = useAppStore(s =>
    s.strategies.find(x => x.id === s.selectedStrategyId)
  );

  let content = <Overview />;
  if (view === 'Trade list') {
    content = <BacktestUnavailableView featureName="Trade list" />;
  } else if (view === 'Equity chart') {
    content = selected ? (
      <div style={{ padding: 16 }}>
        <div style={{ padding: '8px 12px', background: 'rgba(255, 180, 0, 0.08)', border: '1px solid rgba(255, 180, 0, 0.4)', borderRadius: 6, marginBottom: 12, fontSize: '0.82rem' }}>
          <strong>Illustrative Fixture Preview:</strong> Actual trading equity curves require a backtesting engine producing operation (deferred to S6).
        </div>
        <EquityChart data={selected.equity} height={400} />
      </div>
    ) : <Empty />;
  } else if (view === 'Drawdown') {
    content = <BacktestUnavailableView featureName="Drawdown analysis" />;
  } else if (view === 'Trades on chart') {
    content = <BacktestUnavailableView featureName="Trades on chart" />;
  } else if (view === 'Trade analysis') {
    content = <BacktestUnavailableView featureName="Trade analysis" />;
  } else if (view === 'Correlation') {
    content = selected ? <PortfolioCorrelationView strategy={selected} /> : <Empty />;
  } else if (view === 'Strategy config') {
    content = <Config />;
  } else if (view === 'Source code') {
    content = <Source />;
  } else if (view === 'Robustness' || view.includes('Prop')) {
    content = <BacktestUnavailableView featureName={view} />;
  } else if (view === 'Optimization profile') {
    content = (
      <OptimizationSurface
        strategyName={selected?.name ?? 'Optimization Profile'}
      />
    );
  } else if (!['Overview'].includes(view)) {
    content = <OptimizationView mode={view} />;
  }

  return <div className="docked-result-content">{content}</div>;
}

const dockComponents = { result: ResultPanel };

export function ResultsWorkspace() {
  const view = useAppStore(s => s.resultView);
  const set = useAppStore(s => s.setResultView);
  const selected = useAppStore(s =>
    s.strategies.find(x => x.id === s.selectedStrategyId)
  );

  const onReady = (event: DockviewReadyEvent) => {
    event.api.addPanel({
      id: 'linked-result',
      component: 'result',
      title: 'Linked strategy result',
    });
  };

  return (
    <div className="results-workspace">
      <aside>
        {views.map(v => (
          <button
            key={v}
            className={v === view ? 'active' : ''}
            onClick={() => set(v)}
          >
            {v}
          </button>
        ))}
      </aside>
      <main>
        <div style={{ padding: '10px 14px', background: 'rgba(48, 183, 232, 0.1)', border: '1px solid var(--accent)', borderRadius: 6, margin: '8px 16px 0', fontSize: '0.82rem' }}>
          <strong>Graph Evaluation Mode:</strong> Output values and reproducibility metadata are populated from execution gateway results. Trading backtest metrics (Sharpe, Drawdown, Profit Factor, Trade List) require a backtesting engine plugin (deferred to S6).
        </div>
        <div className="results-title">
          <div>
            <strong>{selected?.name ?? 'No strategy'}</strong>
            <span>
              {selected
                ? `${selected.symbol} · ${selected.timeframe} · revision ${selected.revision}`
                : ''}
            </span>
          </div>
          <div>
            <select className="text-input">
              <option>Full data</option>
              <option>In Sample</option>
              <option>Out of Sample</option>
            </select>
            <select className="text-input">
              <option>All directions</option>
              <option>Long</option>
              <option>Short</option>
            </select>
          </div>
        </div>
        <div className="dock-host dockview-theme-dark">
          <DockviewReact components={dockComponents} onReady={onReady} />
        </div>
      </main>
    </div>
  );
}
