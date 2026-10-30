import type { Tool } from './types';
import { line, path, label } from './geometry';
export const FibExtension: Tool = {
  label: 'Fib extension',
  anchors: 3,
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
    return [
      path([a, b, c]),
      ...[0, 0.618, 1, 1.618, 2.618].flatMap((r) => {
        const y = c.y + (b.y - a.y) * r;
        return [
          line({ x: a.x, y }, { x: p.width, y }),
          label({ x: c.x + 8, y: y - 4 }, r.toString()),
        ];
      }),
    ];
  },
};
