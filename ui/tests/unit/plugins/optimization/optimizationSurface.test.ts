import { describe, expect, it } from 'vitest';
import {
  generateOptimizationGrid,
  projectCoordinate,
} from '../../../../app/plugins/optimization/ResultsOptimizationProfile/optimizationSurfaceLogic';

describe('3D Optimization Surface & Plateau Stability (FEAT-UI-3DSURFACE)', () => {
  it('generates a 15x15 parameter optimization grid with 225 surface points', () => {
    const result = generateOptimizationGrid('FastPeriod', 'SlowPeriod', 'Net Profit', 15);

    expect(result.points).toHaveLength(225);
    expect(result.grid).toHaveLength(15);
    expect(result.grid[0]).toHaveLength(15);

    const firstPt = result.points[0];
    expect(firstPt.xParam).toBe('FastPeriod');
    expect(firstPt.yParam).toBe('SlowPeriod');
    expect(firstPt.zMetric).toBe('Net Profit');
    expect(typeof firstPt.x).toBe('number');
    expect(typeof firstPt.y).toBe('number');
    expect(typeof firstPt.z).toBe('number');
  });

  it('computes % of profitable optimizations conforming to SQX rule checks', () => {
    const result = generateOptimizationGrid('FastPeriod', 'SlowPeriod', 'Net Profit', 15);
    const { stats } = result;

    expect(stats.totalSimulations).toBe(225);
    expect(stats.profitableCount + stats.losingCount + stats.zeroCount).toBe(225);

    const sumPct = stats.profitablePct + stats.losingPct + stats.zeroPct;
    expect(Math.round(sumPct)).toBe(100);

    // Verify >60% profitable check rule
    expect(typeof stats.isPass).toBe('boolean');
    expect(stats.isPass).toBe(stats.profitablePct >= 60);
  });

  it('identifies robust parameter plateau clusters with stability scores', () => {
    const result = generateOptimizationGrid('FastPeriod', 'SlowPeriod', 'Net Profit', 15);

    expect(result.clusters.length).toBeGreaterThanOrEqual(1);
    const primary = result.clusters[0];

    expect(primary.id).toBe('cluster-1');
    expect(primary.stabilityScore).toBeGreaterThanOrEqual(80);
    expect(primary.profitablePercentage).toBeGreaterThanOrEqual(90);
    expect(primary.rangeX[0]).toBeLessThan(primary.rangeX[1]);
    expect(primary.rangeY[0]).toBeLessThan(primary.rangeY[1]);
  });

  it('scales values appropriately across different Z-metrics (Profit Factor, Sharpe Ratio, Return / DD)', () => {
    const pfResult = generateOptimizationGrid('ATRPeriod', 'StopLoss', 'Profit Factor', 10);
    expect(pfResult.points.every((p) => p.z >= 0)).toBe(true);

    const sharpeResult = generateOptimizationGrid('ATRPeriod', 'StopLoss', 'Sharpe Ratio', 10);
    expect(sharpeResult.points.some((p) => p.z !== 0)).toBe(true);

    const rddResult = generateOptimizationGrid('ATRPeriod', 'StopLoss', 'Return / DD', 10);
    expect(rddResult.points.every((p) => p.z >= 0)).toBe(true);
  });

  it('projects 3D coordinates into 2D canvas space with depth ordering', () => {
    const width = 800;
    const height = 500;
    const gridSize = 15;

    const proj1 = projectCoordinate(0, 7, 100, gridSize, 0, 1000, 35, 45, 1.0, width, height);
    const proj2 = projectCoordinate(14, 7, 900, gridSize, 0, 1000, 35, 45, 1.0, width, height);

    expect(typeof proj1.screenX).toBe('number');
    expect(typeof proj1.screenY).toBe('number');
    expect(typeof proj1.depth).toBe('number');

    expect(typeof proj2.screenX).toBe('number');
    expect(typeof proj2.screenY).toBe('number');
    expect(typeof proj2.depth).toBe('number');

    // Points with different X indices must have distinct screenX and depths
    expect(proj1.screenX).not.toBe(proj2.screenX);
    expect(proj1.depth).not.toBe(proj2.depth);
  });
});
