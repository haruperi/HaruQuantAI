import type { Bar, Interval } from '../types';
import type { MarketDataAdapter } from './adapter';
import { symbolInfo } from './symbols';
import { marketOpen } from './sessions';
import { bucket, resample } from './resample';
const dayMs = 86400000;
export function seedOf(text: string): number {
  let h = 2166136261;
  for (const c of text) h = Math.imul(h ^ c.charCodeAt(0), 16777619);
  return h >>> 0;
}
export function random(seed: number): () => number {
  let s = seed;
  return () => {
    s += 0x6d2b79f5;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
export function dayBars(symbol: string, day: number): Bar[] {
  const rng = random(seedOf(symbol + day)),
    base = symbolInfo(symbol).base;
  const anchor = (n: number) =>
    Math.log(base) + 0.028 * Math.sin(n / 31 + (seedOf(symbol) % 97)) + 0.013 * Math.sin(n / 4);
  const open = anchor(day),
    target = anchor(day + 1),
    values = [0];
  let walk = 0;
  const volatility = 0.00013 * (1 + 2 * Math.abs(Math.sin(day / 9)));
  for (let i = 0; i < 1440; i++) {
    const normal = Math.sqrt(-2 * Math.log(Math.max(1e-9, rng()))) * Math.cos(2 * Math.PI * rng());
    walk += normal * volatility * (0.5 + Math.abs(Math.sin(i / 87)));
    values.push(walk);
  }
  const finish = walk,
    bars: Bar[] = [];
  for (let i = 0; i < 1440; i++) {
    const time = day * dayMs + i * 60000;
    const price = (j: number) =>
      Math.exp(open + ((target - open) * j) / 1440 + values[j] - (finish * j) / 1440);
    const o = price(i),
      c = price(i + 1),
      spread = base * volatility * (0.15 + rng() * 0.7);
    const b = {
      time,
      open: o,
      close: c,
      high: Math.max(o, c) + spread,
      low: Math.max(0.000001, Math.min(o, c) - spread),
      volume: Math.round(50 + rng() * 900),
    };
    if (marketOpen(symbol, time)) bars.push(b);
  }
  return bars;
}
export class MockFeed implements MarketDataAdapter {
  private cache = new Map<string, Bar[]>();
  constructor(private now: () => number = Date.now) {}
  private day(symbol: string, day: number): Bar[] {
    const key = symbol + day;
    let result = this.cache.get(key);
    if (!result) {
      result = dayBars(symbol, day);
      this.cache.set(key, result);
      if (this.cache.size > 40) this.cache.delete(this.cache.keys().next().value!);
    }
    return result;
  }
  async history(symbol: string, start: number, end: number, signal?: AbortSignal): Promise<Bar[]> {
    const result: Bar[] = [];
    for (let day = Math.floor(start / dayMs); day <= Math.floor(end / dayMs); day++) {
      if (signal?.aborted) throw new DOMException('Canceled', 'AbortError');
      for (const bar of this.day(symbol, day))
        if (bar.time >= start && bar.time <= end) result.push({ ...bar });
      if (day % 8 === 0) await new Promise<void>((resolve) => setTimeout(resolve, 0));
    }
    return result;
  }
  subscribe(
    symbol: string,
    interval: Interval,
    callback: (bar: Readonly<Bar>) => void,
  ): () => void {
    if (interval !== '1m') {
      const start = bucket(this.now(), interval);
      let base: Bar[] = [];
      for (let day = Math.floor(start / dayMs); day <= Math.floor(this.now() / dayMs); day++)
        base.push(...this.day(symbol, day).filter((b) => b.time >= start && b.time <= this.now()));
      return this.subscribe(symbol, '1m', (minute) => {
        if (base.at(-1)?.time === minute.time) base[base.length - 1] = { ...minute };
        else base.push({ ...minute });
        const current = bucket(minute.time, interval);
        if (base[0]?.time < current) base = base.filter((b) => b.time >= current);
        const bar = resample(base, interval).at(-1);
        if (bar) callback(Object.freeze(bar));
      });
    }
    let disposed = false;
    let timer: ReturnType<typeof setTimeout>;
    let previousTime = 0;
    let forming: Bar | undefined;
    const tick = () => {
      if (disposed) return;
      const now = this.now(),
        time = bucket(now, '1m');
      if (previousTime && time > previousTime) {
        for (let n = Math.floor(previousTime / dayMs); n <= Math.floor(time / dayMs); n++)
          for (const missed of this.day(symbol, n))
            if (missed.time >= previousTime && missed.time < time)
              callback(Object.freeze({ ...missed }));
        previousTime = time;
      }
      if (marketOpen(symbol, now)) {
        const day = this.day(symbol, Math.floor(now / dayMs)),
          model = day.find((b) => b.time === time);
        if (model) {
          if (!forming || forming.time !== time)
            forming = {
              time,
              open: model.open,
              high: model.open,
              low: model.open,
              close: model.open,
              volume: 0,
            };
          const f = (now - time) / 60000,
            noise =
              Math.sin(now / 1800 + seedOf(symbol)) *
              Math.sin(Math.PI * f) *
              Math.abs(model.high - model.low) *
              0.2;
          const close = model.open + (model.close - model.open) * f + noise;
          forming = {
            ...forming,
            high: Math.max(forming.high, close),
            low: Math.min(forming.low, close),
            close,
            volume: Math.round(model.volume * f),
          };
          callback(Object.freeze({ ...forming }));
          previousTime = time;
        }
      }
      timer = setTimeout(tick, 300);
    };
    tick();
    return () => {
      disposed = true;
      clearTimeout(timer);
    };
  }
}
