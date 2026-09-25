import { useMemo, useState } from 'react';
import { Layers, Settings, ShieldCheck, Sliders } from 'lucide-react';
import { useAppStore } from '../../app/store';
import { Button, Checkbox, Field, Section, Select, TextInput } from '../../components/ui';
import { ResultsWorkspace } from '../Results/ResultsWorkspace';
import { BuildingBlocksModal } from './BuildingBlocksModal';
import { ATMConfigModal } from './ATMConfigModal';
import { RankingSettingsView } from './RankingSettingsView';
import { BUILDING_BLOCKS_CATALOG } from './BuildingBlocksCatalog';
import { ProgressDashboard } from './ProgressDashboard';
import type { EngineRunStatus } from './fixtures';

/**
 * Builder workspace shell in SQX Progress-tab parity (donor evidence
 * SQX144-EV-000033): the 51px dashboard header with the clickable project
 * name and the Progress / Full settings / Results large tabs. Progress is
 * the initial panel, matching the donor's switch-to-dashboard on load.
 */

export type BuilderPanel = 'progress' | 'settings' | 'results';

const PANEL_TABS: { id: BuilderPanel; label: string }[] = [
  { id: 'progress', label: 'Progress' },
  { id: 'settings', label: 'Full settings' },
  { id: 'results', label: 'Results' },
];

function NumberField({
  label,
  value,
  onChange,
  min = 0,
  max = 10000,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
}) {
  return (
    <Field label={label}>
      <TextInput
        type="number"
        value={value}
        min={min}
        max={max}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </Field>
  );
}

