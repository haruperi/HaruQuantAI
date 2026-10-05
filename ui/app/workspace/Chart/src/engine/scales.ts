import type { ScaleMode } from '../types';
export const clamp = (v: number, min: number, max: number) => Math.max(min, Math.min(max, v));
export const timeToX = (index: number, spacing: number, offset: number) => index * spacing + offset;
export const xToTime = (x: number, spacing: number, offset: number) => (x - offset) / spacing;
export function zoomAt(
  x: number,
  spacing: number,
  offset: number,
  factor: number,
): { spacing: number; offset: number } {
  const index = xToTime(x, spacing, offset);
  const next = clamp(spacing * factor, 0.2, 50);
  return { spacing: next, offset: x - index * next };
}
export const transformPrice = (p: number, mode: ScaleMode, anchor: number) =>
  mode === 'log'
    ? Math.log(p)
    : mode === 'percent'
      ? (p / anchor - 1) * 100
      : mode === 'indexed'
        ? (p / anchor) * 100
        : p;
export const inversePrice = (p: number, mode: ScaleMode, anchor: number) =>
  mode === 'log'
    ? Math.exp(p)
    : mode === 'percent'
      ? (p / 100 + 1) * anchor
      : mode === 'indexed'
        ? (p / 100) * anchor
        : p;
export function priceToY(
  price: number,
  min: number,
  max: number,
  height: number,
  mode: ScaleMode = 'linear',
  reverse = false,
  anchor = 1,
): number {
  const low = transformPrice(min, mode, anchor),
    high = transformPrice(max, mode, anchor),
    v = (transformPrice(price, mode, anchor) - low) / (high - low || 1);
  return height * (reverse ? v : 1 - v);
}
export function yToPrice(
  y: number,
  min: number,
  max: number,
  height: number,
  mode: ScaleMode = 'linear',
  reverse = false,
  anchor = 1,
): number {
  const low = transformPrice(min, mode, anchor),
    high = transformPrice(max, mode, anchor);
  return inversePrice(low + (reverse ? y / height : 1 - y / height) * (high - low), mode, anchor);
}
export function niceTicks(min: number, max: number, count = 8): number[] {
  const raw = (max - min) / count;
  if (!Number.isFinite(raw) || raw <= 0) return [min];
  const p = 10 ** Math.floor(Math.log10(raw));
  const f = raw / p;
  const step = (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * p;
  const ticks: number[] = [];
  for (
    let n = Math.ceil(min / step) * step;
    n <= max + step * 1e-6 && ticks.length < 100;
    n += step
  )
    ticks.push(Number(n.toPrecision(12)));
  return ticks;
}
