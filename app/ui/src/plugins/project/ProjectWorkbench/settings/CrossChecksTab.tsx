import { useState } from 'react';
import { FolderOpen, Save } from 'lucide-react';
import { SqdModal } from '../ProjectModal';
import { crossChecksTabDefaults, crossChecksTabSectionTitles, type CrossCheckTabItem } from './sharedSettingsFixtures';

/**
 * "Cross checks (robustness)" tab (donor evidence SQX144-EV-000043): the
 * load/save buttons, Disable-all switch, the three speed sections with
 * their description lines, and cross-check rows with settings/filters
 * links opening donor-style dialogs.
 */
export function CrossChecksTab() {
  const [checks, setChecks] = useState<CrossCheckTabItem[]>(crossChecksTabDefaults);
  const [snapshot, setSnapshot] = useState<{checks:CrossCheckTabItem[];disabledAll:boolean}|null>(null);
  const [notice, setNotice] = useState('');
  const [disabledAll, setDisabledAll] = useState(false);
  const [dialog, setDialog] = useState<{ item: CrossCheckTabItem; kind: 'settings' | 'filters' } | null>(null);

  const toggle = (id: string) =>
    setChecks(current => current.map(c => (c.id === id && !disabledAll ? { ...c, use: !c.use } : c)));

  return (
    <div className="cross-checks sqd-tab-content">
      <div className="sqd-cc-actions">
        <button type="button" className="sqd-btn sqd-icon-btn" title="Load cross checks" onClick={() => { if(snapshot) {setChecks(structuredClone(snapshot.checks));setDisabledAll(snapshot.disabledAll);setNotice("Local demo snapshot restored.");} else setNotice("No local demo snapshot saved yet."); }}>
          <FolderOpen size={14} />
        </button>
        <button type="button" className="sqd-btn sqd-icon-btn" title="Save cross checks" onClick={() => {setSnapshot({checks:structuredClone(checks),disabledAll});setNotice("Local demo snapshot saved for this settings session.");}}>
          <Save size={14} />
        </button>
      </div>

      {notice && <p role="status" className="sqd-gen-help">{notice}</p>}
      <label className="sqd-check">
        <input type="checkbox" checked={disabledAll} onChange={e => setDisabledAll(e.target.checked)} />
        <span className="sqd-check-mark" />
        <span className="sqd-check-text">Disable all cross checks</span>
      </label>

      <div className="sqd-cc-titles">
        <legend>Basic (fast)</legend>
        <legend>Cross Check Settings</legend>
        <legend>Filters</legend>
      </div>
      {crossChecksTabSectionTitles.map(section => (
        <div key={section.section}>
          {section.section !== 0 && <div className="sqd-cc-titles">
            <legend>{section.title}</legend>
            <legend />
            <legend />
          </div>}
          <div className="sqd-cc-desc">{section.desc}</div>
          {checks.filter(c => c.section === section.section).map(check => (
            <div className={`sqd-cc-row${disabledAll ? ' disabled' : ''}`} key={check.id}>
              <label className="sqd-check">
                <input type="checkbox" checked={check.use} disabled={disabledAll} onChange={() => toggle(check.id)} />
                <span className="sqd-check-mark" />
                <span className="sqd-check-text">{check.title}</span>
              </label>
              <button type="button" className="sqd-cc-link" onClick={() => setDialog({ item: check, kind: 'settings' })}>
                {check.settingsInfo}
              </button>
              <button type="button" className="sqd-cc-link" onClick={() => setDialog({ item: check, kind: 'filters' })}>
                {check.acceptInfo}
              </button>
            </div>
          ))}
        </div>
      ))}

      {dialog && (
        <SqdModal
          title={`${dialog.item.title} — ${dialog.kind === 'settings' ? 'settings' : 'filters'}`}
          onClose={() => setDialog(null)}
          width={520}
        >
          <p className="sqd-gen-help">
            {dialog.kind === 'settings'
              ? 'Cross check parameters (demo — engine-fed in the donor).'
              : 'Acceptance filters for this cross check (demo — engine-fed in the donor).'}
          </p>
          <div className="sqd-prop-grid">
            <div className="sqd-prop-row">
              <label className="sqd-label">Enabled</label>
              <span className={`sqd-switch${dialog.item.use ? ' on' : ''}`}><input aria-label="Enable cross check" type="checkbox" checked={dialog.item.use} onChange={e=>{const use=e.target.checked;setChecks(items=>items.map(c=>c.id===dialog.item.id?{...c,use}:c));setDialog({...dialog,item:{...dialog.item,use}});}} /><i /></span>
            </div>
          </div>
        </SqdModal>
      )}
    </div>
  );
}
