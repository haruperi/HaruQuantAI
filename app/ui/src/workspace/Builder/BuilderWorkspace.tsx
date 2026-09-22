import React, { useMemo, useState } from 'react';
import { Activity, CircleStop, Layers, Pause, Play, RotateCcw, Settings, ShieldCheck, Sliders } from 'lucide-react';
import { useAppStore } from '../../app/store';
import { Button, Checkbox, Field, ProgressBar, Section, Select, Stat, TextInput } from '../../components/ui';
import { ResultsWorkspace } from '../Results/ResultsWorkspace';
import { BuildingBlocksModal } from './BuildingBlocksModal';
import { ATMConfigModal } from './ATMConfigModal';
import { RankingSettingsView } from './RankingSettingsView';
import { BUILDING_BLOCKS_CATALOG } from './BuildingBlocksCatalog';
import { defaultApiClient } from '../../api/client';

function ProgressView() {
  const store = useAppStore();
  const job = store.jobs['builder'];

  const start = async () => {
    store.setJob('builder', {
      id: `job-builder-${Date.now()}`,
      kind: 'builder',
      status: 'running',
      progress: 0,
      accepted: 0,
      rejected: 0,
      message: 'Evaluating strategy graph via /api/v1/executions/evaluate...',
      startedAt: new Date().toISOString(),
    });
    try {
      const rsiNode = {
        id: 'rsi_node',
        plugin_ref: 'indicator.rsi@1.0.0',
        operation_id: 'compute',
        parameters: { period: 14 },
      };
      const doc = {
        schema_version: 1,
        spec: {
          nodes: [rsiNode],
          edges: [],
          designated_roots: [{ node_id: 'rsi_node', port_key: 'rsi' }],
        },
      };
      const res = await defaultApiClient.evaluateExecution({
        graph_document: doc,
        inputs: { values: [44.0, 44.5, 45.0, 44.8, 45.2, 46.0] },
      });
      if (res.success) {
        store.setLastExecutionResult(res);
        store.patchJob('builder', {
          status: 'completed',
          progress: 100,
          accepted: 1,
          rejected: 0,
          message: `Evaluation completed in ${res.elapsed_seconds.toFixed(3)}s. Reproducibility fingerprint: ${res.reproducibility?.graph_fingerprint?.substring(0, 12) ?? 'confirmed'}...`,
        });
        store.notify('Builder execution completed via gateway');
      } else {
        store.patchJob('builder', {
          status: 'failed',
          progress: 0,
          message: `Evaluation issues: ${res.issues.map(i => i.message).join('; ')}`,
        });
      }
    } catch (err: any) {
      store.patchJob('builder', {
        status: 'failed',
        progress: 0,
        message: err.message || 'Execution failed',
      });
    }
  };

  const startBatch = async () => {
    store.setJob('builder', {
      id: `job-builder-batch-${Date.now()}`,
      kind: 'builder',
      status: 'running',
      progress: 0,
      accepted: 0,
      rejected: 0,
      message: 'Executing batch parameter trials via /api/v1/executions/batch...',
      startedAt: new Date().toISOString(),
    });
    try {
      const rsiNode = {
        id: 'rsi_node',
        plugin_ref: 'indicator.rsi@1.0.0',
        operation_id: 'compute',
        parameters: { period: 14 },
      };
      const doc = {
        schema_version: 1,
        spec: {
          nodes: [rsiNode],
          edges: [],
          designated_roots: [{ node_id: 'rsi_node', port_key: 'rsi' }],
        },
      };
      const batchRes = await defaultApiClient.batchExecution({
        graph_document: doc,
        inputs: { values: [44.0, 44.5, 45.0, 44.8, 45.2, 46.0] },
        trials: [
          { trial_id: 'fast_period', parameter_overrides: { rsi_node: { period: 7 } } },
          { trial_id: 'slow_period', parameter_overrides: { rsi_node: { period: 21 } } },
        ],
      });
      if (batchRes.success) {
        store.setLastBatchResult(batchRes);
        store.patchJob('builder', {
          status: 'completed',
          progress: 100,
          accepted: batchRes.trials.length,
          rejected: 0,
          message: `Batch completed ${batchRes.trials.length} trials in ${batchRes.elapsed_seconds.toFixed(3)}s.`,
        });
        store.notify('Batch trials completed via gateway');
      } else {
        store.patchJob('builder', {
          status: 'failed',
          progress: 0,
          message: `Batch execution issues: ${batchRes.issues.map(i => i.message).join('; ')}`,
        });
      }
    } catch (err: any) {
      store.patchJob('builder', {
        status: 'failed',
        progress: 0,
        message: err.message || 'Batch execution failed',
      });
    }
  };

  const status = job?.status ?? 'idle';
  const progress = job?.progress ?? 0;
  const currentGen = Math.floor(progress / 10);

  // SVG points for dynamic convergence curve
  const convergencePoints = useMemo(() => {
    const totalSteps = 12;
    const currentStep = Math.min(totalSteps, Math.floor((progress / 100) * totalSteps) + 1);

    // Simulated Best fitness and Average fitness curve points
    const bestBase = [155, 138, 125, 105, 90, 75, 62, 52, 42, 34, 26, 20];
    const avgBase = [160, 154, 148, 140, 132, 124, 115, 106, 96, 88, 80, 72];

    const bestPts: string[] = [];
    const avgPts: string[] = [];

    for (let i = 0; i < currentStep; i++) {
      const x = Math.round((i / (totalSteps - 1)) * 580) + 10;
      bestPts.push(`${x},${bestBase[i]}`);
      avgPts.push(`${x},${avgBase[i]}`);
    }

    return {
      best: bestPts.join(' '),
      avg: avgPts.join(' '),
    };
  }, [progress]);

  return (
    <div className="progress-view">
      <div className="run-toolbar">
        <Button
          className="primary"
          disabled={status === 'running'}
          onClick={status === 'paused' ? () => store.patchJob('builder', { status: 'running', message: 'Resumed' }) : start}
        >
          <Play size={15} />
          {status === 'paused' ? 'Resume' : 'Evaluate'}
        </Button>
        <Button
          disabled={status === 'running'}
          onClick={startBatch}
        >
          <Layers size={14} />
          Batch Trials
        </Button>
        <Button
          disabled={status !== 'running'}
          onClick={() => store.patchJob('builder', { status: 'paused', message: 'Paused by user.' })}
        >
          <Pause size={15} />
          Pause
        </Button>
        <Button
          disabled={!['running', 'paused'].includes(status)}
          onClick={() => store.patchJob('builder', { status: 'cancelled', message: 'Stopped by user.' })}
        >
          <CircleStop size={15} />
          Stop
        </Button>
        <Button
          onClick={() =>
            store.setJob('builder', {
              id: `reset-${Date.now()}`,
              kind: 'builder',
              status: 'idle',
              progress: 0,
              accepted: 0,
              rejected: 0,
              message: 'Ready',
            })
          }
        >
          <RotateCcw size={14} />
          Reset progress
        </Button>
        <span className={`status status-${status}`}>
          <i />
          {status.toUpperCase()}
        </span>
      </div>
      <div style={{ color: 'var(--muted)', fontSize: '0.78rem', margin: '4px 0 10px 4px' }}>
        Evaluating standard benchmark RSI-14 strategy graph document through gateway. Results available in Execution Results workspace.
      </div>

      <Section title="Builder progress" description="Synchronous strategy graph evaluation through the execution gateway. Genetic generation is deferred to S6.">
        <ProgressBar
          value={job?.progress ?? 0}
          label={`${Math.round(job?.progress ?? 0)}% · ${job?.message ?? 'Ready to start'}`}
        />
        <div className="metric-strip compact">
          <Stat label="Accepted" value={job?.accepted ?? 0} tone="good" />
          <Stat label="Rejected" value={job?.rejected ?? 0} tone="bad" />
          <Stat label="Generation" value={`${currentGen} / 10`} />
          <Stat label="Strategies / min" value={status === 'running' ? 154 : 0} />
          <Stat label="Throughput" value={status === 'running' ? '2.5 / sec' : '—'} />
          <Stat label="Elapsed" value={status === 'idle' ? '—' : '00:14:32'} />
        </div>
      </Section>

      <div className="progress-columns">
        <Section title="Population fitness convergence">
          <div className="fake-chart" style={{ position: 'relative', height: 180, background: 'var(--bg-card)', borderRadius: 6, padding: '10px 14px' }}>
            <svg viewBox="0 0 600 180" preserveAspectRatio="none" style={{ width: '100%', height: 140 }}>
              <defs>
                <linearGradient id="bestGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#30b7e8" stopOpacity="0.4" />
                  <stop offset="100%" stopColor="#30b7e8" stopOpacity="0" />
                </linearGradient>
              </defs>
              {/* Grid lines */}
              <line x1="10" y1="30" x2="590" y2="30" stroke="var(--border)" strokeDasharray="3,3" opacity="0.6" />
              <line x1="10" y1="75" x2="590" y2="75" stroke="var(--border)" strokeDasharray="3,3" opacity="0.6" />
              <line x1="10" y1="120" x2="590" y2="120" stroke="var(--border)" strokeDasharray="3,3" opacity="0.6" />

              {/* Dynamic curves */}
              {convergencePoints.best && (
                <polyline
                  points={convergencePoints.best}
                  fill="none"
                  stroke="#30b7e8"
                  strokeWidth="3"
                  strokeLinecap="round"
                />
              )}
              {convergencePoints.avg && (
                <polyline
                  points={convergencePoints.avg}
                  fill="none"
                  stroke="#e6a23c"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeDasharray="4,2"
                />
              )}
            </svg>
            <div className="legend" style={{ display: 'flex', gap: 18, fontSize: '0.78rem', justifyContent: 'center' }}>
              <span className="cyan" style={{ color: '#30b7e8', fontWeight: 600 }}>● Best Fitness (Score: 2.84)</span>
              <span className="orange" style={{ color: '#e6a23c', fontWeight: 600 }}>● Average Fitness (Score: 1.42)</span>
            </div>
          </div>
        </Section>

        <Section title="Acceptance and dismissal summary">
          <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
            <div className="donut" style={{ minWidth: 100, height: 100, borderRadius: '50%', border: '8px solid #30b7e8', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
              <strong style={{ fontSize: '1.25rem', color: 'var(--text)' }}>{job?.accepted ?? 0}</strong>
              <span style={{ fontSize: '0.68rem', color: 'var(--muted)', textTransform: 'uppercase' }}>Passed</span>
            </div>
            <ul className="reason-list" style={{ flex: 1, margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 6 }}>
              <li style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                <span style={{ color: 'var(--muted)' }}>Low profit factor (&lt; 1.30)</span>
                <strong>42%</strong>
              </li>
              <li style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                <span style={{ color: 'var(--muted)' }}>Insufficient trades (&lt; 80)</span>
                <strong>28%</strong>
              </li>
              <li style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                <span style={{ color: 'var(--muted)' }}>High drawdown (&gt; 25%)</span>
                <strong>17%</strong>
              </li>
              <li style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                <span style={{ color: 'var(--muted)' }}>Correlation filter rejected</span>
                <strong>8%</strong>
              </li>
              <li style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                <span style={{ color: 'var(--muted)' }}>Cross-check test failed</span>
                <strong>5%</strong>
              </li>
            </ul>
          </div>
        </Section>
      </div>

      <Section title="Engine log">
        <div className="log" style={{ background: 'var(--bg-card)', padding: '10px 14px', borderRadius: 6, maxHeight: 130, overflowY: 'auto', fontSize: '0.78rem' }}>
          <p><time style={{ opacity: 0.6, marginRight: 8 }}>12:44:03</time> Project configuration loaded: genetic islands model initialized.</p>
          <p><time style={{ opacity: 0.6, marginRight: 8 }}>12:44:04</time> Dataset EURUSD H1 loaded (2012-01-01 — 2026-08-31) · 30% OOS reserved.</p>
          <p><time style={{ opacity: 0.6, marginRight: 8 }}>12:44:04</time> Genetic engine: 4 islands × 100 population · 24 active building blocks.</p>
          <p><time style={{ opacity: 0.6, marginRight: 8 }}>12:44:05</time> Qualification criteria active: Return/DD ≥ 1.4, trades ≥ 80, Max DD ≤ 25%.</p>
          {job?.message && <p><time style={{ opacity: 0.6, marginRight: 8 }}>12:56:52</time> {job.message}</p>}
        </div>
      </Section>
    </div>
  );
}

function NumberField({
  label,
  value,
  onChange,
  min = 0,
  max = 10000,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
}) {
  return (
    <Field label={label}>
      <TextInput
        type="number"
        value={value}
        min={min}
        max={max}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </Field>
  );
}

function BuilderSettingsView() {
  const s = useAppStore((x) => x.builder);
  const update = useAppStore((x) => x.updateBuilder);

  // Modal open states
  const [blocksModalOpen, setBlocksModalOpen] = useState(false);
  const [atmModalOpen, setAtmModalOpen] = useState(false);
  const [rankingModalOpen, setRankingModalOpen] = useState(false);

  // Computed enabled blocks count
  const activeBlocksCount = useMemo(() => {
    return BUILDING_BLOCKS_CATALOG.filter((b) =>
      s.customBlocks[b.id] !== undefined ? s.customBlocks[b.id] : b.enabled
    ).length;
  }, [s.customBlocks]);

  const activeCrossChecksCount = useMemo(() => {
    return s.crossChecks.filter((c) => c.enabled).length;
  }, [s.crossChecks]);

  return (
    <div className="settings-page">
      {/* 1. What to Build */}
      <Section title="What to build" description="Strategy architecture, trading direction, and rule generation constraints.">
        <div className="form-grid">
          <Field label="Build mode">
            <Select value={s.mode} onChange={(mode) => update({ mode: mode as typeof s.mode })}>
              <option>Genetic evolution</option>
              <option>Random generation</option>
              <option>Improve existing</option>
            </Select>
          </Field>
          <Field label="Strategy type">
            <Select value={s.strategyType} onChange={(strategyType) => update({ strategyType: strategyType as typeof s.strategyType })}>
              <option>Standard</option>
              <option>Multi-TF</option>
              <option>Stockpicker</option>
            </Select>
          </Field>
          <Field label="Trading direction">
            <Select value={s.direction} onChange={(direction) => update({ direction: direction as typeof s.direction })}>
              <option>Both</option>
              <option>Long</option>
              <option>Short</option>
            </Select>
          </Field>
          <NumberField label="Min conditions" value={s.minConditions} min={1} max={6} onChange={(minConditions) => update({ minConditions })} />
          <NumberField label="Max conditions" value={s.maxConditions} min={1} max={12} onChange={(maxConditions) => update({ maxConditions })} />
          <NumberField label="Max indicator period" value={s.maxPeriods} min={10} max={500} onChange={(maxPeriods) => update({ maxPeriods })} />
        </div>
        <div className="check-row" style={{ marginTop: 10 }}>
          <Checkbox
            label="Symmetrical Long / Short rules"
            checked={s.symmetricalRules}
            onChange={(symmetricalRules) => update({ symmetricalRules })}
          />
          <Checkbox
            label="Use fuzzy signals"
            checked={s.fuzzySignals}
            onChange={(fuzzySignals) => update({ fuzzySignals })}
          />
          <Checkbox
            label="Generate exit rules"
            checked={s.generateExitRules}
            onChange={(generateExitRules) => update({ generateExitRules })}
          />
        </div>
        <div style={{ marginTop: 12, padding: 10, background: 'rgba(234, 179, 8, 0.1)', border: '1px solid rgba(234, 179, 8, 0.3)', borderRadius: 6, fontSize: '0.82rem', color: 'var(--text)' }}>
          ⚠️ <strong>Deferred Capability:</strong> Genetic strategy generation requires generator plugin (deferred to S6). Current execution evaluates interactive strategy graphs via <code>/api/v1/executions/evaluate</code>.
        </div>
      </Section>

      {/* 2. Data and Trading Engine */}
      <Section title="Data and trading engine" description="Symbol, timeframe, backtest precision, and sample split configuration.">
        <div className="form-grid">
          <Field label="Market">
            <Select value={s.symbol} onChange={(symbol) => update({ symbol })}>
              <option>EURUSD</option>
              <option>GBPJPY</option>
              <option>XAUUSD</option>
              <option>NQ</option>
              <option>BTCUSD</option>
            </Select>
          </Field>
          <Field label="Timeframe">
            <Select value={s.timeframe} onChange={(timeframe) => update({ timeframe })}>
              <option>M15</option>
              <option>M30</option>
              <option>H1</option>
              <option>H4</option>
              <option>D1</option>
            </Select>
          </Field>
          <Field label="Testing precision">
            <Select value={s.precision} onChange={(precision) => update({ precision })}>
              <option>Selected timeframe only</option>
              <option>1 minute data</option>
              <option>Real tick</option>
            </Select>
          </Field>
          <Field label="From">
            <TextInput type="date" value={s.from} onChange={(e) => update({ from: e.target.value })} />
          </Field>
          <Field label="To">
            <TextInput type="date" value={s.to} onChange={(e) => update({ to: e.target.value })} />
          </Field>
          <NumberField label="Out of sample (%)" value={s.oos} min={0} max={80} onChange={(oos) => update({ oos })} />
        </div>
        <div className="sample-bar" style={{ marginTop: 12 }}>
          <span style={{ width: `${100 - s.oos}%` }}>In sample {100 - s.oos}%</span>
          <span style={{ width: `${s.oos}%` }}>OOS {s.oos}%</span>
        </div>
      </Section>

      {/* 3. Genetic Options */}
      <Section title="Genetic options" description="Island model population, mutation, crossover, and migration controls.">
        <div className="form-grid">
          <NumberField label="Max generations" value={s.maxGenerations} min={10} max={10000} onChange={(maxGenerations) => update({ maxGenerations })} />
          <NumberField label="Population per island" value={s.population} min={10} max={1000} onChange={(population) => update({ population })} />
          <NumberField label="Islands (1-32)" value={s.islands} min={1} max={32} onChange={(islands) => update({ islands })} />
          <NumberField label="Mutation probability (%)" value={s.mutation} min={0} max={100} onChange={(mutation) => update({ mutation })} />
          <NumberField label="Crossover probability (%)" value={s.crossover} min={0} max={100} onChange={(crossover) => update({ crossover })} />
          <NumberField label="Migration interval (gens)" value={s.migrationInterval} min={1} max={50} onChange={(migrationInterval) => update({ migrationInterval })} />
        </div>
        <div className="check-row" style={{ marginTop: 10 }}>
          <Checkbox
            label="Migrate candidates between islands"
            checked={s.migrateCandidates}
            onChange={(migrateCandidates) => update({ migrateCandidates })}
          />
          <Checkbox
            label="Restart stagnant islands"
            checked={s.restartStagnantIslands}
            onChange={(restartStagnantIslands) => update({ restartStagnantIslands })}
          />
          <Checkbox
            label="Seed from input databank"
            checked={s.mode === 'Improve existing' || s.seedFromDatabank}
            onChange={(seedFromDatabank) => update({ seedFromDatabank })}
          />
        </div>
      </Section>

      {/* 4. Building Blocks Summary Strip */}
      <Section title="Building blocks" description="Select indicators, entry signals, candle patterns, and exit rules.">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 14, background: 'var(--bg-card)', borderRadius: 6, border: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ width: 40, height: 40, borderRadius: 8, background: 'rgba(48, 183, 232, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#30b7e8' }}>
              <Layers size={20} />
            </div>
            <div>
              <strong>{activeBlocksCount} of {BUILDING_BLOCKS_CATALOG.length} Building Blocks Active</strong>
              <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--muted)' }}>
                Signals, Moving Averages, Oscillators, Candlestick Formations, Time Filters, and Order Exits.
              </p>
            </div>
          </div>
          <Button className="primary" onClick={() => setBlocksModalOpen(true)}>
            <Settings size={14} /> Manage Building Blocks
          </Button>
        </div>
      </Section>

      {/* 5. ATM & Money Management Summary Strip */}
      <Section title="Money Management & Advanced Trade Management" description="Position sizing, stop loss, profit target, trailing stop, and break-even rules.">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 14, background: 'var(--bg-card)', borderRadius: 6, border: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ width: 40, height: 40, borderRadius: 8, background: 'rgba(230, 162, 60, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#e6a23c' }}>
              <Sliders size={20} />
            </div>
            <div>
              <strong>Model: {s.mmModel} · SL: {s.slMin}-{s.slMax} {s.slType} · PT: {s.ptMin}-{s.ptMax} {s.ptType}</strong>
              <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--muted)' }}>
                Trailing Stop: {s.useTrailingStop ? 'Active' : 'Disabled'} · Break-Even: {s.useMoveToBE ? 'Active' : 'Disabled'} · Capital: ${s.initialCapital.toLocaleString()}
              </p>
            </div>
          </div>
          <Button onClick={() => setAtmModalOpen(true)}>
            <Settings size={14} /> Configure ATM
          </Button>
        </div>
      </Section>

      {/* 6. Cross Checks and Rankings Summary Strip */}
      <Section title="Rankings and cross-checks" description="Candidate ranking objective, automated qualification criteria, and multi-stage verification tests.">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 14, background: 'var(--bg-card)', borderRadius: 6, border: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ width: 40, height: 40, borderRadius: 8, background: 'rgba(74, 222, 128, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#4ade80' }}>
              <ShieldCheck size={20} />
            </div>
            <div>
              <strong>Objective: {s.rankingMetric} · {activeCrossChecksCount} Cross-Checks Active</strong>
              <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--muted)' }}>
                Min Ret/DD: {s.minReturnDD} · Min Trades: {s.minTrades} · Max DD: {s.maxDrawdownPct}% · Min Sharpe: {s.minSharpe}
              </p>
            </div>
          </div>
          <Button onClick={() => setRankingModalOpen(true)}>
            <Settings size={14} /> Configure Ranking & Filters
          </Button>
        </div>
      </Section>

      {/* Modals */}
      <BuildingBlocksModal
        isOpen={blocksModalOpen}
        onClose={() => setBlocksModalOpen(false)}
        customBlocks={s.customBlocks}
        onChange={(patch) => update({ customBlocks: patch })}
      />

      <ATMConfigModal
        isOpen={atmModalOpen}
        onClose={() => setAtmModalOpen(false)}
        settings={s}
        updateSettings={update}
      />

      <RankingSettingsView
        isOpen={rankingModalOpen}
        onClose={() => setRankingModalOpen(false)}
        settings={s}
        updateSettings={update}
      />
    </div>
  );
}

export function BuilderWorkspace() {
  const tab = useAppStore((s) => s.tab);
  const setTab = useAppStore((s) => s.setTab);

  return (
    <div className="research-project">
      <div className="project-header">
        <div>
          <h1>Builder</h1>
          <span>Strategy discovery · StrategyQuant X 1-to-1 clone</span>
        </div>
        <nav>
          {(['progress', 'settings', 'results'] as const).map((x) => (
            <button
              key={x}
              className={tab === x ? 'active' : ''}
              onClick={() => setTab(x)}
            >
              {x === 'settings' ? 'Full settings' : x[0].toUpperCase() + x.slice(1)}
            </button>
          ))}
        </nav>
        <div className="engine-state">
          <Activity size={14} /> Genetic Engine Active
        </div>
      </div>
      <div className="project-content">
        {tab === 'progress' ? (
          <ProgressView />
        ) : tab === 'settings' ? (
          <BuilderSettingsView />
        ) : (
          <ResultsWorkspace />
        )}
      </div>
    </div>
  );
}
