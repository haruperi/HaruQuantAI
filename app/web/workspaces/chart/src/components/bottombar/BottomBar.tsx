import { useEffect, useState } from 'react';
import { useStore } from 'zustand';
import { Camera, Maximize, Bell, ListOrdered } from 'lucide-react';
import { useChart } from '../../hooks/useChartEngine';
import { timeLabel } from '../../utils/time';
import { ToolButton } from '../Tooltip';
import { exportChart, fullscreen } from '../../engine/export';
export const zones = [
  'UTC',
  ...Array.from({ length: 12 }, (_, i) => 'UTC+' + (i + 1)),
  ...Array.from({ length: 12 }, (_, i) => 'UTC-' + (i + 1)),
  'Exchange',
  'Local',
];
export function BottomBar() {
  const { store, root, engine } = useChart(),
    s = useStore(store),
    [now, setNow] = useState(Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  return (
    <footer className="cq-bottom">
      <div className="cq-ranges">
        {['1D', '5D', '1M', '3M', '6M', 'YTD', '1Y', '5Y', 'All'].map((r) => (
          <button
            key={r}
            className={s.chart.range === r ? 'cq-active' : ''}
            onClick={() =>
              s.settings({
                range: r,
                interval: r === '1D' ? '3m' : r === '5D' ? '15m' : r === '1M' ? '1h' : '1D',
              })
            }
          >
            {r}
          </button>
        ))}
      </div>
      <span className="cq-bottom-fill" />
      <button
        aria-label="Alerts panel"
        onClick={() => s.setUI({ panel: s.ui.panel === 'alerts' ? null : 'alerts' })}
      >
        <Bell size={14} />
        {s.alerts.reduce((n, a) => n + a.triggers, 0) || ''}
      </button>
      <button
        aria-label="Positions panel"
        onClick={() => s.setUI({ panel: s.ui.panel === 'positions' ? null : 'positions' })}
      >
        <ListOrdered size={14} />
      </button>
      <time>{timeLabel(now, s.chart.timezone, true)}</time>
      <select
        aria-label="Clock timezone"
        value={s.chart.timezone}
        onChange={(e) => s.settings({ timezone: e.target.value })}
      >
        {zones.map((z) => (
          <option key={z}>{z}</option>
        ))}
      </select>
      <ToolButton
        label="Snapshot"
        onClick={() => void exportChart(root.current, engine.current, store)}
      >
        <Camera size={15} />
      </ToolButton>
      <ToolButton label="Expand chart" onClick={() => void fullscreen(root.current, store)}>
        <Maximize size={15} />
      </ToolButton>
    </footer>
  );
}
