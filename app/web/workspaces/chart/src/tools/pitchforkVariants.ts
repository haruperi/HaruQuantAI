import type { Drawing } from '../types';
import type { Tool, Projection, Primitive } from './types';
import { line } from './geometry';

/** Schiff shifts price only; Modified Schiff shifts price and time; Inside halves the tine span. */
export function pitchfork(
  d: Drawing,
  p: Projection,
  variant: 'standard' | 'schiff' | 'modified' | 'inside',
): Primitive[] {
  const points = d.points.map(p.point);
  const a = points[0] ?? { x: 0, y: 0 },
    b = points[1] ?? a,
    c = points[2] ?? b;
  const origin =
    variant === 'schiff'
      ? { x: a.x, y: (a.y + b.y) / 2 }
      : variant === 'modified'
        ? { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 }
        : a;
  const mid = { x: (b.x + c.x) / 2, y: (b.y + c.y) / 2 };
  const left = variant === 'inside' ? { x: (b.x + mid.x) / 2, y: (b.y + mid.y) / 2 } : b;
  const right = variant === 'inside' ? { x: (c.x + mid.x) / 2, y: (c.y + mid.y) / 2 } : c;
  const vector = { x: mid.x - origin.x, y: mid.y - origin.y };
  return [
    line(origin, mid, d.extendLeft, true, p.width, p.height),
    ...[left, right].map((start) =>
      line(
        start,
        { x: start.x + vector.x, y: start.y + vector.y },
        d.extendLeft,
        true,
        p.width,
        p.height,
      ),
    ),
    line(b, c),
  ];
}
export const SchiffPitchfork: Tool = {
  label: 'Schiff pitchfork',
  anchors: 3,
  group: 'Trend',
  build: (d, p) => pitchfork(d, p, 'schiff'),
};
export const ModifiedSchiffPitchfork: Tool = {
  label: 'Modified Schiff pitchfork',
  anchors: 3,
  group: 'Trend',
  build: (d, p) => pitchfork(d, p, 'modified'),
};
export const InsidePitchfork: Tool = {
  label: 'Inside pitchfork',
  anchors: 3,
  group: 'Trend',
  build: (d, p) => pitchfork(d, p, 'inside'),
};
