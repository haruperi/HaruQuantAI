import { ProjectFrame } from '../../common/project';
import { useAppStore } from '../../shell/store';
import { useEngineRun } from '../home/EnginePanel/EngineCtrl';
import { SavedProjectControls, SavedProjectProvider, useSavedProject } from '../home/projectController';
import { StoredResults, progressResult } from '../home/resultProjection';
import { ProgressDashboard } from './ProgressDashboard';
import { FullSettingsView } from './FullSettingsView';

export type BuilderPanel = 'progress' | 'settings' | 'results';
export function BuilderWorkspace() {
  const panel = useAppStore(s => s.tab), setPanel = useAppStore(s => s.setTab);
  const binding = useSavedProject('builder'), { state, controller } = binding;
  const run = useEngineRun(state.project?.manifest.project_id, { taskId: state.taskId, revision: state.project?.revision,
    enabled: !!state.project && !state.dirty && !state.busy && Object.keys(state.validationErrors).length === 0, onCompleted: () => void controller.refreshResults() });
  const selected = state.results.find(r => r.result_id === state.selectedResultId) ?? null;
  return <SavedProjectProvider binding={binding}>
    <ProjectFrame title="Builder" panel={panel} onPanelChange={setPanel} running={['queued', 'running', 'paused'].includes(run.status)}>
      <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0, minHeight: 0 }}>
    <SavedProjectControls binding={binding} />
      <div className="pw-panel" hidden={panel !== 'progress'}><ProgressDashboard run={run} onOpenFullSettings={() => setPanel('settings')}
        onOpenResults={(rank = 0) => { const result = state.results[rank]; if (result) controller.selectResult(result.result_id); setPanel('results'); }} /></div>
      <div className="pw-panel" hidden={panel !== 'settings'}><FullSettingsView runStatus={run.status} onClose={() => setPanel('progress')} /></div>
      <div className="pw-panel" hidden={panel !== 'results'}><StoredResults result={selected} /></div>
    </div></ProjectFrame>
  </SavedProjectProvider>;
}
