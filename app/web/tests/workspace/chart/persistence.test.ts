import {
  tools,
  lineSections,
  fibonacciSections,
  patternSections,
} from '../../../workspaces/chart/src/tools/catalog';
import { it, expect } from 'vitest';
import { createChartStore } from '../../../workspaces/chart/src/store/chartStore';
import {
  decode,
  persisted,
  connectPersistence,
  storageKey,
} from '../../../workspaces/chart/src/store/persistence';
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

it('round-trips every sectioned drawing menu tool with all anchors and favorites', () => {
  const store = createChartStore();
  const ids = [...lineSections, ...fibonacciSections, ...patternSections].flatMap(
    (section) => section.ids,
  );
  const state = persisted(store);
  state.drawings['XAUUSD:3m'] = ids.map((tool) => ({
    id: tool,
    tool,
    points: Array.from({ length: tools[tool].anchors }, (_, i) => ({
      time: 1000 + i * 60000,
      price: 100 + i,
    })),
    color: '#2962ff',
    width: 2,
    dash: false,
    opacity: 1,
    text: 'round trip',
    locked: false,
    hidden: false,
    extendLeft: true,
    extendRight: true,
  }));
  state.favorites = ids;
  expect(decode(JSON.stringify({ version: 1, state }))).toEqual(state);
});
