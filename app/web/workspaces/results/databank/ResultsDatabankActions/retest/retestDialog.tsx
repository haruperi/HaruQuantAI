import { SqxModal, SqxButton } from '../../ProjectDatabanks/DatabankDialogs';
import { useRetestDialog } from './RetestDialogCtrl';

/** Independently authored demo retest dialog; structural alignment only. */
export function RetestDialog({
  onMove,
  onClose,
}: {
  onMove: (removeFromDatabank: boolean) => void;
  onClose: () => void;
}) {
  const { applyConfig, setApplyConfig, copy, move } = useRetestDialog(onMove, onClose);
  return (
    <SqxModal title="Do you want to copy seleted strategies to Retester?" onClose={onClose} width={450}
      footer={
        <>
          <SqxButton onClick={onClose}>Cancel</SqxButton>
          <SqxButton primary onClick={copy}>Copy (keep original)</SqxButton>
          <SqxButton primary onClick={move}>Move (remove from this databank)</SqxButton>
        </>
      }
    >
      <label className="sqx-check">
        <input
          type="checkbox"
          checked={applyConfig}
          onChange={e => setApplyConfig(e.target.checked)}
        />
        <span>
          Apply current config
          <br />
          This will overwrite your Retester config with this task's one.
        </span>
      </label>
    </SqxModal>
  );
}
