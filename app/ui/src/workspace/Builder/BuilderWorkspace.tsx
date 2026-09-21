import { useEffect, useRef } from 'react';
import { Activity, CircleStop, Pause, Play, RotateCcw } from 'lucide-react';
import { useAppStore } from '../../app/store';
import { mockResearchService } from '../../mocks/service';
import { Button, Checkbox, Field, ProgressBar, Section, Select, Stat, TextInput } from '../../components/ui';
import { ResultsWorkspace } from '../Results/ResultsWorkspace';

function ProgressView() {
  const store = useAppStore(); const job = store.jobs['builder']; const timer = useRef<number | null>(null);
  useEffect(() => {
    if (job?.status !== 'running') return;
    timer.current = window.setInterval(() => {
      const latest = useAppStore.getState().jobs['builder'];
      if (!latest || latest.status !== 'running') return;
      const next = Math.min(100, latest.progress + 2);
      useAppStore.getState().patchJob('builder', {
        progress: next, accepted: Math.floor(next * .31), rejected: Math.floor(next * 1.72),
        message: next >= 100 ? 'Research run completed; results retained in databank.' : `Evaluating population ${Math.floor(next / 10) + 1}…`,
        status: next >= 100 ? 'completed' : 'running'
      });
    }, 420);
    return () => { if (timer.current) clearInterval(timer.current); };
  }, [job?.status]);
  const start = async () => { const created = await mockResearchService.start('builder'); store.setJob('builder', created); store.notify('Builder mock run started'); };
  const status = job?.status ?? 'idle';
  return (
    <div className="progress-view">
      <div className="run-toolbar">
        <Button className="primary" disabled={status === 'running'} onClick={status === 'paused' ? () => store.patchJob('builder', { status: 'running', message: 'Resumed' }) : start}><Play size={15}/>{status === 'paused' ? 'Resume' : 'Start'}</Button>
        <Button disabled={status !== 'running'} onClick={() => store.patchJob('builder', { status: 'paused', message: 'Paused by user; job state retained.' })}><Pause size={15}/>Pause</Button>
        <Button disabled={!['running', 'paused'].includes(status)} onClick={() => store.patchJob('builder', { status: 'cancelled', message: 'Stopped by user; accepted results retained.' })}><CircleStop size={15}/>Stop</Button>
        <Button onClick={() => store.setJob('builder', { id: `reset-${Date.now()}`, kind: 'builder', status: 'idle', progress: 0, accepted: 0, rejected: 0, message: 'Ready' })}><RotateCcw size={14}/>Reset progress</Button>
        <span className={`status status-${status}`}><i/>{status.toUpperCase()}</span>
      </div>
      <Section title="Builder progress" description="Deterministic frontend simulation; no native HaruQuantAI engine or external process is running.">
        <ProgressBar value={job?.progress ?? 0} label={`${Math.round(job?.progress ?? 0)}% · ${job?.message ?? 'Ready to start'}`}/>
        <div className="metric-strip compact">
          <Stat label="Accepted" value={job?.accepted ?? 0} tone="good"/>
          <Stat label="Rejected" value={job?.rejected ?? 0} tone="bad"/>
          <Stat label="Generation" value={Math.floor((job?.progress ?? 0) / 10)}/>
          <Stat label="Strategies / min" value={status === 'running' ? 138 : 0}/>
          <Stat label="Elapsed" value={status === 'idle' ? '—' : '00:12:48'}/>
        </div>
      </Section>
      <div className="progress-columns">
        <Section title="Population fitness">
          <div className="fake-chart">
            <svg viewBox="0 0 600 170" preserveAspectRatio="none">
              <polyline points="0,155 45,138 90,142 140,105 190,116 240,83 290,91 340,58 390,66 440,37 490,44 540,21 600,28" fill="none" stroke="#30b7e8" strokeWidth="3"/>
              <polyline points="0,160 45,155 90,148 140,146 190,134 240,130 290,124 340,112 390,106 440,96 490,88 540,82 600,74" fill="none" stroke="#e6a23c" strokeWidth="2"/>
            </svg>
            <div className="legend"><span className="cyan">Best fitness</span><span className="orange">Average fitness</span></div>
          </div>
        </Section>
        <Section title="Acceptance summary">
          <div className="donut"><div><strong>{job?.accepted ?? 0}</strong><span>accepted</span></div></div>
          <ul className="reason-list">
            <li><span>Low profit factor</span><strong>46%</strong></li>
            <li><span>Insufficient trades</span><strong>29%</strong></li>
            <li><span>High drawdown</span><strong>18%</strong></li>
            <li><span>Correlation filter</span><strong>7%</strong></li>
          </ul>
        </Section>
      </div>
      <Section title="Engine log">
        <div className="log">
          <p><time>12:44:03</time> Project configuration loaded from mock persistence.</p>
          <p><time>12:44:04</time> Dataset EURUSD H1 resolved (2012-01-01 — 2026-08-31).</p>
          <p><time>12:44:04</time> Genetic engine: 4 islands × 100 population.</p>
          <p><time>12:44:05</time> Ranking: Return/DD ≥ 1.4, trades ≥ 80.</p>
          {job && <p><time>12:56:52</time> {job.message}</p>}
        </div>
      </Section>
    </div>
  );
}

