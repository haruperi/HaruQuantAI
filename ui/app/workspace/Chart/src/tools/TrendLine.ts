import type { Tool } from './types';
import { line, path, label } from './geometry';
export const TrendLine: Tool = {
  label: 'Trend line',
  anchors: 2,
  group: 'Trend',
  shortcut: 'Alt+T',
  build: (d, p) => {
    const pts = d.points.map(p.point),
      a = pts[0] ?? { x: 0, y: 0 },
      b = pts[1] ?? a,
      c = pts[2] ?? b;
    void line;
    void path;
    void label;
    void c;
    return [line(a, b, d.extendLeft, d.extendRight, p.width, p.height)];
  },
};
