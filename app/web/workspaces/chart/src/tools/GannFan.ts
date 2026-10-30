import type { Tool } from './types';
import { line, path, label } from './geometry';
export const GannFan: Tool = {
  label: 'Gann fan',
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
    return [0.125, 0.25, 0.5, 1, 2, 4, 8].flatMap((r) => {
      const endpoint = p.point({
        time: d.points[1]?.time ?? d.points[0].time + p.barMs,
        price:
          d.points[0].price +
          ((d.points[1]?.price ?? d.points[0].price + 1) - d.points[0].price) * r,
      });
      return [line(a, endpoint, false, true, p.width, p.height), label(endpoint, r + ':1')];
    });
  },
};
