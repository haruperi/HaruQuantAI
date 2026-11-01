import type { Tool } from './types';
import { line, label } from './geometry';

export const InfoLine: Tool = {
  label: 'Info line',
  anchors: 2,
  group: 'Trend',
  build: (d, p) => {
    const first = d.points[0] ?? { time: 0, price: 1 };
    const last = d.points[1] ?? first;
    const a = p.point(first),
      b = p.point(last);
    const delta = last.price - first.price;
    const bars = Math.round(
      p.index ? p.index(last.time) - p.index(first.time) : (last.time - first.time) / p.barMs,
    );
    return [
      line(a, b, d.extendLeft, d.extendRight, p.width, p.height),
      label(
        { x: (a.x + b.x) / 2, y: Math.min(a.y, b.y) - 12 },
        `${delta.toFixed(2)} (${(first.price ? (delta / first.price) * 100 : 0).toFixed(2)}%) � ${bars} bars � ${Math.round((last.time - first.time) / 60000)} min`,
      ),
    ];
  },
};
export const ExtendedLine: Tool = {
  label: 'Extended line',
  anchors: 2,
  group: 'Trend',
  build: (d, p) => {
    const a = p.point(d.points[0] ?? { time: 0, price: 1 });
    const b = p.point(d.points[1] ?? d.points[0] ?? { time: 0, price: 1 });
    return [line(a, b, true, true, p.width, p.height)];
  },
};
export const TrendAngle: Tool = {
  label: 'Trend angle',
  anchors: 2,
  group: 'Trend',
  build: (d, p) => {
    const a = p.point(d.points[0] ?? { time: 0, price: 1 });
    const b = p.point(d.points[1] ?? d.points[0] ?? { time: 0, price: 1 });
    const degrees = (Math.atan2(a.y - b.y, b.x - a.x) * 180) / Math.PI;
    return [
      line(a, b, d.extendLeft, d.extendRight, p.width, p.height),
      line(a, { x: a.x + 35, y: a.y }),
      label({ x: a.x + 10, y: a.y - 12 }, `${degrees.toFixed(1)}�`),
    ];
  },
};
export const CrossLine: Tool = {
  label: 'Crossline',
  anchors: 1,
  group: 'Trend',
  shortcut: 'Alt+C',
  build: (d, p) => {
    const a = p.point(d.points[0] ?? { time: 0, price: 1 });
    return [
      line({ x: 0, y: a.y }, { x: p.width, y: a.y }),
      line({ x: a.x, y: 0 }, { x: a.x, y: p.height }),
    ];
  },
};
