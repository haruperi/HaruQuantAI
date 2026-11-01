import type { Bar, Drawing } from '../types';
import type { Tool, Projection, Primitive } from './types';
import { path, label, line } from './geometry';
import { anchors } from './fibonacciTools';

function selected(d: Drawing, p: Projection, fixed = false): Bar[] {
  const first = d.points[0]?.time ?? 0,
    last = d.points[1]?.time ?? first;
  return (p.bars ?? []).filter((bar) =>
    fixed
      ? bar.time >= Math.min(first, last) && bar.time <= Math.max(first, last)
      : bar.time >= first,
  );
}
export function anchoredVWAP(bars: readonly Bar[]): { time: number; price: number }[] {
  let total = 0,
    weighted = 0;
  const result: { time: number; price: number }[] = [];
  for (const bar of bars) {
    if (bar.volume <= 0) continue;
    total += bar.volume;
    weighted += ((bar.high + bar.low + bar.close) / 3) * bar.volume;
    result.push({ time: bar.time, price: weighted / total });
  }
  return result;
}
/** Approximate candle volume uniformly over its high-low span; preserve total volume. */
export function volumeBins(
  bars: readonly Bar[],
  rows = 32,
): { low: number; high: number; volume: number }[] {
  if (!bars.length) return [];
  const low = Math.min(...bars.map((bar) => bar.low)),
    high = Math.max(...bars.map((bar) => bar.high));
  const count = Math.max(1, Math.min(128, Math.floor(rows) || 32));
  const span = high - low || Math.max(Math.abs(low) * 0.0001, 0.0001),
    step = span / count;
  const bins = Array.from({ length: count }, (_, i) => ({
    low: low + step * i,
    high: low + step * (i + 1),
    volume: 0,
  }));
  for (const bar of bars) {
    if (bar.volume <= 0) continue;
    if (bar.high === bar.low) {
      bins[Math.min(count - 1, Math.max(0, Math.floor((bar.close - low) / step)))].volume +=
        bar.volume;
      continue;
    }
    for (const bin of bins)
      bin.volume +=
        (bar.volume * Math.max(0, Math.min(bin.high, bar.high) - Math.max(bin.low, bar.low))) /
        (bar.high - bar.low);
  }
  return bins;
}
export const AnchoredVWAP: Tool = {
  label: 'Anchored VWAP',
  anchors: 1,
  group: 'Forecasting',
  build: (d, p) => {
    const points = anchoredVWAP(selected(d, p));
    return points.length
      ? [
          path(points.map(p.point)),
          label(
            p.point(points[points.length - 1]),
            `AVWAP ${points[points.length - 1].price.toFixed(2)}`,
          ),
        ]
      : [label(anchors(d, p)[0], 'VWAP: no positive volume in selected range')];
  },
};
function profile(d: Drawing, p: Projection, fixed: boolean): Primitive[] {
  const bars = selected(d, p, fixed),
    bins = volumeBins(bars);
  const maximum = Math.max(0, ...bins.map((bin) => bin.volume));
  if (!maximum)
    return [label(anchors(d, p)[0], 'Volume profile: no positive volume in selected range')];
  const right = fixed
    ? Math.max(...bars.map((bar) => p.point({ time: bar.time, price: bar.close }).x))
    : p.width;
  const width = Math.min(180, p.width * 0.2),
    time = bars[0].time;
  const shapes: Primitive[] = bins.map((bin) => {
    const top = p.point({ time, price: bin.high }).y,
      bottom = p.point({ time, price: bin.low }).y;
    return {
      ...path(
        [
          { x: right, y: top },
          { x: right - (width * bin.volume) / maximum, y: top },
          { x: right - (width * bin.volume) / maximum, y: bottom },
          { x: right, y: bottom },
        ],
        true,
        true,
      ),
      color: '#2962ff',
    };
  });
  const poc = bins.reduce((best, bin) => (bin.volume > best.volume ? bin : best));
  const y = p.point({ time, price: (poc.low + poc.high) / 2 }).y;
  shapes.push(
    { ...line({ x: right - width, y }, { x: right, y }), color: '#ff9800' },
    label({ x: Math.max(0, right - width), y: Math.max(15, y - 8) }, 'POC | OHLC estimate'),
  );
  return shapes;
}
export const FixedVolumeProfile: Tool = {
  label: 'Fixed range volume profile',
  anchors: 2,
  group: 'Forecasting',
  build: (d, p) => profile(d, p, true),
};
export const AnchoredVolumeProfile: Tool = {
  label: 'Anchored volume profile',
  anchors: 1,
  group: 'Forecasting',
  build: (d, p) => profile(d, p, false),
};
