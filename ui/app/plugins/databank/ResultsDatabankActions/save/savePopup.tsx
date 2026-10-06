import { SqxModal, SqxButton } from '../../ProjectDatabanks/DatabankDialogs';
import { useSaveDraft } from './saveBtnPopupCtrl';

/** Existing independently authored simulated Save presentation. */
export function SaveRecordsDialog({
  format,
  onSave,
  onClose,
}: {
  format: string;
  onSave: () => void;
  onClose: () => void;
}) {
  const { prefix, setPrefix, suffix, setSuffix } = useSaveDraft();
  return (
    <SqxModal title={`Save / ${format}`} onClose={onClose}
      footer={
        <>
          <SqxButton onClick={onClose}>Cancel</SqxButton>
          <SqxButton primary onClick={() => { onSave(); onClose(); }}>Save</SqxButton>
        </>
      }
    >
      <div className="sqx-form-row">
        <label>Directory</label>
        <input className="sqx-input" value="C:\\Users\\demo\\Documents\\StrategyQuant X" readOnly />
        <SqxButton onClick={onClose}>Browse</SqxButton>
      </div>
      <div className="sqx-form-row">
        <label>File name</label>
        <input className="sqx-input" value={prefix} onChange={e => setPrefix(e.target.value)} />
        <span className="sqx-form-hint">Strategy X.y.z</span>
        <input className="sqx-input" value={suffix} onChange={e => setSuffix(e.target.value)} />
      </div>
      <p className="sqx-help">
        Selected strategies will be saved to a directory of your choice with given prefix and sufix.
        If file with the same name already exists, it will be overwritten!
      </p>
    </SqxModal>
  );
}
