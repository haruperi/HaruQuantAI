import React, { useState, useMemo } from 'react';
import { Button, Modal } from '../../../components/ui';
import type { Strategy } from '../../../host/types';

export interface CompareStrategiesModalProps {
  isOpen: boolean;
  onClose: () => void;
  strategies: Strategy[];
  initialStrategyId1?: string;
  initialStrategyId2?: string;
}

export function CompareStrategiesModal({
  isOpen,
  onClose,
  strategies,
  initialStrategyId1,
  initialStrategyId2,
}: CompareStrategiesModalProps) {
  const [strategyId1, setStrategyId1] = useState<string>(
    initialStrategyId1 || strategies[0]?.id || ''
  );
  const [strategyId2, setStrategyId2] = useState<string>(
    initialStrategyId2 || strategies[1]?.id || strategies[0]?.id || ''
  );
  const [expandedSections, setExpandedSections] = useState({
    kpi: true,
    equity: true,
    params: true,
  });

  const s1 = useMemo(
    () => strategies.find(s => s.id === strategyId1) || strategies[0],
    [strategies, strategyId1]
  );
  const s2 = useMemo(
    () => strategies.find(s => s.id === strategyId2) || strategies[1] || strategies[0],
    [strategies, strategyId2]
  );

  if (!isOpen || !s1 || !s2) return null;

  const toggleAll = (expand: boolean) => {
    setExpandedSections({
      kpi: expand,
      equity: expand,
      params: expand,
    });
  };

  // Prepare normalized equity curves for dual SVG overlay
  const equity1 = s1.equity?.map(e => e.value) || [10000];
  const equity2 = s2.equity?.map(e => e.value) || [10000];
  const maxLen = Math.max(equity1.length, equity2.length);

  const minVal = Math.min(...equity1, ...equity2);
  const maxVal = Math.max(...equity1, ...equity2);
  const valRange = maxVal - minVal || 1;

  const width = 680;
  const height = 150;
  const pad = 12;

  const toPoints = (data: number[]) => {
    if (data.length <= 1) return '';
    return data
      .map((val, idx) => {
        const x = pad + (idx / (data.length - 1)) * (width - 2 * pad);
        const y = height - pad - ((val - minVal) / valRange) * (height - 2 * pad);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' ');
  };

  const points1 = toPoints(equity1);
  const points2 = toPoints(equity2);

  const kpis: Array<{
    label: string;
    v1: number | string;
    v2: number | string;
    format: (v: any) => string;
    isHigherBetter: boolean;
  }> = [
    {
      label: 'Net profit',
      v1: s1.metrics?.netProfit ?? 0,
      v2: s2.metrics?.netProfit ?? 0,
      format: v => `$${Number(v).toLocaleString()}`,
      isHigherBetter: true,
    },
    {
      label: 'Profit factor',
      v1: s1.metrics?.profitFactor ?? 1,
      v2: s2.metrics?.profitFactor ?? 1,
      format: v => Number(v).toFixed(2),
      isHigherBetter: true,
    },
    {
      label: 'Max drawdown',
      v1: s1.metrics?.maxDrawdown ?? 0,
      v2: s2.metrics?.maxDrawdown ?? 0,
      format: v => `$${Number(v).toLocaleString()}`,
      isHigherBetter: false,
    },
    {
      label: 'Sharpe ratio',
      v1: s1.metrics?.sharpe ?? 0,
      v2: s2.metrics?.sharpe ?? 0,
      format: v => Number(v).toFixed(2),
      isHigherBetter: true,
    },
    {
      label: 'Total trades',
      v1: s1.metrics?.trades ?? s1.trades?.length ?? 0,
      v2: s2.metrics?.trades ?? s2.trades?.length ?? 0,
      format: v => `${v}`,
      isHigherBetter: true,
    },
    {
      label: 'Win rate',
      v1:
        s1.trades && s1.trades.length > 0
          ? (s1.trades.filter(t => t.pnl > 0).length / s1.trades.length) * 100
          : 50,
      v2:
        s2.trades && s2.trades.length > 0
          ? (s2.trades.filter(t => t.pnl > 0).length / s2.trades.length) * 100
          : 50,
      format: v => `${Number(v).toFixed(1)}%`,
      isHigherBetter: true,
    },
    {
      label: 'Stability',
      v1: s1.metrics?.stability ?? 80,
      v2: s2.metrics?.stability ?? 80,
      format: v => `${v}%`,
      isHigherBetter: true,
    },
  ];

  return (
    <Modal
      title="Compare last settings of two strategies"
      onClose={onClose}
      footer={
        <div style={{ display: 'flex', justifyContent: 'flex-end', width: '100%' }}>
          <Button onClick={onClose}>Close</Button>
        </div>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14, minWidth: 700, maxHeight: 580, overflowY: 'auto' }}>
        {/* Strategy Pickers Bar */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 16,
            padding: 12,
            background: 'var(--surface-muted, #1a1e24)',
            borderRadius: 4,
            border: '1px solid var(--border-color, #2d333b)',
          }}
        >
          <div>
            <label style={{ fontSize: 11, fontWeight: 600, color: '#58a6ff', display: 'block', marginBottom: 4 }}>
              Strategy 1 (Primary · Blue)
            </label>
            <select
              className="text-input"
              style={{ width: '100%' }}
              value={strategyId1}
              onChange={e => setStrategyId1(e.target.value)}
            >
              {strategies.map(s => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.symbol} · {s.timeframe})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label style={{ fontSize: 11, fontWeight: 600, color: '#3fb950', display: 'block', marginBottom: 4 }}>
              Strategy 2 (Comparison · Green)
            </label>
            <select
              className="text-input"
              style={{ width: '100%' }}
              value={strategyId2}
              onChange={e => setStrategyId2(e.target.value)}
            >
              {strategies.map(s => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.symbol} · {s.timeframe})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Global Expand / Collapse Bar */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, fontSize: 12 }}>
          <a
            href="#expand"
            onClick={e => {
              e.preventDefault();
              toggleAll(true);
            }}
            style={{ color: '#58a6ff', textDecoration: 'none', cursor: 'pointer' }}
          >
            Expand all
          </a>
          <span style={{ color: '#8b949e' }}>|</span>
          <a
            href="#collapse"
            onClick={e => {
              e.preventDefault();
              toggleAll(false);
            }}
            style={{ color: '#58a6ff', textDecoration: 'none', cursor: 'pointer' }}
          >
            Collapse all
          </a>
        </div>

        {/* 1. Dual Overlaid Equity Curve Chart */}
        <div
          style={{
            border: '1px solid var(--border-color, #2d333b)',
            borderRadius: 4,
            overflow: 'hidden',
          }}
        >
          <div
            onClick={() =>
              setExpandedSections(prev => ({ ...prev, equity: !prev.equity }))
            }
            style={{
              padding: '8px 12px',
              background: 'var(--surface-muted, #1a1e24)',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: 13,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span>Overlaid Equity Curves</span>
            <span style={{ fontSize: 11, color: '#8b949e' }}>
              {expandedSections.equity ? '▲ Hide' : '▼ Show'}
            </span>
          </div>
          {expandedSections.equity && (
            <div style={{ padding: 12, background: '#0d1117' }}>
              <div style={{ display: 'flex', gap: 16, marginBottom: 8, fontSize: 11 }}>
                <span style={{ color: '#58a6ff' }}>■ {s1.name} (Max: ${Math.max(...equity1).toLocaleString()})</span>
                <span style={{ color: '#3fb950' }}>■ {s2.name} (Max: ${Math.max(...equity2).toLocaleString()})</span>
              </div>
              <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`}>
                {/* Horizontal Grid lines */}
                <line x1={pad} y1={pad} x2={width - pad} y2={pad} stroke="#21262d" strokeDasharray="3,3" />
                <line x1={pad} y1={height / 2} x2={width - pad} y2={height / 2} stroke="#21262d" strokeDasharray="3,3" />
                <line x1={pad} y1={height - pad} x2={width - pad} y2={height - pad} stroke="#21262d" />

                {/* S1 Equity Line */}
                {points1 && (
                  <polyline
                    fill="none"
                    stroke="#58a6ff"
                    strokeWidth="2"
                    points={points1}
                  />
                )}
                {/* S2 Equity Line */}
                {points2 && (
                  <polyline
                    fill="none"
                    stroke="#3fb950"
                    strokeWidth="2"
                    points={points2}
                  />
                )}
              </svg>
            </div>
          )}
        </div>

        {/* 2. Key Performance Indicators Comparison */}
        <div
          style={{
            border: '1px solid var(--border-color, #2d333b)',
            borderRadius: 4,
            overflow: 'hidden',
          }}
        >
          <div
            onClick={() =>
              setExpandedSections(prev => ({ ...prev, kpi: !prev.kpi }))
            }
            style={{
              padding: '8px 12px',
              background: 'var(--surface-muted, #1a1e24)',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: 13,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span>Performance Metrics & Delta Comparison</span>
            <span style={{ fontSize: 11, color: '#8b949e' }}>
              {expandedSections.kpi ? '▲ Hide' : '▼ Show'}
            </span>
          </div>
          {expandedSections.kpi && (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ background: '#161b22', textAlign: 'left', borderBottom: '1px solid #30363d' }}>
                  <th style={{ padding: '6px 12px', width: '30%' }}>Metric</th>
                  <th style={{ padding: '6px 12px', width: '25%', color: '#58a6ff' }}>{s1.name}</th>
                  <th style={{ padding: '6px 12px', width: '25%', color: '#3fb950' }}>{s2.name}</th>
                  <th style={{ padding: '6px 12px', width: '20%', textAlign: 'right' }}>Difference</th>
                </tr>
              </thead>
              <tbody>
                {kpis.map((k, idx) => {
                  const num1 = typeof k.v1 === 'number' ? k.v1 : 0;
                  const num2 = typeof k.v2 === 'number' ? k.v2 : 0;
                  const diff = num1 - num2;
                  const is1Better = k.isHigherBetter ? diff > 0 : diff < 0;
                  const is2Better = k.isHigherBetter ? diff < 0 : diff > 0;

                  return (
                    <tr
                      key={k.label}
                      style={{
                        borderBottom: '1px solid #21262d',
                        background: idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)',
                      }}
                    >
                      <td style={{ padding: '6px 12px', fontWeight: 500 }}>{k.label}</td>
                      <td
                        style={{
                          padding: '6px 12px',
                          color: is1Better ? '#58a6ff' : 'inherit',
                          fontWeight: is1Better ? 600 : 400,
                        }}
                      >
                        {k.format(k.v1)}
                      </td>
                      <td
                        style={{
                          padding: '6px 12px',
                          color: is2Better ? '#3fb950' : 'inherit',
                          fontWeight: is2Better ? 600 : 400,
                        }}
                      >
                        {k.format(k.v2)}
                      </td>
                      <td
                        style={{
                          padding: '6px 12px',
                          textAlign: 'right',
                          color: is1Better ? '#58a6ff' : is2Better ? '#3fb950' : '#8b949e',
                        }}
                      >
                        {diff > 0 ? `+${diff.toFixed(2)}` : diff.toFixed(2)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* 3. Strategy Configuration & Parameters Comparison */}
        <div
          style={{
            border: '1px solid var(--border-color, #2d333b)',
            borderRadius: 4,
            overflow: 'hidden',
          }}
        >
          <div
            onClick={() =>
              setExpandedSections(prev => ({ ...prev, params: !prev.params }))
            }
            style={{
              padding: '8px 12px',
              background: 'var(--surface-muted, #1a1e24)',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: 13,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span>Strategy Parameters & Trading Rules</span>
            <span style={{ fontSize: 11, color: '#8b949e' }}>
              {expandedSections.params ? '▲ Hide' : '▼ Show'}
            </span>
          </div>
          {expandedSections.params && (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ background: '#161b22', textAlign: 'left', borderBottom: '1px solid #30363d' }}>
                  <th style={{ padding: '6px 12px', width: '30%' }}>Setting / Parameter</th>
                  <th style={{ padding: '6px 12px', width: '35%', color: '#58a6ff' }}>{s1.name}</th>
                  <th style={{ padding: '6px 12px', width: '35%', color: '#3fb950' }}>{s2.name}</th>
                </tr>
              </thead>
              <tbody>
                <tr style={{ borderBottom: '1px solid #21262d' }}>
                  <td style={{ padding: '6px 12px', fontWeight: 500 }}>Instrument Symbol</td>
                  <td style={{ padding: '6px 12px' }}>{s1.symbol}</td>
                  <td style={{ padding: '6px 12px' }}>{s2.symbol}</td>
                </tr>
                <tr style={{ borderBottom: '1px solid #21262d' }}>
                  <td style={{ padding: '6px 12px', fontWeight: 500 }}>Timeframe</td>
                  <td style={{ padding: '6px 12px' }}>{s1.timeframe}</td>
                  <td style={{ padding: '6px 12px' }}>{s2.timeframe}</td>
                </tr>
                <tr style={{ borderBottom: '1px solid #21262d' }}>
                  <td style={{ padding: '6px 12px', fontWeight: 500 }}>Signal Type</td>
                  <td style={{ padding: '6px 12px' }}>Trend Following Breakout</td>
                  <td style={{ padding: '6px 12px' }}>Mean Reversion Oscillator</td>
                </tr>
                <tr style={{ borderBottom: '1px solid #21262d' }}>
                  <td style={{ padding: '6px 12px', fontWeight: 500 }}>Stop Loss Mode</td>
                  <td style={{ padding: '6px 12px' }}>ATR Based (2.0 x ATR)</td>
                  <td style={{ padding: '6px 12px' }}>Fixed Points (45 pips)</td>
                </tr>
                <tr style={{ borderBottom: '1px solid #21262d' }}>
                  <td style={{ padding: '6px 12px', fontWeight: 500 }}>Profit Target Mode</td>
                  <td style={{ padding: '6px 12px' }}>Trailing Stop (3.5 x ATR)</td>
                  <td style={{ padding: '6px 12px' }}>Fixed Target (90 pips)</td>
                </tr>
                <tr style={{ borderBottom: '1px solid #21262d' }}>
                  <td style={{ padding: '6px 12px', fontWeight: 500 }}>Notes / Metadata</td>
                  <td style={{ padding: '6px 12px', color: '#8b949e' }}>{s1.note || 'None'}</td>
                  <td style={{ padding: '6px 12px', color: '#8b949e' }}>{s2.note || 'None'}</td>
                </tr>
              </tbody>
            </table>
          )}
        </div>
      </div>
    </Modal>
  );
}
