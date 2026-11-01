import type { Tool, Primitive, Projection } from './types';
import type { Drawing } from '../types';
import { anchors } from './fibonacciTools';
import { path, label, line } from './geometry';
function measure(d: Drawing, p: Projection, kind: 'price' | 'date' | 'both'): Primitive[] {
  const [a, b] = anchors(d, p),
    first = d.points[0] ?? { time: 0, price: 1 },
    last = d.points[1] ?? first;
  const delta = last.price - first.price;
  const price = `${delta.toFixed(2)} (${(first.price ? (delta / first.price) * 100 : 0).toFixed(2)}%)`;
  const bars = Math.round(
    p.index ? p.index(last.time) - p.index(first.time) : (last.time - first.time) / p.barMs,
  );
  const duration = `${bars} bars | ${((last.time - first.time) / 60000).toFixed(1)} min`;
  const shapes: Primitive[] =
    kind === 'price'
      ? [
          line(a, { x: a.x, y: b.y }),
          line({ x: a.x - 6, y: a.y }, { x: a.x + 6, y: a.y }),
          line({ x: a.x - 6, y: b.y }, { x: a.x + 6, y: b.y }),
        ]
      : kind === 'date'
        ? [
            line(a, { x: b.x, y: a.y }),
            line({ x: a.x, y: a.y - 6 }, { x: a.x, y: a.y + 6 }),
            line({ x: b.x, y: a.y - 6 }, { x: b.x, y: a.y + 6 }),
          ]
        : [path([a, { x: b.x, y: a.y }, b, { x: a.x, y: b.y }], true, true)];
  shapes.push(
    label(
      { x: (a.x + b.x) / 2 + 6, y: Math.min(a.y, b.y) - 12 },
      kind === 'price' ? price : kind === 'date' ? duration : `${price} | ${duration}`,
    ),
  );
  return shapes;
}
export const PriceRange: Tool = {
  label: 'Price range',
  anchors: 2,
  group: 'Forecasting',
  build: (d, p) => measure(d, p, 'price'),
};
export const DateRange: Tool = {
  label: 'Date range',
  anchors: 2,
  group: 'Forecasting',
  build: (d, p) => measure(d, p, 'date'),
};
export const DatePriceRange: Tool = {
  label: 'Date and price range',
  anchors: 2,
  group: 'Forecasting',
  build: (d, p) => measure(d, p, 'both'),
};
