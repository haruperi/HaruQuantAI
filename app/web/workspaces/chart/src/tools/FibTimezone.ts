import type { Tool } from './types';
import { line, label } from './geometry';
import { anchors } from './fibonacciTools';
export const FibTimezone: Tool = {
  label: 'Fib time zone',
  anchors: 2,
  group: 'Fibonacci',
  build: (d, p) => {
    const [a, b] = anchors(d, p);
    return [0, 1, 2, 3, 5, 8, 13, 21].flatMap((ratio) => {
      const x = a.x + (b.x - a.x) * ratio;
      return [line({ x, y: 0 }, { x, y: p.height }), label({ x: x + 4, y: 28 }, String(ratio))];
    });
  },
};
