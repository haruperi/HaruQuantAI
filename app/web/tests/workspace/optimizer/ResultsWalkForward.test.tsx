import { describe, expect, it } from 'vitest';
import {
  ResultsWalkForward,
  type WFWindowRowData,
} from '../../../workspaces/optimizer/ResultsWalkForward';

describe('ResultsWalkForward', () => {
  it('exports ResultsWalkForward component', () => {
    expect(ResultsWalkForward).toBeDefined();
    expect(typeof ResultsWalkForward).toBe('function');
  });

  it('declares valid WFWindowRowData shape', () => {
    const windowRow: WFWindowRowData = {
      window_index: 1,
      is_start: '2020-01-01',
      is_end: '2020-12-31',
      oos_start: '2021-01-01',
      oos_end: '2021-03-31',
      best_params: { Period: 22 },
      is_net_profit: 750.0,
      oos_net_profit: 180.0,
      passed: true,
    };
    expect(windowRow.window_index).toBe(1);
    expect(windowRow.best_params.Period).toBe(22);
    expect(windowRow.passed).toBe(true);
  });
});
