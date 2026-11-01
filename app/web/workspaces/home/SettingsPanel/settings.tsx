import type { SettingsSection } from '../../../common/project/contracts';
import { ExecutionSettingsEditor, useProjectBinding } from '../projectController';
import { useSettingsPanel } from './SettingsPanelCtrl';

export interface SettingsPanelProps {
  sections: SettingsSection[];
  locked: boolean;
  selectedId?: string;
  onSelect?: (id: string) => void;
}

export function SettingsPanel({ sections, locked, selectedId, onSelect }: SettingsPanelProps) {
  const binding = useProjectBinding();
  const { active, setActiveId } = useSettingsPanel(sections, selectedId, onSelect);
  return <div className="sqd-settings-tabs">
    <div className="sqd-stabs-header" role="tablist" aria-label="Settings tabs">
      {sections.map(s => <div key={s.id} role="tab" tabIndex={0} aria-selected={active?.id === s.id}
        className={active?.id === s.id ? 'active' : ''} onClick={() => setActiveId(s.id)}
        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setActiveId(s.id); } }}>{s.title}</div>)}
    </div>
    <div className="sqd-stabs-body"><div className="sqd-stab-panel">
      <div className="sqd-settings-body-header"><div className="sqd-settings-tab-desc">{active?.help}</div>
        <a className="sqd-btn sqd-btn-help" href={active?.helpUrl} target="_blank" rel="noreferrer">❔ Help</a></div>
      <div className={`sqd-settings-body-inner${locked ? ' disabled-panel' : ''}`}>
        {locked && <div className="sqd-disabled-placeholder">Setting changes locked while execution is active.</div>}
        {sections.map(s => <div key={s.id} hidden={active?.id !== s.id} inert={locked}>
          {!binding || ['data', 'money', 'options', 'notes'].includes(s.id) ? s.content :
            s.id === 'optimization' ? <ExecutionSettingsEditor /> : <p>This configuration is unavailable for the selected execution mode.</p>}
        </div>)}
      </div>
    </div></div>
  </div>;
}
