import type { Tool } from './types';
import { line, label } from './geometry';
export const FibRetracement: Tool = {
  label: 'Fib retracement',
  anchors: 2,
  group: 'Fibonacci',
  shortcut: 'Alt+F',
  build: (d, p) => {
    const first = d.points[0] ?? { time: 0, price: 1 },
      last = d.points[1] ?? first;
    const a = p.point(first),
      b = p.point(last);
    return [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1].flatMap((ratio) => {
      const price = first.price + (last.price - first.price) * ratio;
      const y = p.point({ time: first.time, price }).y;
      const left = d.extendLeft ? 0 : Math.min(a.x, b.x),
        right = d.extendRight ? p.width : Math.max(a.x, b.x);
      return [
        line({ x: left, y }, { x: right, y }),
        label(
          { x: Math.max(0, Math.min(right + 4, p.width - 115)), y: y - 4 },
          `${(ratio * 100).toFixed(1)}% (${price.toFixed(2)})`,
        ),
      ];
    });
  },
};
