import { useState } from 'react';
import { ResultsWorkspace } from '../Results/ResultsWorkspace';
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

const PANEL_TABS: { id: BuilderPanel; label: string }[] = [
  { id: 'progress', label: 'Progress' },
  { id: 'settings', label: 'Full settings' },
  { id: 'results', label: 'Results' },
];

export function BuilderWorkspace() {
  const [panel, setPanel] = useState<BuilderPanel>('progress');
  const [runStatus, setRunStatus] = useState<EngineRunStatus>('idle');

  const projectNameRunning = runStatus !== 'idle' && panel !== 'progress';

  return (
    <div className="builder-workspace">
      <header className="sqd-dashboard-header">
        <div
          className={`sqd-project-name${projectNameRunning ? ' sqd-project-name-running' : ''}`}
          title={projectNameRunning ? 'Project in progress — click to return to Progress' : undefined}
          onClick={() => setPanel('progress')}
        >
          Build
        </div>
        <nav className="sqd-tabs-large" aria-label="Builder panels">
          {PANEL_TABS.map(tab => (
            <div
              key={tab.id}
              role="tab"
              aria-selected={panel === tab.id}
              className={panel === tab.id ? 'active' : ''}
              onClick={() => setPanel(tab.id)}
            >
              {tab.label}
            </div>
          ))}
        </nav>
      </header>
      <div className="sqd-panel-host">
        {panel === 'progress' ? (
          <ProgressDashboard
            runStatus={runStatus}
            onRunStatusChange={setRunStatus}
            onOpenFullSettings={() => setPanel('settings')}
            onOpenResults={() => setPanel('results')}
          />
        ) : panel === 'settings' ? (
          <FullSettingsView runStatus={runStatus} onClose={() => setPanel('progress')} />
        ) : (
          <ResultsWorkspace />
        )}
      </div>
    </div>
  );
}
