import type { IndicatorDefinition, Series } from './types';
export const ATR: IndicatorDefinition = {
  step: (b, c, i, previous) => {
    const v = b[i],
      close = b[i - 1]?.close ?? v.open,
      tr = Math.max(v.high - v.low, Math.abs(v.high - close), Math.abs(v.low - close)),
      atr =
        i < c.period
          ? (previous[0] ?? 0) + tr / c.period
          : ((previous[0] ?? 0) * (c.period - 1) + tr) / c.period;
    return { values: [i < c.period - 1 ? null : atr], state: [atr] };
  },
  name: 'Average True Range',
  pane: true,
  period: 14,
  calculate: (b, c) => {
    let atr = 0;
    const a: Series = [];
    for (let i = 0; i < b.length; i++) {
      const v = b[i],
        previous = b[i - 1]?.close ?? v.open,
        tr = Math.max(v.high - v.low, Math.abs(v.high - previous), Math.abs(v.low - previous));
      if (i < c.period) atr += tr / c.period;
      else atr = (atr * (c.period - 1) + tr) / c.period;
      a.push(i < c.period - 1 ? null : atr);
    }
    return [a];
  },
};
