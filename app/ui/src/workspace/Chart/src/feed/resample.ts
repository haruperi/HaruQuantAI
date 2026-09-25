import type { Bar, Interval } from '../types';
export function bucket(time: number, interval: Interval): number {
  const d = new Date(time);
  if (interval === '1M') return Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), 1);
  if (interval === '1W')
    return Date.UTC(
      d.getUTCFullYear(),
      d.getUTCMonth(),
      d.getUTCDate() - ((d.getUTCDay() + 6) % 7),
    );
  const minutes = interval === '1D' ? 1440 : parseInt(interval) * (interval.endsWith('h') ? 60 : 1);
  return Math.floor(time / (minutes * 60000)) * minutes * 60000;
}
export function nextBucket(time: number, interval: Interval): number {
  const start = bucket(time, interval);
  if (interval === '1M') {
    const d = new Date(start);
    return Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 1);
  }
  return (
    start +
    (interval === '1W'
      ? 7 * 86400000
      : interval === '1D'
        ? 86400000
        : parseInt(interval) * (interval.endsWith('h') ? 3600000 : 60000))
  );
}
export function resample(bars: readonly Bar[], interval: Interval): Bar[] {
  const result: Bar[] = [];
  for (const b of bars) {
    const time = bucket(b.time, interval),
      last = result.at(-1);
    if (last && last.time === time) {
      last.high = Math.max(last.high, b.high);
      last.low = Math.min(last.low, b.low);
      last.close = b.close;
      last.volume += b.volume;
    } else result.push({ ...b, time });
  }
  return result;
}
