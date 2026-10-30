import type { Tool } from './types';
import { line, path, label } from './geometry';
export const Ellipse: Tool = {
  label: 'Ellipse',
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
    return [
      {
        kind: 'ellipse',
        center: { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 },
        rx: Math.abs(b.x - a.x) / 2,
        ry: Math.abs(b.y - a.y) / 2,
      },
    ];
  },
};
