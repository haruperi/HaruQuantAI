import type { Tool } from './types';
import { line, path, label } from './geometry';
export const FibExtension: Tool = {
  label: 'Trend-based fib extension',
  anchors: 3,
  group: 'Fibonacci',
  build: (d, p) => {
    const first = d.points[0] ?? { time: 0, price: 1 },
      second = d.points[1] ?? first,
      third = d.points[2] ?? second;
    const a = p.point(first),
      b = p.point(second),
      c = p.point(third);
    return [
      path([a, b, c]),
      ...[0, 0.236, 0.382, 0.5, 0.618, 1, 1.618, 2.618].flatMap((ratio) => {
        const price = third.price + (second.price - first.price) * ratio;
        if (price <= 0) return [];
        const y = p.point({ time: third.time, price }).y;
        return [
          line(
            { x: d.extendLeft ? 0 : Math.min(a.x, b.x, c.x), y },
            { x: d.extendRight ? p.width : Math.max(a.x, b.x, c.x), y },
          ),
          label({ x: c.x + 8, y: y - 4 }, `${ratio} (${price.toFixed(2)})`),
        ];
      }),
    ];
  },
};
