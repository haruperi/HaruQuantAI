import { createStore } from 'zustand/vanilla';
import type {
  Alert,
  DocumentState,
  Drawing,
  Indicator,
  Persisted,
  Position,
  Settings,
  UIState,
} from '../types';
import { drawingGroups, keyFor } from '../types';
import { tools } from '../tools/catalog';
import { withChartHistory, type History } from './history';
export const defaults: Settings = {
  symbol: 'XAUUSD',
  interval: '3m',
  style: 'Candles',
  scale: 'linear',
  reverse: false,
  auto: true,
  theme: 'dark',
  timezone: 'UTC+3',
  precision: 2,
  countdown: true,
  magnet: false,
  magnetStrength: 'weak',
  snapToIndicators: false,
  volume: true,
  previousClose: false,
  tooltip: false,
  gaps: true,
  sessions: false,
  minimap: false,
  title: 'Gold workspace',
  range: '1D',
  paneHeight: 100,
};
export interface ChartState extends Persisted {
  ui: UIState;
  history: History;
  positions: Position[];
  edit: (change: Partial<DocumentState>) => void;
  settings: (change: Partial<Settings>) => void;
  setUI: (change: Partial<UIState>) => void;
  setDrawings: (drawings: Drawing[]) => void;
  setIndicators: (indicators: Indicator[]) => void;
  setAlerts: (alerts: Alert[]) => void;
  setPositions: (positions: Position[]) => void;
  undo: (redo?: boolean) => void;
  selectSymbol: (symbol: string) => void;
}
export function createChartStore() {
  return createStore<ChartState>(
    withChartHistory((set, get) => ({
      chart: { ...defaults },
      drawings: {},
      indicators: [],
      alerts: [],
      positions: [],
      favorites: ['TrendLine', 'HorizontalLine', 'FibRetracement'],
      recents: ['XAUUSD'],
      lastGroupTools: {},
      ui: {
        tool: 'cursor',
        cursor: 'crosshair',
        cursorFavorites: [],
        valuesOnLongPress: true,
        dialog: null,
        panel: null,
        selected: null,
        lock: false,
        hide: false,
        menu: null,
        side: 'buy',
        toast: '',
        saved: 'Saved locally',
        replay: false,
        replayPick: false,
        replayIndex: 0,
        playing: false,
        speed: 1,
      },
      settings: (change) => get().edit({ chart: { ...get().chart, ...change } }),
      setUI: (change) =>
        set((s) => {
          const next = change.tool;
          const group = next && next !== 'cursor' ? tools[next].group : null;
          return {
            ui: { ...s.ui, ...change },
            // Remember tool choices centrally: toolbar, favorites, and shortcuts all
            // use setUI, while the engine's switch back to cursor must not erase them.
            ...(group && drawingGroups.some((name) => name === group)
              ? { lastGroupTools: { ...s.lastGroupTools, [group]: next } }
              : {}),
          };
        }),
      setDrawings: (drawings) =>
        get().edit({ drawings: { ...get().drawings, [keyFor(get().chart)]: drawings } }),
      setIndicators: (indicators) => get().edit({ indicators }),
      setAlerts: (alerts) => set({ alerts }),
      setPositions: (positions) => set({ positions }),
      selectSymbol: (symbol) => {
        get().settings({ symbol });
        set((s) => ({
          recents: [symbol, ...s.recents.filter((x) => x !== symbol)].slice(0, 8),
          ui: { ...s.ui, dialog: null, selected: null, replay: false, playing: false },
        }));
      },
    })),
  );
}
export type ChartStore = ReturnType<typeof createChartStore>;
