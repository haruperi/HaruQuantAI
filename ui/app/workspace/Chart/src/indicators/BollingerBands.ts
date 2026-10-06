import { rolling, mean, type IndicatorDefinition } from './types';
export const BollingerBands: IndicatorDefinition = {
  step: (b, c, i) => {
    if (i < c.period - 1) return { values: [null, null, null], state: [] };
    const values = b.slice(i - c.period + 1, i + 1).map((v) => v.close),
      m = mean(values),
      sd = Math.sqrt(mean(values.map((v) => (v - m) ** 2)));
    return { values: [m, m + c.deviation * sd, m - c.deviation * sd], state: [] };
  },
  name: 'Bollinger Bands',
  pane: false,
  period: 20,
  calculate: (b, c) => {
    const v = b.map((x) => x.close),
      m = rolling(v, c.period, mean),
      sd = rolling(v, c.period, (a) => Math.sqrt(mean(a.map((x) => (x - mean(a)) ** 2))));
    return [
      m,
      m.map((x, i) => (x === null ? null : x + c.deviation * sd[i]!)),
      m.map((x, i) => (x === null ? null : x - c.deviation * sd[i]!)),
    ];
  },
};
