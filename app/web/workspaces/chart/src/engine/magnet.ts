import type { Bar, XY } from '../types';

export interface MagnetSnap {
  index: number;
  price: number;
  distance: number;
}

export interface MagnetSnapInput {
  cursor: XY;
  fractionalIndex: number;
  bars: readonly Bar[];
  strength: 'weak' | 'strong';
  snapToIndicators: boolean;
  // Only indicator lines drawn on the main price pane should participate.
  priceOverlaySeries: readonly (readonly (number | null)[])[];
  xAtIndex: (index: number) => number;
  yAtPrice: (price: number) => number;
}

/**
 * Snap to visible OHLC endpoints, optionally including price-overlay indicator values.
 * Weak magnet only engages within 12 screen pixels; strong magnet always chooses the
 * closest candidate on the nearest candle (or an immediately adjacent candle).
 * The decision uses pixel distance, so it is stable across linear and log scales.
 */
export function resolveMagnetSnap(input: MagnetSnapInput): MagnetSnap | null {
  const { bars, cursor, fractionalIndex, strength, snapToIndicators, priceOverlaySeries, xAtIndex, yAtPrice } = input;
  if (!bars.length || !Number.isFinite(fractionalIndex)) return null;

  const near = Math.max(0, Math.min(bars.length - 1, Math.round(fractionalIndex)));
  let closest: MagnetSnap | null = null;

  // Adjacent bars allow weak snapping near candle edges and avoid discontinuities
  // at the midpoint between bars.
  for (let index = Math.max(0, near - 1); index <= Math.min(bars.length - 1, near + 1); index++) {
    const bar = bars[index];
    const values: number[] = [bar.open, bar.high, bar.low, bar.close];
    if (snapToIndicators)
      for (const series of priceOverlaySeries) {
        const value = series[index];
        if (value != null && Number.isFinite(value) && value > 0) values.push(value);
      }
    const x = xAtIndex(index);
    for (const price of values) {
      if (!Number.isFinite(price) || price <= 0) continue;
      const y = yAtPrice(price);
      if (!Number.isFinite(x) || !Number.isFinite(y)) continue;
      const distance = Math.hypot(x - cursor.x, y - cursor.y);
      if (!closest || distance < closest.distance)
        closest = { index, price, distance };
    }
  }

  return closest && (strength === 'strong' || closest.distance <= 12) ? closest : null;
}
