import type { Tool } from './types';
import { line, path, label } from './geometry';
export const AnchoredNote: Tool = {
  label: 'Anchored note',
  anchors: 1,
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
    return [
      line(a, { x: a.x + 20, y: a.y - 30 }),
      label({ x: a.x + 22, y: a.y - 32 }, d.text || 'Note'),
    ];
  },
};
