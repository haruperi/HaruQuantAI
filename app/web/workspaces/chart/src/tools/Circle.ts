import type { Tool } from './types';
import { line, path, label } from './geometry';
export const Circle: Tool = {
  label: 'Circle',
  anchors: 2,
  group: 'Shapes',
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
    const r = Math.hypot(b.x - a.x, b.y - a.y);
    return [{ kind: 'ellipse', center: a, rx: r, ry: r }];
  },
};
