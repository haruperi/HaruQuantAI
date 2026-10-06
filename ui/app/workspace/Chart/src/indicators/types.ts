import type { Bar, Indicator } from '../types';
export type Series = (number | null)[];
export interface IndicatorStep {
  values: (number | null)[];
  state: number[];
}
export interface IndicatorDefinition {
  name: string;
  pane: boolean;
  period: number;
  calculate: (bars: readonly Bar[], config: Indicator) => Series[];
  step?: (
    bars: readonly Bar[],
    config: Indicator,
    index: number,
    state: readonly number[],
  ) => IndicatorStep;
}
export const rolling = (
  values: readonly number[],
  period: number,
  fn: (a: number[]) => number,
): Series =>
  values.map((_, i) => (i < period - 1 ? null : fn(values.slice(i - period + 1, i + 1))));
export const mean = (a: readonly number[]) => a.reduce((s, v) => s + v, 0) / a.length;
export function ema(values: readonly number[], period: number): Series {
  const out: Series = [];
  let prev: number | null = null;
  for (let i = 0; i < values.length; i++) {
    if (i < period - 1) {
      out.push(null);
      continue;
    }
    prev =
      prev === null
        ? mean(values.slice(0, period))
        : (values[i] * 2) / (period + 1) + prev * (1 - 2 / (period + 1));
    out.push(prev);
  }
  return out;
}
