import { useEffect, useMemo, useRef, useState } from 'react';
import { useStore } from 'zustand';
import { createChartStore } from './src/store/chartStore';
import { connectPersistence, persisted, storageKey } from './src/store/persistence';
import { ChartContext, type ChartServices } from './src/hooks/useChartEngine';
import { useShortcuts } from './src/hooks/useShortcuts';
import type { ChartEngine } from './src/engine/ChartEngine';
import { getLayout, layoutStorageKey, readLayout, type LayoutState, type SyncSetting } from './src/layout/layouts';
import { TopBar } from './src/components/topbar/TopBar';
import { LeftToolbar } from './src/components/toolbar/LeftToolbar';
import { BottomBar } from './src/components/bottombar/BottomBar';
import { ChartArea } from './src/components/ChartArea';
import { SymbolSearch } from './src/components/dialogs/SymbolSearch';
import { IndicatorsDialog } from './src/components/dialogs/IndicatorsDialog';
import { SettingsDialog } from './src/components/dialogs/SettingsDialog';
import { DrawingSettings } from './src/components/dialogs/DrawingSettings';
import { AlertDialog } from './src/components/dialogs/AlertDialog';
import { OrderTicket } from './src/components/dialogs/OrderTicket';
import { ConfirmDialog } from './src/components/dialogs/ConfirmDialog';
import { HelpDialog } from './src/components/dialogs/HelpDialog';
import { AlertsPanel } from './src/components/panels/AlertsPanel';
import { PositionsPanel } from './src/components/panels/PositionsPanel';
import { FavoritesPanel } from './src/components/panels/FavoritesPanel';
import { ReplayControls } from './src/components/panels/ReplayControls';
import { Minimap } from './src/components/panels/Minimap';
import { Toasts } from './src/components/panels/Toasts';
import { ContextMenu } from './src/components/ContextMenu';
import styles from './ChartWorkspace.module.css';

function Shortcuts() {
  useShortcuts();
  return null;
}
const paneStorageKey = (index: number) => index === 0 ? storageKey : storageKey + '.pane.' + index;

/** Keeps all eight chart instances alive in memory while unused panes are hidden.
 * Each store owns independent indicators, drawings, settings and undo history.
 * Only enabled synchronization dimensions are copied between stores.
 */
