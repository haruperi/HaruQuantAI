import { rolling, mean, type IndicatorDefinition } from './types';
export const SMA: IndicatorDefinition = {
  step: (b, c, i) => ({
    values: [i < c.period - 1 ? null : mean(b.slice(i - c.period + 1, i + 1).map((v) => v.close))],
    state: [],
  }),
  name: 'Simple Moving Average',
  pane: false,
  period: 20,
  calculate: (b, c) => [
    rolling(
      b.map((v) => v.close),
      c.period,
      mean,
    ),
  ],
};
