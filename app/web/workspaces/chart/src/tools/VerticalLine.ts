import type { Tool } from './types';
import { line, path, label } from './geometry';
export const VerticalLine: Tool = {
  label: 'Vertical line',
  anchors: 1,
  group: 'Trend',
  shortcut: 'Alt+V',
  build: (d, p) => {
    const pts = d.points.map(p.point),
      a = pts[0] ?? { x: 0, y: 0 },
      b = pts[1] ?? a,
      c = pts[2] ?? b;
    void line;
    void path;
    void label;
    void c;
    return [line({ x: a.x, y: 0 }, { x: a.x, y: p.height })];
  },
};
