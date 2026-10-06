import { Activity, BrainCircuit, ChartCandlestick, ChartNoAxesCombined, FlaskConical, BriefcaseBusiness, WandSparkles, Workflow, Code2, GitCompareArrows, Gauge, Database, LineChart } from 'lucide-react';
import type { ModuleId } from '../../app/types';
import { useAppStore } from '../../app/store';

const quickNav: { id: ModuleId; label: string; icon: typeof ChartNoAxesCombined }[] = [
  { id: 'datamanager', label: 'Data Manager', icon: Database },
  { id: 'business', label: 'Business', icon: BriefcaseBusiness },
  { id: 'builder', label: 'Builder', icon: WandSparkles },
  { id: 'algowizard', label: 'AlgoWizard', icon: Workflow },
  { id: 'codeeditor', label: 'Code Editor', icon: Code2 },
  { id: 'neuralnet', label: 'Neural Network', icon: BrainCircuit },
  { id: 'retester', label: 'Retester', icon: GitCompareArrows },
  { id: 'optimizer', label: 'Optimizer', icon: Gauge },
  { id: 'mtanalyzer', label: 'MT Analyzer', icon: LineChart },
  { id: 'trading', label: 'Live Trading', icon: Activity },
];


export function HomeScreen() {
  const store = useAppStore();
  return (
    <div className="home-screen">
      <div className="hero">
        <div>
          <span>HaruQuantAI</span>
          <h1>Research workspace</h1>
          <p>Continue a research project, manage market data, or author a trading strategy.</p>
        </div>
        <div className="version">
          Build 144 · recreation<br/>
          <small>Frontend mock profile</small>
        </div>
      </div>
      <div className="home-grid">
        <section>
          <h2>Recent projects</h2>
          {['EURUSD H1 — Genetic research', 'NQ Breakout — Retest pipeline', 'Diversified FX Portfolio'].map((x, i) => (
            <button key={x} onClick={() => store.setModule(i === 2 ? 'composer' : 'builder')}>
              <span className="project-thumb"><ChartCandlestick/></span>
              <span><strong>{x}</strong><small>{i ? 'Last opened yesterday' : 'Last opened 12 minutes ago'}</small></span>
              <em>{i === 2 ? 'Portfolio Composer' : 'Builder'}</em>
            </button>
          ))}
        </section>
        <section>
          <h2>Start</h2>
          <div className="start-grid">
            {quickNav.map(x => (
              <button key={x.id} onClick={() => store.setModule(x.id)}>
                <x.icon/>
                <span>{x.label}</span>
              </button>
            ))}
          </div>
        </section>
        <section>
          <h2>Environment</h2>
          <dl className="details">
            <dt>License profile</dt><dd>Full feature fixture</dd>
            <dt>Engine</dt><dd>Deterministic mock</dd>
            <dt>Persistence</dt><dd>Browser local storage</dd>
            <dt>Market data</dt><dd>4 seeded datasets</dd>
            <dt>Strategies</dt><dd>{store.strategies.length}</dd>
          </dl>
        </section>
      </div>
      <div className="home-note">
        <FlaskConical size={20}/>
        <div>
          <strong>This is a frontend research simulation.</strong>
          <span>No backtests, broker connections, downloads, native compilation, external scripts, or trades are executed.</span>
        </div>
      </div>
    </div>
  );
}