function BuilderSettingsView() {
  const s = useAppStore((x) => x.builder);
  const update = useAppStore((x) => x.updateBuilder);

  // Modal open states
  const [blocksModalOpen, setBlocksModalOpen] = useState(false);
  const [atmModalOpen, setAtmModalOpen] = useState(false);
  const [rankingModalOpen, setRankingModalOpen] = useState(false);

  // Computed enabled blocks count
  const activeBlocksCount = useMemo(() => {
    return BUILDING_BLOCKS_CATALOG.filter((b) =>
      s.customBlocks[b.id] !== undefined ? s.customBlocks[b.id] : b.enabled
    ).length;
  }, [s.customBlocks]);

  const activeCrossChecksCount = useMemo(() => {
    return s.crossChecks.filter((c) => c.enabled).length;
  }, [s.crossChecks]);

  return (
    <div className="settings-page">
      {/* 1. What to Build */}
      <Section title="What to build" description="Strategy architecture, trading direction, and rule generation constraints.">
        <div className="form-grid">
          <Field label="Build mode">
            <Select value={s.mode} onChange={(mode) => update({ mode: mode as typeof s.mode })}>
              <option>Genetic evolution</option>
              <option>Random generation</option>
              <option>Improve existing</option>
            </Select>
          </Field>
          <Field label="Strategy type">
            <Select value={s.strategyType} onChange={(strategyType) => update({ strategyType: strategyType as typeof s.strategyType })}>
              <option>Standard</option>
              <option>Multi-TF</option>
              <option>Stockpicker</option>
            </Select>
          </Field>
          <Field label="Trading direction">
            <Select value={s.direction} onChange={(direction) => update({ direction: direction as typeof s.direction })}>
              <option>Both</option>
              <option>Long</option>
              <option>Short</option>
            </Select>
          </Field>
          <NumberField label="Min conditions" value={s.minConditions} min={1} max={6} onChange={(minConditions) => update({ minConditions })} />
          <NumberField label="Max conditions" value={s.maxConditions} min={1} max={12} onChange={(maxConditions) => update({ maxConditions })} />
          <NumberField label="Max indicator period" value={s.maxPeriods} min={10} max={500} onChange={(maxPeriods) => update({ maxPeriods })} />
        </div>
        <div className="check-row" style={{ marginTop: 10 }}>
          <Checkbox
            label="Symmetrical Long / Short rules"
            checked={s.symmetricalRules}
            onChange={(symmetricalRules) => update({ symmetricalRules })}
          />
          <Checkbox
            label="Use fuzzy signals"
            checked={s.fuzzySignals}
            onChange={(fuzzySignals) => update({ fuzzySignals })}
          />
          <Checkbox
            label="Generate exit rules"
            checked={s.generateExitRules}
            onChange={(generateExitRules) => update({ generateExitRules })}
          />
        </div>
        <div style={{ marginTop: 12, padding: 10, background: 'rgba(234, 179, 8, 0.1)', border: '1px solid rgba(234, 179, 8, 0.3)', borderRadius: 6, fontSize: '0.82rem', color: 'var(--text)' }}>
          ⚠️ <strong>Deferred Capability:</strong> Genetic strategy generation requires generator plugin (deferred to S6). Current execution evaluates interactive strategy graphs via <code>/api/v1/executions/evaluate</code>.
        </div>
      </Section>

      {/* 2. Data and Trading Engine */}
      <Section title="Data and trading engine" description="Symbol, timeframe, backtest precision, and sample split configuration.">
        <div className="form-grid">
          <Field label="Market">
            <Select value={s.symbol} onChange={(symbol) => update({ symbol: symbol as typeof s.symbol })}>
              <option>EURUSD</option>
              <option>GBPJPY</option>
              <option>XAUUSD</option>
              <option>NQ</option>
              <option>BTCUSD</option>
            </Select>
          </Field>
          <Field label="Timeframe">
            <Select value={s.timeframe} onChange={(timeframe) => update({ timeframe: timeframe as typeof s.timeframe })}>
              <option>M15</option>
              <option>M30</option>
              <option>H1</option>
              <option>H4</option>
              <option>D1</option>
            </Select>
          </Field>
          <Field label="Testing precision">
            <Select value={s.precision} onChange={(precision) => update({ precision: precision as typeof s.precision })}>
              <option>Selected timeframe only</option>
              <option>1 minute data</option>
              <option>Real tick</option>
            </Select>
          </Field>
          <Field label="From">
            <TextInput type="date" value={s.from} onChange={(e) => update({ from: e.target.value })} />
          </Field>
          <Field label="To">
            <TextInput type="date" value={s.to} onChange={(e) => update({ to: e.target.value })} />
          </Field>
          <NumberField label="Out of sample (%)" value={s.oos} min={0} max={80} onChange={(oos) => update({ oos })} />
        </div>
        <div className="sample-bar" style={{ marginTop: 12 }}>
          <span style={{ width: `${100 - s.oos}%` }}>In sample {100 - s.oos}%</span>
          <span style={{ width: `${s.oos}%` }}>OOS {s.oos}%</span>
        </div>
      </Section>

      {/* 3. Genetic Options */}
      <Section title="Genetic options" description="Island model population, mutation, crossover, and migration controls.">
        <div className="form-grid">
          <NumberField label="Max generations" value={s.maxGenerations} min={10} max={10000} onChange={(maxGenerations) => update({ maxGenerations })} />
          <NumberField label="Population per island" value={s.population} min={10} max={1000} onChange={(population) => update({ population })} />
          <NumberField label="Islands (1-32)" value={s.islands} min={1} max={32} onChange={(islands) => update({ islands })} />
          <NumberField label="Mutation probability (%)" value={s.mutation} min={0} max={100} onChange={(mutation) => update({ mutation })} />
          <NumberField label="Crossover probability (%)" value={s.crossover} min={0} max={100} onChange={(crossover) => update({ crossover })} />
          <NumberField label="Migration interval (gens)" value={s.migrationInterval} min={1} max={50} onChange={(migrationInterval) => update({ migrationInterval })} />
        </div>
        <div className="check-row" style={{ marginTop: 10 }}>
          <Checkbox
            label="Migrate candidates between islands"
            checked={s.migrateCandidates}
            onChange={(migrateCandidates) => update({ migrateCandidates })}
          />
          <Checkbox
            label="Restart stagnant islands"
            checked={s.restartStagnantIslands}
            onChange={(restartStagnantIslands) => update({ restartStagnantIslands })}
          />
          <Checkbox
            label="Seed from input databank"
            checked={s.mode === 'Improve existing' || s.seedFromDatabank}
            onChange={(seedFromDatabank) => update({ seedFromDatabank })}
          />
        </div>
      </Section>

      {/* 4. Building Blocks Summary Strip */}
      <Section title="Building blocks" description="Select indicators, entry signals, candle patterns, and exit rules.">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 14, background: 'var(--bg-card)', borderRadius: 6, border: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ width: 40, height: 40, borderRadius: 8, background: 'rgba(48, 183, 232, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#30b7e8' }}>
              <Layers size={20} />
            </div>
            <div>
              <strong>{activeBlocksCount} of {BUILDING_BLOCKS_CATALOG.length} Building Blocks Active</strong>
              <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--muted)' }}>
                Signals, Moving Averages, Oscillators, Candlestick Formations, Time Filters, and Order Exits.
              </p>
            </div>
          </div>
          <Button className="primary" onClick={() => setBlocksModalOpen(true)}>
            <Settings size={14} /> Manage Building Blocks
          </Button>
        </div>
      </Section>

      {/* 5. ATM & Money Management Summary Strip */}
      <Section title="Money Management & Advanced Trade Management" description="Position sizing, stop loss, profit target, trailing stop, and break-even rules.">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 14, background: 'var(--bg-card)', borderRadius: 6, border: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ width: 40, height: 40, borderRadius: 8, background: 'rgba(230, 162, 60, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#e6a23c' }}>
              <Sliders size={20} />
            </div>
            <div>
              <strong>Model: {s.mmModel} · SL: {s.slMin}-{s.slMax} {s.slType} · PT: {s.ptMin}-{s.ptMax} {s.ptType}</strong>
              <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--muted)' }}>
                Trailing Stop: {s.useTrailingStop ? 'Active' : 'Disabled'} · Break-Even: {s.useMoveToBE ? 'Active' : 'Disabled'} · Capital: ${s.initialCapital.toLocaleString()}
              </p>
            </div>
          </div>
          <Button onClick={() => setAtmModalOpen(true)}>
            <Settings size={14} /> Configure ATM
          </Button>
        </div>
      </Section>

      {/* 6. Cross Checks and Rankings Summary Strip */}
      <Section title="Rankings and cross-checks" description="Candidate ranking objective, automated qualification criteria, and multi-stage verification tests.">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 14, background: 'var(--bg-card)', borderRadius: 6, border: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ width: 40, height: 40, borderRadius: 8, background: 'rgba(74, 222, 128, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#4ade80' }}>
              <ShieldCheck size={20} />
            </div>
            <div>
              <strong>Objective: {s.rankingMetric} · {activeCrossChecksCount} Cross-Checks Active</strong>
              <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--muted)' }}>
                Min Ret/DD: {s.minReturnDD} · Min Trades: {s.minTrades} · Max DD: {s.maxDrawdownPct}% · Min Sharpe: {s.minSharpe}
              </p>
            </div>
          </div>
          <Button onClick={() => setRankingModalOpen(true)}>
            <Settings size={14} /> Configure Ranking & Filters
          </Button>
        </div>
      </Section>

      {/* Modals */}
      <BuildingBlocksModal
        isOpen={blocksModalOpen}
        onClose={() => setBlocksModalOpen(false)}
        customBlocks={s.customBlocks}
        onChange={(patch) => update({ customBlocks: patch })}
      />

      <ATMConfigModal
        isOpen={atmModalOpen}
        onClose={() => setAtmModalOpen(false)}
        settings={s}
        updateSettings={update}
      />

      <RankingSettingsView
        isOpen={rankingModalOpen}
        onClose={() => setRankingModalOpen(false)}
        settings={s}
        updateSettings={update}
      />
    </div>
  );
}

