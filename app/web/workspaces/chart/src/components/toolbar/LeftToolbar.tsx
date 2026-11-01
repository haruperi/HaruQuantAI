import { useEffect, useRef, useState } from 'react';
import { useStore } from 'zustand';
import {
  MousePointer2,
  CirclePlay,
  WandSparkles,
  Eraser,
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
import { keyFor, toolIds, type ToolId, type CursorMode } from '../../types';
import { ToolButton } from '../Tooltip';
const cursors = [
  { id: 'crosshair', label: 'Cross', icon: Crosshair },
  { id: 'dot', label: 'Dot', icon: Dot },
  { id: 'arrow', label: 'Arrow', icon: MousePointer2 },
  { id: 'demonstration', label: 'Demonstration', icon: CirclePlay },
  { id: 'magic', label: 'Magic', icon: WandSparkles },
  { id: 'eraser', label: 'Eraser', icon: Eraser },
] satisfies { id: CursorMode; label: string; icon: typeof Crosshair }[];
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
  const closeTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const cancelClose = () => clearTimeout(closeTimer.current);
  const scheduleClose = () => {
    clearTimeout(longPress.current);
    cancelClose();
    closeTimer.current = setTimeout(() => setOpen(null), 150);
  };
  useEffect(
    () => () => {
      clearTimeout(longPress.current);
      clearTimeout(closeTimer.current);
    },
    [],
  );
  const choose = (id: ToolId) => {
    cancelClose();
    s.setUI({ tool: id });
    setOpen(null);
  };
  const selected = (s.drawings[keyFor(s.chart)] ?? []).find((d) => d.id === s.ui.selected);
  return (
    <aside className="cq-toolbar" aria-label="Drawing tools">
      <div className="cq-tool-group" onPointerEnter={cancelClose} onPointerLeave={scheduleClose}>
        <ToolButton
          label="Cursor mode"
          shortcut="P"
          aria-haspopup="menu"
          aria-expanded={open === 'cursor'}
          onClick={() => setOpen(open === 'cursor' ? null : 'cursor')}
        >
          {(() => {
            const Icon = cursors.find((cursor) => cursor.id === s.ui.cursor)!.icon;
            return <Icon />;
          })()}
          <ChevronRight className="cq-caret" size={10} onPointerEnter={() => setOpen('cursor')} />
        </ToolButton>
        {open === 'cursor' && (
          <div
            className="cq-flyout cq-cursor-menu"
            role="menu"
            aria-label="Cursor modes"
            onPointerEnter={cancelClose}
            onPointerLeave={scheduleClose}
          >
            {cursors.map(({ id, label, icon: Icon }) => (
              <div
                className={
                  'cq-tool-option cq-cursor-option' +
                  (id === 'eraser' ? ' cq-cursor-separator' : '')
                }
                key={id}
              >
                <button
                  role="menuitemradio"
                  aria-checked={s.ui.cursor === id}
                  onClick={() => {
                    cancelClose();
                    s.setUI({ cursor: id, tool: 'cursor' });
                    setOpen(null);
                  }}
                >
                  <Icon />
                  <span>{label}</span>
                </button>
                <button
                  aria-label={'Favorite cursor ' + label}
                  aria-pressed={s.ui.cursorFavorites.includes(id)}
                  className={s.ui.cursorFavorites.includes(id) ? 'cq-starred' : ''}
                  onClick={() =>
                    s.setUI({
                      cursorFavorites: s.ui.cursorFavorites.includes(id)
                        ? s.ui.cursorFavorites.filter((mode) => mode !== id)
                        : [...s.ui.cursorFavorites, id],
                    })
                  }
                >
                  <Star size={13} />
                </button>
              </div>
            ))}
            <div className="cq-cursor-separator cq-cursor-toggle">
              <span id="cq-values-label">Values tooltip on long press</span>
              <button
                role="switch"
                aria-labelledby="cq-values-label"
                aria-checked={s.ui.valuesOnLongPress}
                onClick={() => s.setUI({ valuesOnLongPress: !s.ui.valuesOnLongPress })}
              >
                <span />
              </button>
            </div>
          </div>
        )}
      </div>
      <hr />
      {groups.map(({ name, icon: Icon }) => (
        <div
          className="cq-tool-group"
          key={name}
          onPointerEnter={cancelClose}
          onPointerLeave={scheduleClose}
        >
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
            <div
              className="cq-flyout"
              role="menu"
              aria-label={name + ' tools'}
              onPointerEnter={cancelClose}
              onPointerLeave={scheduleClose}
            >
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
