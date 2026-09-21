import { useMemo, useState } from 'react';
import {
  ArrowDown,
  ArrowUp,
  Award,
  Calculator,
  Calendar,
  DollarSign,
  Layers,
  Percent,
  Play,
  Plus,
  RefreshCw,
  Save,
  Trash2,
  TrendingDown,
  TrendingUp,
  X,
} from 'lucide-react';
import { useAppStore } from '../../app/store';
import type { PortfolioMember, Strategy } from '../../app/types';
import { Button, Checkbox, Field, Section, Stat, TextInput } from '../../components/ui';
import { PortfolioCandidatesModal } from './PortfolioCandidatesModal';
import {
  computeCorrelationMatrix,
  computeEqualWeights,
  computeMarkowitzWeights,
  computeMinVarianceWeights,
  computeRiskParityWeights,
  computeStrategyReturn,
  computeStrategyVolatility,
  normalizeWeights,
  simulatePortfolio,
} from './portfolioOptimization';

const STRATEGY_COLORS = [
  '#38bdf8', // Sky Blue
  '#f59e0b', // Amber
  '#10b981', // Emerald
  '#ec4899', // Pink
  '#8b5cf6', // Violet
  '#14b8a6', // Teal
  '#f97316', // Orange
  '#06b6d4', // Cyan
];

