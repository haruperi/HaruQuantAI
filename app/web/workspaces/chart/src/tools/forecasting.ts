import type { Bar, Drawing } from '../types';
import type { Tool, Projection, Primitive } from './types';
import { line, path, label } from './geometry';
import { anchors, curve } from './fibonacciTools';

export function sourceCandles(d: Drawing, p: Projection): Bar[] {
  if (d.sourceBars) return d.sourceBars;
  if (d.tool === 'GhostFeed') return [...(p.bars ?? [])].slice(-32);
  const a = d.points[0],
    b = d.points[1] ?? a;
  if (!a) return [];
  return (p.bars ?? [])
    .filter((bar) => bar.time >= Math.min(a.time, b.time) && bar.time <= Math.max(a.time, b.time))
    .slice(0, 512);
}
export function defaultPositionPoints(
  entry: Drawing['points'][number],
  short: boolean,
  barMs: number,
  endTime = entry.time + barMs * 8,
): Drawing['points'] {
  const distance = entry.price * 0.01;
  return [
    { ...entry },
    { time: entry.time, price: entry.price + (short ? distance : -distance) },
    { time: entry.time, price: entry.price + (short ? -distance : distance) },
    { time: Math.max(entry.time + barMs, endTime), price: entry.price },
  ];
}
export function positionPoints(d: Drawing): Drawing['points'] {
  const entry = d.points[0];
  if (!entry) return [];
  const stop = d.points[1] ?? entry,
    target = d.points[2] ?? stop;
  const end = d.points[3] ?? {
    time: Math.max(entry.time, stop.time, target.time),
    price: entry.price,
  };
  return [
    entry,
    { time: entry.time, price: stop.price },
    { time: entry.time, price: target.price },
    { time: end.time, price: entry.price },
  ];
}
export function positionMetrics(d: Drawing) {
  const entry = d.points[0]?.price ?? 0,
    stop = d.points[1]?.price ?? entry,
    target = d.points[2]?.price ?? entry;
  const account = d.positionSizing?.accountSize ?? 1000,
    riskPercent = d.positionSizing?.riskPercent ?? 1;
  const risk = Math.abs(entry - stop),
    reward = Math.abs(target - entry);
  const riskAmount = (account * riskPercent) / 100;
  const quantity = risk > 0 ? riskAmount / risk : 0;
  return {
    entry,
    stop,
    target,
    risk,
    reward,
    account,
    quantity,
    riskAmount,
    rewardAmount: quantity * reward,
    ratio: risk > 0 ? reward / risk : 0,
  };
}
function riskReward(d: Drawing, p: Projection, short: boolean): Primitive[] {
  const [a, b, c] = anchors(d, p);
  const m = positionMetrics(d);
  const valid = short
    ? m.stop > m.entry && m.target < m.entry
    : m.stop < m.entry && m.target > m.entry;
  if (!valid)
    return [path([a, b, c]), label(a, 'Place entry, stop, then target on opposite sides')];
  const points = positionPoints(d).map(p.point);
  const right = points[3].x > a.x ? points[3].x : a.x + 60,
    center = (a.x + right) / 2;
  const zone = (y: number, color: string): Primitive => ({
    ...path([a, { x: right, y: a.y }, { x: right, y }, { x: a.x, y }], true, true),
    color,
    fillOpacity: 0.28,
  });
  const badge = (y: number, text: string, background: string): Primitive => ({
    kind: 'badge',
    at: { x: center, y },
    text,
    background,
  });
  const percent = (value: number) => (m.entry ? (value / m.entry) * 100 : 0).toFixed(3);
  const targetY = points[2].y,
    stopY = points[1].y;
  return [
    zone(stopY, '#f23645'),
    zone(targetY, '#089981'),
    { ...line(a, { x: right, y: a.y }), color: '#a8a8a8' },
    { ...line(a, { x: right, y: targetY }), color: '#a8a8a8', dash: [5, 5] },
    badge(
      targetY + (targetY < a.y ? -22 : 22),
      `Target: ${m.reward.toFixed(5)} (${percent(m.reward)}%) Amount: ${(m.account + m.rewardAmount).toFixed(2)}`,
      '#089981',
    ),
    badge(
      stopY + (stopY < a.y ? -22 : 22),
      `Stop: ${m.risk.toFixed(5)} (${percent(m.risk)}%) Amount: ${(m.account - m.riskAmount).toFixed(2)}`,
      '#f23645',
    ),
    badge(
      a.y + (targetY < a.y ? 25 : -25),
      `Projected P&L: ${m.rewardAmount.toFixed(2)}, Qty: ${m.quantity.toFixed(2)}\nRisk/reward ratio: ${m.ratio.toFixed(2)}`,
      '#089981',
    ),
  ];
}
export const LongPosition: Tool = {
  label: 'Long position',
  anchors: 3,
  group: 'Forecasting',
  build: (d, p) => riskReward(d, p, false),
};
export const ShortPosition: Tool = {
  label: 'Short position',
  anchors: 3,
  group: 'Forecasting',
  build: (d, p) => riskReward(d, p, true),
};
export const PositionForecast: Tool = {
  label: 'Position forecast',
  anchors: 2,
  group: 'Forecasting',
  build: (d, p) => {
    const [a, b] = anchors(d, p),
      delta = (d.points[1]?.price ?? d.points[0]?.price ?? 0) - (d.points[0]?.price ?? 0);
    const angle = Math.atan2(b.y - a.y, b.x - a.x);
    return [
      line(a, b),
      path([
        { x: b.x - 12 * Math.cos(angle - 0.4), y: b.y - 12 * Math.sin(angle - 0.4) },
        b,
        { x: b.x - 12 * Math.cos(angle + 0.4), y: b.y - 12 * Math.sin(angle + 0.4) },
      ]),
      label({ x: b.x + 8, y: b.y - 8 }, `Forecast ${delta.toFixed(2)}`),
    ];
  },
};
function candle(bar: Bar, p: Projection, width: number): Primitive[] {
  const open = p.point({ time: bar.time, price: bar.open }),
    close = p.point({ time: bar.time, price: bar.close });
  const color = bar.close >= bar.open ? '#089981' : '#f23645';
  return [
    {
      ...line(
        p.point({ time: bar.time, price: bar.high }),
        p.point({ time: bar.time, price: bar.low }),
      ),
      color,
    },
    {
      ...path(
        [
          { x: open.x - width / 2, y: open.y },
          { x: open.x + width / 2, y: open.y },
          { x: close.x + width / 2, y: close.y },
          { x: close.x - width / 2, y: close.y },
        ],
        true,
        true,
      ),
      color,
    },
  ];
}
export const BarsPattern: Tool = {
  label: 'Bars pattern',
  anchors: 3,
  group: 'Forecasting',
  build: (d, p) => {
    const source = sourceCandles(d, p),
      place = d.points[2] ?? d.points[1] ?? d.points[0];
    if (!source.length || !place)
      return [label(anchors(d, p)[0], 'Select source candles, then a destination')];
    const delta = place.price - source[0].open,
      timeDelta = place.time - source[0].time;
    const spacing = Math.abs(
      p.point({ time: place.time + p.barMs, price: place.price }).x - p.point(place).x,
    );
    return source.flatMap((bar) =>
      candle(
        {
          ...bar,
          time: bar.time + timeDelta,
          open: Math.max(Number.EPSILON, bar.open + delta),
          high: Math.max(Number.EPSILON, bar.high + delta),
          low: Math.max(Number.EPSILON, bar.low + delta),
          close: Math.max(Number.EPSILON, bar.close + delta),
        },
        p,
        Math.max(1, Math.min(12, spacing * 0.65)),
      ),
    );
  },
};
export const GhostFeed: Tool = {
  label: 'Ghost feed',
  anchors: 2,
  group: 'Forecasting',
  build: (d, p) => {
    const source = sourceCandles(d, p),
      first = d.points[0],
      last = d.points[1] ?? first;
    if (!source.length || !first) return [label(anchors(d, p)[0], 'Ghost feed needs candle data')];
    const volatility = source.reduce((sum, bar) => sum + bar.high - bar.low, 0) / source.length;
    const shapes: Primitive[] = [];
    let previous = first.price;
    for (let i = 1; i <= 16; i++) {
      const time = first.time + ((last.time - first.time) * i) / 16;
      const close = Math.max(
        Number.EPSILON,
        first.price +
          ((last.price - first.price) * i) / 16 +
          Math.sin(i * 2.4) * volatility * 0.2 * Math.sin((Math.PI * i) / 16),
      );
      const high = Math.max(previous, close) + volatility * 0.25,
        low = Math.max(Number.EPSILON, Math.min(previous, close) - volatility * 0.25);
      shapes.push(...candle({ time, open: previous, high, low, close, volume: 0 }, p, 4));
      previous = close;
    }
    return [...shapes, label(anchors(d, p)[0], 'Illustrative ghost feed')];
  },
};
export const Sector: Tool = {
  label: 'Sector',
  anchors: 3,
  group: 'Forecasting',
  build: (d, p) => {
    const [a, b, c] = anchors(d, p),
      radius = Math.hypot(b.x - a.x, b.y - a.y);
    const start = Math.atan2(b.y - a.y, b.x - a.x),
      end = Math.atan2(c.y - a.y, c.x - a.x);
    const sweep = ((end - start + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
    const arc = curve(a, radius, radius, start, sweep, 64);
    return arc.kind === 'path' ? [path([a, ...arc.points], true, true)] : [arc];
  },
};
