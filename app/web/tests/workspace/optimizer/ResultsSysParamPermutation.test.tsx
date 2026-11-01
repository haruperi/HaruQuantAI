import { describe, expect, it } from 'vitest';
import {
  ResultsSysParamPermutation,
  type SPPMetricSummaryRowData,
} from '../../../workspaces/optimizer/ResultsSysParamPermutation';

describe('ResultsSysParamPermutation', () => {
  it('exports ResultsSysParamPermutation component', () => {
    expect(ResultsSysParamPermutation).toBeDefined();
    expect(typeof ResultsSysParamPermutation).toBe('function');
  });

  it('declares valid SPPMetricSummaryRowData shape', () => {
    const row: SPPMetricSummaryRowData = {
      metric_id: 'NetProfit',
      label: 'Net Profit',
      original_value: 300.0,
      median_value: 300.0,
      mean_value: 300.0,
      std_dev: 158.11,
      percentile_5: 100.0,
      percentile_95: 500.0,
    };
    expect(row.median_value).toBe(300.0);
    expect(row.mean_value).toBe(300.0);
  });
});
