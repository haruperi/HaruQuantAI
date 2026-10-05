import { it, expect } from 'vitest';
import { createChartStore } from '../../../../app/workspace/Chart/src/store/chartStore';
import {
  decode,
  persisted,
  connectPersistence,
  storageKey,
} from '../../../../app/workspace/Chart/src/store/persistence';
it('round-trips the chart document and rejects malformed/future versions', () => {
  const s = createChartStore(),
    state = persisted(s);
  expect(decode(JSON.stringify({ version: 1, state }))).toEqual(state);
  expect(() => decode('{"version":9}')).toThrow();
  expect(() =>
    decode(
      JSON.stringify({ version: 1, state: { ...state, chart: { ...state.chart, precision: -1 } } }),
    ),
  ).toThrow();
});
it('preserves unknown data instead of overwriting it', () => {
  const map = new Map([[storageKey, '{"version":99}']]);
  const storage = {
    getItem: (k: string) => map.get(k) ?? null,
    setItem: (k: string, v: string) => {
      map.set(k, v);
    },
    removeItem: (k: string) => map.delete(k),
    clear: () => map.clear(),
    key: () => null,
    length: 1,
  };
  const s = createChartStore();
  const stop = connectPersistence(s, storage);
  s.getState().settings({ title: 'edit' });
  stop();
  expect(map.get(storageKey)).toBe('{"version":99}');
  expect(s.getState().ui.saved).toBe('Storage needs attention');
});