export function ChartWorkspace() {
  const stores = useMemo(() => Array.from({ length: 8 }, () => createChartStore()), []);
  const engines = useMemo(() =>
    Array.from({ length: 8 }, () => ({ current: null as ChartEngine | null })), []);
  const root = useRef<HTMLDivElement>(null);
  const viewRanges = useRef<(readonly [number, number] | null)[]>(Array(8).fill(null));
  const [layout, setLayout] = useState<LayoutState>(() =>
    typeof window === 'undefined' ? { id: 's', active: 0,
      sync: { symbol: false, interval: false, crosshair: true, time: false, dateRange: false } }
      : readLayout(window.localStorage));
  const currentLayout = useRef(layout);
  currentLayout.current = layout;
  const active = Math.min(layout.active, getLayout(layout.id).count - 1);
  const selectedStore = stores[active];
  const s = useStore(selectedStore);

  const paneServices = useMemo<ChartServices[]>(() => stores.map((store, index) => ({
    store,
    engine: engines[index],
    root,
    onCrosshairTime: (time: number | null) => {
      const config = currentLayout.current;
      if (!config.sync.crosshair || config.active !== index) return;
      engines.forEach((target, i) => {
        if (i !== index) target.current?.setLinkedCrosshairTime(time);
      });
    },
    onViewport: (range: readonly [number, number]) => {
      viewRanges.current[index] = range;
      const config = currentLayout.current;
      if (!config.sync.time || config.active !== index) return;
      engines.forEach((target, i) => {
        if (i !== index) {
          target.current?.setVisibleTimeRange(range);
          viewRanges.current[i] = range;
        }
      });
    },
    onReady: (chartEngine: ChartEngine) => {
      const config = currentLayout.current;
      const synchronizedRange = config.sync.time && config.active !== index
        ? engines[config.active].current?.getVisibleTimeRange() : null;
      const range = synchronizedRange ?? viewRanges.current[index];
      if (range) chartEngine.setVisibleTimeRange(range);
      viewRanges.current[index] = chartEngine.getVisibleTimeRange();
    },
    onDispose: (range: readonly [number, number] | null) => {
      if (range) viewRanges.current[index] = range;
    },
  })), [stores, engines]);
  const services = paneServices[active];

  // Hydrate first, then subscribe. The original single-chart storage key is untouched.
  useEffect(() => {
    let stops: (() => void)[] = [];
    try {
      const storage = localStorage;
      stops.push(connectPersistence(stores[0], storage, paneStorageKey(0)));
      for (let i = 1; i < stores.length; i++) {
        const key = paneStorageKey(i);
        if (!storage.getItem(key)) {
          const base = structuredClone(persisted(stores[0]));
          stores[i].setState({ ...base, chart: { ...base.chart, title: 'Chart ' + (i + 1) } });
        }
        stops.push(connectPersistence(stores[i], storage, key));
      }
    } catch {
      stores[0].getState().setUI({ saved: 'Browser storage unavailable' });
    }
    let propagating = false;
    const unsubscribes = stores.map((source, sourceIndex) => source.subscribe((state, previous) => {
      if (propagating) return;
      const sync = currentLayout.current.sync;
      const changes: Partial<typeof state.chart> = {};
      if (sync.symbol && state.chart.symbol !== previous.chart.symbol)
        changes.symbol = state.chart.symbol;
      if (sync.interval && state.chart.interval !== previous.chart.interval)
        changes.interval = state.chart.interval;
      if (sync.dateRange && state.chart.range !== previous.chart.range)
        changes.range = state.chart.range;
      if (!Object.keys(changes).length) return;
      propagating = true;
      try {
        stores.forEach((target, index) => {
          if (index === sourceIndex) return;
          const other = target.getState();
          if (Object.entries(changes).some(([key, value]) =>
            other.chart[key as keyof typeof other.chart] !== value))
            target.setState({ chart: { ...other.chart, ...changes } });
        });
      } finally {
        propagating = false;
      }
    }));
    return () => {
      unsubscribes.forEach(unsubscribe => unsubscribe());
      stops.forEach(stop => stop());
    };
  }, [stores]);

  // Chart engines are resized by ResizeObserver; restore the visible time window
  // after CSS grid cells acquire their new dimensions.
  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      engines.forEach((engine, index) => {
        const range = viewRanges.current[index];
        if (range) engine.current?.setVisibleTimeRange(range);
      });
    });
    return () => cancelAnimationFrame(frame);
  }, [layout.id, engines]);

  useEffect(() => {
    try {
      localStorage.setItem(layoutStorageKey, JSON.stringify(layout));
    } catch {
      // The workspace remains usable without browser storage.
    }
  }, [layout]);

  const updateLayout = (id: string) => {
    const count = getLayout(id).count;
    setLayout(previous => ({
      ...previous, id,
      active: Math.min(previous.active, count - 1),
    }));
  };
  const selectPane = (index: number) => {
    if (index === currentLayout.current.active) return;
    engines.forEach(engine => engine.current?.setLinkedCrosshairTime(null));
    setLayout(previous => ({ ...previous, active: index }));
  };
  const updateSync = (setting: SyncSetting, enabled: boolean) => {
    const chosen = selectedStore.getState().chart;
    if (enabled && (setting === 'symbol' || setting === 'interval' || setting === 'dateRange')) {
      const key = setting === 'dateRange' ? 'range' : setting;
      stores.forEach((store, index) => {
        if (index === active) return;
        const chart = store.getState().chart;
        if (chart[key] !== chosen[key])
          store.setState({ chart: { ...chart, [key]: chosen[key] } });
      });
    }
    if (enabled && setting === 'time') {
      const range = engines[active].current?.getVisibleTimeRange();
      if (range) engines.forEach((target, i) => {
        if (i !== active) target.current?.setVisibleTimeRange(range);
      });
    }
    if (!enabled && setting === 'crosshair')
      engines.forEach(engine => engine.current?.setLinkedCrosshairTime(null));
    setLayout(previous => ({
      ...previous, sync: { ...previous.sync, [setting]: enabled },
    }));
  };

  const definition = getLayout(layout.id);
  const cells = definition.cells;
  const boardStyle = {
    gridTemplateColumns: 'repeat(' + cells[0].length + ', minmax(0, 1fr))',
    gridTemplateRows: 'repeat(' + cells.length + ', minmax(0, 1fr))',
    gridTemplateAreas: cells.map(row => '"' + row.map(i => 'c' + i).join(' ') + '"').join(' '),
  };
  return (
    <ChartContext.Provider value={services}>
      <div ref={root} className={styles.root} data-chart-theme={s.chart.theme}
        tabIndex={0} aria-label="Chart workspace"
        onPointerDown={event => {
          if (event.target instanceof HTMLCanvasElement)
            root.current?.focus({ preventScroll: true });
        }}>
        <Shortcuts />
        <TopBar layout={layout} onLayoutChange={updateLayout} onSyncChange={updateSync} />
        <LeftToolbar />
        <div className="cq-chart-board" style={boardStyle} data-layout={layout.id}>
          {Array.from({ length: definition.count }, (_, index) => (
            <div key={index} role="group" aria-label={'Chart ' + (index + 1)}
              className={'cq-chart-cell' + (active === index ? ' cq-chart-cell-active' : '')}
              data-testid="chart-pane" data-pane-index={index}
              style={{ gridArea: 'c' + index }}
              onPointerDown={() => selectPane(index)}
              onFocusCapture={() => selectPane(index)}>
              <ChartContext.Provider value={paneServices[index]}>
                <ChartArea />
              </ChartContext.Provider>
            </div>
          ))}
        </div>
        <BottomBar />
        {s.ui.panel === 'alerts' && <AlertsPanel />}
        {s.ui.panel === 'positions' && <PositionsPanel />}
        {s.ui.panel === 'favorites' && <FavoritesPanel />}
        {s.ui.dialog === 'symbol' && <SymbolSearch />}
        {s.ui.dialog === 'indicators' && <IndicatorsDialog />}
        {s.ui.dialog === 'settings' && <SettingsDialog />}
        {s.ui.dialog === 'drawing' && <DrawingSettings />}
        {s.ui.dialog === 'alert' && <AlertDialog />}
        {s.ui.dialog === 'order' && <OrderTicket />}
        {s.ui.dialog === 'delete' && <ConfirmDialog />}
        {s.ui.dialog === 'help' && <HelpDialog />}
        {s.chart.minimap && <Minimap />}
        <ReplayControls />
        <ContextMenu />
        <Toasts />
      </div>
    </ChartContext.Provider>
  );
}
