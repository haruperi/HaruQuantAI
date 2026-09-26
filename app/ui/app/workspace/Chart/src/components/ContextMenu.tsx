import { useStore } from 'zustand';
import { useChart } from '../hooks/useChartEngine';
import { keyFor } from '../types';
export function ContextMenu() {
  const { store, engine } = useChart(),
    s = useStore(store),
    menu = s.ui.menu;
  if (!menu) return null;
  const list = s.drawings[keyFor(s.chart)] ?? [],
    selected = list.find((d) => d.id === s.ui.selected);
  const action = (fn: () => void) => () => {
    fn();
    s.setUI({ menu: null });
  };
  const rows: { label: string; run: () => void; disabled?: boolean }[] =
    menu.target === 'drawing' && selected
      ? [
          { label: 'Drawing settings', run: () => s.setUI({ dialog: 'drawing' }) },
          {
            label: selected.locked ? 'Unlock' : 'Lock',
            run: () =>
              s.setDrawings(
                list.map((d) => (d.id === selected.id ? { ...d, locked: !d.locked } : d)),
              ),
          },
          {
            label: 'Hide drawing',
            run: () =>
              s.setDrawings(list.map((d) => (d.id === selected.id ? { ...d, hidden: true } : d))),
          },
          {
            label: 'Delete drawing',
            disabled: selected.locked || s.ui.lock,
            run: () => s.setDrawings(list.filter((d) => d.id !== selected.id)),
          },
        ]
      : menu.target === 'price'
        ? [
            {
              label: 'Auto-scale',
              run: () => {
                s.settings({ auto: true });
                engine.current?.reset();
              },
            },
            ...(['linear', 'log', 'percent', 'indexed'] as const).map((mode) => ({
              label:
                mode === 'indexed'
                  ? 'Indexed to 100'
                  : mode === 'percent'
                    ? 'Percentage scale'
                    : mode === 'log'
                      ? 'Log scale'
                      : 'Linear scale',
              run: () => s.settings({ scale: mode }),
            })),
            { label: 'Reverse scale', run: () => s.settings({ reverse: !s.chart.reverse }) },
            { label: 'Add price line', run: () => engine.current?.addPriceLine(menu.y) },
          ]
        : menu.target === 'time'
          ? [
              { label: 'Reset scale', run: () => engine.current?.reset() },
              { label: 'Scroll to last bar', run: () => engine.current?.scrollLast() },
              {
                label: 'Toggle session breaks',
                run: () => s.settings({ sessions: !s.chart.sessions }),
              },
              { label: 'Timezone settings', run: () => s.setUI({ dialog: 'settings' }) },
            ]
          : [
              { label: 'Reset chart', run: () => engine.current?.reset() },
              { label: 'Scroll to last bar', run: () => engine.current?.scrollLast() },
              { label: 'Add indicator', run: () => s.setUI({ dialog: 'indicators' }) },
              { label: 'Create alert', run: () => s.setUI({ dialog: 'alert' }) },
              { label: 'Chart settings', run: () => s.setUI({ dialog: 'settings' }) },
              { label: 'Object list', run: () => s.setUI({ panel: 'favorites' }) },
            ];
  return (
    <div
      className="cq-context"
      role="menu"
      style={{
        left: Math.min(menu.x, Math.max(0, (engine.current?.width ?? 400) - 200)) + 48,
        top: Math.min(
          menu.y + 40,
          Math.max(40, (engine.current?.height ?? 500) - rows.length * 32),
        ),
      }}
      onKeyDown={(e) => {
        if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
          e.preventDefault();
          const buttons = [
              ...e.currentTarget.querySelectorAll<HTMLButtonElement>('button:not(:disabled)'),
            ],
            index = buttons.indexOf(document.activeElement as HTMLButtonElement);
          buttons[
            (index + (e.key === 'ArrowDown' ? 1 : buttons.length - 1)) % buttons.length
          ]?.focus();
        }
      }}
    >
      {rows.map((row, i) => (
        <button
          autoFocus={i === 0}
          role="menuitem"
          key={row.label}
          disabled={row.disabled}
          onClick={action(row.run)}
        >
          {row.label}
        </button>
      ))}
    </div>
  );
}
