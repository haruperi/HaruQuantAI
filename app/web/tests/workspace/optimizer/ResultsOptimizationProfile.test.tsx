import { describe, expect, it } from 'vitest';
import {
  ResultsOptimizationProfile,
  type OptimizationProfileChartGridData,
} from '../../../workspaces/optimizer/ResultsOptimizationProfile';

describe('ResultsOptimizationProfile', () => {
  it('exports ResultsOptimizationProfile component', () => {
    expect(ResultsOptimizationProfile).toBeDefined();
    expect(typeof ResultsOptimizationProfile).toBe('function');
  });

  it('declares valid grid shape', () => {
    const grid: OptimizationProfileChartGridData = {
      param_x: 'Period',
      param_y: 'Multiplier',
      metric: 'NetProfit',
      x_values: [10, 20],
      y_values: [1, 2],
      z_matrix: [
        [100, 150],
        [120, 180],
      ],
    };
    expect(grid.x_values).toHaveLength(2);
    expect(grid.z_matrix[0][0]).toBe(100);
  });
});
