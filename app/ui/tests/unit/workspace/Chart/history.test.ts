import { it, expect } from 'vitest';
import { createChartStore } from '../../../../src/workspace/Chart/src/store/chartStore';
it('undo and redo restore document changes but not quote-driven orders', () => {
  const s = createChartStore();
  s.getState().settings({ style: 'Line' });
  s.getState().settings({ symbol: 'BTCUSDT' });
  s.getState().undo();
  expect(s.getState().chart.symbol).toBe('XAUUSD');
  s.getState().undo();
  expect(s.getState().chart.style).toBe('Candles');
  s.getState().undo(true);
  expect(s.getState().chart.style).toBe('Line');
  s.getState().settings({ title: 'New branch' });
  expect(s.getState().history.future).toEqual([]);
});
it('history is bounded', () => {
  const s = createChartStore();
  for (let i = 0; i < 110; i++) s.getState().settings({ title: String(i) });
  expect(s.getState().history.past).toHaveLength(100);
});
