import { SqdModal } from '../ProjectWorkbench/ProjectModal';
import { atmDefaults } from '../ProjectWorkbench/settings/sharedSettingsFixtures';
import type { AdvancedTMController } from './AdvancedTMCtrl';

type AddNewExitPopupProps = Pick<AdvancedTMController, 'selected' | 'setSelected' | 'setAdding' | 'addExit'>;

/** Existing Add dialog only; state stays in its owning mounted controller. */
export function AddNewExitPopup({ selected, setSelected, setAdding, addExit }: AddNewExitPopupProps) {
  return (
    <SqdModal title="Add new exit method" onClose={()=>setAdding(false)} footer={<button type="button" className="sqd-btn sqd-btn-primary" onClick={addExit}>Add</button>}>
        <p className="sqd-gen-help">Local UI demo: choose an exit method from the fixture catalog.</p>
        <select aria-label="Exit method" value={selected} onChange={e=>setSelected(e.target.value)}>{atmDefaults.map(m=><option key={m.key} value={m.key}>{m.label}</option>)}</select>
      </SqdModal>
  );
}
