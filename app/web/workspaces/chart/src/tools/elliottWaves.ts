import type { Drawing } from '../types';
import type { Tool, Projection, Primitive } from './types';
import { path, label, line } from './geometry';

function wave(d: Drawing, p: Projection, labels: string[], triangle = false): Primitive[] {
  const points = d.points.slice(0, labels.length).map(p.point);
  const shapes: Primitive[] = [
    path(points),
    ...points.map((point, i) =>
      label({ x: point.x + 4, y: point.y + (i % 2 ? -12 : 18) }, labels[i]),
    ),
  ];
  if (triangle && points.length >= 4) shapes.push(line(points[1], points[3]));
  if (triangle && points.length >= 5) shapes.push(line(points[2], points[4]));
  return shapes;
}
export const ElliottImpulse: Tool = {
  label: 'Elliott impulse wave (1·2·3·4·5)',
  anchors: 6,
  group: 'Patterns',
  build: (d, p) => wave(d, p, ['0', '1', '2', '3', '4', '5']),
};
export const ElliottCorrection: Tool = {
  label: 'Elliott correction wave (A·B·C)',
  anchors: 4,
  group: 'Patterns',
  build: (d, p) => wave(d, p, ['0', 'A', 'B', 'C']),
};
export const ElliottTriangle: Tool = {
  label: 'Elliott triangle wave (A·B·C·D·E)',
  anchors: 6,
  group: 'Patterns',
  build: (d, p) => wave(d, p, ['0', 'A', 'B', 'C', 'D', 'E'], true),
};
export const ElliottDoubleCombo: Tool = {
  label: 'Elliott double combo wave (W·X·Y)',
  anchors: 4,
  group: 'Patterns',
  build: (d, p) => wave(d, p, ['0', 'W', 'X', 'Y']),
};
export const ElliottTripleCombo: Tool = {
  label: 'Elliott triple combo wave (W·X·Y·X·Z)',
  anchors: 6,
  group: 'Patterns',
  build: (d, p) => wave(d, p, ['0', 'W', 'X', 'Y', 'X', 'Z']),
};
