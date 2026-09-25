import { useAppStore } from '../../app/store';
import { demoResult } from './results/resultsModel';
import { useState } from 'react';
import { ResultsView } from './ResultsView';
import { ProgressDashboard } from './ProgressDashboard';
import { FullSettingsView } from './FullSettingsView';
import type { EngineRunStatus } from './fixtures';
/**
 * Builder workspace shell in SQX Progress-tab parity (donor evidence
 * SQX144-EV-000033): the 51px dashboard header with the clickable project
 * name and the Progress / Full settings / Results large tabs. Progress is
 * the initial panel; Full settings mounts the donor-parity Advanced
 * settings surface (SQX144-EV-000038..043).
 */
export type BuilderPanel = 'progress' | 'settings' | 'results';
const PANEL_TABS: {
    id: BuilderPanel;
    label: string;
}[] = [
    { id: 'progress', label: 'Progress' },
    { id: 'settings', label: 'Full settings' },
    { id: 'results', label: 'Results' },
];
export function BuilderWorkspace() {
    const panel = useAppStore(s => s.tab);
    const setPanel = useAppStore(s => s.setTab);
    const strategies = useAppStore(s => s.strategies);
    const selectStrategy = useAppStore(s => s.selectStrategy);
    const selected = useAppStore(s => s.strategies.find(item => item.id === s.selectedStrategyId));
    const [runStatus, setRunStatus] = useState<EngineRunStatus>('idle');
    const projectNameRunning = runStatus !== 'idle' && panel !== 'progress';
    return (<div className="builder-workspace">
      <header className="sqd-dashboard-header">
        <div className={`sqd-project-name${projectNameRunning ? ' sqd-project-name-running' : ''}`} title={projectNameRunning ? 'Project in progress — click to return to Progress' : undefined} onClick={() => setPanel('progress')}>
          Builder
        </div>
        <nav className="sqd-tabs-large" role="tablist" aria-label="Builder panels">
          {PANEL_TABS.map(tab => (<div key={tab.id} role="tab" tabIndex={0} onKeyDown={e => { if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            e.currentTarget.click();
        } }} aria-selected={panel === tab.id} className={panel === tab.id ? 'active' : ''} onClick={() => setPanel(tab.id)}>
              {tab.label}
            </div>))}
        </nav>
      </header>
      <div className="sqd-panel-host">
        {panel === 'progress' ? (<ProgressDashboard strategyNames={strategies.map(s => s.name)} runStatus={runStatus} onRunStatusChange={setRunStatus} onOpenFullSettings={() => setPanel('settings')} onOpenResults={(rank = 0) => { if (strategies[rank])
            selectStrategy(strategies[rank].id); setPanel('results'); }}/>) : panel === 'settings' ? (<FullSettingsView runStatus={runStatus} onClose={() => setPanel('progress')}/>) : (<ResultsView result={selected ? demoResult(selected.id, selected.name) : null}/>)}
      </div>
    </div>);
}
