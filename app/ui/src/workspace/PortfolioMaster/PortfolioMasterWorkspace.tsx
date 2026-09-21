import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Award,
  CheckCircle,
  Database,
  ExternalLink,
  Filter,
  Layers,
  Pause,
  Play,
  RotateCcw,
  Search,
  Settings,
  Sliders,
  TrendingUp,
} from 'lucide-react';
import { useAppStore } from '../../app/store';
import type { PortfolioMember, Strategy } from '../../app/types';
import { Button, Checkbox, Field, Section, Stat, TextInput } from '../../components/ui';
import {
  computeCorrelationMatrix,
  computeEqualWeights,
  simulatePortfolio,
} from '../PortfolioComposer/portfolioOptimization';

interface DiscoveredPortfolio {
  id: string;
  rank: number;
  members: { strategyId: string; symbol: string; name: string; weight: number }[];
  netProfit: number;
  maxDrawdown: number;
  returnDD: number;
  sharpe: number;
  avgCorrelation: number;
  fitness: number;
}

export function PortfolioMasterWorkspace() {
  const store = useAppStore();
  const [tab, setTab] = useState<'setup' | 'progress'>('setup');
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [combinationsTested, setCombinationsTested] = useState(0);
  const [validPortfoliosCount, setValidPortfoliosCount] = useState(0);
  const [fitnessHistory, setFitnessHistory] = useState<{ gen: number; best: number; avg: number }[]>([]);
  const [discoveredPortfolios, setDiscoveredPortfolios] = useState<DiscoveredPortfolio[]>([]);

  const settings = store.portfolioMasterSettings;
  const setSettings = store.updatePortfolioMasterSettings;

  // Filter candidates from source databank
  const candidateStrategies = useMemo(() => {
    return store.strategies.filter(s => {
      if (settings.sourceDatabank === 'all') return true;
      const bank = store.databanks.find(b => b.name === settings.sourceDatabank || b.id === settings.sourceDatabank.toLowerCase());
      return bank ? bank.strategyIds.includes(s.id) : true;
    });
  }, [store.strategies, store.databanks, settings.sourceDatabank]);

  // Pre-calculate pairwise correlation matrix for candidates
  const candidateCurves = useMemo(() => {
    return candidateStrategies.map(s => s.equity.map(p => p.value));
  }, [candidateStrategies]);

  const candidateCorr = useMemo(() => {
    return computeCorrelationMatrix(candidateCurves);
  }, [candidateCurves]);

  // Simulation execution loop
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    if (!isRunning) {
      if (timerRef.current) clearInterval(timerRef.current);
      return;
    }

    timerRef.current = window.setInterval(() => {
      setProgress(prev => {
        const next = prev + 5;
        if (next >= 100) {
          setIsRunning(false);
          store.notify('Portfolio Master search completed! Top candidate portfolios ready.');
          return 100;
        }
        return next;
      });

      setCombinationsTested(prev => prev + 18);

      // Generate a mock evaluated candidate portfolio
      if (candidateStrategies.length >= settings.minStrategies) {
        const k = Math.min(
          candidateStrategies.length,
          Math.floor(settings.minStrategies + Math.random() * (settings.maxStrategies - settings.minStrategies + 1))
        );

        // Pick k random strategies
        const shuffled = [...candidateStrategies].sort(() => 0.5 - Math.random());
        const selected = shuffled.slice(0, k);

        // Check correlation threshold
        const selectedIndices = selected.map(s => candidateStrategies.findIndex(cs => cs.id === s.id));
        let maxPairwiseCorr = 0;
        let sumCorr = 0;
        let pairs = 0;

        for (let i = 0; i < selectedIndices.length; i++) {
          for (let j = i + 1; j < selectedIndices.length; j++) {
            const idx1 = selectedIndices[i];
            const idx2 = selectedIndices[j];
            const c = (candidateCorr[idx1] && candidateCorr[idx1][idx2]) || 0;
            if (c > maxPairwiseCorr) maxPairwiseCorr = c;
            sumCorr += c;
            pairs++;
          }
        }

        const avgCorr = pairs > 0 ? Math.round((sumCorr / pairs) * 100) / 100 : 0;

        // If passes correlation threshold
        if (maxPairwiseCorr <= settings.maxCorrelation) {
          const weights = computeEqualWeights(k);
          const simMembers = selected.map((s, idx) => ({
            id: s.id,
            name: s.name,
            symbol: s.symbol,
            sector: 'FX',
            weight: weights[idx],
            multiplier: 1.0,
            enabled: true,
            equity: s.equity,
          }));

          const sim = simulatePortfolio(simMembers, 100000, 20, true);

          if (sim.returnDD >= 1.2 && sim.sharpe >= 1.0) {
            setValidPortfoliosCount(c => c + 1);

            const fitness =
              settings.fitness === 'Sharpe ratio'
                ? sim.sharpe
                : settings.fitness === 'Net profit'
                ? sim.netProfit / 10000
                : settings.fitness === 'Minimum Drawdown'
                ? 100000 / Math.max(1, sim.maxDrawdown)
                : sim.returnDD;

            const newPortfolio: DiscoveredPortfolio = {
              id: `disc-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
              rank: 0,
              members: selected.map((s, idx) => ({
                strategyId: s.id,
                symbol: s.symbol,
                name: s.name,
                weight: weights[idx],
              })),
              netProfit: sim.netProfit,
              maxDrawdown: sim.maxDrawdown,
              returnDD: sim.returnDD,
              sharpe: sim.sharpe,
              avgCorrelation: avgCorr,
              fitness,
            };

            setDiscoveredPortfolios(curr => {
              const merged = [...curr, newPortfolio]
                .sort((a, b) => b.fitness - a.fitness)
                .slice(0, 15)
                .map((item, idx) => ({ ...item, rank: idx + 1 }));
              return merged;
            });

            // Update fitness convergence curve
            setFitnessHistory(hist => {
              const gen = hist.length + 1;
              const best = Math.max(fitness, hist.length > 0 ? hist[hist.length - 1].best : fitness);
              const avg = (best + fitness) / 2;
              return [...hist, { gen, best: Math.round(best * 100) / 100, avg: Math.round(avg * 100) / 100 }].slice(-25);
            });
          }
        }
      }
    }, 250);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isRunning, candidateStrategies, candidateCorr, settings]);

  const handleStartSearch = () => {
    if (candidateStrategies.length < settings.minStrategies) {
      store.notify(`Need at least ${settings.minStrategies} candidate strategies in databank`);
      return;
    }
    setProgress(0);
    setCombinationsTested(0);
    setValidPortfoliosCount(0);
    setDiscoveredPortfolios([]);
    setFitnessHistory([]);
    setIsRunning(true);
    setTab('progress');
  };

  const handleLoadIntoComposer = (p: DiscoveredPortfolio) => {
    const portfolioMembers: PortfolioMember[] = p.members.map(m => ({
      strategyId: m.strategyId,
      weight: m.weight,
      enabled: true,
      sector: m.symbol.includes('USD') ? 'Forex' : 'Indices',
      multiplier: 1.0,
    }));

    store.setPortfolioMembers(portfolioMembers);
    store.normalizePortfolioWeights();
    store.setModule('composer');
    store.notify(`Discovered Portfolio #${p.rank} (${p.members.length} strategies) loaded into Portfolio Composer`);
  };

  // SVG Convergence Chart calculations
  const chartW = 600;
  const chartH = 180;
  const pad = { top: 15, right: 20, bottom: 25, left: 45 };
  const innerW = chartW - pad.left - pad.right;
  const innerH = chartH - pad.top - pad.bottom;

  const maxFitness = fitnessHistory.length > 0 ? Math.max(...fitnessHistory.map(h => h.best), 5) : 5;
  const getX = (idx: number) => pad.left + (idx / Math.max(1, fitnessHistory.length - 1)) * innerW;
  const getY = (val: number) => pad.top + innerH - (val / maxFitness) * innerH;

  const bestPoints = fitnessHistory.map((h, i) => `${getX(i)},${getY(h.best)}`).join(' ');
  const avgPoints = fitnessHistory.map((h, i) => `${getX(i)},${getY(h.avg)}`).join(' ');

  return (
    <div className="portfolio-master" style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Top Header */}
      <div className="pc-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 1.25rem', borderBottom: '1px solid var(--border)', background: 'var(--panel)' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 600 }}>Portfolio Master</h1>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Automated multi-strategy portfolio search engine with genetic and brute-force optimization
          </span>
        </div>

        <nav style={{ display: 'flex', gap: '0.5rem', background: 'var(--bg-card)', padding: '3px', borderRadius: '6px', border: '1px solid var(--border)' }}>
          <button
            className={`btn-tab ${tab === 'setup' ? 'active' : ''}`}
            onClick={() => setTab('setup')}
            style={{ padding: '0.35rem 1rem', border: 'none', background: tab === 'setup' ? 'var(--primary)' : 'transparent', color: tab === 'setup' ? '#fff' : 'inherit', borderRadius: '4px', cursor: 'pointer' }}
          >
            Search Setup
          </button>
          <button
            className={`btn-tab ${tab === 'progress' ? 'active' : ''}`}
            onClick={() => setTab('progress')}
            style={{ padding: '0.35rem 1rem', border: 'none', background: tab === 'progress' ? 'var(--primary)' : 'transparent', color: tab === 'progress' ? '#fff' : 'inherit', borderRadius: '4px', cursor: 'pointer' }}
          >
            Search Progress & Candidates ({discoveredPortfolios.length})
          </button>
        </nav>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {isRunning ? (
            <Button onClick={() => setIsRunning(false)} className="secondary">
              <Pause size={14} /> Pause Search
            </Button>
          ) : (
            <Button onClick={handleStartSearch} className="primary">
              <Play size={14} /> Start Search
            </Button>
          )}
        </div>
      </div>

      {tab === 'setup' ? (
        <div style={{ flex: 1, overflowY: 'auto', padding: '1.25rem', display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.25rem' }}>
          {/* Column 1: Search Strategy & Databanks */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <Section title="Search Strategy & Routing">
              <Field label="Search Algorithm">
                <div style={{ display: 'flex', gap: '1rem', marginTop: '0.35rem' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                    <input
                      type="radio"
                      name="searchType"
                      checked={settings.searchType === 'bruteforce'}
                      onChange={() => setSettings({ searchType: 'bruteforce' })}
                    />
                    <span>Brute force</span>
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                    <input
                      type="radio"
                      name="searchType"
                      checked={settings.searchType === 'genetic'}
                      onChange={() => setSettings({ searchType: 'genetic' })}
                    />
                    <span>Genetic search</span>
                  </label>
                </div>
              </Field>

              <Field label="Source Databank">
                <select
                  className="text-input"
                  value={settings.sourceDatabank}
                  onChange={e => setSettings({ sourceDatabank: e.target.value })}
                >
                  <option value="all">All Databanks</option>
                  {store.databanks.map(b => (
                    <option key={b.id} value={b.name}>{b.name} ({b.strategyIds.length} strats)</option>
                  ))}
                </select>
              </Field>

              <Field label="Target Databank">
                <select
                  className="text-input"
                  value={settings.targetDatabank}
                  onChange={e => setSettings({ targetDatabank: e.target.value })}
                >
                  {store.databanks.map(b => (
                    <option key={b.id} value={b.name}>{b.name}</option>
                  ))}
                </select>
              </Field>

              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', background: 'var(--bg-card)', padding: '0.5rem', borderRadius: '4px', marginTop: '0.5rem' }}>
                Available candidates: <strong>{candidateStrategies.length}</strong> strategies
              </div>
            </Section>
          </div>

          {/* Column 2: Portfolio Constraints */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <Section title="Portfolio Constraints">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <Field label="Min Strategies">
                  <TextInput
                    type="number"
                    min="2"
                    max="10"
                    value={settings.minStrategies}
                    onChange={e => setSettings({ minStrategies: Number(e.target.value) || 2 })}
                  />
                </Field>
                <Field label="Max Strategies">
                  <TextInput
                    type="number"
                    min="3"
                    max="15"
                    value={settings.maxStrategies}
                    onChange={e => setSettings({ maxStrategies: Number(e.target.value) || 6 })}
                  />
                </Field>
              </div>

              <Field label="Max Pairwise Correlation (≤)">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <TextInput
                    type="number"
                    step="0.05"
                    min="0.1"
                    max="0.9"
                    value={settings.maxCorrelation}
                    onChange={e => setSettings({ maxCorrelation: Number(e.target.value) || 0.5 })}
                  />
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    (Discards portfolios with corr &gt; {settings.maxCorrelation})
                  </span>
                </div>
              </Field>

              <Field label="Objective / Fitness Function">
                <select
                  className="text-input"
                  value={settings.fitness}
                  onChange={e => setSettings({ fitness: e.target.value as any })}
                >
                  <option value="Return / Drawdown ratio">Return / Drawdown ratio</option>
                  <option value="Sharpe ratio">Sharpe ratio</option>
                  <option value="Net profit">Net profit</option>
                  <option value="Minimum Drawdown">Minimum Drawdown</option>
                </select>
              </Field>
            </Section>
          </div>

          {/* Column 3: Genetic Engine Options */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <Section title="Genetic Engine Options">
              <Field label="Population Size">
                <TextInput
                  type="number"
                  value={settings.population}
                  onChange={e => setSettings({ population: Number(e.target.value) || 100 })}
                />
              </Field>

              <Field label="Max Generations">
                <TextInput
                  type="number"
                  value={settings.generations}
                  onChange={e => setSettings({ generations: Number(e.target.value) || 30 })}
                />
              </Field>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <Field label="Mutation Rate (%)">
                  <TextInput
                    type="number"
                    value={settings.mutation}
                    onChange={e => setSettings({ mutation: Number(e.target.value) || 30 })}
                  />
                </Field>
                <Field label="Crossover Rate (%)">
                  <TextInput
                    type="number"
                    value={settings.crossover}
                    onChange={e => setSettings({ crossover: Number(e.target.value) || 80 })}
                  />
                </Field>
              </div>
            </Section>
          </div>
        </div>
      ) : (
        /* Progress & Discovered Candidates View */
        <div style={{ flex: 1, overflowY: 'auto', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Progress Strip */}
          <div className="metric-strip" style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '0.75rem' }}>
            <Stat label="Search Status" value={isRunning ? 'RUNNING' : progress >= 100 ? 'FINISHED' : 'IDLE'} tone={isRunning ? 'good' : undefined} />
            <Stat label="Combinations Evaluated" value={combinationsTested.toLocaleString()} />
            <Stat label="Valid Portfolios Found" value={validPortfoliosCount} tone="good" />
            <Stat label="Throughput" value={isRunning ? '72 / sec' : '0 / sec'} />
            <Stat label="Best Fitness Score" value={discoveredPortfolios[0] ? discoveredPortfolios[0].fitness.toFixed(2) : '-'} tone="good" />
          </div>

          {/* Progress Bar */}
          <div style={{ background: 'var(--border)', height: '8px', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{ background: 'var(--primary)', width: `${progress}%`, height: '100%', transition: 'width 0.3s ease' }} />
          </div>

          {/* Fitness Convergence SVG Curve */}
          <Section title="Portfolio Fitness Convergence Curve (Best vs Avg)">
            <div style={{ width: '100%', height: '180px', background: '#0b1120', borderRadius: '6px', border: '1px solid var(--border)', position: 'relative', overflow: 'hidden' }}>
              <svg width="100%" height="100%" viewBox={`0 0 ${chartW} ${chartH}`} preserveAspectRatio="none">
                {/* Horizontal guide lines */}
                {[0.25, 0.5, 0.75].map(r => (
                  <line
                    key={r}
                    x1={pad.left}
                    y1={pad.top + innerH * r}
                    x2={chartW - pad.right}
                    y2={pad.top + innerH * r}
                    stroke="rgba(255,255,255,0.08)"
                    strokeDasharray="3 3"
                  />
                ))}

                {/* Average Fitness curve */}
                {avgPoints && <polyline fill="none" stroke="#64748b" strokeWidth="1.5" strokeDasharray="4 2" points={avgPoints} />}

                {/* Best Fitness curve */}
                {bestPoints && <polyline fill="none" stroke="#38bdf8" strokeWidth="2.5" points={bestPoints} />}
              </svg>

              <div style={{ position: 'absolute', top: '8px', right: '12px', display: 'flex', gap: '1rem', fontSize: '0.75rem' }}>
                <span style={{ color: '#38bdf8' }}>— Best Portfolio Fitness</span>
                <span style={{ color: '#64748b' }}>- - Population Average</span>
              </div>
            </div>
          </Section>

          {/* Discovered Portfolios Table */}
          <Section title="Top Discovered Compatible Portfolios">
            <div style={{ overflowX: 'auto', border: '1px solid var(--border)', borderRadius: '6px' }}>
              <table className="plain-table" style={{ width: '100%', fontSize: '0.85rem' }}>
                <thead>
                  <tr>
                    <th style={{ width: '50px' }}>Rank</th>
                    <th>Size</th>
                    <th>Constituent Strategies</th>
                    <th>Net Profit</th>
                    <th>Max DD</th>
                    <th>Return / DD</th>
                    <th>Sharpe</th>
                    <th>Avg Corr</th>
                    <th style={{ textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {discoveredPortfolios.map(p => (
                    <tr key={p.id}>
                      <td>
                        <span style={{ fontWeight: 700, color: p.rank === 1 ? '#f59e0b' : p.rank <= 3 ? '#38bdf8' : 'inherit' }}>
                          #{p.rank}
                        </span>
                      </td>
                      <td>{p.members.length} strats</td>
                      <td>
                        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                          {p.members.map(m => (
                            <span
                              key={m.strategyId}
                              style={{
                                padding: '1px 5px',
                                background: 'rgba(255,255,255,0.06)',
                                borderRadius: '3px',
                                fontSize: '0.75rem',
                              }}
                            >
                              {m.symbol} ({m.weight}%)
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="positive">${p.netProfit.toLocaleString()}</td>
                      <td className="negative">${p.maxDrawdown.toLocaleString()}</td>
                      <td>{p.returnDD.toFixed(2)}</td>
                      <td>{p.sharpe.toFixed(2)}</td>
                      <td>
                        <span style={{ color: p.avgCorrelation < 0.3 ? '#22c55e' : '#f59e0b' }}>
                          {p.avgCorrelation.toFixed(2)}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <Button className="primary" onClick={() => handleLoadIntoComposer(p)} style={{ padding: '0.2rem 0.6rem', fontSize: '0.8rem' }}>
                          <ExternalLink size={12} /> Load into Composer
                        </Button>
                      </td>
                    </tr>
                  ))}
                  {discoveredPortfolios.length === 0 && (
                    <tr>
                      <td colSpan={9} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                        {isRunning
                          ? 'Search in progress... Evaluating strategy combinations.'
                          : 'No portfolios discovered yet. Configure constraints and click "Start Search".'}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </Section>
        </div>
      )}
    </div>
  );
}

export { PortfolioMasterWorkspace as PortfolioMaster };
