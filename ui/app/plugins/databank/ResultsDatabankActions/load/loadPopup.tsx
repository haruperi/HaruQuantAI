import { SqxModal } from '../../ProjectDatabanks/DatabankDialogs';
import { useLoadPopup } from './LoadPopupCtrl';
import './styles.css';

/** Independently authored simulated load view; structural alignment only. */
export function LoadRecordsDialog({ onFinished }: { onFinished: () => void }) {
  const progress = useLoadPopup(onFinished);

  return (
    <SqxModal title="Loading records" onClose={onFinished}>
      <p className="sqx-dialog-text">Loading selected records into databank...</p>
      <div className="sqx-progress" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
        <div className="sqx-progress-bar" style={{ width: `${progress}%` }}>{progress}%</div>
      </div>
    </SqxModal>
  );
}
