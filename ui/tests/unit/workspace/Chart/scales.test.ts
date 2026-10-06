import { describe, it, expect } from 'vitest';
import {
  priceToY,
  yToPrice,
  zoomAt,
  xToTime,
  niceTicks,
} from '../../../../src/workspace/Chart/src/engine/scales';
describe('chart coordinates', () => {
  it('round trips all price scales and direction', () => {
    for (const mode of ['linear', 'log', 'percent', 'indexed'] as const)
      for (const reverse of [false, true])
        expect(
          yToPrice(
            priceToY(125, 100, 200, 500, mode, reverse, 110),
            100,
            200,
            500,
            mode,
            reverse,
            110,
          ),
        ).toBeCloseTo(125, 9);
  });
  it('anchors zoom and clamps spacing', () => {
    const next = zoomAt(300, 5, -100, 100);
    expect(next.spacing).toBe(50);
    expect(xToTime(300, next.spacing, next.offset)).toBe(80);
  });
  it('uses nice ticks', () => expect(niceTicks(101, 199, 5)).toEqual([120, 140, 160, 180]));
});
