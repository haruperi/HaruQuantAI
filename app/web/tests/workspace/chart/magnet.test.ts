import { expect, it } from 'vitest';
import { resolveMagnetSnap } from '../../../workspaces/chart/src/engine/magnet';

const bars = [
  { time: 1000, open: 100, high: 110, low: 90, close: 105, volume: 1 },
  { time: 2000, open: 106, high: 116, low: 96, close: 111, volume: 1 },
  { time: 3000, open: 112, high: 120, low: 102, close: 115, volume: 1 },
];

const base = {
  fractionalIndex: 1,
  bars,
  strength: 'weak' as const,
  snapToIndicators: false,
  priceOverlaySeries: [] as (number | null)[][],
  xAtIndex: (index: number) => index * 40,
  yAtPrice: (price: number) => 200 - price,
};

it('weak magnet snaps only near OHLC anchors', () => {
  const close = resolveMagnetSnap({ ...base, cursor: { x: 44, y: 90 } });
  expect(close?.index).toBe(1);
  expect(close?.price).toBe(111);
  expect(resolveMagnetSnap({ ...base, cursor: { x: 44, y: 30 } })).toBeNull();
});

it('strong magnet snaps even when the cursor is away from a candle', () => {
  const snap = resolveMagnetSnap({ ...base, strength: 'strong', cursor: { x: 40, y: 45 } });
  expect(snap).toMatchObject({ index: 1, price: 116 });
});

it('indicator candidates only participate when indicator snapping is enabled', () => {
  const input = { ...base, cursor: { x: 40, y: 71 }, priceOverlaySeries: [[null, 129, null]] };
  expect(resolveMagnetSnap(input)).toBeNull();
  expect(resolveMagnetSnap({ ...input, snapToIndicators: true })).toMatchObject({
    index: 1,
    price: 129,
  });
});

it('missing bars, invalid indices and nonfinite indicator points are ignored', () => {
  expect(resolveMagnetSnap({ ...base, bars: [], cursor: { x: 40, y: 90 } })).toBeNull();
  expect(resolveMagnetSnap({ ...base, fractionalIndex: NaN, cursor: { x: 40, y: 90 } })).toBeNull();
  const snap = resolveMagnetSnap({
    ...base,
    snapToIndicators: true,
    priceOverlaySeries: [[null, NaN, null]],
    cursor: { x: 40, y: 89 },
  });
  expect(snap).toMatchObject({ index: 1, price: 111 });
});
