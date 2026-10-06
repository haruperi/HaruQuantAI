import type { Tool } from './types';
import { line, path, label } from './geometry';
export const PriceLine: Tool = {
  label: 'Price line',
  anchors: 1,
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
    return [
      line({ x: 0, y: a.y }, { x: p.width, y: a.y }),
      label({ x: a.x + 8, y: a.y - 8 }, d.text || d.points[0]?.price.toFixed(2) || 'Price'),
    ];
  },
};
