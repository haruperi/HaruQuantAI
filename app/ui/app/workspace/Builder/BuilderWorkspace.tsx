import { useProjectWorkbench } from './documents';

import { useAppStore } from './localState';
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
export function BuilderWorkspace() {
const { ProjectFrame } = useProjectWorkbench();

    const panel = useAppStore(s => s.tab);
    const setPanel = useAppStore(s => s.setTab);
    const strategies = useAppStore(s => s.strategies);
    const selectStrategy = useAppStore(s => s.selectStrategy);
    const selected = useAppStore(s => s.strategies.find(item => item.id === s.selectedStrategyId));
    const [runStatus, setRunStatus] = useState<EngineRunStatus>('idle');
    return (<ProjectFrame title="Builder" panel={panel} onPanelChange={setPanel} running={runStatus !== 'idle'}>
        {panel === 'progress' ? (<ProgressDashboard strategyNames={strategies.map(s => s.name)} runStatus={runStatus} onRunStatusChange={setRunStatus} onOpenFullSettings={() => setPanel('settings')} onOpenResults={(rank = 0) => { if (strategies[rank])
            selectStrategy(strategies[rank].id); setPanel('results'); }}/>) : panel === 'settings' ? (<FullSettingsView runStatus={runStatus} onClose={() => setPanel('progress')}/>) : (<ResultsView result={selected ? demoResult(selected.id, selected.name) : null}/>)}
    </ProjectFrame>);
}
