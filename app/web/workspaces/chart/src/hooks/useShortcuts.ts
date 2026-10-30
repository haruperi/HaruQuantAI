import { useEffect } from 'react';
import { useChart } from './useChartEngine';
import { keyFor, type ToolId } from '../types';
import { fullscreen } from '../engine/export';
export const shortcuts = [
  ['Alt+T', 'Trend line'],
  ['Alt+H', 'Horizontal line'],
  ['Alt+V', 'Vertical line'],
  ['Alt+F', 'Fib retracement'],
  ['Alt+R', 'Ray'],
  ['T', 'Text'],
  ['M', 'Magnet'],
  ['Ctrl/Cmd+Z', 'Undo'],
  ['Ctrl/Cmd+Shift+Z', 'Redo'],
  ['Delete', 'Delete selected'],
  ['Esc', 'Cancel tool / close dialog'],
  ['+ / −', 'Zoom in / out'],
  ['0', 'Reset scales'],
  ['L', 'Log scale'],
  ['A', 'Auto-scale'],
  ['P', 'Crosshair'],
  ['/', 'Symbol search'],
  ['F', 'Fullscreen'],
  ['?', 'Keyboard help'],
  ['Enter', 'Complete polygon'],
];
export function useShortcuts() {
  const { store, engine, root } = useChart();
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const s = store.getState(),
        target = e.target;
      if (e.key === 'Escape') {
        s.setUI({ dialog: null, menu: null, replayPick: false });
        engine.current?.cancel();
        return;
      }
      if (
        target instanceof HTMLElement &&
        (target.closest('input,textarea,select,[contenteditable="true"]') || s.ui.dialog)
      )
        return;
      const key = e.key.toLowerCase();
      if (e.altKey) {
        const tool: Record<string, ToolId> = {
          t: 'TrendLine',
          h: 'HorizontalLine',
          v: 'VerticalLine',
          f: 'FibRetracement',
          r: 'Ray',
        };
        if (tool[key]) {
          e.preventDefault();
          s.setUI({ tool: tool[key] });
        }
        return;
      }
      if ((e.ctrlKey || e.metaKey) && key === 'z') {
        e.preventDefault();
        s.undo(e.shiftKey);
        return;
      }
      if (e.ctrlKey || e.metaKey) return;
      if (key === 't') s.setUI({ tool: 'Text' });
      else if (key === 'm') s.settings({ magnet: !s.chart.magnet });
      else if (key === 'delete' || key === 'backspace') {
        if (!s.ui.lock)
          s.setDrawings(
            (s.drawings[keyFor(s.chart)] ?? []).filter((d) => d.id !== s.ui.selected || d.locked),
          );
      } else if (key === '+' || key === '=') engine.current?.zoom(1.3);
      else if (key === '-') engine.current?.zoom(1 / 1.3);
      else if (key === '0') engine.current?.reset();
      else if (key === 'l') s.settings({ scale: s.chart.scale === 'log' ? 'linear' : 'log' });
      else if (key === 'a') s.settings({ auto: !s.chart.auto });
      else if (key === 'p')
        s.setUI({ cursor: s.ui.cursor === 'crosshair' ? 'arrow' : 'crosshair' });
      else if (key === '/') {
        e.preventDefault();
        s.setUI({ dialog: 'symbol' });
      } else if (key === 'f') void fullscreen(root.current, store);
      else if (key === '?') s.setUI({ dialog: 'help' });
      else if (key === 'enter') engine.current?.finish();
    };
    const element = root.current;
    element?.addEventListener('keydown', handler);
    return () => element?.removeEventListener('keydown', handler);
  }, [store, engine, root]);
}
