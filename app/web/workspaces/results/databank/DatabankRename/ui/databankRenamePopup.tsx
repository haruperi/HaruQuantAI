import { SqxModal, SqxButton } from '../../ProjectDatabanks/DatabankDialogs';
import { useDatabankRenamePopup, type RenameValue } from './DatabankRenamePopupCtrl';
import './styles.css';

/** Independently authored mock rename presentation; structural mapping only. */
export function RenameStrategiesDialog({
  count,
  currentName,
  onRename,
  onClose,
}: {
  count: number;
  currentName: string;
  onRename: (value: RenameValue) => void;
  onClose: () => void;
}) {
  const { name, setName, prefix, setPrefix, postfix, setPostfix, confirm } = useDatabankRenamePopup(count, currentName, onRename, onClose);
  return (
    <SqxModal title={`Rename selected strategies (${count})`} onClose={onClose} width={470}
      footer={
        <>
          <button type="button" className="sqx-link-button" onClick={onClose}>Close</button>
          <SqxButton
            primary
            onClick={confirm}
          >
            Rename
          </SqxButton>
        </>
      }
    >
      {count === 1 ? (
        <div className="hq-databank-rename-row">
          <label>Name</label>
          <input className="sqx-input grow" value={name} onChange={e => setName(e.target.value)} autoFocus />
        </div>
      ) : (
        <div className="hq-databank-rename-row">
          <label>Prefix</label>
          <input className="sqx-input" value={prefix} onChange={e => setPrefix(e.target.value)} autoFocus />
          <span className="sqx-form-hint">Original</span>
          <label>Postfix</label>
          <input className="sqx-input" value={postfix} onChange={e => setPostfix(e.target.value)} />
        </div>
      )}
    </SqxModal>
  );
}
