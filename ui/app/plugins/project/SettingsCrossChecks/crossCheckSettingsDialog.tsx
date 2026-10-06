import { SqdModal } from '../ProjectWorkbench/ProjectModal';
import type { CrossCheckDialog, CrossChecksController } from './CrossChecksCtrl';

type CrossCheckSettingsDialogProps = Pick<CrossChecksController, 'setChecks' | 'setDialog'> & { dialog: CrossCheckDialog };

/** Existing demo settings/filters shell; no acceptance-condition editor. */
export function CrossCheckSettingsDialog({ dialog, setChecks, setDialog }: CrossCheckSettingsDialogProps) {
  return (
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
  );
}
