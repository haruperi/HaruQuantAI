import { useStore } from 'zustand';
import {
  Search,
  ChevronDown,
  ChartCandlestick,
  Undo2,
  Redo2,
  Rewind,
  BellPlus,
  Camera,
  Maximize,
  Settings,
  ChartNoAxesCombined,
} from 'lucide-react';
import { intervals, chartStyles } from '../../types';
import { useChart } from '../../hooks/useChartEngine';
import { ToolButton } from '../Tooltip';
import { exportChart, fullscreen } from '../../engine/export';
export function TopBar() {
  const { store, engine, root } = useChart(),
    s = useStore(store);
  return (
    <header className="cq-top">
      <button className="cq-symbol" onClick={() => s.setUI({ dialog: 'symbol' })}>
        <Search size={15} />
        <strong>{s.chart.symbol}</strong>
        <ChevronDown size={12} />
      </button>
      <span className="cq-divider" />
      <select
        aria-label="Interval"
        value={s.chart.interval}
        onChange={(e) => s.settings({ interval: e.target.value as typeof s.chart.interval })}
      >
        {intervals.map((i) => (
          <option key={i}>{i}</option>
        ))}
      </select>
      <span className="cq-divider" />
      <ChartCandlestick size={18} />
      <select
        aria-label="Chart style"
        className="cq-style-select"
        value={s.chart.style}
        onChange={(e) => s.settings({ style: e.target.value as typeof s.chart.style })}
      >
        {chartStyles.map((i) => (
          <option key={i}>{i}</option>
        ))}
      </select>
      <span className="cq-divider" />
      <button onClick={() => s.setUI({ dialog: 'indicators' })}>
        <ChartNoAxesCombined size={17} />
        Indicators
        <ChevronDown size={11} />
      </button>
      <ToolButton label="Search indicators" onClick={() => s.setUI({ dialog: 'indicators' })}>
        <Search size={16} />
      </ToolButton>
      <span className="cq-divider" />
      <ToolButton label="Create alert" onClick={() => s.setUI({ dialog: 'alert' })}>
        <BellPlus size={18} />
      </ToolButton>
      <button
        className={s.ui.replay || s.ui.replayPick ? 'cq-active' : ''}
        onClick={() =>
          s.setUI(
            s.ui.replay ? { replay: false, playing: false } : { replayPick: !s.ui.replayPick },
          )
        }
      >
        <Rewind size={17} />
        Replay
      </button>
      <ToolButton
        label="Undo"
        shortcut="Ctrl Z"
        disabled={!s.history.past.length}
        onClick={() => s.undo()}
      >
        <Undo2 size={17} />
      </ToolButton>
      <ToolButton
        label="Redo"
        shortcut="Ctrl Shift Z"
        disabled={!s.history.future.length}
        onClick={() => s.undo(true)}
      >
        <Redo2 size={17} />
      </ToolButton>
      <div className="cq-top-spacer" />
      <input
        className="cq-title"
        aria-label="Layout title"
        value={s.chart.title}
        onChange={(e) => s.settings({ title: e.target.value })}
        maxLength={80}
      />
      <ToolButton label="Chart settings" onClick={() => s.setUI({ dialog: 'settings' })}>
        <Settings size={18} />
      </ToolButton>
      <ToolButton
        label="Fullscreen"
        shortcut="F"
        onClick={() => void fullscreen(root.current, store)}
      >
        <Maximize size={18} />
      </ToolButton>
      <ToolButton
        label="Save chart image"
        onClick={() => void exportChart(root.current, engine.current, store)}
      >
        <Camera size={18} />
      </ToolButton>
    </header>
  );
}
