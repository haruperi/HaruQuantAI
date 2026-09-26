import React, { useState, useMemo } from 'react';
import type { Strategy, Trade } from '../../../host/types';

interface TradeAnalysisViewProps {
  strategy?: Strategy;
}

export function TradeAnalysisView({ strategy }: TradeAnalysisViewProps) {
  const [periodBy, setPeriodBy] = useState<'open' | 'close'>('open');
  const [selectedYear, setSelectedYear] = useState<string>('All');
  const [sampleFilter, setSampleFilter] = useState<'all' | 'is' | 'oos'>('all');
  const [directionFilter, setDirectionFilter] = useState<'all' | 'long' | 'short'>('all');

  const trades: Trade[] = useMemo(() => {
    if (!strategy?.trades) return [];
    return strategy.trades.filter(t => {
      if (sampleFilter === 'is' && t.sample !== 'IS') return false;
      if (sampleFilter === 'oos' && t.sample !== 'OOS') return false;
      if (directionFilter === 'long' && t.side !== 'Long') return false;
      if (directionFilter === 'short' && t.side !== 'Short') return false;
      return true;
    });
  }, [strategy, sampleFilter, directionFilter]);

  // Extract years present in trades
  const years = useMemo(() => {
    const set = new Set<string>();
    trades.forEach(t => {
      const d = new Date(periodBy === 'open' ? t.entryTime : t.exitTime);
      set.add(String(d.getFullYear()));
    });
    return Array.from(set).sort();
  }, [trades, periodBy]);

  // Annual Stats Calculation
  const annualStats = useMemo(() => {
    const map = new Map<
      string,
      { profit: number; trades: number; wins: number; grossProfit: number; grossLoss: number }
    >();

    trades.forEach(t => {
      const year = String(
        new Date(periodBy === 'open' ? t.entryTime : t.exitTime).getFullYear()
      );
      if (!map.has(year)) {
        map.set(year, { profit: 0, trades: 0, wins: 0, grossProfit: 0, grossLoss: 0 });
      }
      const item = map.get(year)!;
      item.profit += t.pnl;
      item.trades += 1;
      if (t.pnl > 0) {
        item.wins += 1;
        item.grossProfit += t.pnl;
      } else {
        item.grossLoss += Math.abs(t.pnl);
      }
    });

    const rows = Array.from(map.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([yr, data]) => {
        const pf = data.grossLoss === 0 ? (data.grossProfit > 0 ? 99.9 : 1.0) : data.grossProfit / data.grossLoss;
        const winPct = data.trades > 0 ? (data.wins / data.trades) * 100 : 0;
        return {
          year: yr,
          profit: data.profit,
          profitFactor: pf,
          trades: data.trades,
          winPct,
        };
      });

    // Total row
    const totalProfit = rows.reduce((acc, r) => acc + r.profit, 0);
    const totalTrades = rows.reduce((acc, r) => acc + r.trades, 0);
    const totalWins = trades.filter(t => t.pnl > 0).length;
    const totalGrossWin = trades.reduce((acc, t) => (t.pnl > 0 ? acc + t.pnl : acc), 0);
    const totalGrossLoss = Math.abs(trades.reduce((acc, t) => (t.pnl < 0 ? acc + t.pnl : acc), 0));
    const totalPF = totalGrossLoss === 0 ? (totalGrossWin > 0 ? 99.9 : 1.0) : totalGrossWin / totalGrossLoss;
    const totalWinPct = totalTrades > 0 ? (totalWins / totalTrades) * 100 : 0;

    return {
      rows,
      total: {
        year: 'Total',
        profit: totalProfit,
        profitFactor: totalPF,
        trades: totalTrades,
        winPct: totalWinPct,
      },
    };
  }, [trades, periodBy]);

  // Filtered trades by year (if a year is selected)
  const activeTrades = useMemo(() => {
    if (selectedYear === 'All' || selectedYear === 'Total') return trades;
    return trades.filter(t => {
      const yr = String(
        new Date(periodBy === 'open' ? t.entryTime : t.exitTime).getFullYear()
      );
      return yr === selectedYear;
    });
  }, [trades, selectedYear, periodBy]);

  // 1. Day of Week Breakdown
  const dayOfWeekStats = useMemo(() => {
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
    const pnl = [0, 0, 0, 0, 0];
    const counts = [0, 0, 0, 0, 0];

    activeTrades.forEach(t => {
      const d = new Date(periodBy === 'open' ? t.entryTime : t.exitTime);
      const day = d.getDay(); // 0 is Sun, 1 is Mon...
      const idx = day >= 1 && day <= 5 ? day - 1 : 0;
      pnl[idx] += t.pnl;
      counts[idx] += 1;
    });

    return days.map((name, i) => ({
      name,
      profit: pnl[i],
      trades: counts[i],
    }));
  }, [activeTrades, periodBy]);

  // 2. Hour of Day Breakdown
  const hourOfDayStats = useMemo(() => {
    const hours = Array.from({ length: 24 }, (_, i) => i);
    const pnl = new Array(24).fill(0);
    const counts = new Array(24).fill(0);

    activeTrades.forEach(t => {
      const d = new Date(periodBy === 'open' ? t.entryTime : t.exitTime);
      const h = d.getHours();
      pnl[h] += t.pnl;
      counts[h] += 1;
    });

    return hours.map(h => ({
      hour: `${h.toString().padStart(2, '0')}:00`,
      profit: pnl[h],
      trades: counts[h],
    }));
  }, [activeTrades, periodBy]);

  // 3. Monthly Matrix (Jan - Dec)
  const monthlyMatrix = useMemo(() => {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const matrix: Record<string, number[]> = {};

    years.forEach(yr => {
      matrix[yr] = new Array(12).fill(0);
    });

    trades.forEach(t => {
      const d = new Date(periodBy === 'open' ? t.entryTime : t.exitTime);
      const yr = String(d.getFullYear());
      const m = d.getMonth();
      if (matrix[yr]) {
        matrix[yr][m] += t.pnl;
      }
    });

    return { months, matrix };
  }, [trades, years, periodBy]);

  // 4. Streak Analysis
  const streakStats = useMemo(() => {
    let currentWinStreak = 0;
    let currentLossStreak = 0;
    let maxWin = 0;
    let maxLoss = 0;
    const winDistribution: Record<number, number> = {};
    const lossDistribution: Record<number, number> = {};

    activeTrades.forEach(t => {
      if (t.pnl > 0) {
        currentWinStreak++;
        if (currentLossStreak > 0) {
          lossDistribution[currentLossStreak] = (lossDistribution[currentLossStreak] || 0) + 1;
          currentLossStreak = 0;
        }
        maxWin = Math.max(maxWin, currentWinStreak);
      } else if (t.pnl < 0) {
        currentLossStreak++;
        if (currentWinStreak > 0) {
          winDistribution[currentWinStreak] = (winDistribution[currentWinStreak] || 0) + 1;
          currentWinStreak = 0;
        }
        maxLoss = Math.max(maxLoss, currentLossStreak);
      }
    });

    if (currentWinStreak > 0) {
      winDistribution[currentWinStreak] = (winDistribution[currentWinStreak] || 0) + 1;
    }
    if (currentLossStreak > 0) {
      lossDistribution[currentLossStreak] = (lossDistribution[currentLossStreak] || 0) + 1;
    }

    return { maxWin, maxLoss, winDistribution, lossDistribution };
  }, [activeTrades]);

  // 5. Duration Distribution
  const durationStats = useMemo(() => {
    const buckets = [
      { label: '< 1 hr', count: 0, pnl: 0 },
      { label: '1 - 4 hrs', count: 0, pnl: 0 },
      { label: '4 - 12 hrs', count: 0, pnl: 0 },
      { label: '12 - 24 hrs', count: 0, pnl: 0 },
      { label: '1 - 3 days', count: 0, pnl: 0 },
      { label: '> 3 days', count: 0, pnl: 0 },
    ];

    activeTrades.forEach(t => {
      const openTime = new Date(t.entryTime).getTime();
      const closeTime = new Date(t.exitTime).getTime();
      const hours = Math.max(0.1, (closeTime - openTime) / (3600 * 1000));

      let bIdx = 5;
      if (hours < 1) bIdx = 0;
      else if (hours < 4) bIdx = 1;
      else if (hours < 12) bIdx = 2;
      else if (hours < 24) bIdx = 3;
      else if (hours < 72) bIdx = 4;

      buckets[bIdx].count += 1;
      buckets[bIdx].pnl += t.pnl;
    });

    return buckets;
  }, [activeTrades]);

  return (
    <div
      className="trade-analysis-view"
      style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#0d1117' }}
    >
      {/* SQX Results Toolbar */}
      <div
        className="trade-analysis-toolbar"
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
        {/* Period by: Open Time / Close Time */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ color: '#8b949e', fontSize: 11 }}>Period by:</span>
          <div style={{ display: 'inline-flex', borderRadius: 3, overflow: 'hidden', border: '1px solid #30363d' }}>
            <button
              style={{
                padding: '2px 8px',
                fontSize: 11,
                background: periodBy === 'open' ? '#1f6feb' : '#21262d',
                border: 'none',
                color: '#fff',
                cursor: 'pointer',
              }}
              onClick={() => setPeriodBy('open')}
            >
              Open Time
            </button>
            <button
              style={{
                padding: '2px 8px',
                fontSize: 11,
                background: periodBy === 'close' ? '#1f6feb' : '#21262d',
                border: 'none',
                color: '#fff',
                cursor: 'pointer',
              }}
              onClick={() => setPeriodBy('close')}
            >
              Close Time
            </button>
          </div>
        </div>

        <div style={{ width: 1, height: 18, background: '#30363d' }} />

        {/* Sample Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{ color: '#8b949e', fontSize: 11 }}>Sample:</span>
          <select
            className="text-input"
            style={{ width: 110, height: 26, fontSize: 11, padding: '2px 4px' }}
            value={sampleFilter}
            onChange={e => setSampleFilter(e.target.value as any)}
          >
            <option value="all">Full data</option>
            <option value="is">In Sample</option>
            <option value="oos">Out of Sample</option>
          </select>
        </div>

        {/* Direction Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{ color: '#8b949e', fontSize: 11 }}>Direction:</span>
          <select
            className="text-input"
            style={{ width: 90, height: 26, fontSize: 11, padding: '2px 4px' }}
            value={directionFilter}
            onChange={e => setDirectionFilter(e.target.value as any)}
          >
            <option value="all">All</option>
            <option value="long">Long</option>
            <option value="short">Short</option>
          </select>
        </div>

        <div style={{ marginLeft: 'auto', color: '#8b949e', fontSize: 11 }}>
          Selected Year: <strong style={{ color: '#58a6ff' }}>{selectedYear}</strong> ({activeTrades.length} trades)
        </div>
      </div>

      {/* Main Content Area */}
      <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflowY: 'auto', padding: 12, gap: 14 }}>
        {/* Top Annual Stats Grid (SQX annualStatsGrid) */}
        <div
          style={{
            border: '1px solid #30363d',
            borderRadius: 4,
            background: '#161b22',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              padding: '6px 12px',
              background: '#21262d',
              borderBottom: '1px solid #30363d',
              fontWeight: 600,
              fontSize: 12,
              color: '#c9d1d9',
              display: 'flex',
              justifyContent: 'space-between',
            }}
          >
            <span>Annual Performance Statistics</span>
            <span style={{ fontSize: 11, color: '#8b949e', fontWeight: 400 }}>
              (Click a row to isolate analysis to that period)
            </span>
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
            <thead>
              <tr style={{ background: '#12161c', textAlign: 'left', borderBottom: '1px solid #30363d' }}>
                <th style={{ padding: '6px 12px' }}>Period</th>
                <th style={{ padding: '6px 12px', textAlign: 'right' }}>Net Profit</th>
                <th style={{ padding: '6px 12px', textAlign: 'right' }}>Profit Factor</th>
                <th style={{ padding: '6px 12px', textAlign: 'right' }}># of trades</th>
                <th style={{ padding: '6px 12px', textAlign: 'right' }}>% Wins</th>
              </tr>
            </thead>
            <tbody>
              {/* Total Row */}
              <tr
                onClick={() => setSelectedYear('All')}
                style={{
                  borderBottom: '1px solid #30363d',
                  cursor: 'pointer',
                  background: selectedYear === 'All' ? 'rgba(56, 139, 253, 0.15)' : 'rgba(255, 255, 255, 0.02)',
                  fontWeight: 600,
                }}
              >
                <td style={{ padding: '6px 12px', color: '#58a6ff' }}>{annualStats.total.year}</td>
                <td
                  style={{
                    padding: '6px 12px',
                    textAlign: 'right',
                    color: annualStats.total.profit >= 0 ? '#3fb950' : '#f85149',
                  }}
                >
                  ${annualStats.total.profit.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </td>
                <td style={{ padding: '6px 12px', textAlign: 'right' }}>{annualStats.total.profitFactor.toFixed(2)}</td>
                <td style={{ padding: '6px 12px', textAlign: 'right' }}>{annualStats.total.trades}</td>
                <td style={{ padding: '6px 12px', textAlign: 'right' }}>{annualStats.total.winPct.toFixed(1)}%</td>
              </tr>

              {/* Annual Rows */}
              {annualStats.rows.map(row => {
                const isSelected = selectedYear === row.year;
                return (
                  <tr
                    key={row.year}
                    onClick={() => setSelectedYear(row.year)}
                    style={{
                      borderBottom: '1px solid #21262d',
                      cursor: 'pointer',
                      background: isSelected ? 'rgba(56, 139, 253, 0.15)' : 'transparent',
                    }}
                  >
                    <td style={{ padding: '6px 12px' }}>{row.year}</td>
                    <td
                      style={{
                        padding: '6px 12px',
                        textAlign: 'right',
                        color: row.profit >= 0 ? '#3fb950' : '#f85149',
                      }}
                    >
                      ${row.profit.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td style={{ padding: '6px 12px', textAlign: 'right' }}>{row.profitFactor.toFixed(2)}</td>
                    <td style={{ padding: '6px 12px', textAlign: 'right' }}>{row.trades}</td>
                    <td style={{ padding: '6px 12px', textAlign: 'right' }}>{row.winPct.toFixed(1)}%</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* 2-Column Grid of Trade Analysis Panels */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
          {/* Panel 1: Profit by Day of Week */}
          <div
            style={{
              border: '1px solid #30363d',
              borderRadius: 4,
              background: '#161b22',
              padding: 12,
            }}
          >
            <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 10, color: '#c9d1d9' }}>
              Profit by Day of Week ({selectedYear})
            </div>
            <div style={{ display: 'flex', alignItems: 'flex-end', height: 130, gap: 12, paddingTop: 10 }}>
              {dayOfWeekStats.map(d => {
                const maxP = Math.max(...dayOfWeekStats.map(x => Math.abs(x.profit)), 100);
                const heightPct = Math.min(100, Math.max(10, (Math.abs(d.profit) / maxP) * 100));
                const isPos = d.profit >= 0;

                return (
                  <div
                    key={d.name}
                    style={{
                      flex: 1,
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: 4,
                    }}
                  >
                    <span style={{ fontSize: 10, color: isPos ? '#3fb950' : '#f85149' }}>
                      ${Math.round(d.profit)}
                    </span>
                    <div
                      style={{
                        width: '70%',
                        height: `${heightPct}%`,
                        background: isPos ? '#238636' : '#da3633',
                        borderRadius: 2,
                      }}
                    />
                    <span style={{ fontSize: 11, fontWeight: 500, color: '#8b949e' }}>{d.name}</span>
                    <span style={{ fontSize: 9, color: '#6e7681' }}>{d.trades} trades</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Panel 2: Duration Distribution */}
          <div
            style={{
              border: '1px solid #30363d',
              borderRadius: 4,
              background: '#161b22',
              padding: 12,
            }}
          >
            <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 10, color: '#c9d1d9' }}>
              Trade Duration Distribution ({selectedYear})
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {durationStats.map(bucket => {
                const total = activeTrades.length || 1;
                const pct = (bucket.count / total) * 100;
                return (
                  <div key={bucket.label} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11 }}>
                    <span style={{ width: 75, color: '#8b949e' }}>{bucket.label}</span>
                    <div style={{ flex: 1, height: 14, background: '#21262d', borderRadius: 2, overflow: 'hidden' }}>
                      <div
                        style={{
                          height: '100%',
                          width: `${pct}%`,
                          background: bucket.pnl >= 0 ? '#1f6feb' : '#8957e5',
                        }}
                      />
                    </div>
                    <span style={{ width: 45, textAlign: 'right' }}>{bucket.count}</span>
                    <span style={{ width: 65, textAlign: 'right', color: bucket.pnl >= 0 ? '#3fb950' : '#f85149' }}>
                      ${Math.round(bucket.pnl)}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Panel 3: Streak Analysis */}
          <div
            style={{
              border: '1px solid #30363d',
              borderRadius: 4,
              background: '#161b22',
              padding: 12,
            }}
          >
            <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 10, color: '#c9d1d9' }}>
              Consecutive Trades & Streak Analysis
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div style={{ background: '#12161c', padding: 8, borderRadius: 4 }}>
                <div style={{ fontSize: 11, color: '#8b949e' }}>Max Consecutive Wins</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: '#3fb950', margin: '4px 0' }}>
                  {streakStats.maxWin}
                </div>
                <div style={{ fontSize: 10, color: '#8b949e' }}>
                  Single win streaks: {streakStats.winDistribution[1] || 0}
                </div>
              </div>
              <div style={{ background: '#12161c', padding: 8, borderRadius: 4 }}>
                <div style={{ fontSize: 11, color: '#8b949e' }}>Max Consecutive Losses</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: '#f85149', margin: '4px 0' }}>
                  {streakStats.maxLoss}
                </div>
                <div style={{ fontSize: 10, color: '#8b949e' }}>
                  Single loss streaks: {streakStats.lossDistribution[1] || 0}
                </div>
              </div>
            </div>
          </div>

          {/* Panel 4: Profit by Hour of Day */}
          <div
            style={{
              border: '1px solid #30363d',
              borderRadius: 4,
              background: '#161b22',
              padding: 12,
            }}
          >
            <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 10, color: '#c9d1d9' }}>
              Profit by Hour of Day (00:00 - 23:00)
            </div>
            <div style={{ display: 'flex', alignItems: 'flex-end', height: 95, gap: 2 }}>
              {hourOfDayStats.map(h => {
                const maxP = Math.max(...hourOfDayStats.map(x => Math.abs(x.profit)), 50);
                const heightPct = Math.min(100, Math.max(8, (Math.abs(h.profit) / maxP) * 100));
                const isPos = h.profit >= 0;

                return (
                  <div
                    key={h.hour}
                    title={`${h.hour}: $${Math.round(h.profit)} (${h.trades} trades)`}
                    style={{
                      flex: 1,
                      height: `${heightPct}%`,
                      background: isPos ? '#238636' : '#da3633',
                      borderRadius: 1,
                      cursor: 'pointer',
                    }}
                  />
                );
              })}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#8b949e', marginTop: 4 }}>
              <span>00h</span>
              <span>06h</span>
              <span>12h</span>
              <span>18h</span>
              <span>23h</span>
            </div>
          </div>
        </div>

        {/* Monthly Returns Heatmap Matrix (Years x Jan..Dec + Total) */}
        <div
          style={{
            border: '1px solid #30363d',
            borderRadius: 4,
            background: '#161b22',
            padding: 12,
          }}
        >
          <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 10, color: '#c9d1d9' }}>
            Monthly Returns Matrix (Jan – Dec)
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
              <thead>
                <tr style={{ background: '#12161c', borderBottom: '1px solid #30363d' }}>
                  <th style={{ padding: '6px 8px', textAlign: 'left' }}>Year</th>
                  {monthlyMatrix.months.map(m => (
                    <th key={m} style={{ padding: '6px 8px', textAlign: 'center' }}>
                      {m}
                    </th>
                  ))}
                  <th style={{ padding: '6px 8px', textAlign: 'right' }}>YTD Total</th>
                </tr>
              </thead>
              <tbody>
                {years.map(yr => {
                  const monthsData = monthlyMatrix.matrix[yr] || [];
                  const ytd = monthsData.reduce((acc, v) => acc + v, 0);

                  return (
                    <tr key={yr} style={{ borderBottom: '1px solid #21262d' }}>
                      <td style={{ padding: '6px 8px', fontWeight: 600 }}>{yr}</td>
                      {monthsData.map((val, mIdx) => {
                        const isPos = val > 0;
                        const isNeg = val < 0;
                        const bg = isPos
                          ? 'rgba(46, 160, 67, 0.18)'
                          : isNeg
                          ? 'rgba(248, 81, 73, 0.18)'
                          : 'transparent';

                        return (
                          <td
                            key={mIdx}
                            style={{
                              padding: '6px 8px',
                              textAlign: 'center',
                              background: bg,
                              color: isPos ? '#3fb950' : isNeg ? '#f85149' : '#8b949e',
                            }}
                          >
                            {val !== 0 ? `$${Math.round(val)}` : '—'}
                          </td>
                        );
                      })}
                      <td
                        style={{
                          padding: '6px 8px',
                          textAlign: 'right',
                          fontWeight: 600,
                          color: ytd >= 0 ? '#3fb950' : '#f85149',
                        }}
                      >
                        ${Math.round(ytd).toLocaleString()}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
