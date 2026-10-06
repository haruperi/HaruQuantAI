import { useStore } from 'zustand';
import { useChart } from '../../hooks/useChartEngine';
export function ReplayControls() {
  const { store, engine } = useChart(),
    s = useStore(store);
  if (!s.ui.replay) return null;
  return (
    <div className="cq-replay">
      <strong>BAR REPLAY</strong>
      <button aria-label="Previous replay bar" onClick={() => engine.current?.step(-1)}>
        ⏮
      </button>
      <button
        aria-label={s.ui.playing ? 'Pause replay' : 'Play replay'}
        onClick={() => s.setUI({ playing: !s.ui.playing })}
      >
        {s.ui.playing ? 'Pause' : 'Play'}
      </button>
      <button aria-label="Next replay bar" onClick={() => engine.current?.step(1)}>
        ⏭
      </button>
      <select
        aria-label="Replay speed"
        value={s.ui.speed}
        onChange={(e) => s.setUI({ speed: Number(e.target.value) })}
      >
        {[1, 2, 3, 5, 10].map((v) => (
          <option key={v} value={v}>
            {v}×
          </option>
        ))}
      </select>
      <button onClick={() => s.setUI({ replay: false, playing: false })}>Exit replay</button>
    </div>
  );
}
