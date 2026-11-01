import {
  tools,
  lineSections,
  fibonacciSections,
  patternSections,
  forecastingSections,
  shapeSections,
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
it('persists magnet options and upgrades older chart documents without losing drawings', () => {
  const state = persisted(createChartStore());
  state.chart.magnet = true;
  state.chart.magnetStrength = 'strong';
  state.chart.snapToIndicators = true;
  expect(decode(JSON.stringify({ version: 1, state }))).toEqual(state);

  const legacy = structuredClone(state);
  delete (legacy.chart as Partial<typeof legacy.chart>).magnetStrength;
  delete (legacy.chart as Partial<typeof legacy.chart>).snapToIndicators;
  const decoded = decode(JSON.stringify({ version: 1, state: legacy }));
  expect(decoded.chart).toMatchObject({ magnet: true, magnetStrength: 'weak', snapToIndicators: false });

  const invalid = structuredClone(state);
  (invalid.chart as unknown as Record<string, unknown>).magnetStrength = 'extra';
  expect(() => decode(JSON.stringify({ version: 1, state: invalid }))).toThrow('Invalid magnet strength.');
  (invalid.chart as unknown as Record<string, unknown>).magnetStrength = 'weak';
  (invalid.chart as unknown as Record<string, unknown>).snapToIndicators = 'yes';
  expect(() => decode(JSON.stringify({ version: 1, state: invalid }))).toThrow('Invalid indicator snapping setting.');
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
  const ids = [
    ...lineSections,
    ...fibonacciSections,
    ...patternSections,
    ...forecastingSections,
    ...shapeSections,
  ].flatMap((section) => section.ids);
  const state = persisted(store);
  state.drawings['XAUUSD:3m'] = ids.map((tool) => ({
    id: tool,
    tool,
    points: Array.from({ length: tools[tool].anchors || (tool === 'Polygon' ? 3 : 2) }, (_, i) => ({
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

it('snapshot decoding preserves candles and rejects malformed, unordered and oversized snapshots', () => {
  const state = persisted(createChartStore());
  const bar = { time: 1000, open: 10, high: 12, low: 8, close: 11, volume: 20 };
  const item = {
    id: 'snapshot',
    tool: 'BarsPattern' as const,
    points: [
      { time: 1000, price: 10 },
      { time: 2000, price: 12 },
      { time: 3000, price: 20 },
    ],
    sourceBars: [bar],
    color: '#2962ff',
    width: 2,
    dash: false,
    opacity: 1,
    text: '',
    locked: false,
    hidden: false,
    extendLeft: false,
    extendRight: false,
  };
  state.drawings['XAUUSD:3m'] = [item];
  expect(decode(JSON.stringify({ version: 1, state }))).toEqual(state);
  for (const sourceBars of [
    [{ ...bar, volume: -1 }],
    [{ ...bar, low: 11 }],
    [bar, bar],
    Array.from({ length: 513 }, (_, i) => ({ ...bar, time: i })),
  ]) {
    state.drawings['XAUUSD:3m'] = [{ ...item, sourceBars }];
    expect(() => decode(JSON.stringify({ version: 1, state }))).toThrow(/snapshot/);
  }
  state.drawings['XAUUSD:3m'] = [{ ...item, tool: 'TrendLine' }];
  expect(() => decode(JSON.stringify({ version: 1, state }))).toThrow(/snapshot/);
});

it('position sizing remains optional and rejects invalid account and risk settings', () => {
  const state = persisted(createChartStore());
  const item = {
    id: 'position',
    tool: 'LongPosition' as const,
    points: [
      { time: 0, price: 100 },
      { time: 0, price: 90 },
      { time: 0, price: 120 },
      { time: 1000, price: 100 },
    ],
    positionSizing: { accountSize: 1000, riskPercent: 1 },
    color: '#2962ff',
    width: 2,
    dash: false,
    opacity: 1,
    text: '',
    locked: false,
    hidden: false,
    extendLeft: false,
    extendRight: false,
  };
  state.drawings['XAUUSD:3m'] = [item];
  expect(decode(JSON.stringify({ version: 1, state }))).toEqual(state);
  for (const positionSizing of [
    { accountSize: 0, riskPercent: 1 },
    { accountSize: 1000, riskPercent: 101 },
    { accountSize: 1e13, riskPercent: 1 },
  ]) {
    state.drawings['XAUUSD:3m'] = [{ ...item, positionSizing }];
    expect(() => decode(JSON.stringify({ version: 1, state }))).toThrow(/position sizing/);
  }
});
