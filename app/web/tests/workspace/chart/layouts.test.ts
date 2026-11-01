import { expect, it } from 'vitest';
import { defaultLayout, getLayout, getLayoutSizes, layoutSplitters, layouts, resizeTracks, layoutStorageKey, readLayout } from '../../../workspaces/chart/src/layout/layouts';

it('defines rectangular non-overlapping 1–8-chart layouts with exact chart indices', () => {
  expect(layouts.length).toBeGreaterThan(30);
  for (const layout of layouts) {
    const { count, cells, id } = layout;
    expect(count).toBeGreaterThanOrEqual(1);
    expect(count).toBeLessThanOrEqual(8);
    expect(getLayout(id)).toBe(layout);
    const columns = cells[0].length;
    expect(cells.every(row => row.length === columns)).toBe(true);
    const values = cells.flat();
    expect(new Set(values)).toEqual(new Set(Array.from({ length: count }, (_, i) => i)));
    // CSS grid areas must be a single rectangle per chart.
    for (let id = 0; id < count; id++) {
      const positions = cells.flatMap((row, y) =>
        row.map((value, x) => ({ value, x, y })).filter(p => p.value === id));
      const xs = positions.map(p => p.x), ys = positions.map(p => p.y);
      const minX = Math.min(...xs), maxX = Math.max(...xs);
      const minY = Math.min(...ys), maxY = Math.max(...ys);
      expect(positions).toHaveLength((maxX - minX + 1) * (maxY - minY + 1));
    }
  }
});

it('retains TradingView layout keys and example arrangements', () => {
  expect(getLayout('s').cells).toEqual([[0]]);
  expect(getLayout('2h').cells).toEqual([[0, 1]]);
  expect(getLayout('2v').cells).toEqual([[0], [1]]);
  expect(getLayout('4').cells).toEqual([[0, 2], [1, 3]]);
  expect(getLayout('6c').cells).toEqual([[0, 1], [2, 3], [4, 5]]);
  expect(getLayout('8').cells).toEqual([[0, 2, 4, 6], [1, 3, 5, 7]]);
});

it('reads sync settings and active pane safely, with backward-compatible defaults', () => {
  const from = (payload: unknown) =>
    readLayout({ getItem: key => key === layoutStorageKey ? JSON.stringify(payload) : null });
  expect(readLayout({ getItem: () => null })).toEqual(defaultLayout);
  expect(from({ id: '4', active: 2, sync: { symbol: true, crosshair: false } })).toEqual({
    id: '4', active: 2,
    sync: { symbol: true, interval: false, crosshair: false, time: false, dateRange: false },
    sizes: {},
  });
  expect(from({ id: '2h', active: 6, sync: { interval: 'wrong' } }).active).toBe(0);
  expect(from({ id: '__invalid__', active: 0 })).toEqual(defaultLayout);
  expect(readLayout({ getItem: () => '{' })).toEqual(defaultLayout);
});

it('finds grid boundaries and keeps drag resizing bounded and normalized', () => {
  const cells = getLayout('4').cells;
  const splits = layoutSplitters(cells);
  expect(splits.some(split => split.axis === 'columns' && split.edge === 1)).toBe(true);
  expect(splits.some(split => split.axis === 'rows' && split.edge === 1)).toBe(true);
  const original = getLayoutSizes('4');
  const changed = resizeTracks(original, 'columns', 1, 18);
  expect(changed.columns[0]).toBeCloseTo(68);
  expect(changed.columns[1]).toBeCloseTo(32);
  expect(changed.columns.reduce((a, b) => a + b, 0)).toBeCloseTo(100);
  const clamped = resizeTracks(original, 'rows', 1, -999);
  expect(clamped.rows[0]).toBeGreaterThanOrEqual(8);
  expect(clamped.rows[1]).toBeLessThanOrEqual(92);
  const restored = readLayout({ getItem: () => JSON.stringify({
    id: '4', active: 1, sync: defaultLayout.sync, sizes: { '4': changed },
  }) });
  expect(restored.sizes['4'].columns).toEqual(changed.columns);
  expect(getLayoutSizes('4', restored.sizes['4'])).toEqual(changed);
});
