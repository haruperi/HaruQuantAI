import { useState } from 'react';
import type { SettingsSection } from './contracts';

export function ProjectSettings({ sections, locked, selectedId, onSelect }: { sections: SettingsSection[]; locked: boolean; selectedId?:string; onSelect?:(id:string)=>void }) {
  const [localId, setLocalId] = useState(sections[0]?.id);
  const activeId=selectedId??localId;
  const setActiveId=(id:string)=>{setLocalId(id);onSelect?.(id);};
  const active = sections.find(s => s.id === activeId) ?? sections[0];
  return <div className="sqd-fullsettings">
    <div className="sqd-advanced-title">Advanced settings</div>
    <div className="sqd-settings-tabs">
      <div className="sqd-stabs-header" role="tablist" aria-label="Settings tabs">
        {sections.map(s => <div key={s.id} role="tab" tabIndex={0} aria-selected={active?.id === s.id}
          className={active?.id === s.id ? 'active' : ''} onClick={() => setActiveId(s.id)}
          onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setActiveId(s.id); } }}>{s.title}</div>)}
      </div>
      <div className="sqd-stabs-body"><div className="sqd-stab-panel">
        <div className="sqd-settings-body-header"><div className="sqd-settings-tab-desc">{active?.help}</div>
          <a className="sqd-btn sqd-btn-help" href={active?.helpUrl} target="_blank" rel="noreferrer">❔ Help</a></div>
        <div className={`sqd-settings-body-inner${locked ? ' disabled-panel' : ''}`}>
          {locked && <div className="sqd-disabled-placeholder">Setting changes locked while the local preview is running.</div>}
          {sections.map(s => <div key={s.id} hidden={active?.id !== s.id} inert={locked}>{s.content}</div>)}
        </div>
      </div></div>
    </div>
  </div>;
}
