import type { IndicatorDefinition, Series } from './types';
export const RSI: IndicatorDefinition = {
  step: (b, c, i, previous) => {
    if (!i) return { values: [null], state: [0, 0] };
    const d = b[i].close - b[i - 1].close,
      g = Math.max(0, d),
      l = Math.max(0, -d);
    const gain =
        i <= c.period
          ? (previous[0] ?? 0) + g / c.period
          : ((previous[0] ?? 0) * (c.period - 1) + g) / c.period,
      loss =
        i <= c.period
          ? (previous[1] ?? 0) + l / c.period
          : ((previous[1] ?? 0) * (c.period - 1) + l) / c.period;
    return {
      values: [
        i < c.period
          ? null
          : gain === 0 && loss === 0
            ? 50
            : loss === 0
              ? 100
              : 100 - 100 / (1 + gain / loss),
      ],
      state: [gain, loss],
    };
  },
  name: 'Relative Strength Index',
  pane: true,
  period: 14,
  calculate: (b, c) => {
    let gain = 0,
      loss = 0;
    const result: Series = b.map(() => null);
    for (let i = 1; i < b.length; i++) {
      const d = b[i].close - b[i - 1].close,
        g = Math.max(0, d),
        l = Math.max(0, -d);
      if (i <= c.period) {
        gain += g / c.period;
        loss += l / c.period;
      } else {
        gain = (gain * (c.period - 1) + g) / c.period;
        loss = (loss * (c.period - 1) + l) / c.period;
      }
      if (i >= c.period)
        result[i] =
          gain === 0 && loss === 0 ? 50 : loss === 0 ? 100 : 100 - 100 / (1 + gain / loss);
    }
    return [result];
  },
};
