import { useEffect } from 'react';
import { useStore } from 'zustand';
import { useChart } from '../../hooks/useChartEngine';
export function Toasts() {
  const { store } = useChart(),
    toast = useStore(store, (s) => s.ui.toast);
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => store.getState().setUI({ toast: '' }), 6000);
    return () => clearTimeout(timer);
  }, [toast, store]);
  return toast ? (
    <div className="cq-toast" role="status">
      {toast}
      <button
        aria-label="Dismiss notification"
        onClick={() => store.getState().setUI({ toast: '' })}
      >
        ×
      </button>
    </div>
  ) : null;
}
