import React from 'react';
import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import {
  GRID_TEST_COLUMNS,
  GridTestWorkspace,
} from '../../../workspaces/grid_test/GridTestWorkspace';
import { GridTestRows } from '../../../workspaces/grid_test/rows';

describe('HaruQuantAI grid test workspace harness', () => {
  it('conforms to the 3-column donor model and initial batch', () => {
    expect(GRID_TEST_COLUMNS).toEqual(['Index', 'Multiplier (x2)', 'Text']);

    const batch = GridTestRows.manual_batch();
    expect(batch).toHaveLength(100);
    expect(batch[0]).toEqual([0, 0, '0-text']);
    expect(batch[50]).toEqual([50, 100, '50-text']);
    expect(batch[99]).toEqual([99, 198, '99-text']);
  });

  it('renders initial manual batch and donor control buttons', () => {
    const html = renderToString(React.createElement(GridTestWorkspace));

    // Header and info panel
    expect(html).toContain('Grid test');
    expect(html).toContain('Rows in grid:');
    expect(html).toContain('100');

    // Donor table container and headers
    expect(html).toContain('id="testGrid"');
    expect(html).toContain('Index');
    expect(html).toContain('Multiplier (x2)');
    expect(html).toContain('Text');

    // Donor control button IDs
    expect(html).toContain('id="buttonStartStopTest-64a"');
    expect(html).toContain('id="buttonSelectAll-64b"');
    expect(html).toContain('id="buttonSelectNone-64c"');
    expect(html).toContain('id="buttonClear-64d"');
    expect(html).toContain('id="buttonAdd100Rows-64e"');
  });

  it('generates independent timed rows without affecting manual batches', () => {
    const timed1 = GridTestRows.timed_row(1);
    expect(timed1.row).toEqual([1, 2, '1-text']);
    expect(timed1.next_counter).toBe(2);
    expect(timed1.change_count).toBe(0);

    const timed2 = GridTestRows.timed_row(timed1.next_counter);
    expect(timed2.row).toEqual([2, 4, '2-text']);
    expect(timed2.next_counter).toBe(3);

    // Manual batch should remain pristine
    const manual = GridTestRows.manual_batch();
    expect(manual[0]).toEqual([0, 0, '0-text']);
    expect(manual).toHaveLength(100);
  });
});
