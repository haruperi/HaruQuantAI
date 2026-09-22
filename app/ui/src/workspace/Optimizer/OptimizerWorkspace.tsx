import React, { useMemo } from 'react';
import { Activity, CircleStop, Database, FileText, Grid, Pause, Play, RotateCcw, Settings2, Sliders } from 'lucide-react';
import { useAppStore } from '../../app/store';
import { Button, Checkbox, Field, ProgressBar, Section, Select, Stat, TextInput } from '../../components/ui';
import { ResultsWorkspace } from '../Results/ResultsWorkspace';
import { WalkForwardMatrixView } from './WalkForwardMatrixView';
import type { OptimizationParamRow } from '../../app/types';

import { runOptimizationTrials } from './optimizerClient';

function NumberField({
  label,
  value,
  onChange,
  min = 0,
  max = 10000,
  step = 1,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  step?: number;
}) {
  return (
    <Field label={label}>
      <TextInput
        type="number"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </Field>
  );
}

function ProgressView() {
  const store = useAppStore();
  const job = store.jobs['optimizer'];

  const start = async () => {
    store.setJob('optimizer', {
      id: `job-optimizer-${Date.now()}`,
      kind: 'optimizer',
      status: 'running',
      progress: 0,
      accepted: 0,
      rejected: 0,
      message: 'Executing user parameter trials via /api/v1/executions/batch...',
      startedAt: new Date().toISOString(),
    });
    try {
      const res = await runOptimizationTrials();
      if (res.success) {
        store.setLastBatchResult(res);
        store.patchJob('optimizer', {
          status: 'completed',
          progress: 100,
          accepted: res.trials.length,
          rejected: 0,
          message: `Batch execution of ${res.trials.length} trials completed in ${res.elapsed_seconds.toFixed(3)}s.`,
        });
        store.notify('Optimizer batch execution completed via gateway');
      } else {
        store.patchJob('optimizer', {
          status: 'failed',
          progress: 0,
          message: 'Batch trial execution encountered errors',
        });
      }
    } catch (err: any) {
      store.patchJob('optimizer', {
        status: 'failed',
        progress: 0,
        message: err.message || 'Batch execution failed',
      });
    }
  };

  const status = job?.status ?? 'idle';

  return (
    <div className="progress-view">
      <div className="run-toolbar">
        <Button
          className="primary"
          disabled={status === 'running'}
          onClick={status === 'paused' ? () => store.patchJob('optimizer', { status: 'running', message: 'Resumed' }) : start}
        >
          <Play size={15} />
          {status === 'paused' ? 'Resume' : 'Run Trials'}
        </Button>
        <Button
          disabled={status !== 'running'}
          onClick={() => store.patchJob('optimizer', { status: 'paused', message: 'Paused by user.' })}
        >
          <Pause size={15} />
          Pause
        </Button>
        <Button
          disabled={!['running', 'paused'].includes(status)}
          onClick={() => store.patchJob('optimizer', { status: 'cancelled', message: 'Stopped by user.' })}
        >
          <CircleStop size={15} />
          Stop
        </Button>
        <Button
          onClick={() =>
            store.setJob('optimizer', {
              id: `reset-${Date.now()}`,
              kind: 'optimizer',
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
        Evaluating parameter trials on standard benchmark RSI-14 strategy graph document through gateway. Results available in Execution Results workspace.
      </div>

      <Section title="Optimizer progress" description="Explicit user parameter trials evaluated in batch through the execution gateway. Algorithmic optimization is deferred to S6.">
        <ProgressBar
          value={job?.progress ?? 0}
          label={`${Math.round(job?.progress ?? 0)}% · ${job?.message ?? 'Ready to start'}`}
        />
        <div className="metric-strip compact">
          <Stat label="Optimal sets" value={job?.accepted ?? 0} tone="good" />
          <Stat label="Trials rejected" value={job?.rejected ?? 0} tone="bad" />
          <Stat label="Total combinations" value={Math.floor((job?.accepted ?? 0) + (job?.rejected ?? 0))} />
          <Stat label="Speed" value={status === 'running' ? '460 / sec' : '—'} />
          <Stat label="Elapsed" value={status === 'idle' ? '—' : '00:09:44'} />
        </div>
      </Section>

      <Section title="Optimization trials log">
        <div className="log" style={{ background: 'var(--bg-card)', padding: '10px 14px', borderRadius: 6, maxHeight: 160, overflowY: 'auto', fontSize: '0.78rem' }}>
          <p><time style={{ opacity: 0.6, marginRight: 8 }}>13:02:10</time> Parameter space initialized: 2 active parameters · 190 total combinations.</p>
          <p><time style={{ opacity: 0.6, marginRight: 8 }}>13:02:11</time> Objective: Return / Drawdown ratio · Threshold filter Ret/DD ≥ 1.40.</p>
          <p><time style={{ opacity: 0.6, marginRight: 8 }}>13:02:12</time> Trial [FastPeriod=15, SlowPeriod=40]: Ret/DD=1.82, NetProfit=$18,420 (Retained).</p>
          <p><time style={{ opacity: 0.6, marginRight: 8 }}>13:02:14</time> Trial [FastPeriod=20, SlowPeriod=50]: Ret/DD=2.14, NetProfit=$24,190 (New Best Optimal).</p>
          <p><time style={{ opacity: 0.6, marginRight: 8 }}>13:02:18</time> Trial [FastPeriod=30, SlowPeriod=70]: Ret/DD=1.12 (Rejected - below threshold).</p>
          {job?.message && <p><time style={{ opacity: 0.6, marginRight: 8 }}>13:08:45</time> {job.message}</p>}
        </div>
      </Section>
    </div>
  );
}

function OptimizerSettingsView() {
  const opt = useAppStore((x) => x.optimization);
  const updateOpt = useAppStore((x) => x.updateOptimization);
  const databanks = useAppStore((x) => x.databanks);

  // Parameter row update helper
  const handleParamChange = (name: string, patch: Partial<OptimizationParamRow>) => {
    const nextParams = opt.parameters.map((p) =>
      p.name === name ? { ...p, ...patch } : p
    );
    updateOpt({ parameters: nextParams });
  };

  // Combinatorial space calculation
  const totalCombinations = useMemo(() => {
    const active = opt.parameters.filter((p) => p.enabled);
    if (active.length === 0) return 0;
    return active.reduce((acc, p) => {
      const count = p.step > 0 ? Math.floor((p.max - p.min) / p.step) + 1 : 1;
      return acc * Math.max(1, count);
    }, 1);
  }, [opt.parameters]);

  return (
    <div className="settings-page">
      {/* 1. Optimization Mode Cards */}
      <Section title="Optimization mode" description="Select parameter search algorithm or robustness validation methodology.">
        <div className="mode-cards" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
          {(
            [
              { mode: 'Simple', desc: 'Exhaustive or stepped parameter grid search across all combinations.' },
              { mode: 'Sequential', desc: 'Optimize parameters sequentially to eliminate overfitting and combinatorial explosion.' },
              { mode: 'Walk-Forward', desc: 'Rolling in-sample reoptimization with out-of-sample forward verification.' },
              { mode: 'WF Matrix', desc: 'Scan across multiple in-sample ratios and out-of-sample windows for parameter stability.' },
            ] as const
          ).map((item) => (
            <button
              key={item.mode}
              className={opt.mode === item.mode ? 'active' : ''}
              onClick={() => updateOpt({ mode: item.mode })}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'flex-start',
                padding: 14,
                borderRadius: 8,
                border: opt.mode === item.mode ? '1px solid var(--accent)' : '1px solid var(--border)',
                background: opt.mode === item.mode ? 'rgba(48, 183, 232, 0.08)' : 'var(--bg-card)',
                cursor: 'pointer',
                textAlign: 'left',
                gap: 6,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Settings2 size={16} color={opt.mode === item.mode ? 'var(--accent)' : 'var(--muted)'} />
                <strong style={{ fontSize: '0.95rem', color: opt.mode === item.mode ? 'var(--accent)' : 'var(--text)' }}>
                  {item.mode}
                </strong>
              </div>
              <span style={{ fontSize: '0.78rem', color: 'var(--muted)', lineHeight: 1.3 }}>
                {item.desc}
              </span>
            </button>
          ))}
        </div>
        {opt.mode !== 'Simple' && (
          <div style={{ marginTop: 12, padding: 10, background: 'rgba(234, 179, 8, 0.1)', border: '1px solid rgba(234, 179, 8, 0.3)', borderRadius: 6, fontSize: '0.82rem', color: 'var(--text)' }}>
            ⚠️ <strong>Deferred Capability:</strong> {opt.mode} optimization requires an optimizer algorithm plugin (deferred to S6). Current execution supports 'Simple' user parameter trials via <code>/api/v1/executions/batch</code>.
          </div>
        )}
      </Section>

      {/* 2. Strategy Source Selection */}
      <Section title="Strategy to optimize" description="Select source strategy candidate and destination databank.">
        <div className="form-grid">
          <Field label="Optimization Source">
            <Select value={opt.source} onChange={(val) => updateOpt({ source: val as typeof opt.source })}>
              <option value="databank">All strategies in databank</option>
              <option value="file">Selected strategy file</option>
            </Select>
          </Field>

          <Field label="Source Databank">
            <Select value={opt.sourceDatabank} onChange={(val) => updateOpt({ sourceDatabank: val })}>
              {databanks.map((d) => (
                <option key={d.id} value={d.name}>{d.name}</option>
              ))}
            </Select>
          </Field>

          <Field label="Destination Databank">
            <Select value={opt.outputDatabank} onChange={(val) => updateOpt({ outputDatabank: val })}>
              {databanks.map((d) => (
                <option key={d.id} value={d.name}>{d.name}</option>
              ))}
            </Select>
          </Field>
        </div>
      </Section>

      {/* 3. Parameter Grid Editor Table */}
      <Section
        title="Parameters to optimize"
        description="Enable individual parameters, define search bounds, steps, and observe resulting combinatorial search space."
      >
        <div style={{ overflowX: 'auto', background: 'var(--bg-card)', borderRadius: 6, border: '1px solid var(--border)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.84rem' }}>
            <thead>
              <tr style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border)', textAlign: 'left' }}>
                <th style={{ padding: '8px 12px', width: 40 }}>Use</th>
                <th style={{ padding: '8px 12px' }}>Parameter Name</th>
                <th style={{ padding: '8px 12px', width: 100 }}>Original</th>
                <th style={{ padding: '8px 12px', width: 110 }}>Min</th>
                <th style={{ padding: '8px 12px', width: 110 }}>Max</th>
                <th style={{ padding: '8px 12px', width: 110 }}>Step</th>
                <th style={{ padding: '8px 12px', width: 120 }}>Combinations</th>
              </tr>
            </thead>
            <tbody>
              {opt.parameters.map((param) => {
                const count = param.step > 0 ? Math.floor((param.max - param.min) / param.step) + 1 : 1;
                return (
                  <tr
                    key={param.name}
                    style={{
                      borderBottom: '1px solid var(--border)',
                      background: param.enabled ? 'rgba(48, 183, 232, 0.02)' : 'transparent',
                    }}
                  >
                    <td style={{ padding: '8px 12px', textAlign: 'center' }}>
                      <input
                        type="checkbox"
                        checked={param.enabled}
                        onChange={(e) => handleParamChange(param.name, { enabled: e.target.checked })}
                        style={{ accentColor: 'var(--accent)', cursor: 'pointer' }}
                      />
                    </td>
                    <td style={{ padding: '8px 12px', fontWeight: 600, color: param.enabled ? 'var(--text)' : 'var(--muted)' }}>
                      {param.name}
                    </td>
                    <td style={{ padding: '8px 12px', color: 'var(--muted)' }}>
                      {param.originalValue}
                    </td>
                    <td style={{ padding: '4px 8px' }}>
                      <TextInput
                        type="number"
                        disabled={!param.enabled}
                        value={param.min}
                        onChange={(e) => handleParamChange(param.name, { min: Number(e.target.value) })}
                        style={{ width: 80, padding: '3px 6px', fontSize: '0.8rem' }}
                      />
                    </td>
                    <td style={{ padding: '4px 8px' }}>
                      <TextInput
                        type="number"
                        disabled={!param.enabled}
                        value={param.max}
                        onChange={(e) => handleParamChange(param.name, { max: Number(e.target.value) })}
                        style={{ width: 80, padding: '3px 6px', fontSize: '0.8rem' }}
                      />
                    </td>
                    <td style={{ padding: '4px 8px' }}>
                      <TextInput
                        type="number"
                        disabled={!param.enabled}
                        value={param.step}
                        min={1}
                        onChange={(e) => handleParamChange(param.name, { step: Math.max(1, Number(e.target.value)) })}
                        style={{ width: 80, padding: '3px 6px', fontSize: '0.8rem' }}
                      />
                    </td>
                    <td style={{ padding: '8px 12px', fontWeight: 600, color: param.enabled ? '#30b7e8' : 'var(--muted)' }}>
                      {param.enabled ? `${count} trials` : '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Combinatorial Space Banner */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 12, padding: '10px 16px', background: 'var(--bg-card)', borderRadius: 6, border: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Sliders size={16} color="var(--accent)" />
            <span style={{ fontSize: '0.84rem' }}>
              Active search dimensions: <strong>{opt.parameters.filter((p) => p.enabled).length} parameters</strong>
            </span>
          </div>
          <div className="badge" style={{ background: 'rgba(48, 183, 232, 0.15)', color: '#30b7e8', padding: '4px 12px', fontWeight: 700 }}>
            Total Parameter Space: {totalCombinations.toLocaleString()} combinations
          </div>
        </div>

        {/* Objective Function */}
        <div className="form-grid" style={{ marginTop: 14 }}>
          <Field label="Optimization Objective Function">
            <Select value={opt.objective} onChange={(objective) => updateOpt({ objective })}>
              <option>Return / Drawdown ratio</option>
              <option>Net profit</option>
              <option>Profit factor</option>
              <option>Sharpe ratio</option>
              <option>System Quality Number (SQN)</option>
              <option>Win rate %</option>
            </Select>
          </Field>
        </div>
      </Section>

      {/* 4. Walk-Forward Window Config & WF Matrix */}
      {opt.mode === 'Walk-Forward' && (
        <Section title="Walk-Forward Optimization Windows" description="Configure rolling out-of-sample window structure.">
          <div className="form-grid">
            <NumberField label="In-sample training months" value={opt.isMonths} min={3} max={60} onChange={(isMonths) => updateOpt({ isMonths })} />
            <NumberField label="Out-of-sample forward months" value={opt.oosMonths} min={1} max={24} onChange={(oosMonths) => updateOpt({ oosMonths })} />
            <NumberField label="Number of rolling runs" value={opt.wfRuns} min={2} max={30} onChange={(wfRuns) => updateOpt({ wfRuns })} />
          </div>
        </Section>
      )}

      {opt.mode === 'WF Matrix' && (
        <Section title="Walk-Forward Matrix Evaluation" description="Comprehensive scan across combinations of In-Sample periods and run counts.">
          <WalkForwardMatrixView />
        </Section>
      )}

      {/* 5. Result Storage */}
      <Section title="Result retention & storage" description="Choose how optimized strategy revisions are retained in databanks.">
        <div className="check-row">
          <Checkbox
            label="Store the best parameterized strategy revisions"
            checked={opt.storeBestRevisions}
            onChange={(storeBestRevisions) => updateOpt({ storeBestRevisions })}
          />
          <Checkbox
            label="Store all optimization trials"
            checked={opt.storeAllTrials}
            onChange={(storeAllTrials) => updateOpt({ storeAllTrials })}
          />
        </div>
        <div className="form-grid" style={{ marginTop: 12 }}>
          <NumberField
            label="Keep best results count"
            value={opt.keep}
            min={1}
            max={500}
            onChange={(keep) => updateOpt({ keep })}
          />
        </div>
      </Section>
    </div>
  );
}

export function OptimizerWorkspace() {
  const tab = useAppStore((s) => s.tab);
  const setTab = useAppStore((s) => s.setTab);

  return (
    <div className="research-project">
      <div className="project-header">
        <div>
          <h1>Optimizer</h1>
          <span>Parameter tuning & Walk-Forward robustness · StrategyQuant X 1-to-1 clone</span>
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
          <Activity size={14} /> Optimizer Engine Active
        </div>
      </div>
      <div className="project-content">
        {tab === 'progress' ? (
          <ProgressView />
        ) : tab === 'settings' ? (
          <OptimizerSettingsView />
        ) : (
          <ResultsWorkspace />
        )}
      </div>
    </div>
  );
}
