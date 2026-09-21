import { useEffect, useState } from 'react';
import { Activity, Bell, BrainCircuit, BriefcaseBusiness, ChartNoAxesCombined, Code2, Database, FolderKanban, Gauge, GitCompareArrows, Layers3, LineChart, WandSparkles, Workflow, X } from 'lucide-react';
import type { ModuleId } from './types';
import { useAppStore } from './store';
import { DatabankPanel } from '../plugins/databank/ProjectDatabanks/DatabankPanel';
import { HomeScreen } from '../workspace/Home/HomeScreen';
import { DataManager } from '../workspace/DataManager/DataManager';
import { BuilderWorkspace } from '../workspace/Builder/BuilderWorkspace';
import { RetesterWorkspace } from '../workspace/Retester/RetesterWorkspace';
import { OptimizerWorkspace } from '../workspace/Optimizer/OptimizerWorkspace';
import { AlgoWizardWorkspace } from '../workspace/AlgoWizard/AlgoWizardWorkspace';
import { CustomProjectsWorkspace } from '../workspace/CustomProjects/CustomProjectsWorkspace';
import { PortfolioComposerWorkspace } from '../workspace/PortfolioComposer/PortfolioComposerWorkspace';
import { PortfolioMasterWorkspace } from '../workspace/PortfolioMaster/PortfolioMasterWorkspace';
import { CodeEditorWorkspace } from '../workspace/CodeEditor/CodeEditorWorkspace';
import { BusinessWorkspace } from '../workspace/Business/BusinessWorkspace';
import { TradingDashboard } from '../workspace/Trading/TradingDashboard';
import { NeuralNetworkTrainer } from '../workspace/NeuralNetwork/NeuralNetworkTrainer';
import { MTAnalyzerWorkspace } from '../workspace/MTAnalyzer/MTAnalyzerWorkspace';
import { GlobalSettingsMenu } from './GlobalSettingsMenu';
import { DebugConsole, GridControl, HeaderApplicationActions } from './HeaderApplications';

const nav: { id: ModuleId; label: string; icon: typeof ChartNoAxesCombined; group?: string }[] = [
  { id: 'home', label: 'HaruQuantAI', icon: ChartNoAxesCombined },
  { id: 'datamanager', label: 'Data Manager', icon: Database, group: 'Fundamentals' },
  { id: 'business', label: 'Business', icon: BriefcaseBusiness },
  { id: 'builder', label: 'Builder', icon: WandSparkles, group: 'Development' },
  { id: 'algowizard', label: 'AlgoWizard', icon: Workflow },
  { id: 'codeeditor', label: 'Code Editor', icon: Code2 },
  { id: 'neuralnet', label: 'Neural Network', icon: BrainCircuit },
  { id: 'retester', label: 'Retester', icon: GitCompareArrows, group: 'Robustness' },
  { id: 'optimizer', label: 'Optimizer', icon: Gauge },
  { id: 'mtanalyzer', label: 'MT Analyzer', icon: LineChart },
  { id: 'projects', label: 'Custom Projects', icon: FolderKanban, group: 'Automation' },
  { id: 'portfolio', label: 'Portfolio Master', icon: Layers3, group: 'Trading' },
  { id: 'composer', label: 'Portfolio Composer', icon: ChartNoAxesCombined },
  { id: 'trading', label: 'Live Trading', icon: Activity },
];

export function App() {
  const store = useAppStore();
  const [notifications, setNotifications] = useState(false);
  const [navOpen, setNavOpen] = useState(false);
  const showBank = ['builder', 'retester', 'optimizer', 'portfolio', 'projects'].includes(store.module);

  useEffect(() => {
    document.documentElement.dataset.theme = store.settings.theme;
    document.documentElement.dataset.profile = store.settings.profile;
    document.documentElement.style.setProperty('--app-zoom', String(store.settings.zoom));
  }, [store.settings.profile, store.settings.theme, store.settings.zoom]);

  let content = <HomeScreen />;
  if (store.module === 'builder') content = <BuilderWorkspace />;
  else if (store.module === 'retester') content = <RetesterWorkspace />;
  else if (store.module === 'optimizer') content = <OptimizerWorkspace />;
  else if (store.module === 'portfolio') content = <PortfolioMasterWorkspace />;
  else if (store.module === 'composer') content = <PortfolioComposerWorkspace />;
  else if (store.module === 'datamanager') content = <DataManager />;
  else if (store.module === 'algowizard') content = <AlgoWizardWorkspace />;
  else if (store.module === 'projects') content = <CustomProjectsWorkspace />;
  else if (store.module === 'codeeditor') content = <CodeEditorWorkspace />;
  else if (store.module === 'business') content = <BusinessWorkspace />;
  else if (store.module === 'trading') content = <TradingDashboard />;
  else if (store.module === 'neuralnet') content = <NeuralNetworkTrainer />;
  else if (store.module === 'mtanalyzer') content = <MTAnalyzerWorkspace />;
  else if (store.module === 'debugconsole') content = <DebugConsole />;
  else if (store.module === 'gridcontrol') content = <GridControl />;


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
                  store.setModule(item.id);
                  setNavOpen(false);
                }}
              >
                {item.id === 'home' ? (
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
        <div className="module-area">{content}</div>
        {showBank && (
          <div className="databank-resize">
            <DatabankPanel />
          </div>
        )}
      </main>

      <footer className="statusbar">
        <div className="status-metrics">
          <span>Workers {store.settings.workers}</span>
          <span>Memory 4.2/{store.settings.memoryGb} GB</span>
          <span>CPU 34%</span>
          <span><i className="online" />Backend</span>
          <span>Latency 12 ms</span>
          <span><i className="online" />Database</span>
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
