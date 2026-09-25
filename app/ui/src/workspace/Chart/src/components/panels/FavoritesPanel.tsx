import { useStore } from 'zustand';
import { useChart } from '../../hooks/useChartEngine';
import { tools } from '../../tools/catalog';
import { keyFor } from '../../types';
export function FavoritesPanel() {
  const { store } = useChart(),
    s = useStore(store);
  return (
    <section className="cq-panel" aria-label="Favorites and objects">
      <header>
        <h2>Favorite tools & objects</h2>
        <button aria-label="Close favorites" onClick={() => s.setUI({ panel: null })}>
          ×
        </button>
      </header>
      <div className="cq-favorites">
        {s.favorites.map((id) => (
          <button key={id} onClick={() => s.setUI({ tool: id })}>
            {tools[id].label}
          </button>
        ))}
      </div>
      {(s.drawings[keyFor(s.chart)] ?? []).map((d) => (
        <div className="cq-panel-row" key={d.id}>
          <button onClick={() => s.setUI({ selected: d.id, dialog: 'drawing' })}>
            {tools[d.tool].label} {d.text}
          </button>
          <span>
            {d.hidden ? 'Hidden' : ''} {d.locked ? 'Locked' : ''}
          </span>
        </div>
      ))}
    </section>
  );
}
