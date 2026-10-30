import { describe, expect, it } from 'vitest';
import { GridTestRows, type GridTestRow } from '../../../workspaces/grid_test/rows';

describe('GridTestRows deterministic behavior', () => {
  it('manual row boundaries', () => {
    const batch1 = GridTestRows.manual_batch();
    expect(batch1).toHaveLength(100);
    expect(batch1[0]).toEqual([0, 0, '0-text']);
    expect(batch1[99]).toEqual([99, 198, '99-text']);

    // Mutating batch1 should not affect batch2
    const mutableBatch = [...batch1] as GridTestRow[];
    mutableBatch[0] = [999, 999, 'mutated'];
    const batch2 = GridTestRows.manual_batch();
    expect(batch2[0]).toEqual([0, 0, '0-text']);
  });

  it('timed counter independent of manual rows', () => {
    const timed1 = GridTestRows.timed_row(1);
    expect(timed1).toEqual({
      row: [1, 2, '1-text'],
      next_counter: 2,
      change_count: 0,
    });

    // Calling manual_batch then timed_row(1) produces the same object values
    GridTestRows.manual_batch();
    const timedAfter = GridTestRows.timed_row(1);
    expect(timedAfter).toEqual(timed1);

    // Verify next counter increment
    const timed2 = GridTestRows.timed_row(timed1.next_counter);
    expect(timed2).toEqual({
      row: [2, 4, '2-text'],
      next_counter: 3,
      change_count: 0,
    });
  });

  it('timer metadata', () => {
    const intervals = GridTestRows.intervals_ms();
    expect(intervals).toEqual({
      add: 20,
      remove: 30,
      change: 40,
      count: 50,
    });
  });
});
