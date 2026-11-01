import { useState } from 'react';
import { useAppStore } from '../../shell/store';
import { ProjectFrame } from '../../common/project';
import { useEngineRun } from '../home/EnginePanel/EngineCtrl';
import { SavedProjectControls, SavedProjectProvider, useSavedProject } from '../home/projectController';
import { StoredResults, progressResult } from '../home/resultProjection';
import { RetesterSettings } from './RetesterSettings';
import { RetesterProgress } from './RetesterProgress';
export function RetesterWorkspace() {
  const panel = useAppStore(s => s.tab), setPanel = useAppStore(s => s.setTab);
  const binding = useSavedProject('retester'), { state, controller } = binding;
  const [section, setSection] = useState('data');
  const run = useEngineRun(state.project?.manifest.project_id, { taskId: state.taskId, revision: state.project?.revision,
    enabled: !!state.project && !state.dirty && !state.busy && Object.keys(state.validationErrors).length === 0, onCompleted: () => void controller.refreshResults() });
  const result = state.results.find(r => r.result_id === state.selectedResultId) ?? null;
  const draft = { source: 'Saved selected strategies', destination: state.project?.tasks[state.taskId]?.databank_target ?? '', selectedOnly: true };
  const openSettings = (id = 'data') => { setSection(id); setPanel('settings'); };
  return <SavedProjectProvider binding={binding}><ProjectFrame title="Retester" panel={panel} onPanelChange={setPanel} running={['queued', 'running', 'paused'].includes(run.status)}>
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0, minHeight: 0 }}>
    <SavedProjectControls binding={binding} />
    <div className="pw-panel" hidden={panel !== 'progress'}><RetesterProgress run={run} draft={draft} onChange={() => openSettings()} banks={Object.values(state.project?.databanks ?? {})}
      result={progressResult(result)} selectionCount={1} onResults={() => setPanel('results')} onSettings={openSettings} /></div>
    <div className="pw-panel" hidden={panel !== 'settings'}><RetesterSettings selectedId={section} onSelect={setSection} locked={['queued', 'running', 'paused'].includes(run.status)} /></div>
    <div className="pw-panel" hidden={panel !== 'results'}><StoredResults result={result} /></div>
  </div></ProjectFrame></SavedProjectProvider>;
}
