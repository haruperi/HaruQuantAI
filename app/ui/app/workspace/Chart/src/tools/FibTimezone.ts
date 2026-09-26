import type { Tool } from './types';
import { line, path, label } from './geometry';
export const FibTimezone: Tool = {
  label: 'Fib timezone',
  anchors: 2,
  group: 'Fibonacci',
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
    return [0, 1, 2, 3, 5, 8, 13].flatMap((r) => {
      const x = a.x + (b.x - a.x) * r;
      return [line({ x, y: 0 }, { x, y: p.height }), label({ x: x + 4, y: 30 }, r.toString())];
    });
  },
};
