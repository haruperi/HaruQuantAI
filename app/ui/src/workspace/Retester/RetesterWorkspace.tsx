import { useEffect, useRef } from 'react';
import { Activity, CircleStop, Pause, Play, RotateCcw } from 'lucide-react';
import { useAppStore } from '../../app/store';
import { mockResearchService } from '../../mocks/service';
import { Button, Checkbox, Field, ProgressBar, Section, Select, Stat, TextInput } from '../../components/ui';
import { ResultsWorkspace } from '../Results/ResultsWorkspace';

function ProgressView() {
  const store = useAppStore(); const job = store.jobs['retester']; const timer = useRef<number | null>(null);
  useEffect(() => {
    if (job?.status !== 'running') return;
    timer.current = window.setInterval(() => {
      const latest = useAppStore.getState().jobs['retester'];
      if (!latest || latest.status !== 'running') return;
      const next = Math.min(100, latest.progress + 3);
      useAppStore.getState().patchJob('retester', {
        progress: next, accepted: Math.floor(next * .45), rejected: Math.floor(next * .85),
        message: next >= 100 ? 'Retest run completed; retested strategies updated.' : `Retesting strategies on alternative data…`,
        status: next >= 100 ? 'completed' : 'running'
      });
    }, 380);
    return () => { if (timer.current) clearInterval(timer.current); };
  }, [job?.status]);
  const start = async () => { const created = await mockResearchService.start('retester'); store.setJob('retester', created); store.notify('Retester mock run started'); };
  const status = job?.status ?? 'idle';
  return (
    <div className="progress-view">
      <div className="run-toolbar">
        <Button className="primary" disabled={status === 'running'} onClick={status === 'paused' ? () => store.patchJob('retester', { status: 'running', message: 'Resumed' }) : start}><Play size={15}/>{status === 'paused' ? 'Resume' : 'Start'}</Button>
        <Button disabled={status !== 'running'} onClick={() => store.patchJob('retester', { status: 'paused', message: 'Paused by user; job state retained.' })}><Pause size={15}/>Pause</Button>
        <Button disabled={!['running', 'paused'].includes(status)} onClick={() => store.patchJob('retester', { status: 'cancelled', message: 'Stopped by user; accepted results retained.' })}><CircleStop size={15}/>Stop</Button>
        <Button onClick={() => store.setJob('retester', { id: `reset-${Date.now()}`, kind: 'retester', status: 'idle', progress: 0, accepted: 0, rejected: 0, message: 'Ready' })}><RotateCcw size={14}/>Reset progress</Button>
        <span className={`status status-${status}`}><i/>{status.toUpperCase()}</span>
      </div>
      <Section title="Retester progress" description="Deterministic frontend simulation; no native HaruQuantAI engine or external process is running.">
        <ProgressBar value={job?.progress ?? 0} label={`${Math.round(job?.progress ?? 0)}% · ${job?.message ?? 'Ready to start'}`}/>
        <div className="metric-strip compact">
          <Stat label="Passed" value={job?.accepted ?? 0} tone="good"/>
          <Stat label="Failed" value={job?.rejected ?? 0} tone="bad"/>
          <Stat label="Total Retests" value={(job?.accepted ?? 0) + (job?.rejected ?? 0)}/>
          <Stat label="Elapsed" value={status === 'idle' ? '—' : '00:04:12'}/>
        </div>
      </Section>
    </div>
  );
}

function RetesterSettingsView() {
  const s = useAppStore(x => x.builder);
  return (
    <div className="settings-page">
      <Section title="What to retest" description="Source and destination databanks for strategy retesting.">
        <div className="form-grid">
          <Field label="Retest strategies from databank">
            <Select value="Results" onChange={() => {}}>
              <option>Results</option>
              <option>Portfolio</option>
              <option>Candidates</option>
            </Select>
          </Field>
          <Field label="Store results in databank">
            <Select value="Retest" onChange={() => {}}>
              <option>Results</option>
              <option>Retest</option>
              <option>Portfolio</option>
            </Select>
          </Field>
        </div>
        <p className="dialog-note">If you choose a different databank to store retested results, strategies will be copied to destination. Storing in the same databank will overwrite results.</p>
      </Section>
      <Section title="Retest Data and Precision">
        <div className="form-grid">
          <Field label="Alternative Market"><Select value={s.symbol} onChange={() => {}}><option>EURUSD</option><option>GBPUSD</option><option>USDJPY</option><option>XAUUSD</option></Select></Field>
          <Field label="Alternative Timeframe"><Select value={s.timeframe} onChange={() => {}}><option>M15</option><option>M30</option><option>H1</option><option>H4</option><option>D1</option></Select></Field>
          <Field label="Testing precision"><Select value={s.precision} onChange={() => {}}><option>Selected timeframe only</option><option>1 minute data</option><option>Real tick</option></Select></Field>
        </div>
        <div className="check-row">
          <Checkbox label="Apply additional spread & slippage stress test" checked onChange={() => {}}/>
          <Checkbox label="Skip worst 5% trades" checked={false} onChange={() => {}}/>
        </div>
      </Section>
    </div>
  );
}

export function RetesterWorkspace() {
  const tab = useAppStore(s => s.tab);
  const setTab = useAppStore(s => s.setTab);
  return (
    <div className="research-project">
      <div className="project-header">
        <div><h1>Retester</h1><span>Strategy verification & stress testing · mock workspace</span></div>
        <nav>
          {(['progress', 'settings', 'results'] as const).map(x => (
            <button key={x} className={tab === x ? 'active' : ''} onClick={() => setTab(x)}>{x === 'settings' ? 'Full settings' : x[0].toUpperCase() + x.slice(1)}</button>
          ))}
        </nav>
        <div className="engine-state"><Activity size={14}/> Mock engine</div>
      </div>
      <div className="project-content">
        {tab === 'progress' ? <ProgressView/> : tab === 'settings' ? <RetesterSettingsView/> : <ResultsWorkspace/>}
      </div>
    </div>
  );
}
