import { it, expect } from 'vitest';
import { resample, bucket, nextBucket } from '../../../../app/workspace/Chart/src/feed/resample';
it('aggregates OHLCV and partial buckets', () => {
  const b = [0, 1, 2, 3].map((i) => ({
    time: i * 60000,
    open: 10 + i,
    high: 12 + i,
    low: 8 + i,
    close: 11 + i,
    volume: 100,
  }));
  expect(resample(b, '3m')).toEqual([
    { time: 0, open: 10, high: 14, low: 8, close: 13, volume: 300 },
    { ...b[3] },
  ]);
});
it('aligns calendar months, leap years and Monday weeks', () => {
  expect(nextBucket(Date.UTC(2024, 1, 2), '1M')).toBe(Date.UTC(2024, 2, 1));
  expect(bucket(Date.UTC(2024, 2, 3), '1W')).toBe(Date.UTC(2024, 1, 26));
});
