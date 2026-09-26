import { useStore } from 'zustand';
import { useChart } from '../../hooks/useChartEngine';
export function AlertsPanel() {
  const { store } = useChart(),
    s = useStore(store);
  return (
    <section className="cq-panel" aria-label="Alerts">
      <header>
        <h2>
          Alerts <small>{s.alerts.length}</small>
        </h2>
        <button onClick={() => s.setUI({ dialog: 'alert' })}>+ New alert</button>
        <button aria-label="Close alerts" onClick={() => s.setUI({ panel: null })}>
          ×
        </button>
      </header>
      {!s.alerts.length && (
        <p>No alerts yet. Create a price condition to monitor simulated ticks.</p>
      )}
      {s.alerts.map((a) => (
        <div className="cq-panel-row" key={a.id}>
          <strong>{a.symbol}</strong>
          <span>
            {a.condition} {a.value.toFixed(2)} · {a.triggers} triggers
          </span>
          <button
            onClick={() =>
              s.setAlerts(s.alerts.map((v) => (v.id === a.id ? { ...v, active: !v.active } : v)))
            }
          >
            {a.active ? 'Pause' : 'Enable'}
          </button>
          <button
            aria-label={'Delete alert ' + a.symbol}
            onClick={() => s.setAlerts(s.alerts.filter((v) => v.id !== a.id))}
          >
            ×
          </button>
        </div>
      ))}
    </section>
  );
}
