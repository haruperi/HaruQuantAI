import type { CrossCheckTabItem } from '../../ProjectWorkbench/settings/sharedSettingsFixtures';
import type { CrossChecksController } from '../CrossChecksCtrl';

type CrossCheckProps = Pick<CrossChecksController, 'disabledAll' | 'toggle' | 'setDialog'> & { check: CrossCheckTabItem };

/** Existing checkbox/settings/filter row; parent retains all state. */
export function CrossCheck({ check, disabledAll, toggle, setDialog }: CrossCheckProps) {
  return (
            <div className={`sqd-cc-row${disabledAll ? ' disabled' : ''}`}>
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
  );
}
