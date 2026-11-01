import type { Tool, Primitive, Projection } from './types';
import type { Drawing, XY } from '../types';
import { line, path, label } from './geometry';

function channel(d: Drawing, p: Projection, disjoint = false, flat = false): Primitive[] {
  const points = d.points.map(p.point);
  const a = points[0] ?? { x: 0, y: 0 },
    b = points[1] ?? a,
    c = points[2] ?? b;
  const start: XY = disjoint ? c : { x: a.x, y: c.y };
  if (!disjoint && !flat && b.x !== a.x) start.y = c.y - ((b.y - a.y) * (c.x - a.x)) / (b.x - a.x);
  if (!disjoint && !flat && b.x === a.x) start.x = c.x;
  const end = { x: start.x + b.x - a.x, y: flat ? start.y : start.y + b.y - a.y };
  const middleA = { x: (a.x + start.x) / 2, y: (a.y + start.y) / 2 };
  const middleB = { x: (b.x + end.x) / 2, y: (b.y + end.y) / 2 };
  return [
    path([a, b, end, start], true, true),
    line(a, b, d.extendLeft, d.extendRight, p.width, p.height),
    line(start, end, d.extendLeft, d.extendRight, p.width, p.height),
    line(middleA, middleB, d.extendLeft, d.extendRight, p.width, p.height),
  ];
}
export const ParallelChannel: Tool = {
  label: 'Parallel channel',
  anchors: 3,
  group: 'Trend',
  build: (d, p) => channel(d, p),
};
export const FlatTopBottom: Tool = {
  label: 'Flat top/bottom',
  anchors: 3,
  group: 'Trend',
  build: (d, p) => channel(d, p, false, true),
};
export const DisjointChannel: Tool = {
  label: 'Disjoint channel',
  anchors: 3,
  group: 'Trend',
  build: (d, p) => channel(d, p, true),
};
export const RegressionTrend: Tool = {
  label: 'Regression trend',
  anchors: 2,
  group: 'Trend',
  build: (d, p) => {
    const first = d.points[0] ?? { time: 0, price: 1 },
      last = d.points[1] ?? first;
    const bars = (p.bars ?? []).filter(
      (bar) =>
        bar.time >= Math.min(first.time, last.time) && bar.time <= Math.max(first.time, last.time),
    );
    if (bars.length < 2) return [label(p.point(first), 'Regression: select at least 2 candles')];
    const n = bars.length,
      meanX = (n - 1) / 2,
      meanY = bars.reduce((sum, bar) => sum + bar.close, 0) / n;
    let numerator = 0,
      denominator = 0;
    bars.forEach((bar, i) => {
      numerator += (i - meanX) * (bar.close - meanY);
      denominator += (i - meanX) ** 2;
    });
    const slope = numerator / denominator;
    const fitted = (i: number) => meanY + slope * (i - meanX);
    if (fitted(0) <= 0 || fitted(n - 1) <= 0)
      return [label(p.point(first), 'Regression: fitted prices must be positive')];
    const deviation =
      Math.sqrt(bars.reduce((sum, bar, i) => sum + (bar.close - fitted(i)) ** 2, 0) / n) * 2;
    const a = p.point({ time: bars[0].time, price: fitted(0) });
    const b = p.point({ time: bars[n - 1].time, price: fitted(n - 1) });
    const upA = p.point({ time: bars[0].time, price: fitted(0) + deviation });
    const upB = p.point({ time: bars[n - 1].time, price: fitted(n - 1) + deviation });
    const downA = p.point({
      time: bars[0].time,
      price: Math.max(Number.EPSILON, fitted(0) - deviation),
    });
    const downB = p.point({
      time: bars[n - 1].time,
      price: Math.max(Number.EPSILON, fitted(n - 1) - deviation),
    });
    return [
      path([upA, upB, downB, downA], true, true),
      ...[
        [a, b],
        [upA, upB],
        [downA, downB],
      ].map(([start, end]) => line(start, end, d.extendLeft, d.extendRight, p.width, p.height)),
    ];
  },
};
