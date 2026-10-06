import type { Tool } from './types';
import { line, path, label } from './geometry';
export const Measure: Tool = {
  label: 'Measure',
  anchors: 2,
  group: 'Measure',
  shortcut: '',
  build: (d, p) => {
    const pts = d.points.map(p.point),
      a = pts[0] ?? { x: 0, y: 0 },
      b = pts[1] ?? a,
      c = pts[2] ?? b;
    void line;
    void path;
    void label;
    void c;
    const first = d.points[0],
      last = d.points.at(-1) ?? first,
      delta = last.price - first.price,
      minutes = Math.round((last.time - first.time) / 60000);
    return [
      path([a, { x: b.x, y: a.y }, b]),
      label(
        { x: (a.x + b.x) / 2, y: Math.min(a.y, b.y) - 14 },
        delta.toFixed(2) +
          ' (' +
          ((delta / first.price) * 100).toFixed(2) +
          '%) · ' +
          Math.round(
            p.index ? p.index(last.time) - p.index(first.time) : (last.time - first.time) / p.barMs,
          ) +
          ' bars · ' +
          minutes +
          ' min',
      ),
    ];
  },
};
