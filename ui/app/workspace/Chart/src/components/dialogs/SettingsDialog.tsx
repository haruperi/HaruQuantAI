import { useStore } from 'zustand';
import { useChart } from '../../hooks/useChartEngine';
import type { Settings } from '../../types';
import { zones } from '../bottombar/BottomBar';
import { Modal } from '../Modal';
export function SettingsDialog() {
  const { store } = useChart(),
    s = useStore(store);
  const toggles: [keyof Settings, string][] = [
    ['countdown', 'Bar-close countdown'],
    ['magnet', 'Magnet default'],
    ['volume', 'Volume histogram'],
    ['previousClose', 'Previous close'],
    ['tooltip', 'Floating OHLC tooltip'],
    ['gaps', 'Compress session gaps'],
    ['sessions', 'Session breaks'],
    ['minimap', 'History minimap'],
    ['reverse', 'Reverse price scale'],
    ['auto', 'Auto-scale'],
  ];
  return (
    <Modal title="Chart settings">
      <div className="cq-form">
        <div className="cq-fields">
          <label>
            Theme
            <select
              aria-label="Chart theme"
              value={s.chart.theme}
              onChange={(e) => s.settings({ theme: e.target.value as 'dark' | 'light' })}
            >
              <option value="dark">Dark</option>
              <option value="light">Light</option>
            </select>
          </label>
          <label>
            Timezone
            <select
              value={s.chart.timezone}
              onChange={(e) => s.settings({ timezone: e.target.value })}
            >
              {zones.map((z) => (
                <option key={z}>{z}</option>
              ))}
            </select>
          </label>
          <label>
            Price precision
            <input
              aria-label="Price precision"
              type="number"
              min="0"
              max="8"
              value={s.chart.precision}
              onChange={(e) =>
                s.settings({
                  precision: Math.max(0, Math.min(8, Math.round(Number(e.target.value)))),
                })
              }
            />
          </label>
          <label>
            Scale
            <select
              value={s.chart.scale}
              onChange={(e) => s.settings({ scale: e.target.value as Settings['scale'] })}
            >
              {['linear', 'log', 'percent', 'indexed'].map((v) => (
                <option key={v}>{v}</option>
              ))}
            </select>
          </label>
        </div>
        {toggles.map(([key, label]) => (
          <label className="cq-check" key={key}>
            <input
              type="checkbox"
              checked={Boolean(s.chart[key])}
              onChange={(e) => s.settings({ [key]: e.target.checked })}
            />
            {label}
          </label>
        ))}
        <p className="cq-muted">
          These settings apply only to this chart. Data, alerts, and orders are simulated.
        </p>
      </div>
    </Modal>
  );
}
