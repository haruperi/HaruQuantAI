import { ema, type IndicatorDefinition } from './types';
export const EMA: IndicatorDefinition = {
  step: (b, c, i, previous) => {
    const sum = (previous[0] ?? 0) + (i < c.period ? b[i].close : 0);
    const value =
      i < c.period - 1
        ? null
        : i === c.period - 1
          ? sum / c.period
          : (b[i].close * 2) / (c.period + 1) + (previous[1] ?? 0) * (1 - 2 / (c.period + 1));
    return { values: [value], state: [sum, value ?? 0] };
  },
  name: 'Exponential Moving Average',
  pane: false,
  period: 20,
  calculate: (b, c) => [
    ema(
      b.map((v) => v.close),
      c.period,
    ),
  ],
};
