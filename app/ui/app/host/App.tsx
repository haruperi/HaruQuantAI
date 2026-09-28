import { navigation, workspaceContributions } from './contributions';
import { WorkspaceView, EmptyWorkspace } from './composition';
import { useEffect, useState } from 'react';
import { Navigate, Route, Routes, useNavigate } from 'react-router-dom';
import { Activity, Bell, BrainCircuit, BriefcaseBusiness, ChartNoAxesCombined, Code2, Database, FolderKanban, Gauge, GitCompareArrows, Layers3, LineChart, WandSparkles, Workflow, X } from 'lucide-react';
import type { ModuleId } from './types';
import { useAppStore } from './store';
import { getPathForModule, useRouteSync } from './router';
import { GlobalSettingsMenu } from './GlobalSettingsMenu';
import { HeaderApplicationActions } from './HeaderApplications';
import { HostConnectionProvider, useHostConnection } from './HostConnection';

const nav = navigation.filter(item => !item.hidden);

function AppShell() {
  const store = useAppStore();
  const { status: hostStatus } = useHostConnection();
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState(false);
  const [navOpen, setNavOpen] = useState(false);

  // Hook up bidirectional route and query parameter synchronization
  useRouteSync();



  useEffect(() => {
    document.documentElement.dataset.theme = store.settings.theme;
    document.documentElement.dataset.profile = store.settings.profile;
    document.documentElement.style.setProperty('--app-zoom', String(store.settings.zoom));
  }, [store.settings.profile, store.settings.theme, store.settings.zoom]);

  return (
    <div className="app-shell">
      <aside
        className={`main-nav ${navOpen ? 'nav-open' : ''}`}
        aria-label="Applications"
        onMouseEnter={() => setNavOpen(true)}
        onMouseLeave={() => setNavOpen(false)}
      >
        <div className="nav-flyout">
          {nav.map((item) => (
            <div key={item.id}>
              {item.group && <small className="nav-group">{item.group}</small>}
              <button
                type="button"
                title={item.label}
                aria-label={item.label}
                className={store.module === item.id ? 'active' : ''}
                onClick={() => {
                  navigate(getPathForModule(item.id));
                  setNavOpen(false);
                }}
              >
                {item.home ? (
                  <span className="brand-mark">
                    <item.icon aria-hidden="true" />
                  </span>
                ) : (
                  <item.icon aria-hidden="true" />
                )}
                <span>{item.label}</span>
              </button>
            </div>
          ))}
        </div>
      </aside>

      <main className="app-main">
        <Routes>
          {workspaceContributions.flatMap(item => item.navigation ? [item.navigation.path, ...(item.navigation.aliases ?? [])].map(route => <Route key={route} path={route} element={<WorkspaceView contribution={item}/>}/>) : [])}
          {!navigation.some(item => item.path === '/') && <Route path="/" element={<EmptyWorkspace/>}/>}
          <Route path="*" element={<p role="status">This workspace is unavailable.</p>}/>
        </Routes>
      </main>

      <footer className="statusbar">
        <div className="status-metrics">
          <span>Configured workers {store.settings.workers}</span>
          <span>Configured memory {store.settings.memoryGb} GB</span>
          <span>Host {hostStatus}</span>
        </div>
        <div className="status-actions">
          <div className="status-bell">
            <button
              className="status-action"
              title="Notifications"
              aria-label="Notifications"
              onClick={() => setNotifications(!notifications)}
            >
              <Bell />
              {store.notifications.length > 0 && <i>{store.notifications.length}</i>}
            </button>
            {notifications && (
              <div className="notifications">
                <header>
                  <strong>Notifications</strong>
                  <button onClick={() => setNotifications(false)}>
                    <X size={14} />
                  </button>
                </header>
                {store.notifications.length ? (
                  store.notifications.map((x, i) => (
                    <p key={`${x}${i}`}>
                      {x}
                      <small>Just now</small>
                    </p>
                  ))
                ) : (
                  <div className="empty-mini">No notifications</div>
                )}
              </div>
            )}
          </div>
          <HeaderApplicationActions />
          <GlobalSettingsMenu />
        </div>
      </footer>
    </div>
  );
}

export function App() {
  return <HostConnectionProvider><AppShell /></HostConnectionProvider>;
}
