import React, { useEffect } from 'react';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { WorkspaceGrid } from './components/layout/WorkspaceGrid';
import { OrderTicketModal } from './components/widgets/OrderTicketModal';
import { useTradingStore } from './store/useTradingStore';

export function App() {
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
      <OrderTicketModal />
    </div>
  );
}

export default App;