function NumberField({ label, value, onChange, min = 0, max = 10000 }: { label: string; value: number; onChange: (v: number) => void; min?: number; max?: number }) {
  return <Field label={label}><TextInput type="number" value={value} min={min} max={max} onChange={e => onChange(Number(e.target.value))}/></Field>;
}

function BuilderSettingsView() {
  const s = useAppStore(x => x.builder);
  const update = useAppStore(x => x.updateBuilder);
  return (
    <div className="settings-page">
      <Section title="What to build" description="Strategy architecture and discovery mode.">
        <div className="form-grid">
          <Field label="Build mode"><Select value={s.mode} onChange={mode => update({ mode: mode as typeof s.mode })}><option>Genetic evolution</option><option>Random generation</option><option>Improve existing</option></Select></Field>
          <Field label="Strategy type"><Select value={s.strategyType} onChange={strategyType => update({ strategyType: strategyType as typeof s.strategyType })}><option>Standard</option><option>Multi-TF</option><option>Stockpicker</option></Select></Field>
          <Field label="Trading direction"><Select value={s.direction} onChange={direction => update({ direction: direction as typeof s.direction })}><option>Both</option><option>Long</option><option>Short</option></Select></Field>
          <NumberField label="Maximum conditions" value={s.maxConditions} min={1} max={12} onChange={maxConditions => update({ maxConditions })}/>
        </div>
        <div className="check-row">
          <Checkbox label="Symmetrical Long / Short rules" checked onChange={() => {}}/>
          <Checkbox label="Use fuzzy signals" checked={false} onChange={() => {}}/>
          <Checkbox label="Generate exit rules" checked onChange={() => {}}/>
        </div>
      </Section>
      <Section title="Data and trading engine">
        <div className="form-grid">
          <Field label="Market"><Select value={s.symbol} onChange={symbol => update({ symbol })}><option>EURUSD</option><option>GBPJPY</option><option>XAUUSD</option><option>NQ</option></Select></Field>
          <Field label="Timeframe"><Select value={s.timeframe} onChange={timeframe => update({ timeframe })}><option>M15</option><option>M30</option><option>H1</option><option>H4</option><option>D1</option></Select></Field>
          <Field label="Testing precision"><Select value={s.precision} onChange={precision => update({ precision })}><option>Selected timeframe only</option><option>1 minute data</option><option>Real tick</option></Select></Field>
          <Field label="From"><TextInput type="date" value={s.from} onChange={e => update({ from: e.target.value })}/></Field>
          <Field label="To"><TextInput type="date" value={s.to} onChange={e => update({ to: e.target.value })}/></Field>
          <NumberField label="Out of sample (%)" value={s.oos} min={0} max={80} onChange={oos => update({ oos })}/>
        </div>
        <div className="sample-bar">
          <span style={{ width: `${100 - s.oos}%` }}>In sample {100 - s.oos}%</span>
          <span style={{ width: `${s.oos}%` }}>OOS {s.oos}%</span>
        </div>
      </Section>
      <Section title="Genetic options">
        <div className="form-grid">
          <NumberField label="Population per island" value={s.population} min={10} onChange={population => update({ population })}/>
          <NumberField label="Islands" value={s.islands} min={1} max={32} onChange={islands => update({ islands })}/>
          <NumberField label="Mutation probability (%)" value={s.mutation} min={0} max={100} onChange={mutation => update({ mutation })}/>
          <NumberField label="Crossover probability (%)" value={s.crossover} min={0} max={100} onChange={crossover => update({ crossover })}/>
        </div>
        <div className="check-row">
          <Checkbox label="Migrate candidates between islands" checked onChange={() => {}}/>
          <Checkbox label="Restart stagnant islands" checked onChange={() => {}}/>
          <Checkbox label="Seed from input databank" checked={s.mode === 'Improve existing'} onChange={() => {}}/>
        </div>
      </Section>
      <Section title="Stop loss and profit target">
        <div className="check-row">
          <Checkbox label="Use stop loss" checked={s.stopLoss} onChange={stopLoss => update({ stopLoss })}/>
          <Checkbox label="Use profit target" checked={s.profitTarget} onChange={profitTarget => update({ profitTarget })}/>
          <Checkbox label="Use Advanced Trade Management" checked={false} onChange={() => {}}/>
        </div>
        <div className="form-grid">
          <NumberField label="SL minimum (pips)" value={s.slMin} onChange={slMin => update({ slMin })}/>
          <NumberField label="SL maximum (pips)" value={s.slMax} onChange={slMax => update({ slMax })}/>
          <NumberField label="PT minimum (pips)" value={s.ptMin} onChange={ptMin => update({ ptMin })}/>
          <NumberField label="PT maximum (pips)" value={s.ptMax} onChange={ptMax => update({ ptMax })}/>
        </div>
      </Section>
      <Section title="Building blocks">
        <div className="block-grid">
          {['Moving Average', 'RSI', 'CCI', 'ATR', 'Bollinger Bands', 'Highest / Lowest', 'Candle pattern', 'Day / Time', 'Market position', 'Profit / Loss'].map(x => (
            <label key={x} className="block-item"><input type="checkbox" defaultChecked={!x.includes('CCI')}/><span>{x}</span><em>Configure</em></label>
          ))}
        </div>
      </Section>
      <Section title="Cross checks and rankings">
        <div className="crosschecks">
          {['Higher testing precision', 'Additional markets', 'Monte Carlo trades', 'Monte Carlo retest', 'What-if analysis', 'Optimization profile', 'Walk-forward', 'Sequential optimization'].map((x, i) => (
            <label key={x}><input type="checkbox" defaultChecked={i < 4}/><span>{x}</span><small>{i < 4 ? 'Enabled' : 'Disabled'}</small></label>
          ))}
        </div>
      </Section>
    </div>
  );
}

export function BuilderWorkspace() {
  const tab = useAppStore(s => s.tab);
  const setTab = useAppStore(s => s.setTab);
  return (
    <div className="research-project">
      <div className="project-header">
        <div><h1>Builder</h1><span>Strategy discovery · mock workspace</span></div>
        <nav>
          {(['progress', 'settings', 'results'] as const).map(x => (
            <button key={x} className={tab === x ? 'active' : ''} onClick={() => setTab(x)}>{x === 'settings' ? 'Full settings' : x[0].toUpperCase() + x.slice(1)}</button>
          ))}
        </nav>
        <div className="engine-state"><Activity size={14}/> Mock engine</div>
      </div>
      <div className="project-content">
        {tab === 'progress' ? <ProgressView/> : tab === 'settings' ? <BuilderSettingsView/> : <ResultsWorkspace/>}
      </div>
    </div>
  );
}
