import type { Tool } from './types';
import { line, path, label } from './geometry';
export const Arrow: Tool = {
  label: 'Arrow',
  anchors: 2,
  group: 'Trend',
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
    const angle = Math.atan2(b.y - a.y, b.x - a.x);
    return [
      line(a, b),
      path([
        { x: b.x - 12 * Math.cos(angle - 0.45), y: b.y - 12 * Math.sin(angle - 0.45) },
        b,
        { x: b.x - 12 * Math.cos(angle + 0.45), y: b.y - 12 * Math.sin(angle + 0.45) },
      ]),
    ];
  },
};
