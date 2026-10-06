import { useCrossChecksController } from './CrossChecksCtrl';
import { CrossCheck } from './crosscheck/crossCheck';
import { CrossCheckSettingsDialog } from './crossCheckSettingsDialog';
import { FolderOpen, Save } from 'lucide-react';
import { crossChecksTabSectionTitles } from '../ProjectWorkbench/settings/sharedSettingsFixtures';

/**
 * "Cross checks (robustness)" tab (donor evidence retained target UI; current donor equivalence unverified): the
 * load/save buttons, Disable-all switch, the three speed sections with
 * their description lines, and cross-check rows with settings/filters
 * links opening donor-style dialogs.
 */
export function CrossChecksTab() {
  const { checks, setChecks, notice, disabledAll, setDisabledAll, dialog, setDialog, toggle, loadSnapshot, saveSnapshot } = useCrossChecksController();

  return (
    <div className="cross-checks sqd-tab-content">
      <div className="sqd-cc-actions">
        <button type="button" className="sqd-btn sqd-icon-btn" title="Load cross checks" onClick={loadSnapshot}>
          <FolderOpen size={14} />
        </button>
        <button type="button" className="sqd-btn sqd-icon-btn" title="Save cross checks" onClick={saveSnapshot}>
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
            <CrossCheck key={check.id} check={check} disabledAll={disabledAll} toggle={toggle} setDialog={setDialog} />
          ))}
        </div>
      ))}

      {dialog && (
        <CrossCheckSettingsDialog dialog={dialog} setChecks={setChecks} setDialog={setDialog} />
      )}
    </div>
  );
}
