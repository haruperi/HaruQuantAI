import { useEffect, useRef } from 'react';
import { Activity, CircleStop, Pause, Play, RotateCcw, Settings2 } from 'lucide-react';
import { useAppStore } from '../../app/store';
import { mockResearchService } from '../../mocks/service';
import { Button, Checkbox, Field, ProgressBar, Section, Select, Stat, TextInput } from '../../components/ui';
import { ResultsWorkspace } from '../Results/ResultsWorkspace';

function NumberField({ label, value, onChange, min = 0, max = 10000 }: { label: string; value: number; onChange: (v: number) => void; min?: number; max?: number }) {
  return <Field label={label}><TextInput type="number" value={value} min={min} max={max} onChange={e => onChange(Number(e.target.value))}/></Field>;
}

function ProgressView() {
  const store = useAppStore(); const job = store.jobs['optimizer']; const timer = useRef<number | null>(null);
  useEffect(() => {
    if (job?.status !== 'running') return;
    timer.current = window.setInterval(() => {
      const latest = useAppStore.getState().jobs['optimizer'];
      if (!latest || latest.status !== 'running') return;
      const next = Math.min(100, latest.progress + 4);
      useAppStore.getState().patchJob('optimizer', {
        progress: next, accepted: Math.floor(next * .2), rejected: Math.floor(next * .8),
        message: next >= 100 ? 'Optimization run completed; optimal parameter sets stored.' : `Evaluating parameter combination ${Math.floor(next * 2.5)}…`,
        status: next >= 100 ? 'completed' : 'running'
      });
    }, 350);
    return () => { if (timer.current) clearInterval(timer.current); };
  }, [job?.status]);
  const start = async () => { const created = await mockResearchService.start('optimizer'); store.setJob('optimizer', created); store.notify('Optimizer mock run started'); };
  const status = job?.status ?? 'idle';
  return (
    <div className="progress-view">
      <div className="run-toolbar">
        <Button className="primary" disabled={status === 'running'} onClick={status === 'paused' ? () => store.patchJob('optimizer', { status: 'running', message: 'Resumed' }) : start}><Play size={15}/>{status === 'paused' ? 'Resume' : 'Start'}</Button>
        <Button disabled={status !== 'running'} onClick={() => store.patchJob('optimizer', { status: 'paused', message: 'Paused by user; job state retained.' })}><Pause size={15}/>Pause</Button>
        <Button disabled={!['running', 'paused'].includes(status)} onClick={() => store.patchJob('optimizer', { status: 'cancelled', message: 'Stopped by user; accepted results retained.' })}><CircleStop size={15}/>Stop</Button>
        <Button onClick={() => store.setJob('optimizer', { id: `reset-${Date.now()}`, kind: 'optimizer', status: 'idle', progress: 0, accepted: 0, rejected: 0, message: 'Ready' })}><RotateCcw size={14}/>Reset progress</Button>
        <span className={`status status-${status}`}><i/>{status.toUpperCase()}</span>
      </div>
      <Section title="Optimizer progress" description="Deterministic frontend simulation; no native HaruQuantAI engine or external process is running.">
        <ProgressBar value={job?.progress ?? 0} label={`${Math.round(job?.progress ?? 0)}% · ${job?.message ?? 'Ready to start'}`}/>
        <div className="metric-strip compact">
          <Stat label="Optimal sets" value={job?.accepted ?? 0} tone="good"/>
          <Stat label="Trials rejected" value={job?.rejected ?? 0} tone="bad"/>
          <Stat label="Combinations / sec" value={status === 'running' ? 420 : 0}/>
          <Stat label="Elapsed" value={status === 'idle' ? '—' : '00:08:15'}/>
        </div>
      </Section>
    </div>
  );
}

function OptimizerSettingsView() {
  const opt = useAppStore(x => x.optimization);
  const updateOpt = useAppStore(x => x.updateOptimization);
  return (
    <div className="settings-page">
      <Section title="Optimization mode">
        <div className="mode-cards">
          {(['Simple', 'Sequential', 'Walk-Forward', 'WF Matrix'] as const).map(mode => (
            <button key={mode} className={opt.mode === mode ? 'active' : ''} onClick={() => updateOpt({ mode })}>
              <Settings2 size={18}/>
              <strong>{mode}</strong>
              <span>{mode === 'Simple' ? 'Parameter grid search' : mode === 'Sequential' ? 'Optimize periods in sequence' : mode === 'Walk-Forward' ? 'Rolling reoptimization' : 'Test window combinations'}</span>
            </button>
          ))}
        </div>
      </Section>
      <Section title="Parameters to optimize">
        <div className="form-grid">
          <Field label="Parameter">
            <Select value={opt.parameter} onChange={parameter => updateOpt({ parameter })}>
              <option>FastPeriod</option><option>SlowPeriod</option><option>ATRPeriod</option><option>StopLoss</option>
            </Select>
          </Field>
          <NumberField label="Minimum" value={opt.min} onChange={min => updateOpt({ min })}/>
          <NumberField label="Maximum" value={opt.max} onChange={max => updateOpt({ max })}/>
          <NumberField label="Step" value={opt.step} onChange={step => updateOpt({ step })}/>
          <Field label="Combinations">
            <TextInput readOnly value={opt.step > 0 ? Math.floor((opt.max - opt.min) / opt.step) + 1 : 'Invalid step'}/>
          </Field>
          <Field label="Objective">
            <Select value={opt.objective} onChange={objective => updateOpt({ objective })}>
              <option>Return / Drawdown ratio</option><option>Net profit</option><option>Profit factor</option><option>Sharpe ratio</option>
            </Select>
          </Field>
        </div>
        {opt.mode.includes('Walk') || opt.mode === 'WF Matrix' ? (
          <div className="inline-box">
            <NumberField label="In-sample months" value={24} onChange={() => {}}/>
            <NumberField label="Out-of-sample months" value={6} onChange={() => {}}/>
            <NumberField label="Runs" value={8} onChange={() => {}}/>
          </div>
        ) : null}
      </Section>
      <Section title="Result storage">
        <Checkbox label="Store the best parameterized strategy revisions" checked onChange={() => {}}/>
        <Checkbox label="Store all optimization trials" checked={false} onChange={() => {}}/>
        <NumberField label="Keep best results" value={opt.keep} onChange={keep => updateOpt({ keep })}/>
      </Section>
    </div>
  );
}

export function OptimizerWorkspace() {
  const tab = useAppStore(s => s.tab);
  const setTab = useAppStore(s => s.setTab);
  return (
    <div className="research-project">
      <div className="project-header">
        <div><h1>Optimizer</h1><span>Parameter tuning & sensitivity analysis · mock workspace</span></div>
        <nav>
          {(['progress', 'settings', 'results'] as const).map(x => (
            <button key={x} className={tab === x ? 'active' : ''} onClick={() => setTab(x)}>{x === 'settings' ? 'Full settings' : x[0].toUpperCase() + x.slice(1)}</button>
          ))}
        </nav>
        <div className="engine-state"><Activity size={14}/> Mock engine</div>
      </div>
      <div className="project-content">
        {tab === 'progress' ? <ProgressView/> : tab === 'settings' ? <OptimizerSettingsView/> : <ResultsWorkspace/>}
      </div>
    </div>
  );
}
