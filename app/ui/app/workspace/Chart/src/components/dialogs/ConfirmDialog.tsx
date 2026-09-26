import { useChart } from '../../hooks/useChartEngine';
import { keyFor } from '../../types';
import { Modal } from '../Modal';
export function ConfirmDialog() {
  const { store } = useChart(),
    s = store.getState();
  return (
    <Modal title="Delete all drawings?">
      <div className="cq-form">
        <p>
          Remove unlocked drawings for {s.chart.symbol} · {s.chart.interval}? You can undo this
          change.
        </p>
        <button
          className="cq-danger"
          disabled={s.ui.lock}
          onClick={() => {
            s.setDrawings((s.drawings[keyFor(s.chart)] ?? []).filter((d) => d.locked));
            s.setUI({ dialog: null, selected: null });
          }}
        >
          Delete drawings
        </button>
        <button onClick={() => s.setUI({ dialog: null })}>Cancel</button>
      </div>
    </Modal>
  );
}