export function BuilderWorkspace() {
  const [panel, setPanel] = useState<BuilderPanel>('progress');
  const [runStatus, setRunStatus] = useState<EngineRunStatus>('idle');

  const projectNameRunning = runStatus !== 'idle' && panel !== 'progress';

  return (
    <div className="builder-workspace">
      <header className="sqd-dashboard-header">
        <div
          className={`sqd-project-name${projectNameRunning ? ' sqd-project-name-running' : ''}`}
          title={projectNameRunning ? 'Project in progress — click to return to Progress' : undefined}
          onClick={() => setPanel('progress')}
        >
          Build
        </div>
        <nav className="sqd-tabs-large" aria-label="Builder panels">
          {PANEL_TABS.map(tab => (
            <div
              key={tab.id}
              role="tab"
              aria-selected={panel === tab.id}
              className={panel === tab.id ? 'active' : ''}
              onClick={() => setPanel(tab.id)}
            >
              {tab.label}
            </div>
          ))}
        </nav>
      </header>
      <div className="sqd-panel-host">
        {panel === 'progress' ? (
          <ProgressDashboard
            runStatus={runStatus}
            onRunStatusChange={setRunStatus}
            onOpenFullSettings={() => setPanel('settings')}
            onOpenResults={() => setPanel('results')}
          />
        ) : panel === 'settings' ? (
          <BuilderSettingsView />
        ) : (
          <ResultsWorkspace />
        )}
      </div>
    </div>
  );
}
