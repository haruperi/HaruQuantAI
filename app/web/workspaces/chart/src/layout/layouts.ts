/** TradingView-compatible layout identifiers, cells, and persisted synchronization preferences. */
export const layoutStorageKey = 'haruquantai.chart.layout.v1';
export type SyncSetting = 'symbol' | 'interval' | 'crosshair' | 'time' | 'dateRange';
export type SyncOptions = Record<SyncSetting, boolean>;
export interface LayoutSizes { columns: number[]; rows: number[] }
export interface LayoutState {
  id: string;
  active: number;
  sync: SyncOptions;
  sizes: Record<string, LayoutSizes>;
}
export interface LayoutDefinition {
  id: string;
  count: number;
  cells: number[][];
  label: string;
}
const linear = (n: number) => Array.from({ length: n }, (_, i) => i);
const rows = (top: number, bottom: number): number[][] => {
  const columns = top * bottom;
  return [
    linear(columns).map(i => Math.floor(i / (columns / top))),
    linear(columns).map(i => top + Math.floor(i / (columns / bottom))),
  ];
};
const stacked = (n: number, left = true) =>
  linear(n - 1).map(i => left ? [0, i + 1] : [i + 1, 0]);
const columns = (n: number, count: number) =>
  linear(Math.ceil(n / count)).map(row =>
    linear(count).map(col => Math.min(n - 1, row * count + col)));
const grid = (n: number) => [
  linear(n / 2).map(i => i * 2),
  linear(n / 2).map(i => i * 2 + 1),
];
const special: Record<string, number[][]> = {
  s: [[0]],
  '2-1': [[0, 2], [1, 1]],
  '1-2': [[0, 0], [1, 2]],
  '3s': stacked(3),
  '3r': stacked(3, false),
  '4s': stacked(4),
  '4s-l': stacked(4, false),
  '2-2': [[0, 1], [2, 2], [3, 3]],
  '2-2-l': [[0, 0, 1, 2], [0, 0, 1, 3]],
  '2-2-r': [[0, 2, 2, 3], [1, 2, 2, 3]],
  '5s': stacked(5),
  '5s-l': stacked(5, false),
  '2-3-l': [[0, 1, 2], [0, 1, 3], [0, 1, 4]],
  '2-3-r': [[0, 1, 2], [0, 3, 2], [0, 4, 2]],
  '7s': stacked(7),
};
export const layoutGroups: { count: number; ids: string[] }[] = [
  { count: 1, ids: ['s'] },
  { count: 2, ids: ['2h', '2v'] },
  { count: 3, ids: ['3h', '3v', '3s', '3r', '2-1', '1-2'] },
  { count: 4, ids: ['4', '4h', '4v', '1-3', '3-1', '4s', '4s-l', '2-2-l', '2-2-r', '2-2'] },
  { count: 5, ids: ['5h', '5v', '1-4', '4-1', '2-3', '3-2', '5s', '5s-l', '2-3-l', '2-3-r'] },
  { count: 6, ids: ['6', '6h', '6v', '6c', '2-4', '4-2'] },
  { count: 7, ids: ['7h', '4-3', '7s'] },
  { count: 8, ids: ['8', '8c', '8h', '8v'] },
];
function cellsFor(id: string, n: number): number[][] {
  if (special[id]) return special[id];
  if (id.endsWith('h')) return [linear(n)];
  if (id.endsWith('v')) return linear(n).map(i => [i]);
  if (id.endsWith('c')) return columns(n, 2);
  if (id.includes('-')) {
    const [top, bottom] = id.split('-').map(Number);
    return rows(top, bottom);
  }
  return grid(n);
}
export const layouts: LayoutDefinition[] = layoutGroups.flatMap(group =>
  group.ids.map(id => ({
    id,
    count: group.count,
    cells: cellsFor(id, group.count),
    label: id === 's' ? 'Single chart' : group.count + ' charts · ' + id,
  })));
