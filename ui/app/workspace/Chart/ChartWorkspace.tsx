import { useEffect, useMemo, useRef } from 'react';
import { useStore } from 'zustand';
import { createChartStore } from './src/store/chartStore';
import { connectPersistence } from './src/store/persistence';
import { ChartContext } from './src/hooks/useChartEngine';
import { useShortcuts } from './src/hooks/useShortcuts';
import type { ChartEngine } from './src/engine/ChartEngine';
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
export function ChartWorkspace() {
  const store = useMemo(createChartStore, []),
    engine = useRef<ChartEngine | null>(null),
    root = useRef<HTMLDivElement>(null),
    s = useStore(store),
    services = useMemo(() => ({ store, engine, root }), [store]);
  useEffect(() => {
    try {
      return connectPersistence(store, localStorage);
    } catch {
      store.getState().setUI({ saved: 'Browser storage unavailable' });
    }
  }, [store]);
  return (
    <ChartContext.Provider value={services}>
      <div
        ref={root}
        className={styles.root}
        data-chart-theme={s.chart.theme}
        tabIndex={0}
        aria-label="Chart workspace"
        onPointerDown={(e) => {
          if (e.target instanceof HTMLCanvasElement) root.current?.focus({ preventScroll: true });
        }}
      >
        <Shortcuts />
        <TopBar />
        <LeftToolbar />
        <ChartArea />
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
