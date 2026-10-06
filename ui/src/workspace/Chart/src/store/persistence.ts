import type { ChartStore } from './chartStore';
import { intervals, chartStyles, toolIds, indicatorIds, type Persisted } from '../types';
import { symbols } from '../feed/symbols';
import { tools } from '../tools/catalog';
export const storageKey = 'haruquantai.chart.v1';
const object = (v: unknown): v is Record<string, unknown> =>
  typeof v === 'object' && v !== null && !Array.isArray(v);
const finite = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v);
const text = (v: unknown): v is string => typeof v === 'string';
export function decode(raw: string): Persisted {
  const root: unknown = JSON.parse(raw);
  if (!object(root) || root.version !== 1 || !object(root.state))
    throw new Error('Unsupported chart storage version.');
  const s = root.state,
    c = s.chart;
  if (
    !object(c) ||
    !symbols.some((x) => x.id === c.symbol) ||
    !intervals.some((x) => x === c.interval) ||
    !chartStyles.some((x) => x === c.style) ||
    !['linear', 'log', 'percent', 'indexed'].includes(String(c.scale)) ||
    !['dark', 'light'].includes(String(c.theme)) ||
    !text(c.title) ||
    !text(c.timezone) ||
    !/^(UTC([+-]([1-9]|1[0-2]))?|Exchange|Local)$/.test(c.timezone) ||
    !text(c.range) ||
    !['1D', '5D', '1M', '3M', '6M', 'YTD', '1Y', '5Y', 'All'].includes(c.range) ||
    !finite(c.precision) ||
    c.precision < 0 ||
    c.precision > 8 ||
    !Number.isInteger(c.precision) ||
    !finite(c.paneHeight) ||
    c.paneHeight < 40 ||
    c.paneHeight > 300
  )
    throw new Error('Invalid chart settings.');
  for (const k of [
    'reverse',
    'auto',
    'countdown',
    'magnet',
    'volume',
    'previousClose',
    'tooltip',
    'gaps',
    'sessions',
    'minimap',
  ])
    if (typeof c[k] !== 'boolean') throw new Error('Invalid chart toggle.');
  if (
    !object(s.drawings) ||
    !Array.isArray(s.indicators) ||
    !Array.isArray(s.alerts) ||
    !Array.isArray(s.favorites) ||
    !Array.isArray(s.recents)
  )
    throw new Error('Invalid chart document.');
  for (const [scope, list] of Object.entries(s.drawings)) {
    const [symbol, interval] = scope.split(':');
    if (!symbols.some((s) => s.id === symbol) || !intervals.some((i) => i === interval))
      throw new Error('Invalid drawing scope.');
    if (!Array.isArray(list)) throw new Error('Invalid drawing collection.');
    for (const d of list) {
      if (
        !object(d) ||
        !text(d.id) ||
        !toolIds.some((x) => x === d.tool) ||
        !Array.isArray(d.points) ||
        d.points.length < 1 ||
        d.points.length > 10000 ||
        d.points.some(
          (p: unknown) => !object(p) || !finite(p.time) || !finite(p.price) || p.price <= 0,
        ) ||
        !text(d.color) ||
        !text(d.text) ||
        !finite(d.width) ||
        d.width <= 0 ||
        !finite(d.opacity) ||
        d.opacity < 0 ||
        d.opacity > 1
      )
        throw new Error('Invalid drawing.');
      const tool = tools[d.tool as keyof typeof tools];
      if (d.points.length < (tool.anchors || (d.tool === 'Polygon' ? 3 : 2)))
        throw new Error('Incomplete drawing anchors.');
      for (const k of ['dash', 'locked', 'hidden', 'extendLeft', 'extendRight'])
        if (typeof d[k] !== 'boolean') throw new Error('Invalid drawing setting.');
    }
  }
  for (const i of s.indicators)
    if (
      !object(i) ||
      !text(i.id) ||
      !indicatorIds.some((x) => x === i.kind) ||
      !['period', 'slow', 'signal', 'deviation', 'width', 'opacity'].every(
        (k) => finite(i[k]) && Number(i[k]) > 0,
      ) ||
      !text(i.color)
    )
      throw new Error('Invalid indicator.');
  for (const a of s.alerts)
    if (
      !object(a) ||
      !text(a.id) ||
      !symbols.some((x) => x.id === a.symbol) ||
      !['up', 'down', 'enter', 'exit'].includes(String(a.condition)) ||
      !['value', 'upper', 'expires', 'triggers'].every((k) => finite(a[k])) ||
      typeof a.once !== 'boolean' ||
      typeof a.active !== 'boolean'
    )
      throw new Error('Invalid alert.');
  if (
    s.favorites.some((x: unknown) => !toolIds.some((t) => t === x)) ||
    s.recents.some((x: unknown) => !symbols.some((t) => t.id === x))
  )
    throw new Error('Invalid chart preferences.');
  const validated = s as unknown as Persisted;
  return {
    chart: validated.chart,
    drawings: validated.drawings,
    indicators: validated.indicators,
    alerts: validated.alerts,
    favorites: validated.favorites,
    recents: validated.recents,
  };
}
export function persisted(store: ChartStore): Persisted {
  const s = store.getState();
  return {
    chart: s.chart,
    drawings: s.drawings,
    indicators: s.indicators,
    alerts: s.alerts,
    favorites: s.favorites,
    recents: s.recents,
  };
}
export function connectPersistence(store: ChartStore, storage: Storage): () => void {
  let writable = true;
  try {
    const raw = storage.getItem(storageKey);
    if (raw) store.setState(decode(raw));
  } catch (error) {
    writable = false;
    store.getState().setUI({
      saved: 'Storage needs attention',
      toast:
        error instanceof Error ? error.message : 'Cannot read storage. Original data preserved.',
    });
  }
  let previous = JSON.stringify(persisted(store));
  let timer: ReturnType<typeof setTimeout> | undefined;
  const save = () => {
    if (!writable) return;
    try {
      storage.setItem(storageKey, JSON.stringify({ version: 1, state: persisted(store) }));
      store.getState().setUI({ saved: 'Saved locally' });
    } catch {
      store.getState().setUI({ saved: 'Not saved — storage unavailable' });
    }
  };
  const unsubscribe = store.subscribe(() => {
    const next = JSON.stringify(persisted(store));
    if (next === previous) return;
    previous = next;
    if (!writable) return;
    clearTimeout(timer);
    timer = setTimeout(save, 250);
    store.getState().setUI({ saved: 'Saving…' });
  });
  return () => {
    unsubscribe();
    clearTimeout(timer);
    save();
  };
}
