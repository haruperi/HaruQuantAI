import { it, expect } from 'vitest';
import { indicators } from '../../../../app/workspace/Chart/src/indicators/catalog';
import { indicatorIds, type Bar, type Indicator } from '../../../../app/workspace/Chart/src/types';
import { IndicatorRuntime } from '../../../../app/workspace/Chart/src/indicators/renderers';
const config = (kind: Indicator['kind']): Indicator => ({
  id: kind,
  kind,
  period: 3,
  slow: 5,
  signal: 2,
  deviation: 2,
  color: '#fff',
  width: 1,
  opacity: 1,
});
const bars: Bar[] = Array.from({ length: 20 }, (_, i) => ({
  time: i * 60000,
  open: i + 1,
  high: i + 2,
  low: i,
  close: i + 1,
  volume: 10,
}));
it('incremental checkpoints match full calculations after updates, append and replay', () => {
  for (const id of indicatorIds) {
    const runtime = new IndicatorRuntime(config(id));
    const input = bars.map((b) => ({ ...b }));
    const check = () => {
      const output = runtime.update(input),
        expected = indicators[id].calculate(input, config(id));
      expected.forEach((line, n) =>
        line.forEach((v, i) => {
          if (v === null) expect(output[n][i]).toBeNull();
          else expect(output[n][i]).toBeCloseTo(v, 9);
        }),
      );
    };
    check();
    input[input.length - 1] = { ...input.at(-1)!, close: 18.5, volume: 25 };
    check();
    input.push({ ...input.at(-1)!, time: 1200000, close: 20 });
    check();
    input.splice(10);
    check();
  }
});
it('matches hand-calculated averages, deviation, RSI and ATR', () => {
  expect(indicators.SMA.calculate(bars, config('SMA'))[0].slice(0, 4)).toEqual([null, null, 2, 3]);
  expect(indicators.EMA.calculate(bars, config('EMA'))[0][3]).toBe(3);
  expect(indicators.WMA.calculate(bars, config('WMA'))[0][2]).toBeCloseTo(14 / 6);
  expect(indicators.BollingerBands.calculate(bars, config('BollingerBands'))[1][2]).toBeCloseTo(
    2 + 2 * Math.sqrt(2 / 3),
  );
  expect(indicators.RSI.calculate(bars, config('RSI'))[0][3]).toBe(100);
  expect(indicators.ATR.calculate(bars, config('ATR'))[0][2]).toBe(2);
});
it('all indicators handle empty, warmup and flat prices without NaN', () => {
  for (const id of indicatorIds) {
    expect(indicators[id].calculate([], config(id)).every((a) => a.length === 0)).toBe(true);
    const flat = bars.map((b) => ({ ...b, open: 10, high: 10, low: 10, close: 10 }));
    for (const series of indicators[id].calculate(flat, config(id)))
      for (const value of series) expect(value === null || Number.isFinite(value)).toBe(true);
  }
});
it('VWAP resets per UTC day and MACD does not leak future values', () => {
  const b = [
    { ...bars[0], time: 0, high: 10, low: 10, close: 10 },
    { ...bars[0], time: 86400000, high: 20, low: 20, close: 20 },
  ];
  expect(indicators.VWAP.calculate(b, config('VWAP'))[0]).toEqual([10, 20]);
  expect(indicators.MACD.calculate(bars.slice(0, 10), config('MACD'))).toEqual(
    indicators.MACD.calculate(bars, config('MACD')).map((line) => line.slice(0, 10)),
  );
});