export function getLayout(id: string): LayoutDefinition {
  return layouts.find(layout => layout.id === id) ?? layouts[0];
}
export const defaultLayout: LayoutState = {
  id: 's', active: 0,
  sync: { symbol: false, interval: false, crosshair: true, time: false, dateRange: false },
  sizes: {},
};
export function getLayoutSizes(id: string, saved?: LayoutSizes): LayoutSizes {
  const layout = getLayout(id);
  const dimensions = [layout.cells[0].length, layout.cells.length];
  const good = (values: number[] | undefined, count: number): values is number[] =>
    Array.isArray(values) && values.length === count &&
    values.every(n => typeof n === 'number' && Number.isFinite(n) && n >= 4 && n <= 100) &&
    Math.abs(values.reduce((total, value) => total + value, 0) - 100) < 0.1;
  return {
    columns: good(saved?.columns, dimensions[0]) ? saved!.columns : Array(dimensions[0]).fill(100 / dimensions[0]),
    rows: good(saved?.rows, dimensions[1]) ? saved!.rows : Array(dimensions[1]).fill(100 / dimensions[1]),
  };
}
export type Splitter = { axis: 'columns' | 'rows'; edge: number; start: number; end: number; key: string };
/** Dividers exist only where adjacent chart cells belong to different panes. */
export function layoutSplitters(cells: number[][]): Splitter[] {
  const result: Splitter[] = [];
  const height = cells.length, width = cells[0].length;
  const appendRuns = (axis: 'columns' | 'rows', edge: number, flags: boolean[]) => {
    let start = -1;
    for (let n = 0; n <= flags.length; n++) {
      if (n < flags.length && flags[n]) {
        if (start < 0) start = n;
      } else if (start >= 0) {
        result.push({ axis, edge, start, end: n, key: axis + ':' + edge + ':' + start });
        start = -1;
      }
    }
  };
  for (let col = 1; col < width; col++)
    appendRuns('columns', col, cells.map(row => row[col - 1] !== row[col]));
  for (let row = 1; row < height; row++)
    appendRuns('rows', row, Array.from({ length: width }, (_, col) =>
      cells[row - 1][col] !== cells[row][col]));
  return result;
}
export function resizeTracks(sizes: LayoutSizes, axis: 'columns' | 'rows', edge: number, delta: number): LayoutSizes {
  const tracks = [...sizes[axis]];
  const minimum = Math.min(8, 80 / tracks.length);
  const left = tracks[edge - 1], right = tracks[edge];
  if (left === undefined || right === undefined) return sizes;
  const adjustment = Math.max(minimum - left, Math.min(right - minimum, delta));
  tracks[edge - 1] = left + adjustment;
  tracks[edge] = right - adjustment;
  return { ...sizes, [axis]: tracks };
}
export function readLayout(storage: Pick<Storage, 'getItem'>): LayoutState {
  try {
    const raw = storage.getItem(layoutStorageKey);
    if (!raw) return { ...defaultLayout, sync: { ...defaultLayout.sync }, sizes: {} };
    const value: unknown = JSON.parse(raw);
    if (!value || typeof value !== 'object' || Array.isArray(value))
      return { ...defaultLayout, sync: { ...defaultLayout.sync }, sizes: {} };
    const data = value as Record<string, unknown>;
    if (typeof data.id !== 'string' || !layouts.some(l => l.id === data.id))
      return { ...defaultLayout, sync: { ...defaultLayout.sync } };
    const count = getLayout(data.id).count;
    const settings = data.sync && typeof data.sync === 'object' && !Array.isArray(data.sync)
      ? data.sync as Record<string, unknown> : {};
    const sync = { ...defaultLayout.sync };
    for (const name of Object.keys(sync) as SyncSetting[])
      if (typeof settings[name] === 'boolean') sync[name] = settings[name] as boolean;
    const sizes: Record<string, LayoutSizes> = {};
    if (data.sizes && typeof data.sizes === 'object' && !Array.isArray(data.sizes)) {
      for (const [key, value] of Object.entries(data.sizes)) {
        if (!layouts.some(layout => layout.id === key) || !value || typeof value !== 'object' || Array.isArray(value)) continue;
        const maybe = value as Partial<LayoutSizes>;
        const dimensions = getLayout(key).cells;
        if (Array.isArray(maybe.columns) && maybe.columns.length === dimensions[0].length &&
            Array.isArray(maybe.rows) && maybe.rows.length === dimensions.length) {
          sizes[key] = getLayoutSizes(key, maybe as LayoutSizes);
        }
      }
    }
    return { id: data.id, active: Number.isInteger(data.active) && Number(data.active) >= 0
      && Number(data.active) < count ? Number(data.active) : 0, sync, sizes };
  } catch {
    return { ...defaultLayout, sync: { ...defaultLayout.sync } };
  }
}
