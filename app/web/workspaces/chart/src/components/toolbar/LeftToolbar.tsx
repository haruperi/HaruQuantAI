import { useEffect, useRef, useState } from 'react';
import { useStore } from 'zustand';
import {
  MousePointer2,
  Crosshair,
  Dot,
  TrendingUp,
  Hash,
  Shapes,
  Type,
  Ruler,
  Magnet,
  LockKeyhole,
  EyeOff,
  Trash2,
  Star,
  ZoomIn,
  ZoomOut,
  ChevronRight,
  HelpCircle,
  Minus,
  ArrowUpRight,
} from 'lucide-react';
import { useChart } from '../../hooks/useChartEngine';
import { tools } from '../../tools/catalog';
import { keyFor, toolIds, type ToolId } from '../../types';
import { ToolButton } from '../Tooltip';
const groups = [
  { name: 'Trend', icon: TrendingUp },
  { name: 'Fibonacci', icon: Hash },
  { name: 'Shapes', icon: Shapes },
  { name: 'Annotate', icon: Type },
];
export function LeftToolbar() {
  const { store, engine } = useChart(),
    s = useStore(store),
    [open, setOpen] = useState<string | null>(null);
  const longPress = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const longPressed = useRef(false);
  useEffect(() => () => clearTimeout(longPress.current), []);
  const choose = (id: ToolId) => {
    s.setUI({ tool: id });
    setOpen(null);
  };
  const selected = (s.drawings[keyFor(s.chart)] ?? []).find((d) => d.id === s.ui.selected);
  return (
    <aside className="cq-toolbar" aria-label="Drawing tools">
      <ToolButton
        label="Cursor mode"
        shortcut="P"
        onClick={() =>
          s.setUI({
            cursor:
              s.ui.cursor === 'crosshair' ? 'dot' : s.ui.cursor === 'dot' ? 'arrow' : 'crosshair',
            tool: 'cursor',
          })
        }
      >
        {s.ui.cursor === 'crosshair' ? (
          <Crosshair />
        ) : s.ui.cursor === 'dot' ? (
          <Dot />
        ) : (
          <MousePointer2 />
        )}
      </ToolButton>
      <hr />
      {groups.map(({ name, icon: Icon }) => (
        <div className="cq-tool-group" key={name}>
          <ToolButton
            label={name + ' tools'}
            className={s.ui.tool !== 'cursor' && tools[s.ui.tool].group === name ? 'cq-active' : ''}
            onPointerDown={() => {
              longPressed.current = false;
              longPress.current = setTimeout(() => {
                longPressed.current = true;
                setOpen(name);
              }, 450);
            }}
            onPointerUp={() => clearTimeout(longPress.current)}
            onPointerCancel={() => clearTimeout(longPress.current)}
            onClick={() => {
              if (!longPressed.current) setOpen(open === name ? null : name);
            }}
          >
            <Icon />
            <ChevronRight className="cq-caret" size={10} onPointerEnter={() => setOpen(name)} />
          </ToolButton>
          {open === name && (
            <div className="cq-flyout" role="menu" aria-label={name + ' tools'}>
              {toolIds
                .filter((id) => tools[id].group === name)
                .map((id) => (
                  <div key={id} className="cq-tool-option">
                    <button role="menuitem" onClick={() => choose(id)}>
                      <span>{tools[id].label}</span>
                      <kbd>{tools[id].shortcut}</kbd>
                    </button>
                    <button
                      aria-label={'Favorite ' + tools[id].label}
                      className={s.favorites.includes(id) ? 'cq-starred' : ''}
                      onClick={() =>
                        store.setState({
                          favorites: s.favorites.includes(id)
                            ? s.favorites.filter((x) => x !== id)
                            : [...s.favorites, id],
                        })
                      }
                    >
                      <Star size={13} />
                    </button>
                  </div>
                ))}
            </div>
          )}
        </div>
      ))}
      <hr />
      <ToolButton
        label="Measure"
        onClick={() => choose('Measure')}
        className={s.ui.tool === 'Measure' ? 'cq-active' : ''}
      >
        <Ruler />
      </ToolButton>
      <ToolButton label="Zoom in" shortcut="+" onClick={() => engine.current?.zoom(1.3)}>
        <ZoomIn />
      </ToolButton>
      <ToolButton label="Zoom out" shortcut="−" onClick={() => engine.current?.zoom(1 / 1.3)}>
        <ZoomOut />
      </ToolButton>
      <hr />
      <ToolButton
        label="Magnet"
        shortcut="M"
        aria-pressed={s.chart.magnet}
        className={s.chart.magnet ? 'cq-active' : ''}
        onClick={() => s.settings({ magnet: !s.chart.magnet })}
      >
        <Magnet />
      </ToolButton>
      <ToolButton
        label="Lock all drawings"
        aria-pressed={s.ui.lock}
        className={s.ui.lock ? 'cq-active' : ''}
        onClick={() => s.setUI({ lock: !s.ui.lock })}
      >
        <LockKeyhole />
      </ToolButton>
      <ToolButton
        label="Hide all drawings"
        aria-pressed={s.ui.hide}
        className={s.ui.hide ? 'cq-active' : ''}
        onClick={() => s.setUI({ hide: !s.ui.hide })}
      >
        <EyeOff />
      </ToolButton>
      <hr />
      <ToolButton
        label="Delete selected drawing"
        shortcut="Delete"
        disabled={!selected || selected.locked || s.ui.lock}
        onClick={() =>
          s.setDrawings((s.drawings[keyFor(s.chart)] ?? []).filter((d) => d.id !== s.ui.selected))
        }
      >
        <Minus />
      </ToolButton>
      <ToolButton
        label="Delete all drawings"
        disabled={s.ui.lock}
        onClick={() => s.setUI({ dialog: 'delete' })}
      >
        <Trash2 />
      </ToolButton>
      <div className="cq-tool-bottom">
        <ToolButton
          label="Favorites"
          aria-pressed={s.ui.panel === 'favorites'}
          onClick={() => s.setUI({ panel: s.ui.panel === 'favorites' ? null : 'favorites' })}
        >
          <Star />
        </ToolButton>
        <ToolButton label="Keyboard shortcuts" onClick={() => s.setUI({ dialog: 'help' })}>
          <HelpCircle />
        </ToolButton>
      </div>
      <span className="cq-tool-badge">
        <ArrowUpRight size={10} />
      </span>
    </aside>
  );
}
