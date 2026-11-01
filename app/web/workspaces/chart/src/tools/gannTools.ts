import type { Drawing } from '../types';
import type { Tool, Projection, Primitive } from './types';
import { line, path, label } from './geometry';
import { anchors, curve } from './fibonacciTools';

function gann(d: Drawing, p: Projection, kind: 'box' | 'square' | 'fixed'): Primitive[] {
  const [a, b] = anchors(d, p);
  const size = Math.max(Math.abs(b.x - a.x), Math.abs(b.y - a.y));
  const end =
    kind === 'fixed'
      ? { x: a.x + (Math.sign(b.x - a.x) || 1) * size, y: a.y + (Math.sign(b.y - a.y) || 1) * size }
      : b;
  const dx = end.x - a.x,
    dy = end.y - a.y;
  const levels = kind === 'box' ? [0, 0.25, 0.5, 0.75, 1] : [0, 0.2, 0.4, 0.6, 0.8, 1];
  const shapes: Primitive[] = [
    path([a, { x: end.x, y: a.y }, end, { x: a.x, y: end.y }], true, true),
  ];
  for (const ratio of levels) {
    const x = a.x + dx * ratio,
      y = a.y + dy * ratio;
    shapes.push(
      line({ x, y: a.y }, { x, y: end.y }),
      line({ x: a.x, y }, { x: end.x, y }),
      label({ x: x + 3, y: a.y - 5 }, String(ratio)),
    );
  }
  if (kind !== 'box') {
    for (const ratio of [0.25, 0.5, 1, 2, 4]) {
      const reachX = ratio > 1 ? dx / ratio : dx,
        reachY = ratio > 1 ? dy : dy * ratio;
      shapes.push(line(a, { x: a.x + reachX, y: a.y + reachY }));
      shapes.push(line(end, { x: end.x - reachX, y: end.y - reachY }));
    }
    const start = dx >= 0 ? 0 : Math.PI;
    const direction = dx * dy >= 0 ? 1 : -1;
    for (const ratio of [0.5, 1])
      shapes.push(
        curve(a, Math.abs(dx) * ratio, Math.abs(dy) * ratio, start, (direction * Math.PI) / 2),
      );
  }
  return shapes;
}
export const GannBox: Tool = {
  label: 'Gann box',
  anchors: 2,
  group: 'Fibonacci',
  build: (d, p) => gann(d, p, 'box'),
};
export const GannSquareFixed: Tool = {
  label: 'Gann square fixed',
  anchors: 2,
  group: 'Fibonacci',
  build: (d, p) => gann(d, p, 'fixed'),
};
export const GannSquare: Tool = {
  label: 'Gann square',
  anchors: 2,
  group: 'Fibonacci',
  build: (d, p) => gann(d, p, 'square'),
};
