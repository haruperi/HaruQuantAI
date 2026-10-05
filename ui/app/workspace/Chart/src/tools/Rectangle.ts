import type { Tool } from './types';
import { line, path, label } from './geometry';
export const Rectangle: Tool = {
  label: 'Rectangle',
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
    return [path([a, { x: b.x, y: a.y }, b, { x: a.x, y: b.y }], true, true)];
  },
};
