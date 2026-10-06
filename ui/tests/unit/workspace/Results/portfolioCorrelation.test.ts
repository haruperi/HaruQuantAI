import { describe, it, expect } from 'vitest';
import {
  calculatePearsonCorrelation,
  extractReturnsSeries,
} from '../../../../app/plugins/databank/ProjectDatabanks/FilterByCorrelationModal';
import { strategies } from '../../../../app/plugins/databank/fixtures';

describe('Portfolio Correlation Engine & Overlapping Trades', () => {
  it('generates a valid symmetric correlation matrix with 1.0 on diagonal', () => {
    const list = strategies.slice(0, 3);
    const seriesList = list.map(s => extractReturnsSeries(s, 'Day'));

    const matrix: number[][] = [];
    for (let i = 0; i < list.length; i++) {
      const row: number[] = [];
      for (let j = 0; j < list.length; j++) {
        if (i === j) {
          row.push(1.0);
        } else {
          row.push(calculatePearsonCorrelation(seriesList[i], seriesList[j]));
        }
      }
      matrix.push(row);
    }

    expect(matrix.length).toBe(3);
    for (let i = 0; i < 3; i++) {
      expect(matrix[i][i]).toBe(1.0);
      for (let j = 0; j < 3; j++) {
        expect(matrix[i][j]).toBeCloseTo(matrix[j][i], 5);
      }
    }
  });

  it('detects concurrent overlapping trade time windows', () => {
    const tradeA = {
      entryTime: '2025-01-01T10:00:00Z',
      exitTime: '2025-01-02T10:00:00Z',
    };
    const tradeB = {
      entryTime: '2025-01-01T14:00:00Z',
      exitTime: '2025-01-03T10:00:00Z',
    };
    const tradeC = {
      entryTime: '2025-01-05T10:00:00Z',
      exitTime: '2025-01-06T10:00:00Z',
    };

    const isOverlap = (
      t1: { entryTime: string; exitTime: string },
      t2: { entryTime: string; exitTime: string }
    ) => {
      const s1 = new Date(t1.entryTime).getTime();
      const e1 = new Date(t1.exitTime).getTime();
      const s2 = new Date(t2.entryTime).getTime();
      const e2 = new Date(t2.exitTime).getTime();
      return Math.max(s1, s2) < Math.min(e1, e2);
    };

    expect(isOverlap(tradeA, tradeB)).toBe(true);
    expect(isOverlap(tradeA, tradeC)).toBe(false);
  });
});
