import { describe, expect, it } from 'vitest';

import { GRID_TEST_COLUMNS, GRID_TEST_MAX_ROWS, buildGridTestRows } from '../../../../app/workspace/GridTest/GridTestWorkspace';

describe('HaruQuantAI grid test workspace', () => {
  it('builds a deterministic seeded row set', () => {
    expect(buildGridTestRows(100)).toEqual(buildGridTestRows(100));
    expect(buildGridTestRows(100, 7)).not.toEqual(buildGridTestRows(100, 42));
  });

  it('clamps requested row counts to the safe bound', () => {
    expect(buildGridTestRows(-5)).toHaveLength(0);
    expect(buildGridTestRows(2.9)).toHaveLength(2);
    expect(buildGridTestRows(9999)).toHaveLength(GRID_TEST_MAX_ROWS);
  });

  it('keeps every row consistent with the column model', () => {
    const rows = buildGridTestRows(24);
    expect(GRID_TEST_COLUMNS).toEqual(['Row', 'Instrument', 'Session', 'Bid', 'Ask', 'Spread', 'Tick #', 'Status']);
    expect(rows.map(row => row.row)).toEqual(Array.from({ length: 24 }, (_, index) => index + 1));
    for (const row of rows) {
      expect(row.bid).toBeGreaterThanOrEqual(1);
      expect(row.ask).toBeGreaterThan(row.bid);
      expect(row.spread).toBeCloseTo(row.ask - row.bid, 5);
      expect(['Live', 'Delayed', 'Closed']).toContain(row.status);
    }
  });
});
