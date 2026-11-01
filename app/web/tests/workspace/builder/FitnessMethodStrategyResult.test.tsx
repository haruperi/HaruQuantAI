import { describe, expect, it } from 'vitest';
import {
  FitnessMethodStrategyResult,
  type FitnessCriterionItem,
} from '../../../workspaces/builder/FitnessMethodStrategyResult';

describe('FitnessMethodStrategyResult', () => {
  it('exports FitnessMethodStrategyResult component properly', () => {
    expect(FitnessMethodStrategyResult).toBeDefined();
    expect(typeof FitnessMethodStrategyResult).toBe('function');
  });

  it('declares valid default criterion shape', () => {
    const defaultCriterion: FitnessCriterionItem = {
      columnId: 'ReturnDDRatio',
      weight: 1.0,
      maximize: true,
      sampleType: 'InSample',
    };
    expect(defaultCriterion.columnId).toBe('ReturnDDRatio');
    expect(defaultCriterion.weight).toBe(1.0);
    expect(defaultCriterion.maximize).toBe(true);
    expect(defaultCriterion.sampleType).toBe('InSample');
  });
});
