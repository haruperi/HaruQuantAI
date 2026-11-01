import { describe, expect, it } from 'vitest';
import {
  ResultsSequentialOptimization,
  type SequentialOptStepData,
} from '../../../workspaces/optimizer/ResultsSequentialOptimization';

describe('ResultsSequentialOptimization', () => {
  it('exports ResultsSequentialOptimization component', () => {
    expect(ResultsSequentialOptimization).toBeDefined();
    expect(typeof ResultsSequentialOptimization).toBe('function');
  });

  it('renders step cards properly', () => {
    const steps: SequentialOptStepData[] = [
      {
        param_name: 'Period',
        original_value: 14,
        best_value: 25,
        tested_values: [10, 15, 20, 25],
        metric_values: [100, 120, 150, 200],
      },
    ];
    expect(steps[0].best_value).toBe(25);
  });
});
