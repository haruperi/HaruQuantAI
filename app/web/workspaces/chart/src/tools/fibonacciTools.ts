import type { Drawing, XY } from '../types';
import type { Tool, Primitive, Projection } from './types';
import { line, path, label } from './geometry';

export const fibRatios = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1, 1.618];
export function anchors(d: Drawing, p: Projection): [XY, XY, XY] {
  const points = d.points.map(p.point);
  const a = points[0] ?? { x: 0, y: 0 },
    b = points[1] ?? a;
  return [a, b, points[2] ?? b];
}
/** Bounded polygonal curves share the renderer's existing path hit testing. */
export function curve(
  center: XY,
  rx: number,
  ry: number,
  start = 0,
  sweep = Math.PI * 2,
  samples = 96,
): Primitive {
  return path(
    Array.from({ length: samples + 1 }, (_, i) => {
      const theta = start + (sweep * i) / samples;
      return { x: center.x + rx * Math.cos(theta), y: center.y + ry * Math.sin(theta) };
    }),
  );
}
export const FibChannel: Tool = {
  label: 'Fib channel',
  anchors: 3,
  group: 'Fibonacci',
  build: (d, p) => {
    const [a, b, c] = anchors(d, p);
    const dx = b.x - a.x,
      dy = b.y - a.y;
    const offset = dx ? { x: 0, y: c.y - a.y - (dy * (c.x - a.x)) / dx } : { x: c.x - a.x, y: 0 };
    return fibRatios.flatMap((ratio) => {
      const start = { x: a.x + offset.x * ratio, y: a.y + offset.y * ratio };
      const end = { x: b.x + offset.x * ratio, y: b.y + offset.y * ratio };
      return [
        line(start, end, d.extendLeft, d.extendRight, p.width, p.height),
        label({ x: end.x + 4, y: end.y - 4 }, String(ratio)),
      ];
    });
  },
};
export const FibSpeedFan: Tool = {
  label: 'Fib speed resistance fan',
  anchors: 2,
  group: 'Fibonacci',
  build: (d, p) => {
    const [a, b] = anchors(d, p);
    return fibRatios
      .filter((r) => r > 0 && r <= 1)
      .flatMap((ratio) => {
        const end = { x: b.x, y: a.y + (b.y - a.y) * ratio };
        return [line(a, end, d.extendLeft, true, p.width, p.height), label(end, String(ratio))];
      });
  },
};
export const TrendFibTime: Tool = {
  label: 'Trend-based fib time',
  anchors: 3,
  group: 'Fibonacci',
  build: (d, p) => {
    const [a, b, c] = anchors(d, p);
    return [
      path([a, b, c]),
      ...[0, 0.618, 1, 1.618, 2.618, 4.236].flatMap((ratio) => {
        const x = c.x + (b.x - a.x) * ratio;
        return [line({ x, y: 0 }, { x, y: p.height }), label({ x: x + 4, y: 28 }, String(ratio))];
      }),
    ];
  },
};
export const FibCircles: Tool = {
  label: 'Fib circles',
  anchors: 2,
  group: 'Fibonacci',
  build: (d, p) => {
    const [a, b] = anchors(d, p),
      radius = Math.hypot(b.x - a.x, b.y - a.y);
    return fibRatios
      .filter((r) => r > 0)
      .flatMap((ratio) => [
        curve(a, radius * ratio, radius * ratio),
        label({ x: a.x + radius * ratio, y: a.y - 4 }, String(ratio)),
      ]);
  },
};
export const FibSpiral: Tool = {
  label: 'Fib spiral',
  anchors: 2,
  group: 'Fibonacci',
  build: (d, p) => {
    const [a, b] = anchors(d, p),
      radius = Math.hypot(b.x - a.x, b.y - a.y);
    const orientation = Math.atan2(b.y - a.y, b.x - a.x),
      phi = (1 + Math.sqrt(5)) / 2;
    // Golden logarithmic spiral: radius grows by phi every quarter turn.
    return [
      path(
        Array.from({ length: 257 }, (_, i) => {
          const angle = -Math.PI * 4 + (i / 256) * Math.PI * 6;
          const length = Math.min(
            radius * phi ** (angle / (Math.PI / 2)),
            (p.width + p.height) * 8,
          );
          return {
            x: a.x + length * Math.cos(orientation + angle),
            y: a.y + length * Math.sin(orientation + angle),
          };
        }),
      ),
    ];
  },
};
export const FibSpeedArcs: Tool = {
  label: 'Fib speed resistance arcs',
  anchors: 2,
  group: 'Fibonacci',
  build: (d, p) => {
    const [a, b] = anchors(d, p),
      radius = Math.hypot(b.x - a.x, b.y - a.y);
    const orientation = Math.atan2(b.y - a.y, b.x - a.x);
    return [
      line(a, b),
      ...fibRatios
        .filter((r) => r > 0 && r <= 1)
        .flatMap((ratio) => [
          curve(a, radius * ratio, radius * ratio, orientation - Math.PI / 2, Math.PI),
          label(
            {
              x: a.x + radius * ratio * Math.cos(orientation),
              y: a.y + radius * ratio * Math.sin(orientation),
            },
            String(ratio),
          ),
        ]),
    ];
  },
};
export const FibWedge: Tool = {
  label: 'Fib wedge',
  anchors: 3,
  group: 'Fibonacci',
  build: (d, p) => {
    const [a, b, c] = anchors(d, p),
      radius = Math.hypot(b.x - a.x, b.y - a.y);
    const start = Math.atan2(b.y - a.y, b.x - a.x),
      end = Math.atan2(c.y - a.y, c.x - a.x);
    const sweep = ((end - start + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
    return [
      line(a, b),
      line(a, { x: a.x + radius * Math.cos(end), y: a.y + radius * Math.sin(end) }),
      ...fibRatios
        .filter((r) => r > 0)
        .map((ratio) => curve(a, radius * ratio, radius * ratio, start, sweep)),
    ];
  },
};
export const Pitchfan: Tool = {
  label: 'Pitchfan',
  anchors: 3,
  group: 'Fibonacci',
  build: (d, p) => {
    const [a, b, c] = anchors(d, p),
      mid = { x: (b.x + c.x) / 2, y: (b.y + c.y) / 2 };
    return [
      line(b, c),
      ...[-1, -0.618, -0.382, 0, 0.382, 0.618, 1].flatMap((ratio) => {
        const end = { x: mid.x + ((c.x - b.x) / 2) * ratio, y: mid.y + ((c.y - b.y) / 2) * ratio };
        return [line(a, end, d.extendLeft, true, p.width, p.height), label(end, String(ratio))];
      }),
    ];
  },
};
