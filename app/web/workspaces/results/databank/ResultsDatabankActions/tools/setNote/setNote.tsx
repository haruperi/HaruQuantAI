import { SqxModal, SqxButton } from '../../../ProjectDatabanks/DatabankDialogs';
import { useSetNoteDraft } from './SetNotePopupCtrl';

/** Existing note presentation; shared modal lifecycle remains authoritative. */
export function SetNoteDialog({ currentNote, onSetNote, onClose }: {
  currentNote: string;
  onSetNote: (note: string) => void;
  onClose: () => void;
}) {
  const { note, setNote } = useSetNoteDraft(currentNote);
  return (
    <SqxModal title="Set note" onClose={onClose}
      footer={<>
        <SqxButton onClick={onClose}>Cancel</SqxButton>
        <SqxButton primary onClick={() => { onSetNote(note); onClose(); }}>Set note</SqxButton>
      </>}
    >
      <textarea className="sqx-input sqx-textarea" value={note}
        onChange={e => setNote(e.target.value)} rows={4} autoFocus />
    </SqxModal>
  );
}
