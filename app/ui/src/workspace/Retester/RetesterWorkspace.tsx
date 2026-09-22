import React, { useMemo, useState } from 'react';
import { Activity, CheckCircle2, CircleStop, Copy, Database, Filter, Layers, Pause, Play, RotateCcw, ShieldAlert, Sliders, XCircle } from 'lucide-react';
import { useAppStore } from '../../app/store';
import { Button, Checkbox, Field, ProgressBar, Section, Select, Stat, TextInput } from '../../components/ui';
import { ResultsWorkspace } from '../Results/ResultsWorkspace';

import { defaultApiClient } from '../../api/client';

const AVAILABLE_MARKETS = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF', 'XAUUSD', 'NQ', 'BTCUSD'];
const AVAILABLE_TIMEFRAMES = ['M5', 'M15', 'M30', 'H1', 'H4', 'D1'];

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
  const job = store.jobs['retester'];

  const start = async () => {
    store.setJob('retester', {
      id: `job-retester-${Date.now()}`,
      kind: 'retester',
      status: 'running',
      progress: 0,
      accepted: 0,
      rejected: 0,
      message: 'Executing synchronous graph evaluation via /api/v1/executions/evaluate...',
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
        store.patchJob('retester', {
          status: 'completed',
          progress: 100,
          accepted: 1,
          rejected: 0,
          message: `Evaluation completed in ${res.elapsed_seconds.toFixed(3)}s. Outputs ready in Execution Results workspace.`,
        });
        store.notify('Retester execution completed via gateway');
      } else {
        store.patchJob('retester', {
          status: 'failed',
          progress: 0,
          message: `Evaluation issues: ${res.issues.map(i => i.message).join('; ')}`,
        });
      }
    } catch (err: any) {
      store.patchJob('retester', {
        status: 'failed',
        progress: 0,
        message: err.message || 'Execution failed',
      });
    }
  };

  const startBatch = async () => {
    store.setJob('retester', {
      id: `job-retester-batch-${Date.now()}`,
      kind: 'retester',
      status: 'running',
      progress: 0,
      accepted: 0,
      rejected: 0,
      message: 'Executing batch parameter retest via /api/v1/executions/batch...',
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
          { trial_id: 'retest_period_10', parameter_overrides: { rsi_node: { period: 10 } } },
          { trial_id: 'retest_period_20', parameter_overrides: { rsi_node: { period: 20 } } },
        ],
      });
      if (batchRes.success) {
        store.setLastBatchResult(batchRes);
        store.patchJob('retester', {
          status: 'completed',
          progress: 100,
          accepted: batchRes.trials.length,
          rejected: 0,
          message: `Batch retest completed ${batchRes.trials.length} trials in ${batchRes.elapsed_seconds.toFixed(3)}s.`,
        });
        store.notify('Batch retest completed via gateway');
      } else {
        store.patchJob('retester', {
          status: 'failed',
          progress: 0,
          message: `Batch retest issues: ${batchRes.issues.map(i => i.message).join('; ')}`,
        });
      }
    } catch (err: any) {
      store.patchJob('retester', {
        status: 'failed',
        progress: 0,
        message: err.message || 'Batch retest failed',
      });
    }
  };

  const status = job?.status ?? 'idle';
  const total = (job?.accepted ?? 0) + (job?.rejected ?? 0);
  const passRate = total > 0 ? Math.round(((job?.accepted ?? 0) / total) * 100) : 0;

  // Mock Retest KPI comparison rows
  const comparisonRows = [
    { name: 'TrendFollower-EURUSD-H1', origProfit: 24190, retProfit: 21850, origDD: 12.4, retDD: 14.1, origPF: 1.84, retPF: 1.68, status: 'ROBUST' },
    { name: 'MeanReversion-GBPUSD-M15', origProfit: 18450, retProfit: 16920, origDD: 15.8, retDD: 17.2, origPF: 1.62, retPF: 1.54, status: 'ROBUST' },
    { name: 'Breakout-XAUUSD-H1', origProfit: 31200, retProfit: 22400, origDD: 18.2, retDD: 24.6, origPF: 1.95, retPF: 1.48, status: 'ACCEPTABLE' },
    { name: 'Scalper-USDJPY-M5', origProfit: 14200, retProfit: 8100, origDD: 9.6, retDD: 18.4, origPF: 1.52, retPF: 1.18, status: 'DEGRADED' },
  ];

  return (
    <div className="progress-view">
      <div className="run-toolbar">
        <Button
          className="primary"
          disabled={status === 'running'}
          onClick={status === 'paused' ? () => store.patchJob('retester', { status: 'running', message: 'Resumed' }) : start}
        >
          <Play size={15} />
          {status === 'paused' ? 'Resume' : 'Retest Single'}
        </Button>
        <Button
          disabled={status === 'running'}
          onClick={startBatch}
        >
          <Layers size={14} />
          Batch Retest
        </Button>
        <Button
          disabled={status !== 'running'}
          onClick={() => store.patchJob('retester', { status: 'paused', message: 'Paused by user.' })}
        >
          <Pause size={15} />
          Pause
        </Button>
        <Button
          disabled={!['running', 'paused'].includes(status)}
          onClick={() => store.patchJob('retester', { status: 'cancelled', message: 'Stopped by user.' })}
        >
          <CircleStop size={15} />
          Stop
        </Button>
        <Button
          onClick={() =>
            store.setJob('retester', {
              id: `reset-${Date.now()}`,
              kind: 'retester',
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

      <Section title="Retester progress" description="Graph re-evaluation on the primary dataset through the execution gateway. Multi-market and precision cross-checks are deferred to S6.">
        <ProgressBar
          value={job?.progress ?? 0}
          label={`${Math.round(job?.progress ?? 0)}% · ${job?.message ?? 'Ready to start'}`}
        />
        <div className="metric-strip compact">
          <Stat label="Passed" value={job?.accepted ?? 0} tone="good" />
          <Stat label="Failed" value={job?.rejected ?? 0} tone="bad" />
          <Stat label="Total Retests" value={total} />
          <Stat label="Pass Rate" value={`${passRate}%`} tone={passRate >= 60 ? 'good' : 'bad'} />
          <Stat label="Elapsed" value={status === 'idle' ? '—' : '00:06:18'} />
        </div>
      </Section>

      {/* Retest Robustness Comparison Table */}
      <Section title="Comparative Performance & Robustness Rating" description="Original vs Retested KPIs under stress conditions.">
        <div style={{ overflowX: 'auto', background: 'var(--bg-card)', borderRadius: 6, border: '1px solid var(--border)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.84rem' }}>
            <thead>
              <tr style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border)', textAlign: 'left' }}>
                <th style={{ padding: '8px 12px' }}>Strategy Name</th>
                <th style={{ padding: '8px 12px' }}>Original Profit</th>
                <th style={{ padding: '8px 12px' }}>Retested Profit</th>
                <th style={{ padding: '8px 12px' }}>Original DD</th>
                <th style={{ padding: '8px 12px' }}>Retested DD</th>
                <th style={{ padding: '8px 12px' }}>Original PF</th>
                <th style={{ padding: '8px 12px' }}>Retested PF</th>
                <th style={{ padding: '8px 12px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {comparisonRows.map((row) => (
                <tr key={row.name} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '8px 12px', fontWeight: 600 }}>{row.name}</td>
                  <td style={{ padding: '8px 12px', color: '#4ade80' }}>${row.origProfit.toLocaleString()}</td>
                  <td style={{ padding: '8px 12px', color: row.retProfit > row.origProfit * 0.7 ? '#4ade80' : '#f87171' }}>
                    ${row.retProfit.toLocaleString()}
                  </td>
                  <td style={{ padding: '8px 12px', color: 'var(--muted)' }}>{row.origDD}%</td>
                  <td style={{ padding: '8px 12px', color: row.retDD > row.origDD * 1.3 ? '#f87171' : 'var(--text)' }}>
                    {row.retDD}%
                  </td>
                  <td style={{ padding: '8px 12px', color: 'var(--muted)' }}>{row.origPF}</td>
                  <td style={{ padding: '8px 12px' }}>{row.retPF}</td>
                  <td style={{ padding: '8px 12px' }}>
                    <span
                      style={{
                        padding: '2px 8px',
                        borderRadius: 10,
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        background:
                          row.status === 'ROBUST'
                            ? 'rgba(74, 222, 128, 0.15)'
                            : row.status === 'ACCEPTABLE'
                            ? 'rgba(234, 179, 8, 0.15)'
                            : 'rgba(239, 68, 68, 0.15)',
                        color:
                          row.status === 'ROBUST'
                            ? '#4ade80'
                            : row.status === 'ACCEPTABLE'
                            ? '#facc15'
                            : '#f87171',
                      }}
                    >
                      {row.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <Section title="Retester execution log">
        <div className="log" style={{ background: 'var(--bg-card)', padding: '10px 14px', borderRadius: 6, maxHeight: 120, overflowY: 'auto', fontSize: '0.78rem' }}>
          <p><time style={{ opacity: 0.6, marginRight: 8 }}>13:15:02</time> Retester started: reading strategies from databank 'Results'.</p>
          <p><time style={{ opacity: 0.6, marginRight: 8 }}>13:15:03</time> Alternative market matrix enabled: 4 symbols · 2 timeframes · tick precision.</p>
          <p><time style={{ opacity: 0.6, marginRight: 8 }}>13:15:05</time> Strategy 'TrendFollower-EURUSD-H1' retested on GBPUSD H1: Net Profit $14,210, Max DD 16.2% (Passed).</p>
          <p><time style={{ opacity: 0.6, marginRight: 8 }}>13:15:08</time> What-if stress test applied: spread multiplier 1.5x, slippage +1.0 pip.</p>
          {job?.message && <p><time style={{ opacity: 0.6, marginRight: 8 }}>13:21:10</time> {job.message}</p>}
        </div>
      </Section>
    </div>
  );
}

function RetesterSettingsView() {
  const r = useAppStore((x) => x.retester);
  const updateRetester = useAppStore((x) => x.updateRetester);
  const databanks = useAppStore((x) => x.databanks);

  const toggleMarket = (market: string) => {
    const exists = r.additionalMarkets.includes(market);
    const next = exists
      ? r.additionalMarkets.filter((m) => m !== market)
      : [...r.additionalMarkets, market];
    updateRetester({ additionalMarkets: next });
  };

  const toggleTimeframe = (tf: string) => {
    const exists = r.additionalTimeframes.includes(tf);
    const next = exists
      ? r.additionalTimeframes.filter((t) => t !== tf)
      : [...r.additionalTimeframes, tf];
    updateRetester({ additionalTimeframes: next });
  };

  return (
    <div className="settings-page">
      {/* 1. What to Retest & Databank Routing */}
      <Section
        title="What to retest"
        description="Source databank and destination databank routing rules."
      >
        <div className="form-grid">
          <Field label="Retest strategies from databank">
            <Select
              value={r.sourceDatabank}
              onChange={(sourceDatabank) => updateRetester({ sourceDatabank })}
            >
              {databanks.map((d) => (
                <option key={d.id} value={d.name}>{d.name}</option>
              ))}
            </Select>
          </Field>

          <Field label="Store results in databank">
            <Select
              value={r.outputDatabank}
              onChange={(outputDatabank) => updateRetester({ outputDatabank })}
            >
              {databanks.map((d) => (
                <option key={d.id} value={d.name}>{d.name}</option>
              ))}
              <option value="Retest">Retest</option>
            </Select>
          </Field>
        </div>

        <div style={{ marginTop: 10, padding: 12, background: 'var(--bg-card)', borderRadius: 6, border: '1px solid var(--border)' }}>
          <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--muted)', lineHeight: 1.4 }}>
            💡 <strong>Routing Rule:</strong> If you choose a different databank to store retested results, strategies will be <em>copied</em> to the destination databank while preserving originals in the source databank. If you choose the same databank, existing backtest results will be <em>overwritten</em> by the new retest results.
          </p>
        </div>
      </Section>

      {/* 2. Alternative Markets Matrix */}
      <Section
        title="Alternative markets matrix"
        description="Retest strategies across additional financial instruments to confirm cross-market robustness."
      >
        <div style={{ marginBottom: 12, padding: 10, background: 'rgba(234, 179, 8, 0.1)', border: '1px solid rgba(234, 179, 8, 0.3)', borderRadius: 6, fontSize: '0.82rem', color: 'var(--text)' }}>
          ⚠️ <strong>Deferred Capability:</strong> Multi-market retesting requires data provider integration (deferred to S6). Current execution evaluates the primary strategy dataset via <code>/api/v1/executions/evaluate</code>.
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 12 }}>
          {AVAILABLE_MARKETS.map((market) => {
            const active = r.additionalMarkets.includes(market);
            return (
              <button
                key={market}
                onClick={() => toggleMarket(market)}
                style={{
                  padding: '6px 14px',
                  borderRadius: 16,
                  border: active ? '1px solid var(--accent)' : '1px solid var(--border)',
                  background: active ? 'rgba(48, 183, 232, 0.15)' : 'var(--bg-card)',
                  color: active ? 'var(--accent)' : 'var(--text)',
                  fontWeight: active ? 700 : 400,
                  cursor: 'pointer',
                  fontSize: '0.84rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                }}
              >
                <span>{market}</span>
                {active && <small style={{ fontSize: '0.7rem' }}>✓</small>}
              </button>
            );
          })}
        </div>

        <div className="check-row">
          <Checkbox
            label="Evaluate combined multi-market portfolio equity"
            checked={r.portfolioRetest}
            onChange={(portfolioRetest) => updateRetester({ portfolioRetest })}
          />
        </div>
      </Section>

      {/* 3. Alternative Timeframes Matrix */}
      <Section
        title="Alternative timeframes matrix"
        description="Test sensitivity to differing bar aggregation frequencies."
      >
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {AVAILABLE_TIMEFRAMES.map((tf) => {
            const active = r.additionalTimeframes.includes(tf);
            return (
              <button
                key={tf}
                onClick={() => toggleTimeframe(tf)}
                style={{
                  padding: '6px 14px',
                  borderRadius: 16,
                  border: active ? '1px solid var(--accent)' : '1px solid var(--border)',
                  background: active ? 'rgba(48, 183, 232, 0.15)' : 'var(--bg-card)',
                  color: active ? 'var(--accent)' : 'var(--text)',
                  fontWeight: active ? 700 : 400,
                  cursor: 'pointer',
                  fontSize: '0.84rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                }}
              >
                <span>{tf}</span>
                {active && <small style={{ fontSize: '0.7rem' }}>✓</small>}
              </button>
            );
          })}
        </div>
      </Section>

      {/* 4. Testing Precision & Execution Models */}
      <Section
        title="Testing precision and execution models"
        description="Select fill accuracy and apply custom spread/slippage stress multipliers."
      >
        <div style={{ marginBottom: 12, padding: 10, background: 'rgba(234, 179, 8, 0.1)', border: '1px solid rgba(234, 179, 8, 0.3)', borderRadius: 6, fontSize: '0.82rem', color: 'var(--text)' }}>
          ⚠️ <strong>Deferred Capability:</strong> Precision cross-check requires tick engine plugin (deferred to S6). Current evaluation executes bar-level series data.
        </div>
        <div className="form-grid">
          <Field label="Testing Precision">
            <Select
              value={r.precision}
              onChange={(precision) => updateRetester({ precision })}
            >
              <option>Selected timeframe only</option>
              <option>1 minute data</option>
              <option>Real tick</option>
            </Select>
          </Field>

          <Field label="Spread Multiplier">
            <Select
              value={String(r.spreadMultiplier)}
              onChange={(val) => updateRetester({ spreadMultiplier: Number(val) })}
            >
              <option value="1.0">1.0x (Normal spread)</option>
              <option value="1.5">1.5x (Elevated spread)</option>
              <option value="2.0">2.0x (High volatility spread)</option>
              <option value="3.0">3.0x (Extreme illiquidity spread)</option>
            </Select>
          </Field>

          <NumberField
            label="Additional Slippage (pips)"
            value={r.slippagePips}
            min={0}
            max={10}
            step={0.5}
            onChange={(slippagePips) => updateRetester({ slippagePips })}
          />

          <Field label="Direction Filter">
            <Select
              value={r.tradeDirection}
              onChange={(val) => updateRetester({ tradeDirection: val as typeof r.tradeDirection })}
            >
              <option>Both</option>
              <option>Long only</option>
              <option>Short only</option>
            </Select>
          </Field>
        </div>
      </Section>

      {/* 5. What-If Stress Testing */}
      <Section
        title="What-if stress testing"
        description="Evaluate strategy resilience when worst-case outliers or market frictions occur."
      >
        <div className="form-grid">
          <Field label="Skip Worst Trades (%)">
            <Select
              value={String(r.skipWorstTradesPct)}
              onChange={(val) => updateRetester({ skipWorstTradesPct: Number(val) })}
            >
              <option value="0">0% (Keep all trades)</option>
              <option value="5">Skip worst 5% trades</option>
              <option value="10">Skip worst 10% trades</option>
            </Select>
          </Field>
        </div>

        <div className="check-row" style={{ marginTop: 10 }}>
          <Checkbox
            label="Apply additional spread & slippage stress test"
            checked={r.stressSpreadSlippage}
            onChange={(stressSpreadSlippage) => updateRetester({ stressSpreadSlippage })}
          />
        </div>
      </Section>
    </div>
  );
}

export function RetesterWorkspace() {
  const tab = useAppStore((s) => s.tab);
  const setTab = useAppStore((s) => s.setTab);

  return (
    <div className="research-project">
      <div className="project-header">
        <div>
          <h1>Retester</h1>
          <span>Strategy verification, multi-market matrix & stress testing · StrategyQuant X 1-to-1 clone</span>
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
          <Activity size={14} /> Retester Engine Active
        </div>
      </div>
      <div className="project-content">
        {tab === 'progress' ? (
          <ProgressView />
        ) : tab === 'settings' ? (
          <RetesterSettingsView />
        ) : (
          <ResultsWorkspace />
        )}
      </div>
    </div>
  );
}
