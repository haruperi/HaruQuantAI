import React, { useMemo, useState } from 'react';
import { Award, CheckCircle2, Grid, HelpCircle, XCircle } from 'lucide-react';
import { Button } from '../../components/ui';

interface MatrixCell {
  isPct: number;
  runs: number;
  wfe: number; // Walk Forward Efficiency %
  isProfit: number;
  oosProfit: number;
  passed: boolean;
}

export const WalkForwardMatrixView: React.FC = () => {
  const isValues = [20, 25, 30, 35, 40];
  const runValues = [5, 8, 10, 12, 15];

  const [selectedCell, setSelectedCell] = useState<MatrixCell | null>(null);

  // Deterministic matrix evaluation data
  const matrixData: MatrixCell[][] = useMemo(() => {
    return isValues.map((isPct) =>
      runValues.map((runs) => {
        // Deterministic synthetic WFE based on parameters
        const base = 52 + (isPct - 25) * 1.8 + (12 - Math.abs(runs - 10)) * 2.2;
        const wfe = Math.round(Math.min(96, Math.max(28, base)));
        const passed = wfe >= 50;
        const isProfit = Math.round(24000 * (isPct / 30));
        const oosProfit = Math.round(isProfit * (wfe / 100) * 0.85);

        return {
          isPct,
          runs,
          wfe,
          isProfit,
          oosProfit,
          passed,
        };
      })
    );
  }, []);

  const totalCells = isValues.length * runValues.length;
  const passedCells = matrixData.flat().filter((c) => c.passed).length;
  const avgWfe = Math.round(
    matrixData.flat().reduce((acc, c) => acc + c.wfe, 0) / totalCells
  );

  return (
    <div className="wf-matrix-container" style={{ background: 'var(--bg-card)', borderRadius: 8, padding: 18, border: '1px solid var(--border)' }}>
      {/* Header Summary */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <strong style={{ fontSize: '1rem', display: 'flex', alignItems: 'center', gap: 6 }}>
            <Grid size={18} color="var(--accent)" /> Walk-Forward Matrix Stability Heatmap
          </strong>
          <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
            Tests robustness across multiple In-Sample training ratios and Out-of-Sample reoptimization windows
          </span>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <div className="badge" style={{ background: 'rgba(74, 222, 128, 0.15)', color: '#4ade80', padding: '6px 12px', fontSize: '0.82rem', fontWeight: 600 }}>
            Pass Rate: {passedCells} / {totalCells} ({Math.round((passedCells / totalCells) * 100)}%)
          </div>
          <div className="badge" style={{ background: 'rgba(48, 183, 232, 0.15)', color: '#30b7e8', padding: '6px 12px', fontSize: '0.82rem', fontWeight: 600 }}>
            Avg WFE: {avgWfe}%
          </div>
        </div>
      </div>

      {/* 2D Matrix Table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'center', fontSize: '0.84rem' }}>
          <thead>
            <tr>
              <th style={{ padding: '8px 12px', border: '1px solid var(--border)', background: 'var(--bg-secondary)', color: 'var(--muted)' }}>
                IS % \ Runs
              </th>
              {runValues.map((runs) => (
                <th key={runs} style={{ padding: '8px 12px', border: '1px solid var(--border)', background: 'var(--bg-secondary)', color: 'var(--text)' }}>
                  {runs} Runs
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrixData.map((row, rowIdx) => {
              const isPct = isValues[rowIdx];
              return (
                <tr key={isPct}>
                  <td style={{ padding: '8px 12px', border: '1px solid var(--border)', background: 'var(--bg-secondary)', fontWeight: 600 }}>
                    {isPct}% IS
                  </td>
                  {row.map((cell) => {
                    const isSelected =
                      selectedCell?.isPct === cell.isPct && selectedCell?.runs === cell.runs;

                    // Color gradient based on WFE score
                    let bgColor = 'rgba(239, 68, 68, 0.15)';
                    let textColor = '#f87171';
                    let borderColor = 'rgba(239, 68, 68, 0.3)';

                    if (cell.wfe >= 65) {
                      bgColor = 'rgba(74, 222, 128, 0.18)';
                      textColor = '#4ade80';
                      borderColor = 'rgba(74, 222, 128, 0.4)';
                    } else if (cell.wfe >= 50) {
                      bgColor = 'rgba(234, 179, 8, 0.18)';
                      textColor = '#facc15';
                      borderColor = 'rgba(234, 179, 8, 0.4)';
                    }

                    return (
                      <td
                        key={cell.runs}
                        onClick={() => setSelectedCell(cell)}
                        style={{
                          padding: '10px 14px',
                          border: isSelected ? '2px solid var(--accent)' : `1px solid ${borderColor}`,
                          background: isSelected ? 'rgba(48, 183, 232, 0.25)' : bgColor,
                          color: textColor,
                          cursor: 'pointer',
                          fontWeight: 700,
                          transition: 'transform 0.1s ease',
                        }}
                      >
                        <div>{cell.wfe}%</div>
                        <small style={{ fontSize: '0.68rem', opacity: 0.8, fontWeight: 400 }}>
                          {cell.passed ? 'PASSED' : 'FAILED'}
                        </small>
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Selected Cell Inspection Drawer */}
      {selectedCell ? (
        <div style={{ marginTop: 14, padding: 12, borderRadius: 6, background: 'var(--bg-secondary)', border: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {selectedCell.passed ? (
              <CheckCircle2 size={20} color="#4ade80" />
            ) : (
              <XCircle size={20} color="#f87171" />
            )}
            <div>
              <strong style={{ fontSize: '0.9rem' }}>
                Window: {selectedCell.isPct}% In-Sample · {selectedCell.runs} Out-of-Sample Runs
              </strong>
              <div style={{ fontSize: '0.78rem', color: 'var(--muted)', display: 'flex', gap: 14, marginTop: 2 }}>
                <span>WFE: <strong style={{ color: selectedCell.passed ? '#4ade80' : '#f87171' }}>{selectedCell.wfe}%</strong></span>
                <span>IS Profit: <strong>${selectedCell.isProfit.toLocaleString()}</strong></span>
                <span>OOS Profit: <strong>${selectedCell.oosProfit.toLocaleString()}</strong></span>
                <span>Efficiency: <strong>{selectedCell.wfe >= 60 ? 'Robust Plateau' : selectedCell.wfe >= 50 ? 'Acceptable' : 'Overfitted'}</strong></span>
              </div>
            </div>
          </div>
          <Button style={{ padding: '3px 10px', fontSize: '0.78rem' }} onClick={() => setSelectedCell(null)}>
            Close Details
          </Button>
        </div>
      ) : (
        <p style={{ margin: '10px 0 0', fontSize: '0.76rem', color: 'var(--muted)', textAlign: 'center' }}>
          Tip: Click any cell in the Walk-Forward matrix to inspect detailed In-Sample vs Out-of-Sample metrics.
        </p>
      )}
    </div>
  );
};
