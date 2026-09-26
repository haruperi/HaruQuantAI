import { useStore } from 'zustand';
import { useChart } from '../../hooks/useChartEngine';
import { pnl } from '../../store/positions';
export function PositionsPanel() {
  const { store, engine } = useChart(),
    s = useStore(store);
  return (
    <section className="cq-panel" aria-label="Simulated positions">
      <header>
        <h2>
          Paper trading <small>SIMULATED</small>
        </h2>
        <button aria-label="Close positions panel" onClick={() => s.setUI({ panel: null })}>
          ×
        </button>
      </header>
      {!s.positions.length && <p>No positions. Use Buy or Sell to place a simulated order.</p>}
      {s.positions.map((p) => (
        <div className="cq-panel-row" key={p.id}>
          <strong>{p.symbol}</strong>
          <span>
            {p.side.toUpperCase()} {p.quantity} @ {p.entry.toFixed(2)} · {p.status}
          </span>
          <output data-position-pnl={p.id}>
            {pnl(p, engine.current?.quotes.get(p.symbol)?.price ?? p.entry).toFixed(2)}
          </output>
          {['open', 'pending'].includes(p.status) && (
            <button
              disabled={s.ui.replay}
              onClick={() =>
                s.setPositions(
                  s.positions.map((v) =>
                    v.id === p.id
                      ? {
                          ...v,
                          status: p.status === 'pending' ? 'canceled' : 'closed',
                          exit: engine.current?.quotes.get(p.symbol)?.price ?? p.entry,
                        }
                      : v,
                  ),
                )
              }
            >
              {p.status === 'pending' ? 'Cancel order' : 'Close position'}
            </button>
          )}
        </div>
      ))}
    </section>
  );
}
