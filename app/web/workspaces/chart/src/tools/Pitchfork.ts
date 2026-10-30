import type { Tool } from './types';
import { line, path, label } from './geometry';
export const Pitchfork: Tool = {
  label: 'Pitchfork',
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
    const mid = { x: (b.x + c.x) / 2, y: (b.y + c.y) / 2 },
      v = { x: mid.x - a.x, y: mid.y - a.y };
    return [
      line(a, mid, false, true, p.width, p.height),
      line(b, { x: b.x + v.x, y: b.y + v.y }, false, true, p.width, p.height),
      line(c, { x: c.x + v.x, y: c.y + v.y }, false, true, p.width, p.height),
      line(b, c),
    ];
  },
};
