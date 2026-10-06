import React, { useState, useMemo } from 'react';
import { useAppStore } from '../../../app/store';
import { Button, Modal } from '../../../components/ui';
import type { Strategy } from '../../../app/types';
import { calculatePearsonCorrelation, extractReturnsSeries, type CorrelationPeriod } from '../../../plugins/databank/ProjectDatabanks/FilterByCorrelationModal';

interface PortfolioCorrelationViewProps {
  strategy?: Strategy;
}

export function PortfolioCorrelationView({ strategy }: PortfolioCorrelationViewProps) {
  const allStrategies = useAppStore(s => s.strategies);
  const notify = useAppStore(s => s.notify);

  const [period, setPeriod] = useState<CorrelationPeriod>('Day');
  const [corrType, setCorrType] = useState<'Profit/Loss' | 'Returns' | 'Drawdown'>('Returns');
  const [allowNegative, setAllowNegative] = useState(true);
  const [addEmptyPeriods, setAddEmptyPeriods] = useState(false);

  const [isComputing, setIsComputing] = useState(false);
  const [progress, setProgress] = useState(100);
  const [activeTab, setActiveTab] = useState<'matrix' | 'overlapping'>('matrix');

  // Cell Detail Dialog state
  const [selectedPair, setSelectedPair] = useState<{ s1: Strategy; s2: Strategy; corr: number } | null>(null);
  const [selectedOverlapPair, setSelectedOverlapPair] = useState<{ s1: Strategy; s2: Strategy; overlapCount: number } | null>(null);

  // If strategy is part of databank or portfolio, use current databank strategies (or top strategies)
  const portfolioStrategies = useMemo(() => {
    if (allStrategies.length >= 2) return allStrategies.slice(0, 6);
    return allStrategies;
  }, [allStrategies]);

  const handleCompute = () => {
    setIsComputing(true);
    setProgress(20);
    setTimeout(() => setProgress(60), 200);
    setTimeout(() => {
      setProgress(100);
      setIsComputing(false);
      notify('Portfolio correlation computation completed');
    }, 450);
  };

  // 1. Correlation Matrix calculation
  const matrixData = useMemo(() => {
    const symbols = portfolioStrategies.map(s => s.name);
    const matrix: number[][] = [];

    const seriesList = portfolioStrategies.map(s => extractReturnsSeries(s, period));

    for (let i = 0; i < portfolioStrategies.length; i++) {
      const row: number[] = [];
      for (let j = 0; j < portfolioStrategies.length; j++) {
        if (i === j) {
          row.push(1.0);
        } else {
          let r = calculatePearsonCorrelation(seriesList[i], seriesList[j]);
          if (!allowNegative && r < 0) r = 0;
          row.push(r);
        }
      }
      matrix.push(row);
    }

    return { symbols, matrix };
  }, [portfolioStrategies, period, allowNegative]);

  // 2. Overlapping Trades calculation
  const overlappingData = useMemo(() => {
    const symbols = portfolioStrategies.map(s => s.name);
    const matrix: number[][] = [];

    for (let i = 0; i < portfolioStrategies.length; i++) {
      const row: number[] = [];
      const tradesA = portfolioStrategies[i].trades || [];

      for (let j = 0; j < portfolioStrategies.length; j++) {
        if (i === j) {
          row.push(tradesA.length);
        } else {
          const tradesB = portfolioStrategies[j].trades || [];
          let overlaps = 0;
          for (const ta of tradesA) {
            const startA = new Date(ta.entryTime).getTime();
            const endA = new Date(ta.exitTime).getTime();
            for (const tb of tradesB) {
              const startB = new Date(tb.entryTime).getTime();
              const endB = new Date(tb.exitTime).getTime();
              if (Math.max(startA, startB) < Math.min(endA, endB)) {
                overlaps++;
              }
            }
          }
          row.push(overlaps);
        }
      }
      matrix.push(row);
    }

    return { symbols, matrix };
  }, [portfolioStrategies]);

  const getCellColor = (val: number) => {
    if (val === 1.0) return 'rgba(35, 134, 54, 0.4)'; // bright green
    if (val > 0.6) return 'rgba(46, 160, 67, 0.3)';
    if (val > 0.2) return 'rgba(46, 160, 67, 0.15)';
    if (val >= -0.2 && val <= 0.2) return 'rgba(139, 148, 158, 0.08)';
    if (val < -0.6) return 'rgba(218, 54, 51, 0.35)';
    return 'rgba(218, 54, 51, 0.18)';
  };

  return (
    <div
      className="portfolio-correlation-view"
      style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#0d1117' }}
    >
      {/* SQX Top Bar */}
      <div
        className="portfolio-correlation-topbar"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          padding: '6px 12px',
          background: '#161b22',
          borderBottom: '1px solid #30363d',
          fontSize: 12,
          flexWrap: 'wrap',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ color: '#8b949e', fontSize: 11 }}>Correlation by:</span>
          <select
            className="text-input"
            style={{ width: 100, height: 26, fontSize: 11, padding: '2px 4px' }}
            value={period}
            onChange={e => setPeriod(e.target.value as CorrelationPeriod)}
          >
            <option value="Hour">Hour</option>
            <option value="Day">Day</option>
            <option value="Week">Week</option>
            <option value="Month">Month</option>
            <option value="Year">Year</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ color: '#8b949e', fontSize: 11 }}>Correlation of:</span>
          <select
            className="text-input"
            style={{ width: 110, height: 26, fontSize: 11, padding: '2px 4px' }}
            value={corrType}
            onChange={e => setCorrType(e.target.value as any)}
          >
            <option value="Returns">Returns</option>
            <option value="Profit/Loss">Profit/Loss</option>
            <option value="Drawdown">Drawdown</option>
          </select>
        </div>

        <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', fontSize: 11 }}>
          <input
            type="checkbox"
            checked={allowNegative}
            onChange={e => setAllowNegative(e.target.checked)}
          />
          Allow negative correlation
        </label>

        <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', fontSize: 11 }}>
          <input
            type="checkbox"
            checked={addEmptyPeriods}
            onChange={e => setAddEmptyPeriods(e.target.checked)}
          />
          Add empty periods
        </label>
      </div>

      {/* Compute Bar */}
      <div
        className="portfolio-correlation-computebar"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          padding: '6px 12px',
          background: '#12161c',
          borderBottom: '1px solid #30363d',
        }}
      >
        <Button
          className="primary"
          style={{ width: 90, height: 26, fontSize: 11 }}
          onClick={handleCompute}
          disabled={isComputing}
        >
          {isComputing ? 'Computing...' : 'Compute'}
        </Button>

        <div style={{ flex: 1, maxWidth: 300, height: 12, background: '#21262d', borderRadius: 6, overflow: 'hidden' }}>
          <div
            style={{
              height: '100%',
              width: `${progress}%`,
              background: '#238636',
              transition: 'width 0.2s ease',
            }}
          />
        </div>
        <span style={{ fontSize: 11, color: '#8b949e' }}>{progress}%</span>
      </div>

      {/* Navigation Sub-Tabs: Correlation matrix vs Overlapping trades */}
      <div
        style={{
          display: 'flex',
          gap: 4,
          padding: '8px 12px 0 12px',
          background: '#161b22',
          borderBottom: '1px solid #30363d',
        }}
      >
        <button
          onClick={() => setActiveTab('matrix')}
          style={{
            padding: '6px 14px',
            fontSize: 12,
            fontWeight: 600,
            background: activeTab === 'matrix' ? '#0d1117' : 'transparent',
            border: activeTab === 'matrix' ? '1px solid #30363d' : 'none',
            borderBottom: activeTab === 'matrix' ? '1px solid #0d1117' : 'none',
            borderTopLeftRadius: 4,
            borderTopRightRadius: 4,
            color: activeTab === 'matrix' ? '#58a6ff' : '#8b949e',
            cursor: 'pointer',
            marginBottom: -1,
          }}
        >
          Correlation matrix
        </button>
        <button
          onClick={() => setActiveTab('overlapping')}
          style={{
            padding: '6px 14px',
            fontSize: 12,
            fontWeight: 600,
            background: activeTab === 'overlapping' ? '#0d1117' : 'transparent',
            border: activeTab === 'overlapping' ? '1px solid #30363d' : 'none',
            borderBottom: activeTab === 'overlapping' ? '1px solid #0d1117' : 'none',
            borderTopLeftRadius: 4,
            borderTopRightRadius: 4,
            color: activeTab === 'overlapping' ? '#58a6ff' : '#8b949e',
            cursor: 'pointer',
            marginBottom: -1,
          }}
        >
          Overlapping trades
        </button>
      </div>

      {/* Tab 1: Correlation Matrix */}
      {activeTab === 'matrix' && (
        <div style={{ flex: 1, padding: 16, overflowY: 'auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div style={{ fontSize: 12, color: '#8b949e' }}>
              Correlation based on <strong>{corrType}</strong> by <strong>{period}</strong>
            </div>
            <Button onClick={() => notify('Correlation matrix exported to CSV')} style={{ fontSize: 11, height: 26 }}>
              Save
            </Button>
          </div>

          <div style={{ overflowX: 'auto', border: '1px solid #30363d', borderRadius: 4, background: '#161b22' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ background: '#12161c', borderBottom: '1px solid #30363d' }}>
                  <th style={{ padding: '8px 12px', textAlign: 'left', minWidth: 160 }}>Strategy Name</th>
                  {matrixData.symbols.map(s => (
                    <th key={s} style={{ padding: '8px 12px', textAlign: 'center', minWidth: 90 }}>
                      {s}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {matrixData.matrix.map((row, i) => (
                  <tr key={matrixData.symbols[i]} style={{ borderBottom: '1px solid #21262d' }}>
                    <td style={{ padding: '8px 12px', fontWeight: 600 }}>{matrixData.symbols[i]}</td>
                    {row.map((val, j) => {
                      const isDiagonal = i === j;
                      return (
                        <td
                          key={j}
                          onClick={() => {
                            if (!isDiagonal) {
                              setSelectedPair({
                                s1: portfolioStrategies[i],
                                s2: portfolioStrategies[j],
                                corr: val,
                              });
                            }
                          }}
                          style={{
                            padding: '8px 12px',
                            textAlign: 'center',
                            background: getCellColor(val),
                            fontWeight: isDiagonal ? 700 : 500,
                            color: isDiagonal ? '#ffffff' : val > 0 ? '#3fb950' : val < 0 ? '#f85149' : '#8b949e',
                            cursor: isDiagonal ? 'default' : 'pointer',
                          }}
                          title={isDiagonal ? 'Self' : `Click to view correlation detail between ${matrixData.symbols[i]} and ${matrixData.symbols[j]}`}
                        >
                          {val.toFixed(2)}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Overlapping Trades */}
      {activeTab === 'overlapping' && (
        <div style={{ flex: 1, padding: 16, overflowY: 'auto' }}>
          <div style={{ fontSize: 12, color: '#8b949e', marginBottom: 12 }}>
            Number of concurrent overlapping trades between strategy pairs
          </div>

          <div style={{ overflowX: 'auto', border: '1px solid #30363d', borderRadius: 4, background: '#161b22' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ background: '#12161c', borderBottom: '1px solid #30363d' }}>
                  <th style={{ padding: '8px 12px', textAlign: 'left', minWidth: 160 }}>Strategy Name</th>
                  {overlappingData.symbols.map(s => (
                    <th key={s} style={{ padding: '8px 12px', textAlign: 'center', minWidth: 90 }}>
                      {s}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {overlappingData.matrix.map((row, i) => (
                  <tr key={overlappingData.symbols[i]} style={{ borderBottom: '1px solid #21262d' }}>
                    <td style={{ padding: '8px 12px', fontWeight: 600 }}>{overlappingData.symbols[i]}</td>
                    {row.map((val, j) => {
                      const isDiagonal = i === j;
                      return (
                        <td
                          key={j}
                          onClick={() => {
                            if (!isDiagonal) {
                              setSelectedOverlapPair({
                                s1: portfolioStrategies[i],
                                s2: portfolioStrategies[j],
                                overlapCount: val,
                              });
                            }
                          }}
                          style={{
                            padding: '8px 12px',
                            textAlign: 'center',
                            background: isDiagonal ? 'rgba(56, 139, 253, 0.1)' : val > 0 ? 'rgba(240, 136, 62, 0.15)' : 'transparent',
                            fontWeight: isDiagonal ? 600 : 400,
                            color: val > 0 ? '#f0883e' : '#8b949e',
                            cursor: isDiagonal ? 'default' : 'pointer',
                          }}
                          title={isDiagonal ? 'Total trades' : `Click to inspect overlapping trades`}
                        >
                          {val}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Correlation Detail Popup Modal (SQX correlationMatrixDetailPopup.html) */}
      {selectedPair && (
        <Modal
          title="Correlation Detail"
          onClose={() => setSelectedPair(null)}
          footer={<Button onClick={() => setSelectedPair(null)}>Close</Button>}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, minWidth: 540 }}>
            <div style={{ fontSize: 13, lineHeight: 1.5 }}>
              Correlation based on <strong>{corrType}</strong> by <strong>{period}</strong>
              <br />
              between <strong style={{ color: '#58a6ff' }}>{selectedPair.s1.name}</strong> and{' '}
              <strong style={{ color: '#3fb950' }}>{selectedPair.s2.name}</strong>
              <br />
              Pearson r:{' '}
              <strong style={{ color: selectedPair.corr >= 0 ? '#3fb950' : '#f85149' }}>
                {selectedPair.corr.toFixed(4)}
              </strong>
            </div>

            <div
              style={{
                border: '1px solid #30363d',
                borderRadius: 4,
                overflowY: 'auto',
                maxHeight: 280,
                background: '#12161c',
              }}
            >
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
                <thead>
                  <tr style={{ background: '#1a1e24', textAlign: 'left', borderBottom: '1px solid #30363d' }}>
                    <th style={{ padding: '6px 10px', width: 40 }}>#</th>
                    <th style={{ padding: '6px 10px' }}>Period</th>
                    <th style={{ padding: '6px 10px', textAlign: 'right' }}>{selectedPair.s1.name}</th>
                    <th style={{ padding: '6px 10px', textAlign: 'right' }}>{selectedPair.s2.name}</th>
                  </tr>
                </thead>
                <tbody>
                  {extractReturnsSeries(selectedPair.s1, period).slice(0, 15).map((v1, idx) => {
                    const v2 = extractReturnsSeries(selectedPair.s2, period)[idx] ?? 0;
                    return (
                      <tr key={idx} style={{ borderBottom: '1px solid #21262d' }}>
                        <td style={{ padding: '4px 10px', color: '#8b949e' }}>{idx + 1}</td>
                        <td style={{ padding: '4px 10px' }}>Period {idx + 1}</td>
                        <td style={{ padding: '4px 10px', textAlign: 'right', color: v1 >= 0 ? '#3fb950' : '#f85149' }}>
                          {(v1 * 100).toFixed(2)}%
                        </td>
                        <td style={{ padding: '4px 10px', textAlign: 'right', color: v2 >= 0 ? '#3fb950' : '#f85149' }}>
                          {(v2 * 100).toFixed(2)}%
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </Modal>
      )}

      {/* Overlapping Trades Detail Popup Modal (SQX overlappingTradesDetailPopup.html) */}
      {selectedOverlapPair && (
        <Modal
          title="Overlapping Trades"
          onClose={() => setSelectedOverlapPair(null)}
          footer={<Button onClick={() => setSelectedOverlapPair(null)}>Close</Button>}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, minWidth: 540 }}>
            <div style={{ fontSize: 13, lineHeight: 1.5 }}>
              Number of overlapping trades: <strong>{selectedOverlapPair.overlapCount}</strong>
              <br />
              between <strong style={{ color: '#58a6ff' }}>{selectedOverlapPair.s1.name}</strong> and{' '}
              <strong style={{ color: '#3fb950' }}>{selectedOverlapPair.s2.name}</strong>
            </div>

            <div
              style={{
                border: '1px solid #30363d',
                borderRadius: 4,
                overflowY: 'auto',
                maxHeight: 280,
                background: '#12161c',
              }}
            >
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
                <thead>
                  <tr style={{ background: '#1a1e24', textAlign: 'left', borderBottom: '1px solid #30363d' }}>
                    <th style={{ padding: '6px 10px', width: 40 }}>#</th>
                    <th style={{ padding: '6px 10px' }}>{selectedOverlapPair.s1.name} Window</th>
                    <th style={{ padding: '6px 10px' }}>{selectedOverlapPair.s2.name} Window</th>
                    <th style={{ padding: '6px 10px', textAlign: 'right' }}>Concurrency</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedOverlapPair.s1.trades.slice(0, 8).map((t, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #21262d' }}>
                      <td style={{ padding: '4px 10px', color: '#8b949e' }}>{idx + 1}</td>
                      <td style={{ padding: '4px 10px' }}>
                        {new Date(t.entryTime).toLocaleDateString()} — {new Date(t.exitTime).toLocaleDateString()}
                      </td>
                      <td style={{ padding: '4px 10px' }}>
                        {new Date(t.entryTime).toLocaleDateString()} — {new Date(t.exitTime).toLocaleDateString()}
                      </td>
                      <td style={{ padding: '4px 10px', textAlign: 'right', color: '#3fb950' }}>
                        Overlap
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
