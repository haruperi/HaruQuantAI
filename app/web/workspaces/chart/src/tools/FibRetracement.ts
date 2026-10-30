import type { Tool } from './types';
import { line, path, label } from './geometry';
export const FibRetracement: Tool = {
  label: 'Fib retracement',
  anchors: 2,
  group: 'Fibonacci',
  shortcut: 'Alt+F',
  build: (d, p) => {
    const pts = d.points.map(p.point),
      a = pts[0] ?? { x: 0, y: 0 },
      b = pts[1] ?? a,
      c = pts[2] ?? b;
    void line;
    void path;
    void label;
    void c;
    return [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1].flatMap((r) => {
      const y = a.y + (b.y - a.y) * r;
      return [
        line({ x: Math.min(a.x, b.x), y }, { x: d.extendRight ? p.width : Math.max(a.x, b.x), y }),
        label({ x: Math.max(a.x, b.x) + 4, y: y - 4 }, (r * 100).toFixed(1) + '%'),
      ];
    });
  },
};
