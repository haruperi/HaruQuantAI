import type { Tool } from './types';
import { line, label } from './geometry';
import { anchors } from './fibonacciTools';
export const GannFan: Tool = {
  label: 'Gann fan',
  anchors: 2,
  group: 'Fibonacci',
  build: (d, p) => {
    const [a, b] = anchors(d, p);
    return [
      [1, 8],
      [1, 4],
      [1, 3],
      [1, 2],
      [1, 1],
      [2, 1],
      [3, 1],
      [4, 1],
      [8, 1],
    ].flatMap(([price, time]) => {
      const endpoint = { x: b.x, y: a.y + ((b.y - a.y) * price) / time };
      return [
        line(a, endpoint, d.extendLeft, true, p.width, p.height),
        label(endpoint, `${price}�${time}`),
      ];
    });
  },
};
