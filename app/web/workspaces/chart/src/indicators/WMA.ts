import { rolling, type IndicatorDefinition } from './types';
export const WMA: IndicatorDefinition = {
  step: (b, c, i) => ({
    values: [
      i < c.period - 1
        ? null
        : b.slice(i - c.period + 1, i + 1).reduce((sum, v, j) => sum + v.close * (j + 1), 0) /
          ((c.period * (c.period + 1)) / 2),
    ],
    state: [],
  }),
  name: 'Weighted Moving Average',
  pane: false,
  period: 20,
  calculate: (b, c) => [
    rolling(
      b.map((v) => v.close),
      c.period,
      (a) => a.reduce((s, v, i) => s + v * (i + 1), 0) / ((c.period * (c.period + 1)) / 2),
    ),
  ],
};
