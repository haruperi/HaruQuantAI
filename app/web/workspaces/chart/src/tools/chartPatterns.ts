import type { Drawing } from '../types';
import type { Tool, Projection, Primitive } from './types';
import { path, label, line } from './geometry';

/** Draw only placed pivots during previews; undefined ratios are displayed explicitly. */
function pattern(
  d: Drawing,
  p: Projection,
  names: string[],
  kind: 'harmonic' | 'cypher' | 'head' | 'abcd' | 'triangle' | 'drives',
): Primitive[] {
  const points = d.points.slice(0, names.length).map(p.point);
  const shapes: Primitive[] = [path(points)];
  points.forEach((point, i) =>
    shapes.push(label({ x: point.x + 5, y: point.y + (i % 2 ? 18 : -10) }, names[i])),
  );
  if (points.length >= 3 && (kind === 'harmonic' || kind === 'cypher'))
    shapes.push(path([points[0], points[1], points[2]], true, true));
  if (points.length >= 5 && (kind === 'harmonic' || kind === 'cypher')) {
    shapes.push(path([points[2], points[3], points[4]], true, true));
    if (kind === 'cypher') shapes.push(line(points[0], points[3]), line(points[0], points[4]));
  }
  if (kind === 'triangle' && points.length >= 4) {
    shapes.push(
      line(points[0], points[2], false, d.extendRight, p.width, p.height),
      line(points[1], points[3], false, d.extendRight, p.width, p.height),
      path([points[0], points[2], points[3], points[1]], true, true),
    );
  }
  if (kind === 'head' && points.length >= 5) {
    shapes.push(line(points[2], points[4], d.extendLeft, d.extendRight, p.width, p.height));
  }
  // Ratios use actual prices, independent of chart zoom or logarithmic projection.
  if (kind !== 'head' && kind !== 'triangle') {
    for (let i = 2; i < points.length; i++) {
      const denominator = Math.abs(d.points[i - 1].price - d.points[i - 2].price);
      const ratio =
        denominator > Number.EPSILON
          ? (Math.abs(d.points[i].price - d.points[i - 1].price) / denominator).toFixed(3)
          : '—';
      shapes.push(
        label(
          {
            x: (points[i - 1].x + points[i].x) / 2 + 5,
            y: (points[i - 1].y + points[i].y) / 2 - 5,
          },
          ratio,
        ),
      );
    }
  }
  return shapes;
}
export const XABCDPattern: Tool = {
  label: 'XABCD pattern',
  anchors: 5,
  group: 'Patterns',
  build: (d, p) => pattern(d, p, ['X', 'A', 'B', 'C', 'D'], 'harmonic'),
};
export const CypherPattern: Tool = {
  label: 'Cypher pattern',
  anchors: 5,
  group: 'Patterns',
  build: (d, p) => pattern(d, p, ['X', 'A', 'B', 'C', 'D'], 'cypher'),
};
export const HeadShoulders: Tool = {
  label: 'Head and shoulders',
  anchors: 7,
  group: 'Patterns',
  build: (d, p) =>
    pattern(d, p, ['', 'Left shoulder', '', 'Head', '', 'Right shoulder', ''], 'head'),
};
export const ABCDPattern: Tool = {
  label: 'ABCD pattern',
  anchors: 4,
  group: 'Patterns',
  build: (d, p) => pattern(d, p, ['A', 'B', 'C', 'D'], 'abcd'),
};
export const TrianglePattern: Tool = {
  label: 'Triangle pattern',
  anchors: 4,
  group: 'Patterns',
  build: (d, p) => pattern(d, p, ['A', 'B', 'C', 'D'], 'triangle'),
};
export const ThreeDrives: Tool = {
  label: 'Three drives pattern',
  anchors: 7,
  group: 'Patterns',
  build: (d, p) => pattern(d, p, ['0', '1', 'A', '2', 'C', '3', 'D'], 'drives'),
};
