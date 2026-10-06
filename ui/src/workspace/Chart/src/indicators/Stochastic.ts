import { mean, type IndicatorDefinition, type Series } from './types';
export const Stochastic: IndicatorDefinition = {
  step: (b, c, i, previous) => {
    if (i < c.period - 1) return { values: [null, null], state: [] };
    const window = b.slice(i - c.period + 1, i + 1),
      low = Math.min(...window.map((v) => v.low)),
      high = Math.max(...window.map((v) => v.high)),
      k = high === low ? 50 : ((b[i].close - low) / (high - low)) * 100,
      state = [...previous, k].slice(-c.signal);
    return { values: [k, state.length < c.signal ? null : mean(state)], state };
  },
  name: 'Stochastic Oscillator',
  pane: true,
  period: 14,
  calculate: (b, c) => {
    const k: Series = b.map((v, i) => {
      if (i < c.period - 1) return null;
      const w = b.slice(i - c.period + 1, i + 1),
        low = Math.min(...w.map((v) => v.low)),
        high = Math.max(...w.map((v) => v.high));
      return high === low ? 50 : ((v.close - low) / (high - low)) * 100;
    });
    return [
      k,
      k.map((_, i) =>
        i < c.period + c.signal - 2 ? null : mean(k.slice(i - c.signal + 1, i + 1).map((v) => v!)),
      ),
    ];
  },
};
