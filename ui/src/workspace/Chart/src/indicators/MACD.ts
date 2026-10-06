import { ema, type IndicatorDefinition } from './types';
export const MACD: IndicatorDefinition = {
  step: (b, c, i, p) => {
    const close = b[i].close,
      fastSum = (p[0] ?? 0) + (i < c.period ? close : 0),
      slowSum = (p[1] ?? 0) + (i < c.slow ? close : 0);
    const fast =
        i < c.period - 1
          ? 0
          : i === c.period - 1
            ? fastSum / c.period
            : (close * 2) / (c.period + 1) + (p[2] ?? 0) * (1 - 2 / (c.period + 1)),
      slow =
        i < c.slow - 1
          ? 0
          : i === c.slow - 1
            ? slowSum / c.slow
            : (close * 2) / (c.slow + 1) + (p[3] ?? 0) * (1 - 2 / (c.slow + 1));
    const line = i < Math.max(c.period, c.slow) - 1 ? null : fast - slow,
      count = (p[6] ?? 0) + (line === null ? 0 : 1),
      sum = (p[4] ?? 0) + (line !== null && count <= c.signal ? line : 0),
      signal =
        count < c.signal
          ? null
          : count === c.signal
            ? sum / c.signal
            : (line! * 2) / (c.signal + 1) + (p[5] ?? 0) * (1 - 2 / (c.signal + 1));
    return {
      values: [line, signal, line === null || signal === null ? null : line - signal],
      state: [fastSum, slowSum, fast, slow, sum, signal ?? 0, count],
    };
  },
  name: 'MACD',
  pane: true,
  period: 12,
  calculate: (b, c) => {
    const close = b.map((x) => x.close),
      fast = ema(close, c.period),
      slow = ema(close, c.slow);
    const line = fast.map((v, i) => (v === null || slow[i] === null ? null : v - slow[i]!));
    const start = line.findIndex((v) => v !== null);
    const signal =
      start < 0
        ? line.map(() => null)
        : [
            ...Array<null>(start).fill(null),
            ...ema(
              line.slice(start).map((v) => v!),
              c.signal,
            ),
          ];
    return [
      line,
      signal,
      line.map((v, i) => (v === null || signal[i] === null ? null : v - signal[i]!)),
    ];
  },
};
