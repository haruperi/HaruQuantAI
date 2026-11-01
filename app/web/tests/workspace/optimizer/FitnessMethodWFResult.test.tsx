import { describe, expect, it } from 'vitest';
import {
  FitnessMethodWFResult,
  type WFFitnessCriterion,
} from '../../../workspaces/optimizer/FitnessMethodWFResult';

describe('FitnessMethodWFResult', () => {
  it('exports FitnessMethodWFResult component', () => {
    expect(FitnessMethodWFResult).toBeDefined();
    expect(typeof FitnessMethodWFResult).toBe('function');
  });

  it('declares valid WFFitnessCriterion shape', () => {
    const criterion: WFFitnessCriterion = {
      metric: 'NetProfit',
      weight: 1.0,
      maximize: true,
      target_value: 500.0,
    };
    expect(criterion.metric).toBe('NetProfit');
    expect(criterion.weight).toBe(1.0);
    expect(criterion.target_value).toBe(500.0);
  });
});
