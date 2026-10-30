import type { IndicatorDefinition } from './types';
export const VWAP: IndicatorDefinition = {
  step: (b, _c, i, previous) => {
    const v = b[i],
      day = Math.floor(v.time / 86400000),
      total = (previous[0] === day ? previous[1] : 0) + ((v.high + v.low + v.close) / 3) * v.volume,
      volume = (previous[0] === day ? previous[2] : 0) + v.volume;
    return { values: [volume ? total / volume : null], state: [day, total, volume] };
  },
  name: 'Volume Weighted Average Price',
  pane: false,
  period: 1,
  calculate: (b) => {
    let total = 0,
      volume = 0,
      day = -1;
    return [
      b.map((x) => {
        const d = Math.floor(x.time / 86400000);
        if (d !== day) {
          day = d;
          total = 0;
          volume = 0;
        }
        total += ((x.high + x.low + x.close) / 3) * x.volume;
        volume += x.volume;
        return volume ? total / volume : null;
      }),
    ];
  },
};
