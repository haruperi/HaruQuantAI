import { it, expect, vi } from 'vitest';
import type { Bar } from '../../../../app/workspace/Chart/src/types';
import { dayBars, MockFeed } from '../../../../app/workspace/Chart/src/feed/MockFeed';
it('is stable and respects sessions and OHLC invariants', () => {
  const a = dayBars('BTCUSDT', 20000);
  expect(a).toEqual(dayBars('BTCUSDT', 20000));
  expect(a).toHaveLength(1440);
  for (const b of a) {
    expect(b.high).toBeGreaterThanOrEqual(Math.max(b.open, b.close));
    expect(b.low).toBeLessThanOrEqual(Math.min(b.open, b.close));
  }
  expect(dayBars('AAPL', 20000).length).toBeLessThan(1440);
});
it('has identical overlapping history regardless of request start', async () => {
  const f = new MockFeed();
  const end = 20000 * 86400000;
  const a = await f.history('BTCUSDT', end - 600000, end);
  const b = await f.history('BTCUSDT', end - 1200000, end);
  expect(b.slice(-a.length)).toEqual(a);
});
it('rolls over midnight, aggregates requested intervals and disposes timers', () => {
  vi.useFakeTimers();
  try {
    let now = Date.UTC(2026, 8, 24, 23, 59, 59);
    const events: Readonly<Bar>[] = [];
    const feed = new MockFeed(() => now),
      stop = feed.subscribe('BTCUSDT', '1m', (b) => events.push(b));
    now += 2000;
    vi.advanceTimersByTime(300);
    expect(events.at(-1)!.time).toBe(Date.UTC(2026, 8, 25));
    expect(Object.isFrozen(events.at(-1))).toBe(true);
    stop();
    const count = events.length;
    vi.advanceTimersByTime(900);
    expect(events).toHaveLength(count);
    const aggregated: Readonly<Bar>[] = [];
    const stop3 = feed.subscribe('BTCUSDT', '3m', (b) => aggregated.push(b));
    expect(aggregated[0].time % 180000).toBe(0);
    stop3();
    expect(vi.getTimerCount()).toBe(0);
  } finally {
    vi.useRealTimers();
  }
});
