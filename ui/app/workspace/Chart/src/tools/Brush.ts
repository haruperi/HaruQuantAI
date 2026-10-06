import type { Tool } from './types';
import { line, path, label } from './geometry';
export const Brush: Tool = {
  label: 'Brush',
  anchors: 0,
  group: 'Annotate',
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
    return [path(pts)];
  },
};
