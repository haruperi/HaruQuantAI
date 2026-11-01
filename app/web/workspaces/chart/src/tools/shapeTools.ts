import type { Point } from '../types';
import type { Tool, Primitive } from './types';
import { path } from './geometry';
import { anchors } from './fibonacciTools';

export function defaultCurvePoints(first: Point, last: Point, double = false): Point[] {
  const bend = Math.max(Math.abs(last.price - first.price) / 2, first.price * 0.002);
  const control = (fraction: number, sign: number): Point => ({
    time: first.time + (last.time - first.time) * fraction,
    price: Math.max(
      Number.EPSILON,
      first.price + (last.price - first.price) * fraction + bend * sign,
    ),
  });
  return double
    ? [first, last, control(1 / 3, 1), control(2 / 3, -1)]
    : [first, last, control(0.5, 1)];
}
export const RotatedRectangle: Tool = {
  label: 'Rotated rectangle',
  anchors: 3,
  group: 'Shapes',
  build: (d, p) => {
    const [a, b, c] = anchors(d, p),
      dx = b.x - a.x,
      dy = b.y - a.y;
    const length = Math.hypot(dx, dy);
    const distance = length ? ((c.x - a.x) * -dy + (c.y - a.y) * dx) / length : 0;
    const offset = length
      ? { x: (-dy / length) * distance, y: (dx / length) * distance }
      : { x: 0, y: 0 };
    return [
      path(
        [a, b, { x: b.x + offset.x, y: b.y + offset.y }, { x: a.x + offset.x, y: a.y + offset.y }],
        true,
        true,
      ),
    ];
  },
};
function arrowHead(a: { x: number; y: number }, b: { x: number; y: number }): Primitive {
  const angle = Math.atan2(b.y - a.y, b.x - a.x);
  return path([
    { x: b.x - 12 * Math.cos(angle - 0.45), y: b.y - 12 * Math.sin(angle - 0.45) },
    b,
    { x: b.x - 12 * Math.cos(angle + 0.45), y: b.y - 12 * Math.sin(angle + 0.45) },
  ]);
}
export const PathTool: Tool = {
  label: 'Path',
  anchors: 0,
  group: 'Shapes',
  build: (d, p) => {
    const points = d.points.map(p.point);
    return points.length >= 2
      ? [path(points), arrowHead(points[points.length - 2], points[points.length - 1])]
      : [path(points)];
  },
};
export const Polyline: Tool = {
  label: 'Polyline',
  anchors: 0,
  group: 'Shapes',
  build: (d, p) => [path(d.points.map(p.point))],
};
export const ArrowMarker: Tool = {
  label: 'Arrow marker',
  anchors: 2,
  group: 'Shapes',
  build: (d, p) => {
    const [a, b] = anchors(d, p),
      dx = b.x - a.x,
      dy = b.y - a.y,
      length = Math.hypot(dx, dy) || 1;
    const nx = -dy / length,
      ny = dx / length,
      head = Math.min(18, length * 0.4);
    const neck = { x: b.x - (dx / length) * head, y: b.y - (dy / length) * head };
    return [
      {
        ...path(
          [
            { x: a.x + nx * 3, y: a.y + ny * 3 },
            { x: neck.x + nx * 3, y: neck.y + ny * 3 },
            { x: neck.x + nx * 9, y: neck.y + ny * 9 },
            b,
            { x: neck.x - nx * 9, y: neck.y - ny * 9 },
            { x: neck.x - nx * 3, y: neck.y - ny * 3 },
            { x: a.x - nx * 3, y: a.y - ny * 3 },
          ],
          true,
          true,
        ),
        fillOpacity: 0.7,
      },
    ];
  },
};
function mark(up: boolean): Tool {
  return {
    label: up ? 'Arrow mark up' : 'Arrow mark down',
    anchors: 1,
    group: 'Shapes',
    build: (d, p) => {
      const [a] = anchors(d, p),
        sign = up ? -1 : 1;
      return [
        {
          ...path(
            [
              { x: a.x, y: a.y },
              { x: a.x - 10, y: a.y - sign * 12 },
              { x: a.x - 4, y: a.y - sign * 12 },
              { x: a.x - 4, y: a.y - sign * 23 },
              { x: a.x + 4, y: a.y - sign * 23 },
              { x: a.x + 4, y: a.y - sign * 12 },
              { x: a.x + 10, y: a.y - sign * 12 },
            ],
            true,
            true,
          ),
          fillOpacity: 0.7,
        },
      ];
    },
  };
}
export const ArrowMarkUp = mark(true);
export const ArrowMarkDown = mark(false);
export const Curve: Tool = {
  label: 'Curve',
  anchors: 3,
  group: 'Shapes',
  build: (d, p) => {
    const points =
      d.points.length >= 3
        ? d.points
        : defaultCurvePoints(
            d.points[0] ?? { time: 0, price: 1 },
            d.points[1] ?? d.points[0] ?? { time: 0, price: 1 },
          );
    const [a, b, c] = points.map(p.point);
    return [
      path(
        Array.from({ length: 65 }, (_, i) => {
          const t = i / 64,
            u = 1 - t;
          return {
            x: u * u * a.x + 2 * u * t * c.x + t * t * b.x,
            y: u * u * a.y + 2 * u * t * c.y + t * t * b.y,
          };
        }),
      ),
    ];
  },
};
export const DoubleCurve: Tool = {
  label: 'Double curve',
  anchors: 4,
  group: 'Shapes',
  build: (d, p) => {
    const points =
      d.points.length >= 4
        ? d.points
        : defaultCurvePoints(
            d.points[0] ?? { time: 0, price: 1 },
            d.points[1] ?? d.points[0] ?? { time: 0, price: 1 },
            true,
          );
    const [a, b, c, e] = points.map(p.point);
    return [
      path(
        Array.from({ length: 97 }, (_, i) => {
          const t = i / 96,
            u = 1 - t;
          return {
            x: u ** 3 * a.x + 3 * u * u * t * c.x + 3 * u * t * t * e.x + t ** 3 * b.x,
            y: u ** 3 * a.y + 3 * u * u * t * c.y + 3 * u * t * t * e.y + t ** 3 * b.y,
          };
        }),
      ),
    ];
  },
};
export const Arc: Tool = {
  label: 'Arc',
  anchors: 3,
  group: 'Shapes',
  build: (d, p) => {
    const [a, b, c] = anchors(d, p);
    const determinant = 2 * (a.x * (b.y - c.y) + b.x * (c.y - a.y) + c.x * (a.y - b.y));
    if (Math.abs(determinant) < 0.000001) return [path([a, c, b])];
    const aa = a.x ** 2 + a.y ** 2,
      bb = b.x ** 2 + b.y ** 2,
      cc = c.x ** 2 + c.y ** 2;
    const center = {
      x: (aa * (b.y - c.y) + bb * (c.y - a.y) + cc * (a.y - b.y)) / determinant,
      y: (aa * (c.x - b.x) + bb * (a.x - c.x) + cc * (b.x - a.x)) / determinant,
    };
    const start = Math.atan2(a.y - center.y, a.x - center.x),
      end = Math.atan2(b.y - center.y, b.x - center.x),
      middle = Math.atan2(c.y - center.y, c.x - center.x),
      tau = Math.PI * 2;
    const positive = (angle: number) => ((angle % tau) + tau) % tau;
    const sweep =
      positive(middle - start) <= positive(end - start)
        ? positive(end - start)
        : positive(end - start) - tau;
    const radius = Math.hypot(a.x - center.x, a.y - center.y);
    return [
      path(
        Array.from({ length: 97 }, (_, i) => ({
          x: center.x + radius * Math.cos(start + (sweep * i) / 96),
          y: center.y + radius * Math.sin(start + (sweep * i) / 96),
        })),
      ),
    ];
  },
};
