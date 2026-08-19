'use client';

import React, { useEffect } from 'react';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { WorkspaceGrid } from './components/layout/WorkspaceGrid';
import { SystemSettingsModal } from './widgets/system-settings';
import { TradingWidget } from './widgets/trading';
import { useTradingStore } from './store/useTradingStore';

export function App(): React.JSX.Element {
  const { updateQuotes, theme } = useTradingStore();

  // Run real-time price quote tick updates every 1.2 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      updateQuotes();
    }, 1200);
    return () => clearInterval(interval);
  }, [updateQuotes]);

  return (
    <div className="app-container" data-theme={theme}>
      <Header />
      <div className="main-body">
        <Sidebar />
        <WorkspaceGrid />
      </div>
      <TradingWidget ticketHostOnly />
      <SystemSettingsModal />
    </div>
  );
}

export default App;