export function PortfolioComposerWorkspace() {
  const store = useAppStore();
  const [tab, setTab] = useState<'setup' | 'results'>('setup');
  const [candidatesModal, setCandidatesModal] = useState(false);
  const [selectedMemberId, setSelectedMemberId] = useState<string | null>(null);
  const [hiddenCurves, setHiddenCurves] = useState<Record<string, boolean>>({});

  const settings = store.portfolioSettings;
  const setSettings = store.updatePortfolioSettings;

  // Resolve members with linked strategy models
  const members = useMemo(() => {
    return store.portfolio
      .map((m, idx) => {
        const strat = store.strategies.find(s => s.id === m.strategyId);
        if (!strat) return null;
        return {
          ...m,
          color: STRATEGY_COLORS[idx % STRATEGY_COLORS.length],
          multiplier: m.multiplier ?? 1.0,
          strategy: strat,
        };
      })
      .filter((x): x is NonNullable<typeof x> => x !== null);
  }, [store.portfolio, store.strategies]);

  const activeMembers = members.filter(m => m.enabled);
  const totalWeight = activeMembers.reduce((sum, m) => sum + m.weight, 0);

  // Compute correlation matrix between active strategies
  const corrMatrix = useMemo(() => {
    const curves = activeMembers.map(m => m.strategy.equity.map(p => p.value));
    return computeCorrelationMatrix(curves);
  }, [activeMembers]);

  // Compute simulation result
  const simResult = useMemo(() => {
    const simMembers = members.map(m => ({
      id: m.strategy.id,
      name: m.strategy.name,
      symbol: m.strategy.symbol,
      sector: m.sector,
      weight: m.weight,
      multiplier: m.multiplier ?? 1.0,
      enabled: m.enabled,
      equity: m.strategy.equity,
    }));
    return simulatePortfolio(simMembers, settings.initialCapital, settings.leverage, settings.sharedCapital);
  }, [members, settings.initialCapital, settings.leverage, settings.sharedCapital]);

  // Handler: Apply Auto-Computation Weighting Model
  const handleAutoComputeWeights = () => {
    if (activeMembers.length === 0) return;

    let computedWeights: number[] = [];
    const returns = activeMembers.map(m => computeStrategyReturn(m.strategy.equity));
    const volatilities = activeMembers.map(m => computeStrategyVolatility(m.strategy.equity));
    const curves = activeMembers.map(m => m.strategy.equity.map(p => p.value));
    const cov = computeCorrelationMatrix(curves); // Normalized approximation

    switch (settings.weightingModel) {
      case 'Equal weight':
        computedWeights = computeEqualWeights(activeMembers.length);
        break;
      case 'Risk Parity':
        computedWeights = computeRiskParityWeights(volatilities);
        break;
      case 'Minimum Variance':
        computedWeights = computeMinVarianceWeights(cov, volatilities);
        break;
      case 'Markowitz Efficient Frontier':
        computedWeights = computeMarkowitzWeights(returns, volatilities, cov, 0.02);
        break;
      default:
        computedWeights = normalizeWeights(activeMembers.map(m => m.weight));
    }

    // Apply weights to store
    activeMembers.forEach((m, idx) => {
      store.updatePortfolio(m.strategyId, { weight: computedWeights[idx] || 0 });
    });

    store.notify(`Portfolio weights calculated using ${settings.weightingModel}`);
  };

  // Handler: Add candidate strategies
  const handleAddCandidates = (strategyIds: string[]) => {
    const currentIds = store.portfolio.map(m => m.strategyId);
    const newMembers: PortfolioMember[] = strategyIds
      .filter(id => !currentIds.includes(id))
      .map(id => {
        const strat = store.strategies.find(s => s.id === id);
        return {
          strategyId: id,
          weight: Math.floor(100 / (store.portfolio.length + strategyIds.length || 1)),
          enabled: true,
          sector: strat?.symbol.includes('USD') ? 'Forex' : 'Indices',
          multiplier: 1.0,
        };
      });

    newMembers.forEach(m => store.addPortfolioMember(m));
    store.normalizePortfolioWeights();
    store.notify(`Added ${newMembers.length} strategies to portfolio`);
  };

  // Handler: Add Buy & Hold strategy
  const handleAddBuyAndHold = () => {
    const benchmark: Strategy = {
      id: `bench-${Date.now()}`,
      name: 'Buy & Hold SPY Benchmark',
      symbol: 'SPY',
      timeframe: 'D1',
      direction: 'Long',
      bankId: 'results',
      revision: 1,
      note: 'Passive asset baseline',
      metrics: {
        netProfit: 34200,
        trades: 1,
        profitFactor: 3.2,
        maxDrawdown: 18200,
        sharpe: 1.15,
        stability: 0.82,
      },
      trades: [],
      equity: Array.from({ length: 50 }, (_, i) => ({
        time: `2025-${String(Math.floor(i / 4) + 1).padStart(2, '0')}-15`,
        value: 100000 + i * 700 + Math.sin(i * 0.3) * 4000,
        drawdown: Math.max(0, 3000 - Math.sin(i * 0.4) * 2000),
      })),
      parameters: {},
    };

    store.addStrategies([benchmark], 'results');
    store.addPortfolioMember({
      strategyId: benchmark.id,
      weight: 15,
      enabled: true,
      sector: 'Equities',
      multiplier: 1.0,
    });
    store.normalizePortfolioWeights();
    store.notify('Added Buy & Hold SPY Benchmark to portfolio');
  };

  // Handler: Reorder member
  const handleMoveMember = (offset: number) => {
    if (!selectedMemberId) return;
    const list = [...store.portfolio];
    const index = list.findIndex(m => m.strategyId === selectedMemberId);
    if (index < 0) return;
    const target = index + offset;
    if (target < 0 || target >= list.length) return;
    [list[index], list[target]] = [list[target], list[index]];
    store.setPortfolioMembers(list);
  };

  // Handler: Save portfolio to databank
  const handleSavePortfolioToDatabank = () => {
    const newStrategy: Strategy = {
      id: `port-${Date.now()}`,
      name: `Portfolio (${activeMembers.length} Strats)`,
      symbol: 'PORTFOLIO',
      timeframe: 'H1',
      direction: 'Both',
      bankId: 'results',
      revision: 1,
      note: `Combined portfolio with ${settings.weightingModel} weighting`,
      metrics: {
        netProfit: simResult.netProfit,
        trades: simResult.totalTrades,
        profitFactor: simResult.profitFactor,
        maxDrawdown: simResult.maxDrawdown,
        sharpe: simResult.sharpe,
        stability: 0.94,
      },
      trades: [],
      equity: simResult.equity,
      parameters: {},
    };

    store.addStrategies([newStrategy], 'results');
    store.notify(`Portfolio saved as new composite strategy "${newStrategy.name}" to Results databank`);
  };

  // SVG Chart Dimensions
  const chartWidth = 960;
  const chartHeight = 320;
  const padding = { top: 20, right: 30, bottom: 30, left: 70 };
  const innerW = chartWidth - padding.left - padding.right;
  const innerH = chartHeight - padding.top - padding.bottom;

  // Chart min/max scaling
  const allValues = [
    ...simResult.equity.map(p => p.value),
    ...members.flatMap(m => (!hiddenCurves[m.strategyId] ? m.strategy.equity.map(p => p.value) : [])),
  ];
  const minVal = allValues.length > 0 ? Math.min(...allValues) : settings.initialCapital;
  const maxVal = allValues.length > 0 ? Math.max(...allValues) : settings.initialCapital * 1.5;
  const valRange = Math.max(1, maxVal - minVal);

  const getX = (idx: number, total: number) => padding.left + (idx / Math.max(1, total - 1)) * innerW;
  const getY = (val: number) => padding.top + innerH - ((val - minVal) / valRange) * innerH;

  const portfolioPolyline = simResult.equity.map((p, i) => `${getX(i, simResult.equity.length)},${getY(p.value)}`).join(' ');

  return (
    <div className="portfolio-composer" style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Top Header */}
      <div className="pc-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 1.25rem', borderBottom: '1px solid var(--border)', background: 'var(--panel)' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 600 }}>Portfolio Composer</h1>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Capital-aware multi-strategy allocation modeling, Markowitz Efficient Frontier, and Risk Parity simulation
          </span>
        </div>

        <nav style={{ display: 'flex', gap: '0.5rem', background: 'var(--bg-card)', padding: '3px', borderRadius: '6px', border: '1px solid var(--border)' }}>
          <button
            className={`btn-tab ${tab === 'setup' ? 'active' : ''}`}
            onClick={() => setTab('setup')}
            style={{ padding: '0.35rem 1rem', border: 'none', background: tab === 'setup' ? 'var(--primary)' : 'transparent', color: tab === 'setup' ? '#fff' : 'inherit', borderRadius: '4px', cursor: 'pointer' }}
          >
            Setup
          </button>
          <button
            className={`btn-tab ${tab === 'results' ? 'active' : ''}`}
            onClick={() => setTab('results')}
            style={{ padding: '0.35rem 1rem', border: 'none', background: tab === 'results' ? 'var(--primary)' : 'transparent', color: tab === 'results' ? '#fff' : 'inherit', borderRadius: '4px', cursor: 'pointer' }}
          >
            Results & Analytics
          </button>
        </nav>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <Button onClick={handleSavePortfolioToDatabank}>
            <Save size={14} /> Save to Databank
          </Button>
          <Button
            className="primary"
            onClick={() => {
              setTab('results');
              store.notify('Portfolio simulation completed across shared account capital');
            }}
          >
            <Play size={14} /> Run simulation
          </Button>
        </div>
      </div>

      {tab === 'setup' ? (
        <div className="pc-setup" style={{ display: 'grid', gridTemplateColumns: '320px 1fr', flex: 1, overflow: 'hidden' }}>
          {/* Left Sidebar: Settings */}
          <aside style={{ borderRight: '1px solid var(--border)', padding: '1rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <Section title="Simulation settings">
              <Field label="Starting capital ($)">
                <TextInput
                  type="number"
                  value={settings.initialCapital}
                  onChange={e => setSettings({ initialCapital: Number(e.target.value) || 100000 })}
                />
              </Field>

              <Field label="Account leverage (1:N)">
                <TextInput
                  type="number"
                  value={settings.leverage}
                  step="5"
                  onChange={e => setSettings({ leverage: Number(e.target.value) || 20 })}
                />
              </Field>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginTop: '0.5rem' }}>
                <Checkbox
                  label="Use shared account capital"
                  checked={settings.sharedCapital}
                  onChange={checked => setSettings({ sharedCapital: checked })}
                />
                <Checkbox
                  label="Skip orders on insufficient free margin"
                  checked={settings.skipOnMargin}
                  onChange={checked => setSettings({ skipOnMargin: checked })}
                />
              </div>

              <div style={{ marginTop: '0.75rem' }}>
                <Field label="Weighting model">
                  <select
                    className="text-input"
                    value={settings.weightingModel}
                    onChange={e => setSettings({ weightingModel: e.target.value as any })}
                  >
                    <option value="Manual weights">Manual weights</option>
                    <option value="Equal weight">Equal weight (1 / N)</option>
                    <option value="Markowitz Efficient Frontier">Markowitz Efficient Frontier</option>
                    <option value="Risk Parity">Risk Parity (Inverse Volatility)</option>
                    <option value="Minimum Variance">Minimum Variance</option>
                  </select>
                </Field>
                <Button
                  style={{ width: '100%', marginTop: '0.5rem' }}
                  onClick={handleAutoComputeWeights}
                  disabled={activeMembers.length === 0}
                >
                  <Calculator size={14} /> Auto-Compute Weights
                </Button>
              </div>
            </Section>

            <Section title="Portfolio constraints">
              <Field label="Max inter-strategy correlation">
                <TextInput
                  type="number"
                  step="0.05"
                  value={settings.maxCorrelation}
                  onChange={e => setSettings({ maxCorrelation: Number(e.target.value) })}
                />
              </Field>
              <Field label="Max strategies in portfolio">
                <TextInput
                  type="number"
                  value={settings.maxStrategies}
                  onChange={e => setSettings({ maxStrategies: Number(e.target.value) })}
                />
              </Field>
              <Field label="Max allocation per sector (%)">
                <TextInput
                  type="number"
                  value={settings.maxSectorWeight}
                  onChange={e => setSettings({ maxSectorWeight: Number(e.target.value) })}
                />
              </Field>
            </Section>

            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', background: 'var(--bg-card)', padding: '0.75rem', borderRadius: '6px', border: '1px solid var(--border)' }}>
              <strong>Weighting Model Semantics:</strong>
              <p style={{ margin: '0.25rem 0 0 0' }}>
                {settings.weightingModel === 'Markowitz Efficient Frontier' && 'Maximizes portfolio Sharpe ratio by balancing historical return vectors against the asset covariance matrix.'}
                {settings.weightingModel === 'Risk Parity' && 'Equalizes the marginal risk contribution of each strategy inversely proportional to its annualized volatility.'}
                {settings.weightingModel === 'Minimum Variance' && 'Optimizes the weight distribution to minimize overall portfolio variance and maximum drawdown.'}
                {settings.weightingModel === 'Equal weight' && 'Distributes capital equally across all active constituent strategies (1/N).'}
                {settings.weightingModel === 'Manual weights' && 'User-defined bespoke weighting allocations summing to 100%.'}
              </p>
            </div>
          </aside>

          {/* Main: Composition Table & Subtoolbar */}
          <main style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: '1rem', gap: '0.75rem' }}>
            <div className="subtoolbar" style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <Button className="primary" onClick={() => setCandidatesModal(true)}>
                <Plus size={14} /> Add candidates
              </Button>
              <Button onClick={handleAddBuyAndHold}>
                <Award size={14} /> Add Buy & Hold
              </Button>
              <Button
                disabled={!selectedMemberId}
                onClick={() => {
                  if (selectedMemberId) {
                    store.removePortfolioMember(selectedMemberId);
                    setSelectedMemberId(null);
                    store.normalizePortfolioWeights();
                  }
                }}
              >
                <Trash2 size={14} /> Remove
              </Button>
              <Button disabled={!selectedMemberId} onClick={() => handleMoveMember(-1)}>
                <ArrowUp size={14} /> Move Up
              </Button>
              <Button disabled={!selectedMemberId} onClick={() => handleMoveMember(1)}>
                <ArrowDown size={14} /> Move Down
              </Button>
              <Button onClick={() => store.normalizePortfolioWeights()}>
                <Calculator size={14} /> Normalize weights
              </Button>
              <Button
                onClick={() => {
                  store.setPortfolioMembers([]);
                  setSelectedMemberId(null);
                }}
              >
                <X size={14} /> Clear all
              </Button>

              <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  Members: <strong>{activeMembers.length} / {members.length}</strong>
                </span>
                <span
                  style={{
                    padding: '0.25rem 0.65rem',
                    borderRadius: '4px',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    background: totalWeight === 100 ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                    color: totalWeight === 100 ? '#22c55e' : '#ef4444',
                    border: `1px solid ${totalWeight === 100 ? '#22c55e' : '#ef4444'}`,
                  }}
                >
                  Total Allocation: {totalWeight}%
                </span>
              </div>
            </div>

            {/* Members Table */}
            <div style={{ flex: 1, overflowY: 'auto', border: '1px solid var(--border)', borderRadius: '6px' }}>
              <table className="plain-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                <thead style={{ position: 'sticky', top: 0, background: 'var(--panel)', zIndex: 1 }}>
                  <tr>
                    <th style={{ width: '40px' }}>Use</th>
                    <th style={{ width: '20px' }}></th>
                    <th>Strategy</th>
                    <th>Market</th>
                    <th>Sector</th>
                    <th style={{ width: '120px' }}>Weight %</th>
                    <th style={{ width: '100px' }}>Multiplier</th>
                    <th>Net Profit</th>
                    <th>Max DD</th>
                    <th>Sharpe</th>
                    <th>Avg Correlation</th>
                  </tr>
                </thead>
                <tbody>
                  {members.map((m, idx) => {
                    const isSelected = selectedMemberId === m.strategyId;
                    const strat = m.strategy;
                    const avgCorr = corrMatrix[idx]
                      ? (corrMatrix[idx].reduce((a, b) => a + b, 0) / (corrMatrix[idx].length || 1)).toFixed(2)
                      : '0.00';

                    return (
                      <tr
                        key={m.strategyId}
                        onClick={() => setSelectedMemberId(m.strategyId)}
                        style={{
                          background: isSelected ? 'rgba(56, 189, 248, 0.08)' : undefined,
                          cursor: 'pointer',
                          opacity: m.enabled ? 1 : 0.5,
                        }}
                      >
                        <td>
                          <input
                            type="checkbox"
                            checked={m.enabled}
                            onChange={e => store.updatePortfolio(m.strategyId, { enabled: e.target.checked })}
                          />
                        </td>
                        <td>
                          <span
                            style={{
                              display: 'inline-block',
                              width: '10px',
                              height: '10px',
                              borderRadius: '50%',
                              backgroundColor: m.color,
                            }}
                          />
                        </td>
                        <td>
                          <strong>{strat.name}</strong>
                          <span style={{ marginLeft: '6px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            rev. {strat.revision}
                          </span>
                        </td>
                        <td>{strat.symbol} ({strat.timeframe})</td>
                        <td>
                          <input
                            type="text"
                            value={m.sector}
                            onChange={e => store.updatePortfolio(m.strategyId, { sector: e.target.value })}
                            className="cell-input"
                            style={{ width: '90px', padding: '2px 4px', fontSize: '0.8rem' }}
                          />
                        </td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <input
                              type="number"
                              className="cell-input"
                              value={m.weight}
                              min="0"
                              max="100"
                              onChange={e => store.updatePortfolio(m.strategyId, { weight: Number(e.target.value) || 0 })}
                              style={{ width: '60px', padding: '2px 6px' }}
                            />
                            <span>%</span>
                          </div>
                        </td>
                        <td>
                          <input
                            type="number"
                            className="cell-input"
                            value={m.multiplier}
                            step="0.1"
                            min="0.1"
                            max="10"
                            onChange={e => store.updatePortfolio(m.strategyId, { multiplier: Number(e.target.value) || 1.0 })}
                            style={{ width: '60px', padding: '2px 6px' }}
                          />
                          <span>x</span>
                        </td>
                        <td className="positive">${strat.metrics.netProfit.toLocaleString()}</td>
                        <td className="negative">${strat.metrics.maxDrawdown.toLocaleString()}</td>
                        <td>{strat.metrics.sharpe.toFixed(2)}</td>
                        <td>
                          <span
                            style={{
                              padding: '1px 6px',
                              borderRadius: '3px',
                              fontSize: '0.75rem',
                              background: Number(avgCorr) > 0.6 ? 'rgba(239, 68, 68, 0.15)' : 'rgba(34, 197, 94, 0.15)',
                              color: Number(avgCorr) > 0.6 ? '#ef4444' : '#22c55e',
                            }}
                          >
                            {avgCorr}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                  {members.length === 0 && (
                    <tr>
                      <td colSpan={11} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                        No strategies in portfolio composition. Click "Add candidates" to import strategies from databank.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </main>
        </div>
      ) : (
        /* Results & Analytics Tab */
        <div className="pc-results" style={{ flex: 1, overflowY: 'auto', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* KPI Ribbon */}
          <div className="metric-strip" style={{ display: 'grid', gridTemplateColumns: 'repeat(8, 1fr)', gap: '0.75rem' }}>
            <Stat label="Portfolio Net Profit" value={`$${simResult.netProfit.toLocaleString()}`} tone="good" />
            <Stat label="Max Drawdown ($)" value={`$${simResult.maxDrawdown.toLocaleString()}`} tone="bad" />
            <Stat label="Max Drawdown (%)" value={`${simResult.maxDrawdownPct}%`} tone="bad" />
            <Stat label="Return / DD Ratio" value={simResult.returnDD.toFixed(2)} tone="good" />
            <Stat label="Sharpe Ratio" value={simResult.sharpe.toFixed(2)} tone="good" />
            <Stat label="Profit Factor" value={simResult.profitFactor.toFixed(2)} />
            <Stat label="Active Strategies" value={simResult.activeMembers} />
            <Stat label="Peak Margin Peak" value={`${simResult.peakMarginPct}%`} tone={simResult.peakMarginPct > 70 ? 'bad' : 'good'} />
          </div>

          {/* Shared-Capital Overlaid Equity Curves Chart */}
          <Section title="Shared-Capital Portfolio & Constituent Equity Curves">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', flexWrap: 'wrap', gap: '0.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.8rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ display: 'inline-block', width: '18px', height: '4px', background: '#38bdf8', borderRadius: '2px' }} />
                  <strong>Combined Portfolio (Thick Cyan)</strong>
                </div>
                <span style={{ color: 'var(--text-muted)' }}>Constituent Strategies:</span>
                {members.map(m => (
                  <label key={m.strategyId} style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={!hiddenCurves[m.strategyId]}
                      onChange={e => setHiddenCurves({ ...hiddenCurves, [m.strategyId]: !e.target.checked })}
                    />
                    <span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', background: m.color }} />
                    <span>{m.strategy.symbol} ({m.weight}%)</span>
                  </label>
                ))}
              </div>
            </div>

            <div style={{ width: '100%', height: '340px', background: '#0b1120', borderRadius: '6px', border: '1px solid var(--border)', position: 'relative', overflow: 'hidden' }}>
              <svg width="100%" height="100%" viewBox={`0 0 ${chartWidth} ${chartHeight}`} preserveAspectRatio="none">
                {/* Horizontal Grid lines */}
                {[0.2, 0.4, 0.6, 0.8].map(ratio => {
                  const y = padding.top + innerH * ratio;
                  const val = Math.round(maxVal - ratio * valRange);
                  return (
                    <g key={ratio}>
                      <line x1={padding.left} y1={y} x2={chartWidth - padding.right} y2={y} stroke="rgba(255,255,255,0.08)" strokeDasharray="3 3" />
                      <text x={padding.left - 8} y={y + 4} fill="#64748b" fontSize="10" textAnchor="end">${val.toLocaleString()}</text>
                    </g>
                  );
                })}

                {/* Individual Constituent Curves */}
                {members.map(m => {
                  if (hiddenCurves[m.strategyId]) return null;
                  const pts = m.strategy.equity.map((p, i) => `${getX(i, m.strategy.equity.length)},${getY(p.value)}`).join(' ');
                  return (
                    <polyline
                      key={m.strategyId}
                      fill="none"
                      stroke={m.color}
                      strokeWidth="1.2"
                      opacity="0.6"
                      points={pts}
                    />
                  );
                })}

                {/* Combined Portfolio Equity Line */}
                <polyline
                  fill="none"
                  stroke="#38bdf8"
                  strokeWidth="3.2"
                  points={portfolioPolyline}
                />
              </svg>
            </div>
          </Section>

          {/* Bottom Split: Correlation Matrix & Monthly Returns Matrix */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
            {/* Correlation Heatmap */}
            <Section title="Constituent Correlation Matrix">
              <div style={{ overflowX: 'auto' }}>
                <table className="plain-table" style={{ width: '100%', textAlign: 'center', fontSize: '0.8rem' }}>
                  <thead>
                    <tr>
                      <th style={{ textAlign: 'left' }}>Strategy</th>
                      {activeMembers.map(m => (
                        <th key={m.strategyId}>{m.strategy.symbol}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {activeMembers.map((rowM, i) => (
                      <tr key={rowM.strategyId}>
                        <td style={{ textAlign: 'left', fontWeight: 600 }}>{rowM.strategy.symbol}</td>
                        {activeMembers.map((_, j) => {
                          const val = corrMatrix[i] ? corrMatrix[i][j] : 0;
                          const bg = i === j
                            ? 'rgba(255,255,255,0.06)'
                            : val > 0.6
                            ? 'rgba(239, 68, 68, 0.25)'
                            : val > 0.3
                            ? 'rgba(234, 179, 8, 0.2)'
                            : 'rgba(34, 197, 94, 0.2)';
                          return (
                            <td key={j} style={{ background: bg, fontWeight: 500 }}>
                              {val.toFixed(2)}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>

            {/* Monthly Returns Matrix */}
            <Section title="Monthly Returns Matrix (%)">
              <div style={{ overflowX: 'auto' }}>
                <table className="plain-table" style={{ width: '100%', textAlign: 'center', fontSize: '0.78rem' }}>
                  <thead>
                    <tr>
                      <th>Year</th>
                      {['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].map(m => (
                        <th key={m}>{m}</th>
                      ))}
                      <th>YTD</th>
                    </tr>
                  </thead>
                  <tbody>
                    {simResult.monthlyReturns.map(row => (
                      <tr key={row.year}>
                        <td style={{ fontWeight: 600 }}>{row.year}</td>
                        {row.months.map((val, mi) => (
                          <td
                            key={mi}
                            style={{
                              color: val === null ? 'var(--text-muted)' : val >= 0 ? '#22c55e' : '#ef4444',
                              background: val === null ? undefined : val >= 0 ? 'rgba(34, 197, 94, 0.08)' : 'rgba(239, 68, 68, 0.08)',
                            }}
                          >
                            {val !== null ? `${val > 0 ? '+' : ''}${val.toFixed(1)}%` : '-'}
                          </td>
                        ))}
                        <td style={{ fontWeight: 600, color: row.total >= 0 ? '#22c55e' : '#ef4444' }}>
                          {row.total > 0 ? '+' : ''}{row.total.toFixed(1)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
          </div>
        </div>
      )}

      {/* Candidate Selector Modal */}
      {candidatesModal && (
        <PortfolioCandidatesModal
          existingIds={store.portfolio.map(m => m.strategyId)}
          onClose={() => setCandidatesModal(false)}
          onAdd={handleAddCandidates}
        />
      )}
    </div>
  );
}

export { PortfolioComposerWorkspace as PortfolioComposer };
