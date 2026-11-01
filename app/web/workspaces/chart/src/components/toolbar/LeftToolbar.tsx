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
  Network,
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
  StickyNote,
  BadgeDollarSign,
  MapPin,
  Table2,
  MessageSquare,
  MessageCircle,
  Tag,
  Signpost,
  Flag,
  Image as ImageIcon,
  Share2,
  Lightbulb,
  Smile,
} from 'lucide-react';
import { useChart } from '../../hooks/useChartEngine';
import {
  tools,
  lineSections,
  fibonacciSections,
  patternSections,
  forecastingSections,
  shapeSections,
} from '../../tools/catalog';
import { keyFor, type ToolId, type CursorMode, type DrawingGroup } from '../../types';
import { textNoteSections } from '../../tools/textNotes';
import { indicators } from '../../indicators/catalog';
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
  { name: 'Patterns', icon: Network },
  { name: 'Forecasting', icon: ArrowUpRight },
  { name: 'Shapes', icon: Shapes },
  { name: 'Annotate', icon: Type },
] satisfies { name: DrawingGroup; icon: typeof Type }[];
const annotationIcons: Partial<Record<ToolId, typeof Type>> = {
  Text: Type,
  AnchoredNote: StickyNote,
  Sticker: Smile,
  Note: StickyNote,
  PriceNote: BadgeDollarSign,
  Pin: MapPin,
  Table: Table2,
  Callout: MessageSquare,
  Comment: MessageCircle,
  PriceLabel: Tag,
  Signpost,
  FlagMark: Flag,
  Image: ImageIcon,
  Post: Share2,
  Idea: Lightbulb,
};
function AnnotationToolIcon({ id }: { id: ToolId }) {
  const Icon = annotationIcons[id] ?? Type;
  return <Icon aria-hidden="true" />;
}
function MagnetStrengthIcon({ strength }: { strength: 'weak' | 'strong' }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
      <path d="M5 13V8a7 7 0 0 1 14 0v5h-5V8a2 2 0 0 0-4 0v5z" />
      <path d="M5 10h5M14 10h5" />
      <circle cx="12" cy="18" r="1" fill="currentColor" stroke="none" />
      {strength === 'strong' && (
        <>
          <circle cx="7" cy="20.5" r="1" fill="currentColor" stroke="none" />
          <circle cx="17" cy="20.5" r="1" fill="currentColor" stroke="none" />
        </>
      )}
    </svg>
  );
}
function LineToolIcon({ id }: { id: ToolId }) {
  const horizontal = ['HorizontalLine', 'HorizontalRay', 'PriceLine'].includes(id);
  const vertical = id === 'VerticalLine';
  const cross = id === 'CrossLine';
  const channel = [
    'ParallelChannel',
    'RegressionTrend',
    'FlatTopBottom',
    'DisjointChannel',
  ].includes(id);
  const fork = id.includes('Pitchfork');
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      {cross ? (
        <path d="M2 12h20M12 2v20" />
      ) : vertical ? (
        <path d="M12 2v20" />
      ) : horizontal ? (
        <path d="M2 12h20" />
      ) : (
        <path d="M3 20L21 3" />
      )}
      {channel && (
        <>
          <path d={id === 'FlatTopBottom' ? 'M3 4h18' : 'M3 14L16 2'} />
          <path d="M8 22L21 10" />
        </>
      )}
      {fork && (
        <>
          <path d="M3 12L14 2M10 22L22 10M3 12l7 10" />
        </>
      )}
      {id === 'InfoLine' && <rect x="12" y="15" width="9" height="6" rx="1" />}
      {id === 'TrendAngle' && <path d="M3 20h18M10 20a7 7 0 0 0-2-5" />}
      {!cross && (
        <>
          <circle cx={vertical ? 12 : 4} cy={horizontal ? 12 : 19} r="1.5" />
          <circle cx={vertical ? 12 : 20} cy={horizontal ? 12 : 4} r="1.5" />
        </>
      )}
    </svg>
  );
}
function FibonacciToolIcon({ id }: { id: ToolId }) {
  const circles = ['FibCircles', 'FibSpeedArcs', 'FibWedge'].includes(id);
  const time = ['FibTimezone', 'TrendFibTime'].includes(id);
  const fan = ['FibSpeedFan', 'Pitchfan', 'GannFan'].includes(id);
  const box = id.startsWith('Gann') && id !== 'GannFan';
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      {id === 'FibSpiral' ? (
        <path d="M12 12c-3-4-7 0-4 3 5 5 12-2 7-7C8 1-3 10 4 18c7 9 21 0 16-11" />
      ) : box ? (
        <>
          <rect x="3" y="3" width="18" height="18" />
          <path d="M3 9h18M3 15h18M9 3v18M15 3v18" />
          {id !== 'GannBox' && <path d="M3 21L21 3M3 3L21 21" />}
        </>
      ) : circles ? (
        <>
          <path d="M3 12a9 9 0 0 0 18 0M6 12a6 6 0 0 0 12 0M9 12a3 3 0 0 0 6 0" />
          {id === 'FibCircles' && <path d="M3 12a9 9 0 0 1 18 0M6 12a6 6 0 0 1 12 0" />}
        </>
      ) : time ? (
        <path d="M3 3v18M7 3v18M13 3v18M21 3v18M2 12l9 6 9-12" />
      ) : fan ? (
        <path d="M3 21L21 3M3 21L21 10M3 21h18M3 21L10 3" />
      ) : id === 'FibChannel' ? (
        <path d="M3 20L21 4M3 15L16 3M8 22L21 11" />
      ) : (
        <path d="M3 4h18M3 9h18M3 15h18M3 21h18M3 21L21 4" />
      )}
    </svg>
  );
}
function PatternToolIcon({ id }: { id: ToolId }) {
  const glyphs: Partial<Record<ToolId, string>> = {
    XABCDPattern: 'M2 19L6 6L11 16L16 3L22 12M2 19L11 16L22 12M6 6L16 3',
    CypherPattern: 'M2 19L7 8L12 16L17 3L22 12M2 19L17 3M2 19L22 12',
    HeadShoulders: 'M1 20L4 9L7 17L12 2L16 17L20 9L23 20M7 17h9',
    ABCDPattern: 'M3 19L7 3L17 20L21 5M3 19L17 20M7 3L21 5',
    TrianglePattern: 'M2 3L4 21L16 8L20 16M2 3L16 8M4 21L20 16',
    ThreeDrives: 'M1 20L4 8L7 18L11 5L14 15L18 2L22 12',
    CyclicLines: 'M4 2v20M9 2v20M14 2v20M20 2v20',
    TimeCycles: 'M2 14a5 5 0 0 1 10 0 5 5 0 0 1 10 0',
    SineLine: 'M2 12c4-14 6-14 10 0s6 14 10 0',
  };
  const wave = id.startsWith('Elliott');
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      <path d={glyphs[id] ?? 'M2 20L6 11L10 17L15 8L18 14L22 4'} />
      {wave && (
        <text x="3" y="6" fill="currentColor" stroke="none" fontSize="6">
          {id === 'ElliottImpulse'
            ? '1   5'
            : id === 'ElliottDoubleCombo' || id === 'ElliottTripleCombo'
              ? 'W   Y'
              : 'A   C'}
        </text>
      )}
    </svg>
  );
}
function ForecastingToolIcon({ id }: { id: ToolId }) {
  const glyphs: Partial<Record<ToolId, string>> = {
    LongPosition: 'M2 5h20M2 12h20M2 19h20M7 3v18M4 8l3-3 3 3',
    ShortPosition: 'M2 5h20M2 12h20M2 19h20M7 3v18M4 16l3 3 3-3',
    PositionForecast: 'M2 20L21 3M13 3h8v8M3 10v10h10',
    BarsPattern: 'M4 2v20M2 6h4v8H2M11 2v20M9 8h4v9H9M19 2v20M17 5h4v7h-4',
    GhostFeed: 'M2 19l5-7 5 4 5-10 5 3M7 7v10M17 2v10',
    Sector: 'M3 21V3a18 18 0 0 1 18 18H3M3 21L16 8',
    AnchoredVWAP: 'M2 18l5-6 5 2 5-9 5 3M4 4v16M1 12h6',
    FixedVolumeProfile: 'M3 3v18M3 5h10v3H3M3 10h17v3H3M3 15h13v3H3M21 3v18',
    AnchoredVolumeProfile: 'M21 3v18M21 5H11v3h10M21 10H4v3h17M21 15H8v3h13',
    PriceRange: 'M12 2v20M5 3h14M5 21h14M9 6l3-3 3 3M9 18l3 3 3-3',
    DateRange: 'M2 12h20M3 5v14M21 5v14M6 9l-3 3 3 3M18 9l3 3-3 3',
    DatePriceRange: 'M3 3h18v18H3zM12 6v12M6 12h12',
  };
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      <path d={glyphs[id]} />
    </svg>
  );
}
function ShapeToolIcon({ id }: { id: ToolId }) {
  const glyphs: Partial<Record<ToolId, string>> = {
    Brush: 'M2 20c8 4 4-7 9-10l5-7 5 4-7 6c-6 1-3 8-12 7',
    Highlighter: 'M2 20h14M5 17l-3-3 12-12 6 6-12 12z',
    ArrowMarker: 'M2 20L14 5l-1-3 9-1-1 9-3-2L4 22z',
    Arrow: 'M2 22L21 3M12 3h9v9',
    ArrowMarkUp: 'M12 2L2 12h6v10h8V12h6z',
    ArrowMarkDown: 'M12 22L2 12h6V2h8v10h6z',
    Rectangle: 'M3 4h18v16H3z',
    RotatedRectangle: 'M2 13L14 2l8 9-12 11z',
    PathTool: 'M2 19L8 6l6 9 8-11M16 4h6v6',
    Polyline: 'M2 19L8 6l6 9 8-11',
    Circle: 'M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0',
    Ellipse: 'M22 12a10 6 0 1 1-20 0 10 6 0 0 1 20 0',
    Triangle: 'M12 2L2 22h20z',
    Polygon: 'M2 8l8-6 12 8-4 12-14-4z',
    Arc: 'M2 20A18 18 0 0 1 20 2',
    Curve: 'M2 22Q3 2 22 3',
    DoubleCurve: 'M2 20C4-5 20 30 22 4',
  };
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      <path d={glyphs[id]} />
    </svg>
  );
}

