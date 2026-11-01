import { useState } from 'react';
import { useAppStore } from '../../shell/store';
import { ProjectFrame } from '../../common/project';
import { useEngineRun } from '../home/EnginePanel/EngineCtrl';
import { SavedProjectControls, SavedProjectProvider, useSavedProject } from '../home/projectController';
import { StoredResults, progressResult } from '../home/resultProjection';
import { OptimizerSettings } from './OptimizerSettings';
import { OptimizerProgress } from './OptimizerProgress';
import { optimizerDefaults, type OptimizerDraft } from './optimizerFixtures';
export function OptimizerWorkspace() {
  const panel = useAppStore(s => s.tab), setPanel = useAppStore(s => s.setTab);
  const binding = useSavedProject('optimizer'), { state, controller } = binding;
  const [section, setSection] = useState('optimization');
  const run = useEngineRun(state.project?.manifest.project_id, { taskId: state.taskId, revision: state.project?.revision,
    enabled: !!state.project && !state.dirty && !state.busy && Object.keys(state.validationErrors).length === 0, onCompleted: () => void controller.refreshResults() });
  const result = state.results.find(r => r.result_id === state.selectedResultId) ?? null;
  const execution = state.draft.execution as { parameter_ranges?: { name: string; start: number; end: number; step: number }[] } | undefined;
  const draft: OptimizerDraft = { ...optimizerDefaults, parameters: (execution?.parameter_ranges ?? []).map(range => ({ name: range.name, original: range.start, min: range.start, max: range.end, step: range.step, enabled: true })),
    sourceBank: 'Saved selected strategy', targetBank: state.project?.tasks[state.taskId]?.databank_target ?? '' };
  const openSettings = (id = 'optimization') => { setSection(id); setPanel('settings'); };
  return <SavedProjectProvider binding={binding}><ProjectFrame title="Optimizer" panel={panel} onPanelChange={setPanel} running={['queued', 'running', 'paused'].includes(run.status)}>
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0, minHeight: 0 }}>
    <SavedProjectControls binding={binding} />
    <div className="pw-panel" hidden={panel !== 'progress'}><OptimizerProgress run={run} draft={draft} onChange={() => openSettings()} result={progressResult(result)} onResults={() => setPanel('results')} onSettings={openSettings} /></div>
    <div className="pw-panel" hidden={panel !== 'settings'}><OptimizerSettings selectedId={section} onSelect={setSection} draft={draft} onChange={() => openSettings()} banks={Object.values(state.project?.databanks ?? {})} locked={['queued', 'running', 'paused'].includes(run.status)} /></div>
    <div className="pw-panel" hidden={panel !== 'results'}><StoredResults result={result} /></div>
  </div></ProjectFrame></SavedProjectProvider>;
}
