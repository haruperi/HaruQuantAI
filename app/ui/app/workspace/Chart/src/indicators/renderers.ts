import type { Bar, Indicator } from '../types';
import { indicators } from './catalog';
import type { Series } from './types';

/** Per-instance checkpoints let a mutable forming bar be recomputed without double counting. */
export class IndicatorRuntime {
  private states: number[][] = [];
  private output: Series[] = [];
  private first: Bar | undefined;
  private length = 0;
  constructor(private config: Indicator) {}
  update(bars: readonly Bar[]): Series[] {
    const definition = indicators[this.config.kind];
    if (!definition.step) return definition.calculate(bars, this.config);
    const reuse =
      this.first === bars[0] && bars.length >= this.length && bars.length <= this.length + 1;
    const start = reuse ? Math.max(0, this.length - 1) : 0;
    if (!reuse) {
      this.states = [];
      this.output = [];
    }
    for (let i = start; i < bars.length; i++) {
      const result = definition.step(bars, this.config, i, this.states[i - 1] ?? []);
      this.states[i] = result.state;
      result.values.forEach((v, line) => {
        (this.output[line] ??= [])[i] = v;
      });
    }
    this.first = bars[0];
    this.length = bars.length;
    return this.output;
  }
}