/** Shared renderer keeps a group's collapsed icon identical to its menu icon. */
function GroupToolIcon({ name, id }: { name: DrawingGroup; id: ToolId }) {
  if (name === 'Trend') return <LineToolIcon id={id} />;
  if (name === 'Fibonacci') return <FibonacciToolIcon id={id} />;
  if (name === 'Patterns') return <PatternToolIcon id={id} />;
  if (name === 'Forecasting') return <ForecastingToolIcon id={id} />;
  if (name === 'Shapes') return <ShapeToolIcon id={id} />;
  return <AnnotationToolIcon id={id} />;
}
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
      <div
        className="cq-tool-group"
        onPointerEnter={() => {
          if (open === 'cursor') cancelClose();
        }}
        onPointerLeave={scheduleClose}
      >
        <ToolButton
          label="Cursor mode"
          shortcut="P"
          aria-haspopup="menu"
          aria-expanded={open === 'cursor'}
          onClick={() => {
            cancelClose();
            setOpen(open === 'cursor' ? null : 'cursor');
          }}
        >
          {(() => {
            const Icon = cursors.find((cursor) => cursor.id === s.ui.cursor)!.icon;
            return <Icon />;
          })()}
          <ChevronRight
            className="cq-caret"
            size={10}
            onPointerEnter={() => {
              cancelClose();
              setOpen('cursor');
            }}
          />
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
          onPointerEnter={() => {
            if (open === name) cancelClose();
          }}
          onPointerLeave={scheduleClose}
        >
          <ToolButton
            label={name + ' tools'}
            data-last-tool={s.lastGroupTools[name] ?? undefined}
            aria-description={s.lastGroupTools[name] ? 'Last selected: ' + tools[s.lastGroupTools[name]].label : undefined}
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
              cancelClose();
              if (!longPressed.current) setOpen(open === name ? null : name);
            }}
          >
            {s.lastGroupTools[name]
              ? <GroupToolIcon name={name} id={s.lastGroupTools[name]} />
              : <Icon />}
            <ChevronRight
              className="cq-caret"
              size={10}
              onPointerEnter={() => {
                cancelClose();
                setOpen(name);
              }}
            />
          </ToolButton>
          {open === name && (
            <div
              className={
                'cq-flyout' +
                (['Trend', 'Fibonacci', 'Patterns', 'Forecasting', 'Shapes', 'Annotate'].includes(name)
                  ? ' cq-line-menu' + (name === 'Annotate' ? ' cq-text-menu' : '')
                  : '')
              }
              role="menu"
              aria-label={name + ' tools'}
              onPointerEnter={cancelClose}
              onPointerLeave={scheduleClose}
            >
              {(name === 'Trend'
                ? lineSections
                : name === 'Fibonacci'
                  ? fibonacciSections
                  : name === 'Patterns'
                    ? patternSections
                    : name === 'Forecasting'
                      ? forecastingSections
                      : name === 'Shapes'
                        ? shapeSections
                        : textNoteSections
              ).map((section) => (
                <div
                  key={section.title}
                  className={
                    ['Trend', 'Fibonacci', 'Patterns', 'Forecasting', 'Shapes', 'Annotate'].includes(name)
                      ? 'cq-line-section'
                      : undefined
                  }
                >
                  {section.title && <div className="cq-line-heading">{section.title}</div>}
                  {section.ids.map((id) => (
                    <div
                      key={id}
                      className={'cq-tool-option' + (s.lastGroupTools[name] === id ? ' cq-selected-tool' : '')}
                    >
                      <button
                        role="menuitem"
                        aria-current={s.lastGroupTools[name] === id ? 'true' : undefined}
                        onClick={() => choose(id)}
                      >
                        <GroupToolIcon name={name} id={id} />
                        <span>{tools[id].label}</span>
                        {name !== 'Annotate' && <kbd>{id === 'HorizontalRay' ? 'Alt+J' : tools[id].shortcut}</kbd>}
                      </button>
                      <button
                        aria-label={'Favorite ' + tools[id].label}
                        aria-pressed={s.favorites.includes(id)}
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
      <div
        className="cq-tool-group"
        onPointerEnter={() => {
          if (open === 'magnet') cancelClose();
        }}
        onPointerLeave={scheduleClose}
      >
        <ToolButton
          label="Magnet"
          shortcut="M"
          aria-haspopup="menu"
          aria-expanded={open === 'magnet'}
          aria-pressed={s.chart.magnet}
          className={s.chart.magnet ? 'cq-active' : ''}
          onClick={() => {
            cancelClose();
            s.settings({ magnet: !s.chart.magnet });
          }}
        >
          <Magnet />
          <ChevronRight
            className="cq-caret"
            size={10}
            onPointerEnter={() => {
              cancelClose();
              setOpen('magnet');
            }}
          />
        </ToolButton>
        {open === 'magnet' && (
          <div
            className="cq-flyout cq-magnet-menu"
            role="menu"
            aria-label="Magnet modes"
            onPointerEnter={cancelClose}
            onPointerLeave={scheduleClose}
          >
            {(['weak', 'strong'] as const).map((strength) => (
              <button
                key={strength}
                role="menuitemradio"
                aria-checked={s.chart.magnet && s.chart.magnetStrength === strength}
                className="cq-magnet-option"
                onClick={() => {
                  cancelClose();
                  s.settings({ magnet: true, magnetStrength: strength });
                  setOpen(null);
                }}
              >
                <MagnetStrengthIcon strength={strength} />
                <span>{strength === 'weak' ? 'Weak magnet' : 'Strong magnet'}</span>
              </button>
            ))}
            <div className="cq-magnet-switch-row">
              <span id="cq-snap-indicators-label">Snap to indicators</span>
              <button
                type="button"
                role="switch"
                aria-labelledby="cq-snap-indicators-label"
                aria-checked={s.chart.snapToIndicators}
                disabled={!s.indicators.some(indicator => !indicators[indicator.kind].pane)}
                title={!s.indicators.some(indicator => !indicators[indicator.kind].pane)
                  ? 'Add a price-overlay indicator to enable snapping'
                  : 'Include price-overlay indicator points when magnet is enabled'}
                onClick={() => s.settings({ snapToIndicators: !s.chart.snapToIndicators })}
              >
                <span />
              </button>
            </div>
          </div>
        )}
      </div>
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
