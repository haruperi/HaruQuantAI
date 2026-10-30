import type { ReactNode } from 'react';
import type { ProjectPanel } from './contracts';

export function ProjectFrame({ title, panel, onPanelChange, running, children }: {
  title: string; panel: ProjectPanel; onPanelChange: (panel: ProjectPanel) => void;
  running: boolean; children: ReactNode;
}) {
  return <div className={title === 'Builder' ? 'builder-workspace' : 'project-workspace'}>
    <header className="sqd-dashboard-header">
      <div role="button" tabIndex={0} className={`sqd-project-name${running && panel !== 'progress' ? ' sqd-project-name-running' : ''}`}
        onClick={() => onPanelChange('progress')} onKeyDown={e => { if (e.key === 'Enter') onPanelChange('progress'); }}>{title}</div>
      <nav className="sqd-tabs-large" role="tablist" aria-label={`${title} panels`}>
        {(['progress', 'settings', 'results'] as const).map(id => <div key={id} role="tab" tabIndex={0}
          aria-selected={panel === id} className={panel === id ? 'active' : ''}
          onClick={() => onPanelChange(id)} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onPanelChange(id); } }}>
          {id === 'settings' ? 'Full settings' : id === 'progress' ? 'Progress' : 'Results'}
        </div>)}
      </nav>
    </header>
    <div className="sqd-panel-host">{children}</div>
  </div>;
}
