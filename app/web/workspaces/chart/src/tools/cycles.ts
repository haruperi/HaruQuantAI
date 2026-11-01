import type { Tool, Primitive } from './types';
import { anchors, curve } from './fibonacciTools';
import { line, path } from './geometry';

export const CyclicLines: Tool = {
  label: 'Cyclic lines',
  anchors: 2,
  group: 'Patterns',
  build: (d, p) => {
    const [a, b] = anchors(d, p),
      period = Math.abs(b.x - a.x);
    if (period < 2) return [line({ x: a.x, y: 0 }, { x: a.x, y: p.height })];
    const first = Math.ceil(-a.x / period),
      last = Math.floor((p.width - a.x) / period);
    const count = Math.min(256, Math.max(0, last - first + 1));
    return Array.from({ length: count }, (_, i) => {
      const x = a.x + (first + i) * period;
      return line({ x, y: 0 }, { x, y: p.height });
    });
  },
};
export const TimeCycles: Tool = {
  label: 'Time cycles',
  anchors: 2,
  group: 'Patterns',
  build: (d, p) => {
    const [a, b] = anchors(d, p),
      period = Math.abs(b.x - a.x);
    if (period < 2) return [path([a])];
    const first = Math.floor(-a.x / period),
      last = Math.ceil((p.width - a.x) / period);
    const count = Math.min(128, Math.max(0, last - first));
    const height = Math.abs(b.y - a.y) || period / 2;
    const shapes: Primitive[] = [];
    for (let i = 0; i < count; i++) {
      shapes.push(
        curve(
          { x: a.x + (first + i + 0.5) * period, y: a.y },
          period / 2,
          height,
          Math.PI,
          Math.PI,
          32,
        ),
      );
    }
    return shapes.length ? shapes : [path([a])];
  },
};
export const SineLine: Tool = {
  label: 'Sine line',
  anchors: 2,
  group: 'Patterns',
  build: (d, p) => {
    const [a, b] = anchors(d, p),
      dx = b.x - a.x;
    if (Math.abs(dx) < 2) return [path([a, b])];
    // Anchor B is the first crest/trough, a quarter-period from A.
    const period = dx * 4,
      amplitude = b.y - a.y;
    const samples = Math.min(
      4096,
      Math.max(64, Math.ceil(p.width / Math.max(1, Math.abs(period) / 32))),
    );
    return [
      path(
        Array.from({ length: samples + 1 }, (_, i) => {
          const x = (p.width * i) / samples;
          return { x, y: a.y + amplitude * Math.sin(((x - a.x) / period) * Math.PI * 2) };
        }),
      ),
    ];
  },
};
